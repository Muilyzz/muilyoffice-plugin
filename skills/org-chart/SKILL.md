---
name: org-chart
description: >
  Render the organization data ({members:[...]} as in example_organization.json) to a
  monochrome Korean org chart document (HTML and PDF): a tree that follows reports_to
  and a member table with each member's approval chain. Use when asked to draw or print
  the 조직도.
---

# 조직도

조직도 데이터(JSON)를 흑백 조직도 문서로 그립니다. 첫 쪽은 보고선(`reports_to`)을 따르는 나무 그림, 둘째 쪽은 구성원 표입니다. 표의 결재선 칸은 `approver`를 위로 따라간 이름들입니다(예: `결재자A → 책임자A`).

## 입력 데이터 예

형식은 아래 필드 표를 따릅니다. 이 폴더의 `example_organization.json`은 가상 조직(예시 회사)의 예시이고 실제 조직 데이터가 아닙니다. 같은 형식의 자기 조직 데이터 파일을 넣어 렌더합니다.

```json
{
  "members": [
    {"id": "head", "name": "책임자A", "kind": "human", "team": null, "role": "가상 예시 역할",
     "reports_to": null, "approver": null, "delegation": null, "spec": null, "note": "가상 조직(예시 회사), 실제 조직 아님"},
    {"id": "staff-b", "name": "담당자B", "kind": "bot", "team": "B팀", "role": "가상 예시 역할",
     "reports_to": "lead-b", "approver": "lead-b", "assignment": "common", "delegation": null, "spec": null, "pending": true, "note": "▲ 잠정값: team"}
  ]
}
```

`assignment`, `pending`, `note`만 선택이고 나머지 필드는 값이 없어도 `null`로 적습니다(없으면 거부).

| 필드 | 뜻 |
|---|---|
| `id` | 고유 식별자. 다른 구성원의 `reports_to`, `approver`가 이 값을 가리킵니다. |
| `name`, `role` | 상자에 적는 이름과 역할 |
| `kind` | `human`(사람, 이중선 상자) 또는 `bot`(봇, 단선 상자) |
| `team` | 팀 이름. `null`이면 `직속`(`pending` 구성원이면 `미정`) |
| `reports_to` | 보고 상위자 id. 최상위는 `null`. 나무의 선이 됩니다. `null`인 구성원은 모두 나무 맨 위에 그립니다. `pending` 구성원의 `null`은 미정이라 표의 보고 칸에 `미정`을 적습니다(나무에서는 맨 위, 이름 옆 ▲). |
| `approver` | 결재 상위자 id. 표의 결재선 칸이 됩니다. `null`이면 `-`(`pending` 구성원이면 `미정`)이고 `reports_to`로 대신하지 않습니다(같아도 둘 다 적음). |
| `assignment` | `deliverable`(산출물) 또는 `common`(공통), 선택 |
| `delegation`, `spec`, `note` | 전결 범위, 작업 사양, 비고. 표에 그대로 적습니다. `delegation`·`spec`이 `null`이면 `-`(해당 없음), `pending` 구성원이면 `미정`. `spec`은 `null`이 아니면 `model`(모델 id 문자열)이 있어야 합니다. |
| `pending` | `true`면 이름 옆에 ▲를 붙입니다. `null`인 필드는 미정, 값이 있고 `note`에 적힌 필드(예 `▲ 잠정값: team`)는 잠정값입니다. 렌더러는 `note`를 풀어 읽지 않고 표의 비고 칸에 그대로 적습니다. |

## 실행 명령

저장소 루트에서 실행합니다.

```bash
python3 skills/org-chart/render_org_chart.py skills/org-chart/example_organization.json out/org.pdf --date 2026-10-31
```

- `--date`: 머리의 기준일. 없으면 오늘 날짜입니다.
- `--title`: 제목. 없으면 `조직도`입니다.

## 결과 위치

- PDF: 명령에 준 경로(`out/org.pdf`), 가로 A4 두 쪽
- HTML: 같은 폴더의 `out/org.html`
- 터미널에 한 줄 JSON: `pdf`, `html`, 구성원 수 `members`

## 흔한 오류

| 메시지 | 고칠 곳 |
|---|---|
| `조직도 데이터는 {"members": [...]} 하나여야 합니다.` | 맨 바깥을 `members` 배열 하나로 둡니다. |
| `…: reports_to가 가리키는 xxx가 없습니다.` | 오타이거나 그 구성원이 빠졌습니다. id를 맞춥니다. |
| `…: approver가 돌고 돕니다.` | A의 상위가 B, B의 상위가 A처럼 고리가 있습니다. |
| `…: 형식에 없는 필드입니다: …` | 형식에 없는 필드를 지웁니다. |
| `…: 필드가 없습니다: team, … 값이 없으면 null로 적습니다.` | 빠진 필드를 `null`로라도 적습니다. |
| `…: spec에는 model(모델 id 문자열)이 있어야 합니다.` | `spec`에 `model`을 넣거나 `spec`을 `null`로 합니다. |
| 팀이 많아 상자가 좁음 | 한 상위자 아래 팀이 많으면 상자가 좁아집니다. 표(둘째 쪽)에서 내용을 확인합니다. |
