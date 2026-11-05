---
name: proposal-format
description: >
  Draft a Korean proposal (품의서) data file from a plan, open its approval pull request,
  and render the monochrome document (HTML and PDF) with a 기안·결재 approval box and a
  품의-YYYY-NNNN document number. Approval comes from Origin pull request reviews.
---

# 품의서

일을 시작하기 전에 "이렇게 하겠습니다"를 최종 결재자에게 올리는 결재 문서입니다. 플랜에서 품의서 데이터 파일(JSON)을 만들고, 그 파일로 결재 PR을 엽니다. 결재 PR 올리기, 검토자 요청, 리뷰를 결재란으로 읽는 절차와 머지 권한은 `skills/approval-line/SKILL.md` 한 곳에 있습니다.

## 입력 데이터 예

예시 파일은 이 폴더의 `example_proposal.json`입니다. `sampleReviews`는 예시 렌더용이고 실제 파일에는 넣지 않습니다.

```json
{
  "form": "proposal",
  "version": 1,
  "title": "품의서·결과보고서·조직도 서식 도입",
  "verdict": "ok",
  "approval": {
    "steps": [
      {"role": "기안", "title": "담당", "name": "홍길동", "date": "2026-10-31"},
      {"role": "결재", "title": "최종 결재자", "name": "김가상"}
    ]
  },
  "sections": [
    {"title": "추진 개요", "items": ["무엇을 왜 하는지 개조식으로 적음"]},
    {"title": "추진 내용", "items": ["어떻게 할지"]},
    {"title": "확인 필요 사항", "items": ["▲ 아직 모르는 것"]}
  ]
}
```

| 필드 | 뜻 |
|---|---|
| `title` | 제목. 플랜 문서의 첫 제목 |
| `approval.steps` | 결재선. 품의서는 `[기안(봇), 결재(최종 결재자)]` 두 칸이고 검토 칸을 두지 않습니다. 검토 칸이 있으면 경고 후 그대로 렌더합니다. |
| `sections` | 본문. `title`은 □ 없이 적고(렌더가 □를 붙임), `items`의 문장은 ○로 그립니다. |
| `verdict` | 판정(선택). `ok` ✔ 머지 가능, `warn` ▲ 확인 필요, `hold` ✖ 보류 |
| `prUrl` | 관련근거 링크(선택). 없고 `--pr`를 주면 Origin PR 주소를 씁니다. |

- 결재 상태(`진행`, `반려`, `완료`, `확인 필요`)는 파일에 적지 않습니다. 렌더가 리뷰에서 계산해 머리의 `상태` 줄에 찍습니다.
- 판정(`verdict`)은 기안자가 적는 의견이고 결재 상태와 다른 필드입니다. 판정 기호와 문구는 결과보고서와 같은 `make_report.py`의 `VERDICTS`를 씁니다.
- 문서번호는 파일에 적지 않습니다. 렌더할 때 PR 번호로 `품의-YYYY-NNNN`을 찍습니다. 같은 PR의 결과보고서는 `보고-YYYY-NNNN`입니다.
- 같은 PR에 품의서가 둘 이상이면 문서번호는 같고 파일 이름 뒤의 짧은 제목으로 구분합니다(`proposal-서식도입.json`, `proposal-조직도.json`). 파일 이름에는 PR 번호를 넣지 않습니다.

## 실행 명령

저장소 루트에서 실행합니다.

```bash
python3 skills/proposal-format/render_proposal.py skills/proposal-format/example_proposal.json out/proposal.pdf --number 42
python3 skills/proposal-format/render_proposal.py proposal.json out/proposal.pdf --pr 42
```

- `--number 42`: Origin을 읽지 않습니다. 문서번호만 `품의-2026-0042`로 찍고 도장은 `sampleReviews`로 채웁니다.
- `--pr 42`: 그 번호의 Origin PR에서 리뷰·머지 상태·주소를 읽고 문서번호를 찍습니다.

## 결과 위치

- PDF: 명령에 준 경로(`out/proposal.pdf`), A4 한 쪽
- HTML: 같은 폴더의 `out/proposal.html`
- 터미널에 한 줄 JSON: `docNumber`, 결재 상태 `status`, 현재 차례 `turn`, 칸별 도장 `boxes`, 결재 규칙 경고 `warnings`

머리는 문서번호·기안자·기안일·상태·관련근거 표와, 그 오른쪽의 결재란(담당 기안 / 최종 결재자 결재)입니다. 전결 없이 마지막 칸의 최종 결재자가 승인하고 main에 머지하면 마지막 칸 아래 `10/31 merge`입니다. 결재 칸 하나가 전결(`mark: 전결`)로 승인하고 최종 결재자가 main에 머지하면 마지막 칸은 사선이고, 전결 칸 아래 `머지: 이름(전결)`입니다. 이름은 전결한 사람입니다. `stage/*`로의 중간 머지는 결재란 밖에 `취합: …`으로 적습니다. 규칙은 `skills/approval-line/SKILL.md`의 "머지 기록"입니다.

전결 머지 예시와 전결 없는 머지 예시: `example_proposal_jeongyeol.json`, `example_proposal_merge.json`. 두 예시의 `sampleMerge`는 Origin의 `mergedAt`·`mergedBy`·`baseRefName`을 대신하는 예시용 값이고 실제 파일에는 넣지 않습니다.

## 흔한 오류

| 메시지 | 고칠 곳 |
|---|---|
| `경고: 이 서식의 결재선에는 검토 칸을 두지 않습니다. …` (PDF는 나옴) | 규칙을 맞추려면 품의서 `steps`에서 검토 칸을 뺍니다. |
| `각 칸에는 role, title, name이 있어야 합니다.` | 옛 `작성`·`승인` 대신 `기안`·`결재`를 씁니다. `title`도 넣습니다. |
| `데이터 형식에 없는 칸입니다: docNumber, drafter, draftDate` | 옛 형식입니다. 문서번호는 렌더가 찍고, 기안자·기안일은 `steps[0]`의 `name`·`date`입니다. |
| `판정(verdict)은 ok, warn, hold 중 하나여야 합니다.` | `verdict` 값 |
| `google-chrome을 찾지 못했습니다.` | Chrome(`google-chrome-stable`)을 설치합니다. |
| PDF 글자가 □로 보임 | Noto Sans/Serif CJK KR과 Gothic A1 서체를 설치합니다. |
