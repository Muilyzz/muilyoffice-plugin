#!/usr/bin/env python3
"""기안 전 점검: PR·기안을 올리기 전에 본문과 바꾼 파일을 스스로 확인합니다.

판정은 두 가지뿐입니다. ✔ 통과, ▲ 확인 필요. 확인하지 못한 것은 ▲로 남깁니다.
표준 라이브러리만 씁니다. 사용법은 같은 폴더의 SKILL.md에 있습니다.
"""
import argparse, datetime, json, os, re, shutil, subprocess, sys

PASS, CHECK = "✔", "▲"
HEAD_LINES = 10
TIMEOUT = 30

# 값 모양으로만 겁니다. 접두사는 글자 그대로 적지 않고 [ ]로 나눠 적습니다.
SECRET_PATTERNS = [
    ("Git 호스팅 토큰", r"gh[pousr][_][A-Za-z0-9]{20,}"),
    ("Git 호스팅 토큰", r"github[_]pat[_][A-Za-z0-9_]{20,}"),
    ("Git 호스팅 토큰", r"glpat[-][A-Za-z0-9_-]{20,}"),
    ("메신저 토큰", r"xox[abp][-][A-Za-z0-9-]{10,}"),
    ("접속 토큰이 든 주소", r"x[-]access[-]token[:@]"),
    ("API 키", r"(?<![A-Za-z0-9])sk[-](?:proj[-]|ant[-])?[A-Za-z0-9_-]{20,}"),
    ("API 키", r"crsr[_][A-Za-z0-9]{10,}"),
    ("클라우드 접근 키", r"AKIA[0-9A-Z]{16}"),
    ("개인 키", r"BEGIN[ ][A-Z ]*PRIVATE[ ]KEY"),
    ("인증 헤더 값", r"Bearer\s+[A-Za-z0-9._~+/-]{20,}"),
    ("비밀값 대입", r"(?i)\b(?:password|passwd|secret|api[_-]?key|token)\s*[:=]\s*['\"]?(?![<{$])[^\s'\"<>]{8,}"),
    ("이메일 주소", r"[A-Za-z0-9._%+-]+@(?!(?:[A-Za-z0-9-]+\.)*(?:example\.(?:com|net|org)|test|invalid|example)\b)"
                 r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}"),
]
LINE_REF = re.compile(r"(?<![\w/:@.-])([\w가-힣./-]+\.[A-Za-z0-9]+):(\d+)(?:-(\d+))?(?![\w:])")
CODE_BLOCK = re.compile(r"^```(\d+):(\d+):(\S+)\s*\n(.*?)^```", re.M | re.S)
FILE_COUNT = re.compile(r"(?:바꾼|고친|변경한|변경된|바뀐|새로 만든|더한|추가한)\s*파일[^\n\d]{0,20}?(\d+)\s*개"
                        r"|(\d+)\s*개\s*파일을?\s*(?:바꾸|바꿨|고치|고쳤|변경|더하|더했|추가)"
                        r"|(\d+)\s+files?\s+changed", re.I)
DEFAULT_CODE = r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*:[a-z][a-z0-9]*(?:_[a-z0-9]+)*"


def item(no, name, ok, detail):
    return {"no": no, "name": name, "mark": PASS if ok else CHECK, "detail": detail}


