#!/usr/bin/env python3
"""Render a proposal (품의서) JSON file to a monochrome approval document (HTML and PDF).

The file holds the proposal content and the approval line [기안, 결재].
The document number 품의-YYYY-NNNN is made at render time from the PR number.
Head, 결재란, review matching, and output are shared in skills/approval-line.
No database. This script never sends a review or a merge.

  python3 render_proposal.py example_proposal.json out.pdf --number 42   # also writes out.html
  python3 render_proposal.py proposal.json out.pdf --pr 42
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "approval-line"))
sys.path.insert(0, os.path.join(HERE, "..", "report-format", "template"))
import approval
from approval import esc, fail
from make_report import VERDICTS as REPORT_VERDICTS

ROLES = (approval.DRAFT, approval.FINAL)
DOC_KEYS = {"form", "version", "title", "prUrl", "verdict", "approval", "sections", "sampleReviews", "sampleMerge"}
VERDICTS = {k: REPORT_VERDICTS[k] for k in ("ok", "warn", "hold")}


def load_document(path):
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    if not isinstance(doc, dict):
        fail("데이터 파일은 JSON 객체여야 합니다.")
    extra = set(doc) - DOC_KEYS
    if extra:
        fail("데이터 형식에 없는 칸입니다: " + ", ".join(sorted(extra)))
    if doc.get("form") != "proposal" or doc.get("version") != 1:
        fail("form은 proposal, version은 1이어야 합니다.")
    if not approval.has_text(doc, "title"):
        fail("제목(title)이 비어 있습니다.")
    if "prUrl" in doc and not approval.has_text(doc, "prUrl"):
        fail("prUrl은 비우지 말고, 없으면 키를 빼십시오.")
    if "verdict" in doc and doc["verdict"] not in VERDICTS:
        fail("판정(verdict)은 ok, warn, hold 중 하나여야 합니다.")
    approval.check_line(doc.get("approval"))
    sections = doc.get("sections", [])
    if not isinstance(sections, list) or any(
        not isinstance(s, dict) or not approval.has_text(s, "title")
        or not isinstance(s.get("items"), list) or not all(isinstance(i, str) for i in s["items"])
        for s in sections
    ):
        fail("sections는 {title, items:[문장]} 목록이어야 합니다.")
    if "sampleReviews" in doc and not isinstance(doc["sampleReviews"], list):
        fail("sampleReviews는 목록이어야 합니다.")
    approval.check_sample_merge(doc)
    return doc


def sections_html(sections):
    parts = []
    for section in sections:
        if not section["items"]:
            continue
        title = section["title"].lstrip("□ ").strip()
        items = "".join(f"<li>{esc(item)}</li>" for item in section["items"])
        parts.append(f"<h2>{esc(title)}</h2><ul>{items}</ul>")
    return "".join(parts)


def document_html(doc, view, ctx):
    drafter = doc["approval"]["steps"][0]
    url = doc.get("prUrl") or ctx["url"]
    rows = [
        ("문서번호", esc(ctx["docNumber"])),
        ("기안자", esc(drafter["name"])),
        ("기안일", esc(drafter["date"])),
        ("상태", esc(view["status"])),
    ]
    if url:
        href = esc(url).replace('"', "&quot;")
        rows.append(("관련근거", f'<a href="{href}">{esc(url)}</a>'))
    verdict = ""
    if doc.get("verdict"):
        mark, label = VERDICTS[doc["verdict"]]
        verdict = f'<div class="pverdict">판정 <span class="mk">{mark}</span>{esc(label)}</div>'
    report_no = ctx["docNumber"].replace(approval.DOC_KINDS["proposal"], approval.DOC_KINDS["report"], 1)
    body = (
        approval.head("품 의 서", doc["title"], rows, approval.sign_table(view, "line", ctx["merge"]), beside=True)
        + approval.warning_html(view)
        + verdict
        + sections_html(doc.get("sections", []))
        + f'<p class="note report-link">결과보고서는 문서번호 {esc(report_no)}로 같은 PR에 붙입니다.</p>'
    )
    return approval.page("품의서", [os.path.join(HERE, "proposal.css")], body)


def main(argv):
    approval.cli(argv, "품의서 JSON을 흑백 문서(HTML·PDF)로 렌더합니다.", "proposal", load_document, document_html,
                 roles=ROLES)


if __name__ == "__main__":
    main(sys.argv[1:])
