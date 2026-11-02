"""Shared view for the approval forms (품의서, 결과보고서).

head, 결재란, review matching, whose turn, and HTML/PDF output live here once.
Rule words (roles, approval status, document number kinds, merge notes) come from rules.json.
Approve and reject come from Origin pull request reviews, read with the origin CLI
already configured in the environment. No token is read or stored.
Nothing here sends a review or a merge.
"""
import argparse, html, json, os, subprocess, sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "report-format", "template")
REPORT_CSS = os.path.join(TEMPLATE, "report.css")
APPROVAL_CSS = os.path.join(HERE, "approval.css")
with open(os.path.join(HERE, "rules.json"), encoding="utf-8") as _f:
    RULES = json.load(_f)

DRAFT, REVIEW, FINAL = (RULES["roles"][k] for k in ("draft", "review", "final"))
ROLES = (DRAFT, REVIEW, FINAL)
MARKS = tuple(RULES["marks"])
RESULTS = dict(RULES["reviewResults"])
# 결재 상태. 판정(✔/▲/✖)과 다른 개념이며 판정은 make_report.VERDICTS에 있다.
APPROVAL_STATUS = dict(RULES["approvalStatus"])
DOC_KINDS = dict(RULES["docNumber"]["kinds"])
STEP_KEYS = {"role", "title", "name", "date", "mark", "reviewer"}
KST = timezone(timedelta(hours=9))

# Warning kinds named in rules.json warnings (structural, simple, text) use the keys there.
# Any structural warning shows '승인' as approvalStatus needs-check. Simple and
# unclassified warnings leave the status alone. Kinds rules.json gives no text for keep their wording here.
STRUCTURAL = frozenset(RULES["warnings"]["structural"])
CODE_TEXTS = {
    "formRole": "이 서식의 결재선에는 {role} 칸을 두지 않습니다. 파일에 {count}칸이 있습니다.",
    "reviewsOver": "검토 칸이 {count}칸입니다. 규칙은 {limit}칸까지입니다.",
    "reviewAfterFinal": "검토 칸이 결재 칸 뒤에 있습니다. 규칙은 기안-(검토)-결재 순서입니다.",
    "lastNotFinal": "마지막 칸이 {role}입니다. 규칙은 마지막 칸이 결재입니다.",
    "draftMark": "기안 칸에 {mark} 표시가 있습니다. 규칙은 기안 칸에 전결·대결을 적지 않습니다.",
    "draftJeongyeol": "기안 칸에 전결 표시가 있습니다. 규칙은 기안 칸에 전결·대결을 적지 않습니다. 이 표시로 사선을 긋지 않습니다.",
    "draftReviewer": "기안 칸에 reviewer가 있습니다. 규칙은 기안자를 검토자로 요청하지 않습니다.",
    "dateOnNonDraft": "{name} 칸에 date가 있습니다. 규칙은 기안 칸에만 날짜를 적습니다. 이 칸 날짜는 Origin 리뷰 시각을 씁니다.",
    "outsideReview": "리뷰한 사람({who})이 결재선에 없어 결재란에 찍지 않았습니다. 전결이면 그 사람 칸을 두고 mark를 전결로 적습니다.",
    "mergerOutside": "머지한 사람({who})이 결재선에 없습니다. 규칙은 마지막 칸의 사람이 머지합니다.",
    "mergerUnread": "머지한 사람을 Origin 기록(mergedBy)에서 읽지 못했습니다.",
    "mergerSeat": "{name} 칸은 {where}인데 그 사람이 머지했습니다. 규칙은 마지막 칸의 사람이 머지합니다.",
}
WARNING_TEXTS = {**CODE_TEXTS, **RULES["warnings"]["text"]}
# Merge notes not in rules.json mergeNote yet. A merge into a COLLECT_BRANCH branch is 취합, not an approval.
CODE_NOTES = {
    "execution": "집행: {who} {month}/{day}",
    "collect": "취합: {who} {month}/{day} ({branch})",
}
COLLECT_BRANCH = "stage/"


class Finding(str):
    """A warning text that keeps its kind. Callers can still treat it as plain text."""
    kind = None


def warn(kind, **fields):
    finding = Finding(WARNING_TEXTS[kind].format(**fields))
    finding.kind = kind
    return finding


def structure_warnings(warnings):
    return [w for w in warnings if w.kind in STRUCTURAL]


def fail(message):
    raise SystemExit(message)


