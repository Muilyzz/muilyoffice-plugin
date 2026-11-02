#!/usr/bin/env python3
"""Render a result report (결과보고서) JSON file to a monochrome document (HTML and PDF).

The body keeps report-format's fixed order: 요약, 상태 변화, □1 개요 … □6 판정.
The 결재란, document number 보고-YYYY-NNNN, and merge note come from skills/approval-line.

  python3 render_result.py example_result.json out.pdf --number 42   # also writes out.html
  python3 render_result.py result.json out.pdf --pr 42
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "approval-line"))
sys.path.insert(0, os.path.join(HERE, "template"))
import approval
from approval import esc, fail
import make_report as mr

SECTIONS = (
    ("overview", "1. 개요"),
    ("background", "2. 배경"),
    ("changes", "3. 변경 내용"),
    ("verification", "4. 검증 결과"),
    ("risks", "5. 위험 요소"),
)
DOC_KEYS = {"form", "version", "title", "target", "url", "approval", "summary", "change",
            "verdict", "sampleReviews", "sampleMerge"} | {key for key, _ in SECTIONS}
BLOCK_KEYS = {"items", "table", "notes"}


def _strings(value):
    return isinstance(value, list) and all(isinstance(v, str) and v.strip() for v in value)


def _items(value):
    return isinstance(value, list) and all(
        (isinstance(v, str) and v.strip())
        or (isinstance(v, dict) and set(v) == {"text", "sub"} and isinstance(v["text"], str) and _strings(v["sub"]))
        for v in value
    )


def _block(block, label):
    if not isinstance(block, dict) or not block or set(block) - BLOCK_KEYS:
        fail(f"{label}은 items, table, notes 중 하나 이상을 둔 객체여야 합니다.")
    if "items" in block and not _items(block["items"]):
        fail(f"{label}.items는 문장 또는 {{text, sub:[문장]}} 목록이어야 합니다.")
    if "notes" in block and not _strings(block["notes"]):
        fail(f"{label}.notes는 문장 목록이어야 합니다.")
    table = block.get("table")
    if table is not None:
        headers, rows = (table or {}).get("headers"), (table or {}).get("rows")
        if set(table) != {"headers", "rows"} or not _strings(headers) or not isinstance(rows, list) or any(
            not isinstance(r, list) or len(r) != len(headers) or not all(isinstance(c, str) for c in r) for r in rows
        ):
            fail(f"{label}.table은 headers와 같은 칸 수의 rows여야 합니다.")


def load_document(path):
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    if not isinstance(doc, dict):
        fail("데이터 파일은 JSON 객체여야 합니다.")
    extra = set(doc) - DOC_KEYS
    if extra:
        fail("데이터 형식에 없는 칸입니다: " + ", ".join(sorted(extra)))
    if doc.get("form") != "result-report" or doc.get("version") != 1:
        fail("form은 result-report, version은 1이어야 합니다.")
    for key in ("title", "target", "url"):
        if not approval.has_text(doc, key):
            fail(f"{key}가 비어 있습니다.")
    approval.check_line(doc.get("approval"))
    if not _strings(doc.get("summary")):
        fail("summary는 문장 목록이어야 합니다.")
    change = doc.get("change")
    if not isinstance(change, dict) or set(change) != {"before", "after"} or not _strings(change["before"]) or not _strings(change["after"]):
        fail("change는 before, after 문장 목록이어야 합니다.")
    for key, title in SECTIONS:
        if key not in doc:
            fail(f"□ {title}({key})이 없습니다. 결과보고서는 □1부터 □6까지 모두 둡니다.")
        _block(doc[key], key)
    verdict = doc.get("verdict")
    if not isinstance(verdict, dict) or set(verdict) - {"kind", "items", "order"} \
            or verdict.get("kind") not in mr.VERDICTS or not _strings(verdict.get("items")) \
            or ("order" in verdict and not _strings(verdict["order"])):
        fail("verdict는 kind(ok, warn, hold, done), items, 선택 order를 둡니다.")
    if "sampleReviews" in doc and not isinstance(doc["sampleReviews"], list):
        fail("sampleReviews는 목록이어야 합니다.")
    approval.check_sample_merge(doc)
    return doc


def items_html(items):
    return mr.ul([(esc(i["text"]), [esc(s) for s in i["sub"]]) if isinstance(i, dict) else esc(i) for i in items])


def block_html(block):
    parts = []
    if "items" in block:
        parts.append(items_html(block["items"]))
    if "table" in block:
        t = block["table"]
        parts.append(mr.table([esc(h) for h in t["headers"]], [[esc(c) for c in r] for r in t["rows"]]))
    parts += [mr.note(esc(n)) for n in block.get("notes", [])]
    return parts


def document_html(doc, view, ctx):
    drafter = doc["approval"]["steps"][0]
    v = doc["verdict"]
    body = (
        approval.warning_html(view)
        + mr.summary([esc(s) for s in doc["summary"]])
        + mr.chg([esc(s) for s in doc["change"]["before"]], [esc(s) for s in doc["change"]["after"]])
        + "".join(mr.section(title, *block_html(doc[key])) for key, title in SECTIONS)
        + mr.section("6. 판정", mr.verdict(v["kind"], esc(doc["url"]), [esc(s) for s in v["items"]],
                                         order=[esc(s) for s in v.get("order", [])] or None))
    )
    header = f'{ctx["docNumber"]} 결과 보고' if ctx["numbered"] else "결과 보고"
    return mr.document(
        header=header, body=body,
        extra_css=open(approval.APPROVAL_CSS, encoding="utf-8").read(),
        kind="결 과 보 고 서", title=esc(doc["title"]), date=esc(drafter["date"]), author=esc(drafter["name"]),
        url=esc(doc["url"]), target=esc(doc["target"]), doc_no=esc(ctx["docNumber"]),
        sign=approval.sign_table(view, "line", ctx["merge"]),
    )


def main(argv):
    approval.cli(argv, "결과보고서 JSON을 흑백 문서(HTML·PDF)로 렌더합니다.", "report", load_document, document_html)


if __name__ == "__main__":
    main(sys.argv[1:])
