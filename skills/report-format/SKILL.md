---
name: report-format
description: >
  Write and render a monochrome Korean groupware report (결과 보고서 or 검토 보고서)
  with the bundled A4 template. A result report can be rendered straight from a JSON
  data file with a 보고-YYYY-NNNN number and an Origin-review approval box.
  For a proposal, use proposal-format.
---

# 보고서 서식

일을 마친 뒤 결과를 올리는 결과보고서와, PR을 검토한 검토보고서를 흑백 A4로 그립니다. 규격 전문은 `template/README.md`, 조립 코드는 `template/make_report.py`입니다.

두 가지 길이 있습니다.

1. **결과보고서를 데이터 파일로**: JSON 하나를 쓰고 `render_result.py`로 렌더합니다. 결재란·문서번호·리뷰 도장이 자동입니다. 결재 절차는 `skills/approval-line/SKILL.md`입니다.
2. **보고서를 Python으로 직접 조립**: 검토보고서처럼 표·차트가 많은 문서는 `make_report.py` 함수를 씁니다(아래 "직접 조립").

## 본문 순서 (고정)

1. 요약 (`summary`)
2. 상태 변화 (`chg`)
3. `□ 1. 개요`, `□ 2. 배경`, `□ 3. 변경 내용`, `□ 4. 검증 결과`, `□ 5. 위험 요소`, `□ 6. 판정`
4. 판정 상자 (`verdict`, □6 안)
5. 차트가 있으면 붙임 (`figure`, 직접 조립만)

## 1. 결과보고서를 데이터 파일로

### 입력 데이터 예

예시 파일은 이 폴더의 `example_result.json`입니다. `sampleReviews`는 예시 렌더용이고 실제 파일에는 넣지 않습니다.

```json
{
  "form": "result-report",
  "version": 1,
  "title": "제목",
  "target": "링크에 보일 대상 이름",
  "url": "https://example.com/review",
  "approval": {"steps": [
    {"role": "기안", "title": "담당", "name": "홍길동", "date": "2026-10-31"},
    {"role": "결재", "title": "최종 결재자", "name": "김가상"}
  ]},
  "summary": ["한 줄은 개조식으로 끝냄."],
  "change": {"before": ["이전"], "after": ["이후"]},
  "overview": {"table": {"headers": ["구분", "내용"], "rows": [["대상", "…"]]}},
  "background": {"items": ["배경", {"text": "배경 2", "sub": ["세부"]}]},
  "changes": {"items": ["변경"], "notes": ["참고"]},
  "verification": {"items": ["검증"]},
  "risks": {"items": ["위험"]},
  "verdict": {"kind": "ok", "items": ["근거."]}
}
```

- `overview`~`risks`는 □1~□5이고 모두 있어야 합니다. 각각 `items`(○ 문장, `{text, sub}`이면 아래 `-`), `table`, `notes`(※) 중 하나 이상을 둡니다.
- `verdict`는 □6 판정입니다. `kind`는 `ok` ✔ 머지 가능, `warn` ▲ 확인 필요, `hold` ✖ 보류, `done` ✔ 머지 완료. 선택 `order`는 권장 머지 순서입니다.
- 판정은 기안자의 의견이고, 결재 상태(`진행`, `반려`, `승인`)는 리뷰에서 계산하는 다른 값입니다. 결재 상태는 파일에 적지 않습니다.

### 실행 명령

저장소 루트에서 실행합니다.

```bash
python3 skills/report-format/render_result.py skills/report-format/example_result.json out/보고-제목_결과보고서.pdf --number 42
python3 skills/report-format/render_result.py result.json out/보고-제목_결과보고서.pdf --pr 42
```

- `--number 42`: Origin을 읽지 않고 문서번호 `보고-2026-0042`만 찍습니다. 도장은 `sampleReviews`.
- `--pr 42`: 그 번호의 Origin PR에서 리뷰와 머지 상태를 읽습니다.

### 결과 위치

- PDF: 명령에 준 경로. 이름은 `보고-{짧은 제목}_결과보고서.pdf`로 합니다. `보고-`는 문서번호 접두어이고, 번호(`보고-2026-0042`의 연도·PR 번호)는 렌더할 때 머리에 찍으므로 파일 이름에는 넣지 않습니다.
- HTML: 같은 폴더, 같은 이름의 `.html`
- 터미널에 한 줄 JSON: `docNumber`, 결재 상태 `status`, 현재 차례 `turn`, 칸별 도장, 결재 규칙 경고 `warnings`(검토 2칸 등은 `경고: …`를 알리고 그대로 렌더)

머리 오른쪽 결재란은 기안·(검토)·결재 칸입니다. 머지 기록(`merge 대기`, `10/31 merge`, 전결이면 전결 칸 아래 `집행: 이름 10/31`)은 결재란 칸 아래에, `stage/*`로의 중간 머지는 결재란 밖에 `취합: …`으로 찍습니다. 규칙은 `skills/approval-line/SKILL.md`의 "머지 기록"입니다.

## 2. 직접 조립

`template`을 모듈 경로에 넣은 뒤 불러옵니다. 제목, 날짜, 기안자, 링크는 이번 문서의 값만 넣습니다.

```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "template"))
from make_report import *

body = (
    summary(["한 줄은 개조식으로 끝냄."])
    + chg(["이전"], ["이후"])
    + section("1. 개요", ul(["내용"]))
    + section("2. 배경", ul(["내용"]))
    + section("3. 변경 내용", ul(["내용"]))
    + section("4. 검증 결과", ul(["내용"]))
    + section("5. 위험 요소", ul(["내용"]))
    + section("6. 판정", verdict("ok", "https://example.com/review", ["근거."]))
)
HTML = document(header="PR #n 검토 보고", body=body, kind="검 토 보 고 서", title="제목",
                date="2026-11-01", author="기안자", url="https://example.com/review", target="대상",
                approver="결재자", approver_note="merge 대기", doc_no="보고-2026-0042")
```

- 결과 보고서의 `kind`는 `결 과 보 고 서`입니다. 글자 사이에 공백을 둡니다.
- `ul`에 문자열을 주면 `○`, `(문장, [하위])`를 주면 하위가 `-`입니다. 참고는 `note`입니다.
- 색은 넣지 않습니다. 메일 제목은 `[보고] … 결과 보고의 건`입니다.

렌더 확인:

```bash
python3 skills/report-format/template/make_report.py skills/report-format/template/example_content.py out/sample.pdf
```

## 검사

`verify(pdf)`가 쪽 수, 허용 서체(Noto Sans CJK KR, Noto Serif CJK KR, Gothic A1)만 쓰였는지(`disallowed_fonts`가 비어야 함), 쪽마다 채도(`max_chroma`가 0이어야 함)를 돌려줍니다. 저장소 전체 렌더 테스트는 `python3 -m pytest tests`입니다.

## 흔한 오류

| 메시지 | 고칠 곳 |
|---|---|
| `□ 3. 변경 내용(changes)이 없습니다.` | □1~□5 키를 모두 둡니다. |
| `verdict는 kind(ok, warn, hold, done), …` | `verdict.kind` 값 |
| `overview.table은 headers와 같은 칸 수의 rows여야 합니다.` | 표 행의 칸 수 |
| `PDF를 만들지 못했습니다.` / 멈춤 | `google-chrome-stable`이 있는지 확인합니다. 렌더는 임시 프로필로 Chrome을 띄웁니다. |
| `disallowed_fonts`에 다른 서체 | 허용 3가족 서체를 설치합니다. 없으면 대체 서체나 □ 글자가 나옵니다. |