def esc(value):
    return html.escape(value, quote=False)


def parse_date(value, label):
    if not isinstance(value, str):
        fail(label + "은 YYYY-MM-DD여야 합니다.")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        fail(label + "은 YYYY-MM-DD여야 합니다.")


def has_text(obj, key):
    value = obj.get(key)
    return isinstance(value, str) and bool(value.strip())


def check_line(approval):
    """Refuse only a broken line (shape, unknown role, first box not 기안). Rule breaks are line_warnings().

    role is optional. A line with no role on any box has only title and name required, the first box is 기안,
    and role checks are skipped. Once any box has a role, every box needs one."""
    steps = approval.get("steps") if isinstance(approval, dict) else None
    if set(approval or {}) != {"steps"} or not isinstance(steps, list) or not steps:
        fail("approval.steps에 결재선을 순서대로 둡니다.")
    roles = any(isinstance(step, dict) and "role" in step for step in steps)
    kinds = []
    for i, step in enumerate(steps):
        if not isinstance(step, dict) or set(step) - STEP_KEYS:
            fail("결재 칸은 role, title, name과 date, mark, reviewer만 둡니다.")
        if (roles and step.get("role") not in ROLES) or not has_text(step, "title") or not has_text(step, "name"):
            fail("각 칸에는 role, title, name이 있어야 합니다." if roles else "각 칸에는 title, name이 있어야 합니다.")
        kinds.append(step["role"] if roles else DRAFT if i == 0 else None)
        if step.get("mark") is not None and step["mark"] not in MARKS:
            fail("mark는 전결 또는 대결만 적을 수 있습니다.")
        if kinds[-1] == DRAFT:
            parse_date(step.get("date"), "기안 날짜")
    if kinds[0] != DRAFT or kinds.count(DRAFT) != 1:
        fail("결재선의 첫 칸만 기안입니다.")
    return steps


def line_warnings(steps, roles=ROLES):
    """결재 규칙(운영규칙 1.1)과 서식별 칸(roles) 위반 문구. 렌더는 막지 않는다. 위반 점검 자체는 품질 검사 몫이다.
    role이 없는 결재선은 이 규칙으로 보지 않는다."""
    if not any("role" in step for step in steps):
        return []
    kinds = [step["role"] for step in steps]
    out = [warn("formRole", role=role, count=kinds.count(role)) for role in ROLES if role in kinds and role not in roles]
    reviews = kinds.count(REVIEW)
    if reviews > RULES["line"]["maxReviews"]:
        out.append(warn("reviewsOver", count=reviews, limit=RULES["line"]["maxReviews"]))
    if FINAL in kinds and REVIEW in kinds[kinds.index(FINAL):]:
        out.append(warn("reviewAfterFinal"))
    if RULES["line"]["lastIsFinal"] and kinds[-1] != FINAL:
        out.append(warn("lastNotFinal", role=kinds[-1]))
    if FINAL not in kinds:
        out.append(warn("noFinal"))
    jeon = [s for s in steps if s["role"] == FINAL and s.get("mark") == "전결"]
    if len(jeon) > 1:
        out.append(warn("jeongyeolCount", count=len(jeon), name=jeon[0]["name"]))
    for step in steps:
        if step["role"] == REVIEW and step.get("mark") == "전결":
            out.append(warn("jeongyeolOnReview", name=step["name"]))
        if step["role"] == DRAFT:
            if step.get("mark"):
                out.append(warn("draftJeongyeol") if step["mark"] == "전결" else warn("draftMark", mark=step["mark"]))
            if "reviewer" in step:
                out.append(warn("draftReviewer"))
        elif "date" in step:
            out.append(warn("dateOnNonDraft", name=step["name"]))
    drafter = set(step_keys(steps[0]))
    seats = [step for step in steps if step["role"] != DRAFT]
    for n, step in enumerate(seats):
        keys = set(step_keys(step))
        if keys & drafter:
            out.append(warn("drafterInOtherBox", name=steps[0]["name"], box=step["title"]))
        if any(keys & set(step_keys(seat)) for seat in seats[:n]):
            continue
        same = 1 + sum(1 for seat in seats[n + 1:] if keys & set(step_keys(seat)))
        if same > 1:
            out.append(warn("samePersonInTwoBoxes", name=step["name"], count=same))
    return out