def read_text(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None


def read_list(path):
    """한 줄에 하나씩 적은 목록. 읽지 못하면 None."""
    text = read_text(path)
    if text is None:
        return None
    return [s.strip() for s in text.splitlines() if s.strip() and not s.strip().startswith("#")]


def sources(args, body, files):
    """(이름, 글) 목록: 제목, 본문, 읽을 수 있는 바꾼 파일. 읽지 못한 파일 이름도 돌려줍니다."""
    out = [("제목", args.title or ""), ("본문", body)]
    unread = [f"파일 목록({args.files})"] if files is None else []
    for name in files or []:
        text = read_text(os.path.join(args.root, name))
        if text is None:
            unread.append(name)
        else:
            out.append((name, text))
    return out, unread


def check_number(args, body):
    kinds = "|".join(re.escape(k) for k in args.kinds.split(",") if k)
    number = re.compile(rf"({kinds})-(\d{{4}})-(\d{{4}}|{re.escape(args.unassigned)})")
    reasons = []
    if not args.title:
        return item(1, "문서번호·제목 형식", False, "제목을 받지 못해 확인하지 못했습니다(--title).")
    in_title = re.findall(rf"\[{number.pattern}\]", args.title)
    head = "\n".join(body.splitlines()[:HEAD_LINES])
    in_body = [m.groups() for m in re.finditer(rf"^[□\-\s]*문서번호:\s*{number.pattern}\s*$", head, re.M)]
    if len(in_title) != 1:
        reasons.append(f"제목에 [종류-연도-번호]가 {len(in_title)}개입니다. 1개여야 합니다.")
    if len(in_body) != 1:
        reasons.append(f"본문 첫 {HEAD_LINES}줄에 '문서번호:' 줄이 {len(in_body)}개입니다. 1개여야 합니다.")
    if reasons:
        return item(1, "문서번호·제목 형식", False, " ".join(reasons))
    kind, year, no = in_title[0]
    shown = f"{kind}-{year}-{no}"
    if in_title[0] != in_body[0]:
        reasons.append(f"제목({shown})과 본문({'-'.join(in_body[0])})의 번호가 다릅니다.")
    if no == args.unassigned:
        reasons.append(f"번호가 '{args.unassigned}'입니다. PR 번호가 정해지면 채웁니다.")
    elif args.pr_number is not None and no != f"{args.pr_number:04d}":
        reasons.append(f"번호 {no}가 PR 번호 {args.pr_number}과 다릅니다.")
    expected_year = args.year or datetime.date.today().year
    if int(year) != expected_year:
        reasons.append(f"연도 {year}가 {expected_year}과 다릅니다.")
    if args.pr_number is None and no != args.unassigned:
        reasons.append("PR 번호를 받지 못해 번호가 맞는지는 확인하지 못했습니다(--pr-number).")
    if reasons:
        return item(1, "문서번호·제목 형식", False, " ".join(reasons))
    return item(1, "문서번호·제목 형식", True, f"{shown}, 제목과 본문이 같습니다.")


def word_regex(word):
    if word.startswith("re:"):
        return re.compile(word[3:])
    return re.compile(re.escape(word), re.I)


def check_forbidden(args, texts, unread):
    if not args.forbidden:
        return item(2, "금지어", False, "금지어 목록을 받지 못해 확인하지 못했습니다(--forbidden).")
    words = read_list(args.forbidden)
    if words is None:
        return item(2, "금지어", False, f"금지어 목록을 읽지 못했습니다: {args.forbidden}")
    if not words:
        return item(2, "금지어", False, "금지어 목록이 비어 있어 확인하지 못했습니다.")
    regexes, broken = [], []
    for w in words:
        try:
            regexes.append((w, word_regex(w)))
        except re.error as e:
            broken.append(f"'{w}'({e})")
    hits = []
    for name, text in texts:
        for n, line in enumerate(text.splitlines(), 1):
            for w, regex in regexes:
                if regex.search(line):
                    hits.append(f"{name}:{n} '{w}'")
    reasons = [f"걸린 곳 {len(hits)}개: " + ", ".join(hits)] if hits else []
    if broken:
        reasons.append("정규식이 틀려 찾지 못한 금지어: " + ", ".join(broken))
    if unread:
        reasons.append("읽지 못한 파일: " + ", ".join(unread))
    if reasons:
        return item(2, "금지어", False, " ".join(reasons))
    return item(2, "금지어", True, f"금지어 {len(words)}개, 걸린 곳 0개.")


def mask(value):
    return value[:4] + f"…({len(value)}자)"


def check_secrets(texts, unread):
    hits = []
    for name, text in texts:
        for n, line in enumerate(text.splitlines(), 1):
            for kind, pattern in SECRET_PATTERNS:
                for m in re.finditer(pattern, line):
                    hits.append(f"{name}:{n} {kind} {mask(m.group(0))}")
    reasons = [f"걸린 곳 {len(hits)}개: " + ", ".join(hits)] if hits else []
    if unread:
        reasons.append("읽지 못한 파일: " + ", ".join(unread))
    if reasons:
        return item(3, "비밀·토큰 노출", False, " ".join(reasons))
    return item(3, "비밀·토큰 노출", True, f"값 모양 {len(SECRET_PATTERNS)}가지, 걸린 곳 0개.")


def run_origin(cmd, *argv):
    done = subprocess.run([cmd, *argv], capture_output=True, text=True, timeout=TIMEOUT)
    if done.returncode != 0:
        last = (done.stderr or done.stdout).strip().splitlines()[-1:]
        raise RuntimeError(last[0] if last else f"종료 코드 {done.returncode}")
    return done.stdout


def check_overlap(args, files):
    name = "다른 열린 PR과 파일 겹침"
    if files is None:
        return item(4, name, False, f"파일 목록을 읽지 못했습니다: {args.files}")
    if not files:
        return item(4, name, False, "파일 목록을 받지 못해 확인하지 못했습니다(--files).")
    cmd = shutil.which(args.origin_cmd)
    if cmd is None:
        return item(4, name, False, f"'{args.origin_cmd}' 명령이 없어 열린 PR 목록을 읽지 못했습니다.")
    # origin의 open 목록에는 초안 PR이 없어서 두 상태를 따로 읽습니다.
    others, truncated = set(), []
    for state in ("open", "draft"):
        try:
            listed = json.loads(run_origin(cmd, "pr", "list", "--state", state, "--limit", str(args.limit),
                                           "--json", "number,state"))
            numbers = {p["number"] for p in listed if p.get("state", state) in ("open", "draft")}
        except (RuntimeError, subprocess.TimeoutExpired, OSError, ValueError, TypeError, KeyError) as e:
            return item(4, name, False, f"{state} PR 목록을 읽지 못했습니다: {e}")
        if len(listed) >= args.limit:
            truncated.append(state)
        others |= numbers
    others = sorted(others - {args.pr_number})
    mine, overlaps, unread = set(files), [], []
    for number in others:
        try:
            theirs = set(run_origin(cmd, "pr", "diff", str(number), "--name-only").split())
        except (RuntimeError, subprocess.TimeoutExpired, OSError) as e:
            unread.append(f"#{number}({e})")
            continue
        for path in sorted(mine & theirs):
            overlaps.append(f"#{number} {path}")
    reasons = []
    if overlaps:
        reasons.append(f"겹치는 파일 {len(overlaps)}곳: " + ", ".join(overlaps))
    if unread:
        reasons.append("파일 목록을 읽지 못한 PR: " + ", ".join(unread))
    if truncated:
        reasons.append(f"{'·'.join(truncated)} PR 목록이 상한 {args.limit}건에 닿아 잘렸을 수 있습니다(--limit).")
    if reasons:
        return item(4, name, False, " ".join(reasons))
    return item(4, name, True, f"열린 PR {len(others)}건과 겹치는 파일 0개.")


def check_lines(args, body, files):
    reasons, checked = [], 0
    lines_of = {}

    def lines(path):
        if path not in lines_of:
            text = read_text(os.path.join(args.root, path))
            lines_of[path] = None if text is None else text.splitlines()
        return lines_of[path]

    for m in CODE_BLOCK.finditer(body):
        start, end, path, quoted = int(m.group(1)), int(m.group(2)), m.group(3), m.group(4)
        checked += 1
        got = lines(path)
        if got is None:
            reasons.append(f"{path}:{start}-{end} 파일이 없습니다.")
            continue
        if not 1 <= start <= end <= len(got):
            reasons.append(f"{path}:{start}-{end} 줄 범위가 파일({len(got)}줄) 밖입니다.")
            continue
        real = {s.strip() for s in got[start - 1:end]}
        for q in quoted.splitlines():
            q = q.strip()
            if q and not re.match(r"^(?://|#)?\s*\.\.\.", q) and q not in real:
                reasons.append(f"{path}:{start}-{end}에 인용한 줄 '{q[:40]}'이 없습니다.")
                break
    outside = CODE_BLOCK.sub("", body)
    for m in LINE_REF.finditer(outside):
        path, start, end = m.group(1), int(m.group(2)), int(m.group(3) or m.group(2))
        checked += 1
        got = lines(path)
        if got is None:
            reasons.append(f"{path}:{m.group(2)} 파일이 없습니다.")
        elif not 1 <= start <= end <= len(got):
            reasons.append(f"{path}:{start} 줄이 파일({len(got)}줄) 밖입니다.")
    for m in FILE_COUNT.finditer(body):
        checked += 1
        said = int(next(g for g in m.groups() if g))
        if not files:
            reasons.append(f"본문의 '{m.group(0)}'를 비교할 파일 목록이 없습니다(--files).")
        elif said != len(files):
            reasons.append(f"본문은 '{m.group(0)}', 파일 목록은 {len(files)}개입니다.")
    if files is None:
        reasons.append(f"파일 목록을 읽지 못했습니다: {args.files}")
    missing = [f for f in files or [] if not os.path.exists(os.path.join(args.root, f))]
    if missing and not args.allow_deleted:
        reasons.append("파일 목록에 있는데 없는 파일: " + ", ".join(missing))
    if checked == 0:
        reasons.append("본문에 확인할 줄 참조·코드 인용·파일 건수가 없습니다(확인할 대상 없음).")
    if reasons:
        return item(5, "본문 숫자·줄 번호", False, " ".join(reasons))
    return item(5, "본문 숫자·줄 번호", True, f"줄 참조·건수 {checked}곳이 실제와 같습니다.")


def check_terms(args, body):
    name = "오류 코드·약속서 용어"
    if not args.terms:
        return item(6, name, False, "용어 목록을 받지 못해 확인하지 못했습니다(--terms).")
    text = read_text(args.terms)
    if text is None:
        return item(6, name, False, f"용어 목록을 읽지 못했습니다: {args.terms}")
    try:
        terms = json.loads(text)
    except ValueError as e:
        return item(6, name, False, f"용어 목록이 JSON이 아닙니다: {e}")
    if not isinstance(terms, dict):
        return item(6, name, False, "용어 목록은 JSON 객체({...})여야 합니다.")
    codes, words = terms.get("errorCodes", []), terms.get("terms", {})
    if not (isinstance(codes, list) and all(isinstance(c, str) for c in codes)):
        return item(6, name, False, "errorCodes는 글자 목록이어야 합니다.")
    if not (isinstance(words, dict) and all(isinstance(w, list) and all(isinstance(x, str) for x in w)
                                            for w in words.values())):
        return item(6, name, False, 'terms는 {"바른 말": ["쓰지 않을 말", ...]} 꼴이어야 합니다.')
    try:
        pattern = re.compile(terms.get("codePattern", DEFAULT_CODE))
    except (re.error, TypeError) as e:
        return item(6, name, False, f"codePattern 정규식이 틀렸습니다: {e}")
    codes = set(codes)
    reasons = []
    unknown = sorted({c for c in re.findall(r"`([^`\n]+)`", body) if pattern.fullmatch(c) and c not in codes})
    if unknown:
        reasons.append("목록에 없는 오류 코드: " + ", ".join(unknown))
    for right, wrongs in words.items():
        for wrong in wrongs:
            for n, line in enumerate(body.splitlines(), 1):
                if wrong in line:
                    reasons.append(f"본문:{n} '{wrong}' 대신 '{right}'")
    if reasons:
        return item(6, name, False, " ".join(reasons))
    return item(6, name, True, f"오류 코드 {len(codes)}개·용어 {len(terms.get('terms', {}))}개 기준으로 어긋난 곳 0개.")


NAMES = {1: "문서번호·제목 형식", 2: "금지어", 3: "비밀·토큰 노출", 4: "다른 열린 PR과 파일 겹침",
         5: "본문 숫자·줄 번호", 6: "오류 코드·약속서 용어"}


def guarded(no, check):
    """한 항목이 예상 못한 오류를 내도 그 항목만 ▲로 적고 다음 항목으로 넘어갑니다."""
    try:
        return check()
    except Exception as e:
        return item(no, NAMES[no], False, f"점검 중 오류로 확인하지 못했습니다: {type(e).__name__}: {e}")


def run(args):
    body = read_text(args.body)
    if body is None:
        items = [item(no, n, False, f"본문 파일을 읽지 못해 확인하지 못했습니다: {args.body}") for no, n in NAMES.items()]
    else:
        files = read_list(args.files) if args.files else []
        texts, unread = sources(args, body, files)
        items = [
            guarded(1, lambda: check_number(args, body)),
            guarded(2, lambda: check_forbidden(args, texts, unread)),
            guarded(3, lambda: check_secrets(texts, unread)),
            guarded(4, lambda: check_overlap(args, files)),
            guarded(5, lambda: check_lines(args, body, files)),
            guarded(6, lambda: check_terms(args, body)),
        ]
    flagged = [i for i in items if i["mark"] == CHECK]
    items.append(item(7, "통과 못한 항목", not flagged,
                      f"▲ {len(flagged)}개: " + ", ".join(str(i["no"]) for i in flagged) if flagged else "▲ 0개."))
    return items


def render(items):
    out = ["기안 전 점검"]
    out += [f"{i['mark']} {i['no']}. {i['name']}: {i['detail']}" for i in items]
    checks = items[:-1]
    out.append(f"결과: 점검 {len(checks)}개 중 ✔ {sum(i['mark'] == PASS for i in checks)}"
               f" / ▲ {sum(i['mark'] == CHECK for i in checks)}")
    return "\n".join(out)


def parse(argv):
    p = argparse.ArgumentParser(description="기안 전 점검")
    p.add_argument("--body", required=True, help="PR·기안 본문 파일")
    p.add_argument("--title", help="PR·기안 제목")
    p.add_argument("--files", help="바꾼 파일 목록 파일(한 줄에 하나)")
    p.add_argument("--forbidden", help="금지어 목록 파일(한 줄에 하나, re:로 시작하면 정규식)")
    p.add_argument("--terms", help="오류 코드·용어 목록 JSON 파일")
    p.add_argument("--root", default=".", help="파일 경로의 기준 폴더(기본: 지금 폴더)")
    p.add_argument("--kinds", default="품의,보고", help="문서 종류(쉼표로 구분)")
    p.add_argument("--unassigned", default="미부여", help="번호가 아직 없을 때 쓰는 말")
    p.add_argument("--year", type=int, help="문서번호 연도(기본: 오늘 연도)")
    p.add_argument("--pr-number", type=int, help="이 PR의 번호")
    p.add_argument("--origin-cmd", default="origin", help="열린 PR을 읽을 명령(기본: origin)")
    p.add_argument("--limit", type=int, default=1000, help="상태마다 읽을 PR 수 상한")
    p.add_argument("--allow-deleted", action="store_true", help="파일 목록에 지운 파일이 있어도 됨")
    p.add_argument("--json", action="store_true", help="JSON으로 출력")
    return p.parse_args(argv)


def main(argv=None):
    args = parse(argv)
    items = run(args)
    print(json.dumps(items, ensure_ascii=False, indent=2) if args.json else render(items))
    return 0 if all(i["mark"] == PASS for i in items) else 1


if __name__ == "__main__":
    sys.exit(main())
