#!/usr/bin/env python3
"""Render an organization JSON file ({members:[...]}) to a monochrome org chart (HTML and PDF).

The tree follows reports_to. The table lists every member and the approval chain that
follows approver upward. Same format as example_organization.json and data/README.md.

  python3 render_org_chart.py example_organization.json out.pdf   # also writes out.html
  python3 render_org_chart.py example_organization.json out.pdf --date 2026-10-31
"""
import argparse, json, os, sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "report-format", "template"))
from make_report import CSS, esc, render

OPTIONAL = {"assignment", "pending", "note"}
PRESENT = ("team", "reports_to", "approver", "delegation", "spec")
REQUIRED = ("id", "name", "kind", "role")
FIELDS = set(REQUIRED) | set(PRESENT) | OPTIONAL
# data/README.md: in a pending member a null field is 미정, not 직속 or 해당 없음.
UNDECIDED = "미정"
KINDS = {"bot": "봇", "human": "사람"}
ASSIGNMENTS = {"deliverable": "산출물", "common": "공통"}


def fail(message):
    raise SystemExit(message)


def _opt_text(member, key):
    value = member.get(key)
    return value is None or (isinstance(value, str) and bool(value.strip()))


def load_members(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    members = data.get("members") if isinstance(data, dict) else None
    if set(data if isinstance(data, dict) else {}) != {"members"} or not isinstance(members, list) or not members:
        fail("조직도 데이터는 {\"members\": [...]} 하나여야 합니다.")
    ids = {}
    for m in members:
        if not isinstance(m, dict):
            fail("구성원은 JSON 객체여야 합니다.")
        label = m.get("id", "?")
        extra = set(m) - FIELDS
        if extra:
            fail(f"{label}: 형식에 없는 필드입니다: " + ", ".join(sorted(extra)))
        for key in REQUIRED:
            if not isinstance(m.get(key), str) or not m[key].strip():
                fail(f"{label}: {key}가 비어 있습니다.")
        missing = [key for key in PRESENT if key not in m]
        if missing:
            fail(f"{label}: 필드가 없습니다: " + ", ".join(missing) + ". 값이 없으면 null로 적습니다.")
        if m["kind"] not in KINDS:
            fail(f"{label}: kind는 bot 또는 human입니다.")
        if m["id"] in ids:
            fail(f"{label}: id가 겹칩니다.")
        for key in ("team", "delegation", "note"):
            if not _opt_text(m, key):
                fail(f"{label}: {key}는 문자열 또는 null입니다.")
        if m.get("assignment") is not None and m["assignment"] not in ASSIGNMENTS:
            fail(f"{label}: assignment는 deliverable 또는 common입니다.")
        if m.get("spec") is not None and not isinstance(m["spec"], dict):
            fail(f"{label}: spec은 객체 또는 null입니다.")
        model = (m.get("spec") or {}).get("model")
        if m.get("spec") is not None and not (isinstance(model, str) and model.strip()):
            fail(f"{label}: spec에는 model(모델 id 문자열)이 있어야 합니다.")
        if "pending" in m and not isinstance(m["pending"], bool):
            fail(f"{label}: pending은 true 또는 false입니다.")
        ids[m["id"]] = m
    for m in members:
        for key in ("reports_to", "approver"):
            ref = m.get(key)
            if ref is not None and ref not in ids:
                fail(f"{m['id']}: {key}가 가리키는 {ref}가 없습니다.")
        chain(ids, m, "reports_to")
        chain(ids, m, "approver")
    return members, ids


def chain(ids, member, key):
    """Names upward along reports_to or approver. A loop is an error."""
    seen, out, ref = {member["id"]}, [], member.get(key)
    while ref is not None:
        if ref in seen:
            fail(f"{member['id']}: {key}가 돌고 돕니다.")
        seen.add(ref)
        out.append(ids[ref]["name"])
        ref = ids[ref].get(key)
    return out


def shown(m, key, text, empty):
    """text for a set field. A null field is 미정 in a pending member, else empty (직속, -)."""
    if m.get(key) is not None:
        return text
    return UNDECIDED if m.get("pending") else empty


def node_html(m):
    mark = " ▲" if m.get("pending") else ""
    team = shown(m, "team", m.get("team"), "직속")
    return (f'<div class="node {m["kind"]}"><div class="nm">{esc(m["name"])}{mark}</div>'
            f'<div class="rl">{esc(m["role"])}</div><div class="tm">{esc(team)} · {KINDS[m["kind"]]}</div></div>')


def branch_html(m, children):
    kids = children.get(m["id"], [])
    inner = "".join(branch_html(k, children) for k in kids)
    return f'<div class="branch">{node_html(m)}' + (f'<div class="kids">{inner}</div>' if kids else "") + "</div>"


def spec_text(spec):
    if not spec:
        return ""
    return ", ".join(f"{k} {v}" for k, v in spec.items())


def members_table(members, ids):
    head = ["이름", "종류", "팀", "역할", "보고", "결재선", "담당", "전결", "사양", "비고"]
    rows = []
    for m in members:
        boss = shown(m, "reports_to", m["reports_to"] and ids[m["reports_to"]]["name"], "-")
        line = shown(m, "approver", " → ".join(chain(ids, m, "approver")), "-")
        rows.append([
            m["name"] + (" ▲" if m.get("pending") else ""), KINDS[m["kind"]], shown(m, "team", m["team"], "직속"),
            m["role"], boss, line, ASSIGNMENTS.get(m.get("assignment"), "-"), shown(m, "delegation", m["delegation"], "-"),
            shown(m, "spec", spec_text(m["spec"]), "-"), m.get("note") or "",
        ])
    th = "".join(f"<th>{esc(h)}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="g members"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'


def document_html(members, ids, title, date):
    children = {}
    for m in members:
        children.setdefault(m.get("reports_to"), []).append(m)
    tree = "".join(branch_html(r, children) for r in children.get(None, []))
    bots = sum(m["kind"] == "bot" for m in members)
    pending = sum(bool(m.get("pending")) for m in members)
    meta = (f'<tr><td class="k">기준일</td><td>{esc(date)}</td></tr>'
            f'<tr><td class="k">구성원</td><td>{len(members)}명 (봇 {bots} · 사람 {len(members) - bots})</td></tr>'
            f'<tr><td class="k">▲</td><td>{pending}명 (미정·잠정)</td></tr>')
    body = (
        f'<div class="kind">조 직 도</div><div class="titlebox"><h1>{esc(title)}</h1></div>'
        f'<div class="headrow"><table class="meta">{meta}</table></div>'
        f'<div class="org">{tree}</div>'
        '<p class="note">이중선 상자는 사람, 단선 상자는 봇입니다. 선은 보고(reports_to)를 따릅니다. ▲는 미정이거나 잠정값인 항목이 있는 구성원입니다.</p>'
        f'<h2 class="list">구성원</h2>{members_table(members, ids)}'
    )
    css = CSS.replace("@@HEADER@@", title) + open(os.path.join(HERE, "org_chart.css"), encoding="utf-8").read()
    return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{css}</style></head><body>{body}</body></html>'


def main(argv):
    parser = argparse.ArgumentParser(description="조직도 JSON을 흑백 문서(HTML·PDF)로 렌더합니다.")
    parser.add_argument("data")
    parser.add_argument("pdf")
    parser.add_argument("--title", default="조직도")
    parser.add_argument("--date", help="기준일 YYYY-MM-DD. 없으면 오늘.")
    args = parser.parse_args(argv)
    date = args.date or datetime.now().strftime("%Y-%m-%d")
    members, ids = load_members(args.data)
    html_path = os.path.splitext(args.pdf)[0] + ".html"
    render(document_html(members, ids, args.title, date), args.pdf, html_path=html_path)
    print(json.dumps({"pdf": args.pdf, "html": html_path, "members": len(members)}, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:])