def doc_number(form, date, pr):
    """{문서종류}-연도-PR번호 4자리. 예: 품의-2026-0042. PR 번호가 아직 없으면 미부여."""
    tail = f"{int(pr):04d}" if pr else RULES["docNumber"]["unassigned"]
    return f"{DOC_KINDS[form]}-{date[:4]}-{tail}"


def stamp_date(submitted_at):
    text = submitted_at.replace("Z", "+00:00")
    return datetime.fromisoformat(text).astimezone(KST).strftime("%Y-%m-%d")


def merge_note(merged_at):
    if not merged_at:
        return RULES["mergeNote"]["pending"]
    month, day = stamp_date(merged_at).split("-")[1:]
    return RULES["mergeNote"]["merged"].format(month=month, day=day)


def _origin_view(pr, fields):
    proc = subprocess.run(
        ["origin", "pr", "view", str(pr), "--json", fields],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        fail(proc.stderr.strip() or "origin pr view failed")
    return json.loads(proc.stdout)


def origin_reviews(pr):
    reviews = _origin_view(pr, "reviews").get("reviews")
    if not isinstance(reviews, list):
        fail("origin 리뷰 목록을 읽지 못했습니다.")
    return reviews


def origin_pr(pr):
    data = _origin_view(pr, "url,mergedAt,mergedBy,baseRefName")
    return {"url": data.get("url"), "merge": {key: data.get(key) for key in ("mergedAt", "mergedBy", "baseRefName")}}


def actor_keys(actor):
    """Identifiers of an Origin actor: mergedBy {id, displayName} or a review author {user: {...}}."""
    actor = actor if isinstance(actor, dict) else {}
    keys = []
    for part in (actor, *(actor.get(kind) for kind in ("user", "app", "serviceAccount"))):
        part = part if isinstance(part, dict) else {}
        for field in ("displayName", "email", "handle", "id"):
            value = part.get(field)
            if isinstance(value, str) and value.strip():
                keys.append(value.strip())
    return keys


def review_keys(review):
    name = review.get("name")
    keys = [name.strip()] if isinstance(name, str) and name.strip() else []
    return keys + actor_keys(review.get("author"))


def step_keys(step):
    keys = [step["name"].strip()]
    reviewer = step.get("reviewer")
    if isinstance(reviewer, str) and reviewer.strip():
        keys.append(reviewer.strip())
    return keys


def jeon_index(steps):
    """Index of the first 결재 step explicitly marked 전결, or None. Never guessed.
    전결 on a 기안 or 검토 box has no effect: no slash, the 결재 box stays a seat.
    A box without role: any box but the first."""
    for i, step in enumerate(steps):
        if (step["role"] == FINAL if "role" in step else i) and step.get("mark") == "전결":
            return i
    return None


def slashed_indexes(steps):
    """Boxes to the right of 전결 are the higher seats. Draw a slash there."""
    cut = jeon_index(steps)
    if cut is None:
        return set()
    return set(range(cut + 1, len(steps)))


MERGER_NOTE = RULES["mergeNote"]["merger"]
MERGER_UNKNOWN = RULES["mergeNote"]["mergerUnknown"]


def merge_record(steps, merge):
    """Which box carries the merge note, and the note. The merger comes from Origin mergedBy, never guessed.

    The deciding box is the 결재 box marked 전결, or the last box when there is none. A 전결 box decides; it does not
    merge. Merging into main is the last box's person's.
    Not merged: 'merge 대기' under the deciding box.
    Merged by the last box's person with no 전결: '10/31 merge' under that box.
    Merged by the last box's person when there is 전결: '집행: 이름 10/31' under the 전결 box.
    Merged by another slashed box's person: '머지: 이름 10/31' under the 전결 box (a slashed box shows no text), warning.
    Merged into a stage/* branch: '취합: 이름 10/31 (stage/…)' with index None, drawn outside the 결재란.
    Anyone else, or no mergedBy: '머지: 이름 10/31' under that person's box (or the deciding box), with a warning.
    """
    merge = merge if isinstance(merge, dict) else {}
    cut = jeon_index(steps)
    decide = len(steps) - 1 if cut is None else cut
    merged_at, merged_by, base = merge.get("mergedAt"), merge.get("mergedBy"), merge.get("baseRefName")
    if not merged_at:
        return {"index": decide, "text": RULES["mergeNote"]["pending"], "by": None, "warnings": []}
    month, day = stamp_date(merged_at).split("-")[1:]
    keys = set(actor_keys(merged_by))
    found = next((i for i, step in enumerate(steps) if keys & set(step_keys(step))), None)
    shown = (actor_keys(merged_by) or [MERGER_UNKNOWN])[0] if found is None else steps[found]["name"]
    if isinstance(base, str) and base.startswith(COLLECT_BRANCH):
        return {"index": None, "text": CODE_NOTES["collect"].format(who=shown, month=month, day=day, branch=base),
                "by": shown, "warnings": []}
    if found is None:
        warning = warn("mergerOutside", who=shown) if keys else warn("mergerUnread")
        return {"index": decide, "text": MERGER_NOTE.format(who=shown, month=month, day=day), "by": shown,
                "warnings": [warning]}
    if found == decide and cut is None:
        return {"index": found, "text": merge_note(merged_at), "by": shown, "warnings": []}
    slashed = cut is not None and found > cut
    if slashed and found == len(steps) - 1:
        return {"index": cut, "text": CODE_NOTES["execution"].format(who=shown, month=month, day=day), "by": shown,
                "warnings": []}
    where = "전결 칸" if found == cut else "사선 칸" if slashed else "마지막 칸이 아닌 칸"
    return {"index": cut if slashed else found, "text": MERGER_NOTE.format(who=shown, month=month, day=day),
            "by": shown, "warnings": [warn("mergerSeat", name=shown, where=where)]}


def check_sample_merge(doc):
    """sampleMerge: the offline stand-in for Origin's mergedAt / mergedBy / baseRefName, like sampleReviews."""
    if "sampleMerge" not in doc:
        return
    merge = doc["sampleMerge"]
    if (not isinstance(merge, dict) or set(merge) - {"mergedAt", "mergedBy", "baseRefName"}
            or not isinstance(merge.get("mergedAt"), str)):
        fail("sampleMerge는 {mergedAt, mergedBy, baseRefName} 객체여야 합니다.")
    try:
        stamp_date(merge["mergedAt"])
    except ValueError:
        fail("sampleMerge.mergedAt은 ISO 시각(예: 2026-11-01T03:00:00Z)이어야 합니다.")
    if "mergedBy" in merge and not isinstance(merge["mergedBy"], dict):
        fail("sampleMerge.mergedBy는 {displayName, id} 객체여야 합니다.")
    if "baseRefName" in merge and not isinstance(merge["baseRefName"], str):
        fail("sampleMerge.baseRefName은 브랜치 이름(예: main)이어야 합니다.")


def linked_reviews(steps, reviews):
    """(box index, review) for every approve / request_changes that counts, oldest first. Comments, dismissed reviews,
    and the drafter's own reviews do not count. A review goes to the first live box of that person only."""
    slashed = slashed_indexes(steps)
    drafter = set(step_keys(steps[0]))
    usable = []
    for review in reviews:
        if not isinstance(review, dict) or review.get("dismissal"):
            continue
        verdict = review.get("verdict")
        submitted = review.get("submittedAt")
        if verdict not in RESULTS or not isinstance(submitted, str):
            continue
        usable.append(review)
    usable.sort(key=lambda review: review["submittedAt"])
    for review in usable:
        keys = set(review_keys(review))
        if not keys or keys & drafter:
            continue
        for i, step in enumerate(steps):
            if i == 0 or i in slashed:
                continue
            if keys & set(step_keys(step)):
                yield i, review
                break


def latest_decisions(steps, reviews):
    """The latest linked review of each box: what the box shows and what the status uses."""
    return dict(linked_reviews(steps, reviews))


def review_warnings(steps, reviews):
    """approve / request_changes from someone on no box of the line, or from the drafter. Those reviews are not stamped."""
    line_keys = set().union(*(step_keys(step) for step in steps))
    drafter = set(step_keys(steps[0]))
    out = []
    for review in reviews:
        if not isinstance(review, dict) or review.get("dismissal") or review.get("verdict") not in RESULTS:
            continue
        keys = review_keys(review)
        if set(keys) & drafter:
            text = warn("drafterReview", name=keys[0])
        elif keys and not set(keys) & line_keys:
            text = warn("outsideReview", who=keys[0])
        else:
            continue
        if text not in out:
            out.append(text)
    return out


def moment(review):
    return datetime.fromisoformat(review["submittedAt"].replace("Z", "+00:00"))


def order_warnings(steps, reviews, decisions):
    """A later box approved before an earlier one. Origin has no ordered approval, so the stamps stay.

    Only boxes whose latest review is approve are compared, by each box's earliest counted approve, not the latest
    review: a re-approve on the earlier box is not an inversion, a re-approve on the later box does not hide one
    (운영규칙 1.1 '승인 순서')."""
    approved = sorted(i for i, d in decisions.items() if d["verdict"] == "approve")
    first = {}
    for i, review in linked_reviews(steps, reviews):
        if review["verdict"] == "approve":
            first.setdefault(i, review)
    out = []
    for n, late in enumerate(approved):
        early = next((i for i in approved[:n] if moment(first[late]) < moment(first[i])), None)
        if early is not None:
            out.append(warn("orderInversion", later=steps[late]["title"], earlier=steps[early]["title"],
                            laterDate=moment(first[late]).astimezone(KST).strftime("%Y-%m-%d %H:%M"),
                            earlierDate=moment(first[early]).astimezone(KST).strftime("%Y-%m-%d %H:%M")))
    return out


def whose_turn(steps, decisions):
    """Origin does not enforce order. Walk the file's line and name the first open seat."""
    slashed = slashed_indexes(steps)
    drafter = steps[0]
    for i, step in enumerate(steps):
        if i == 0 or i in slashed:
            continue
        decision = decisions.get(i)
        if decision is None:
            return {"state": "in-progress", "name": step["name"], "index": i}
        if decision.get("verdict") == "request_changes":
            return {"state": "rejected", "name": drafter["name"], "index": 0}
    # 승인: at least one 결재 box, and every box but 기안 (and the slashed ones) approved.
    # A line with no role on any box has no 결재 box to count.
    if any("role" in step for step in steps) and not any(step["role"] == FINAL for step in steps):
        return {"state": "needs-check", "name": None, "index": None}
    return {"state": "approved", "name": None, "index": None}


def build_view(steps, reviews, roles=ROLES, merge=None):
    """merge: merge_record(), when the form shows the merge note. Its warnings join the rest."""
    decisions = latest_decisions(steps, reviews)
    warnings = (line_warnings(steps, roles) + review_warnings(steps, reviews) + order_warnings(steps, reviews, decisions)
                + (merge["warnings"] if merge else []))
    turn = whose_turn(steps, decisions)
    state = "needs-check" if turn["state"] == "approved" and structure_warnings(warnings) else turn["state"]
    slashed = slashed_indexes(steps)
    boxes = []
    for i, step in enumerate(steps):
        decision = decisions.get(i)
        boxes.append({
            "title": step["title"],
            "name": step["name"] if i == 0 or decision else "",
            "date": step["date"] if i == 0 else (stamp_date(decision["submittedAt"]) if decision else ""),
            "result": DRAFT if i == 0 else (RESULTS[decision["verdict"]] if decision else ""),
            "mark": step.get("mark") or "",
            "slash": i in slashed,
            "turn": i == turn["index"],
        })
    return {"boxes": boxes, "turn": turn, "state": state, "status": APPROVAL_STATUS[state], "warnings": warnings}


def warning_html(view):
    """The warnings printed on the document, the same for every form, so a PDF reader sees what the terminal saw."""
    if not view["warnings"]:
        return ""
    items = "".join(f"<li>{esc(w)}</li>" for w in view["warnings"])
    return f'<div class="warnings"><div class="wcap">경고</div><ul>{items}</ul></div>'


def box_html(box, note=""):
    if box["slash"]:
        return ('<svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">'
                '<line x1="6" y1="6" x2="94" y2="94" stroke="#000" stroke-width="1.6"/></svg>')
    parts = []
    if box["mark"]:
        parts.append(f'<div class="mark">{esc(box["mark"])}</div>')
    if box["name"]:
        parts.append(f'<div class="who">{esc(box["name"])}</div>')
    if box["date"]:
        parts.append(f'<div class="when">{esc(box["date"])}</div>')
    if box["result"]:
        parts.append(f'<div class="act">{esc(box["result"])}</div>')
    if note:
        parts.append(f'<div class="note">{esc(note)}</div>')
    return "".join(parts)


def sign_table(view, cls, merge=None):
    """결재란. merge: merge_record() — its note goes under the box it names (never a slashed one).
    A note with no box (취합) goes under the table, outside the 결재란."""
    boxes = view["boxes"]
    heads = '<td class="side" rowspan="2">결재</td>' + "".join(f'<th>{esc(box["title"])}</th>' for box in boxes)
    cells = "".join(
        f'<td class="{"slash" if box["slash"] else "turn" if box["turn"] else ""}">'
        f'{box_html(box, merge["text"] if merge and i == merge["index"] else "")}</td>'
        for i, box in enumerate(boxes)
    )
    table = f'<table class="sign {cls}"><tr>{heads}</tr><tr>{cells}</tr></table>'
    if merge and merge["index"] is None:
        return f'<div class="signwrap">{table}<div class="collect">{esc(merge["text"])}</div></div>'
    return table


def head(kind, title, rows, sign, beside):
    """문서 머리. rows: [(label, html)]. beside: 결재란을 머리 표 옆에 둘지, 아래 한 줄로 둘지."""
    meta = "".join(f'<tr><td class="k">{esc(k)}</td><td>{v}</td></tr>' for k, v in rows)
    top = f'<div class="kind">{esc(kind)}</div><div class="titlebox"><h1>{esc(title)}</h1></div>'
    if beside:
        return f'{top}<div class="headrow"><table class="meta">{meta}</table>{sign}</div>'
    return f'{top}<div class="headrow"><table class="meta">{meta}</table></div>{sign}'


def page(header, css_paths, body):
    css = open(REPORT_CSS, encoding="utf-8").read().replace("@@HEADER@@", header)
    for path in (APPROVAL_CSS, *css_paths):
        css += open(path, encoding="utf-8").read()
    return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{css}</style></head><body>{body}</body></html>'


def summary(view):
    turn = view["turn"]
    return {
        "status": view["status"],
        "state": view["state"],
        "turn": turn["name"],
        "boxes": [
            {"title": box["title"], "name": box["name"], "date": box["date"], "result": box["result"],
             "mark": box["mark"], "slash": box["slash"]}
            for box in view["boxes"]
        ],
    }


def context(doc, form, pr=None, number=None):
    """Reviews, document number, URL, and merge record for one render.
    pr: read Origin. number: offline, the document number only, stamps from sampleReviews and sampleMerge."""
    if pr and number and pr != number:
        fail("--pr와 --number가 다릅니다.")
    steps = doc["approval"]["steps"]
    if pr:
        origin = origin_pr(pr)
        reviews, url, merged = origin_reviews(pr), origin["url"], origin["merge"]
    else:
        reviews, url, merged = doc.get("sampleReviews") or [], None, doc.get("sampleMerge")
    merge = merge_record(steps, merged)
    return {
        "reviews": reviews,
        "url": url,
        "merge": merge,
        "numbered": bool(pr or number),
        "docNumber": doc_number(form, steps[0]["date"], pr or number),
    }


def cli(argv, description, form, load_document, document_html, roles=ROLES, shows_merge=True):
    """python3 render_x.py doc.json out.pdf [--pr N | --number N]. Writes out.html next to out.pdf."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("document")
    parser.add_argument("pdf")
    parser.add_argument("--pr", type=int, help="Origin PR 번호. 리뷰·머지 상태를 읽고 문서번호를 찍습니다. sampleReviews는 쓰지 않습니다.")
    parser.add_argument("--number", type=int, help="문서번호에만 쓰는 PR 번호. Origin을 읽지 않고 sampleReviews·sampleMerge로 그립니다.")
    args = parser.parse_args(argv)
    doc = load_document(args.document)
    ctx = context(doc, form, args.pr, args.number)
    view = build_view(doc["approval"]["steps"], ctx["reviews"], roles, ctx["merge"] if shows_merge else None)
    warnings = view["warnings"]
    for warning in warnings:
        print(f"경고: {warning} 그대로 렌더합니다.", file=sys.stderr)
    html_path = os.path.splitext(args.pdf)[0] + ".html"
    sys.path.insert(0, TEMPLATE)
    from make_report import render
    render(document_html(doc, view, ctx), args.pdf, html_path=html_path)
    out = {"pdf": args.pdf, "html": html_path, "docNumber": ctx["docNumber"], "warnings": warnings}
    if shows_merge:
        merge = ctx["merge"]
        box = None if merge["index"] is None else doc["approval"]["steps"][merge["index"]]["title"]
        out["merge"] = {"box": box, "text": merge["text"], "by": merge["by"]}
    print(json.dumps({**out, **summary(view)}, ensure_ascii=False))
