---
name: pre-draft-check
description: >
  Before opening a pull request or a Korean groupware draft (기안), run a self-check on the
  title, body and changed files: document number format, forbidden words, leaked secrets,
  file overlap with other open pull requests, file:line and count claims in the body, and
  error codes and agreed terms. Each item is ✔ (passed) or ▲ (needs a look) with a reason.
---

# 기안 전 점검

PR이나 기안을 올리기 **전에** 기안자(사람이든 봇이든)가 스스로 돌리는 점검표입니다. 점검은 `check.py` 하나가 합니다. Python 3 표준 라이브러리만 씁니다.

## 판정은 두 가지뿐

- `✔` 통과: 확인했고 문제가 없습니다.
- `▲` 확인 필요: 문제가 있거나, **확인하지 못했습니다**. 사유를 함께 적습니다.

확인하지 못한 것을 ✔로 찍지 않습니다. 입력을 주지 않은 항목, 명령이 없어 못 읽은 항목은 모두 ▲입니다.

입력이 잘못되어도(목록 파일이 없음, 용어 목록이 JSON 객체가 아님, `re:` 정규식이 틀림 등) 멈추지 않습니다. 그 항목만 ▲로 적고 사유를 쓴 뒤 다음 항목으로 넘어갑니다.

## 점검 항목

| 번호 | 항목 | 보는 것 | 필요한 입력 |
|---|---|---|---|
| 1 | 문서번호·제목 형식 | 제목의 `[종류-연도-번호]`와 본문 첫 10줄의 `문서번호:` 줄이 각각 1개이고 같은지, 번호가 PR 번호 4자리와 같은지, 연도가 맞는지 | `--title`, `--pr-number` |
| 2 | 금지어 | 제목·본문·바꾼 파일에 금지어가 있는지 | `--forbidden` |
| 3 | 비밀·토큰 노출 | 토큰·키·개인 키·인증 헤더 값·이메일 주소 모양 | 없음(본문만 봐도 됨) |
| 4 | 다른 열린 PR과 파일 겹침 | 열린 PR·초안 PR이 같은 파일을 바꾸는지 | `--files`, `origin` 명령 |
| 5 | 본문 숫자·줄 번호 | 본문에 적은 `파일:줄`, 코드 인용 블록, 파일 건수('바꾼 파일 N개', '바꾼 파일 (새 파일, N개)', 'N개 파일을 고쳤습니다', 'N files changed')가 실제와 같은지. 확인할 곳이 0곳이면 ▲ | `--root`, `--files` |
| 6 | 오류 코드·약속서 용어 | 본문의 오류 코드가 목록에 있는지, 약속서에서 정한 말 대신 다른 말을 쓰지 않았는지 | `--terms` |
| 7 | 통과 못한 항목 | 1~6 중 ▲인 항목 번호 | 없음 |

## 쓰는 법

```bash
python3 check.py \
  --body 본문.md \
  --title "[품의-2026-0012] 빈 이름 처리" \
  --files 바꾼파일.txt \
  --forbidden 금지어.txt \
  --terms 용어.json \
  --root 저장소폴더 \
  --pr-number 12
```

- 끝나면 ▲가 하나도 없을 때만 종료 코드 0입니다. ▲가 있으면 1입니다.
- `--json`을 붙이면 항목마다 `no`, `name`, `mark`, `detail`을 JSON으로 냅니다.
- PR을 열기 전에는 PR 번호가 없습니다. 번호 자리에 `미부여`를 쓰면 1번은 ▲로 남습니다. PR을 연 뒤 번호를 채우고 다시 돌립니다.
- 규칙대로 해도 1번이 ▲일 수 있습니다. PR을 열기 전이라 `미부여`를 쓴 경우, 다시 연 PR이 옛 번호를 그대로 쓰는 경우(번호가 지금 PR 번호와 다름)입니다. 이때는 사유가 규칙과 맞는지 보고 PR 본문에 ▲로 적습니다.

### 입력 파일

모두 쓰는 사람이 만들어 넘깁니다. 이 스킬에는 금지어 원문이 들어 있지 않습니다.

- **바꾼 파일 목록** (`--files`): 한 줄에 경로 하나. `--root` 기준 경로입니다. `git diff --name-only main...HEAD > 바꾼파일.txt`처럼 만들면 됩니다. 지운 파일이 들어 있으면 `--allow-deleted`를 붙입니다.
- **금지어 목록** (`--forbidden`): 한 줄에 하나. `#`로 시작하는 줄은 설명입니다. `re:`로 시작하면 정규식으로 찾습니다. 영문은 대소문자를 가리지 않습니다.
- **용어 목록** (`--terms`): JSON입니다.

```json
{
  "errorCodes": ["error:empty_name"],
  "codePattern": "[a-z][a-z0-9_]*:[a-z][a-z0-9_]*",
  "terms": {"이력": ["로그 기록"]}
}
```

  - `errorCodes`: 약속서에 적힌 오류 코드.
  - `codePattern`: 본문의 `` `…` `` 안 글자 가운데 이 모양이면 오류 코드로 봅니다. 없으면 `앞말:뒷말` 모양을 봅니다.
  - `terms`: `"바른 말": ["쓰지 않을 말", …]`.

### 문서번호 형식 바꾸기

기본은 `품의`·`보고` 두 종류, `{종류}-{연도 4자리}-{번호 4자리}`입니다. 회사마다 다르면 `--kinds 품의,보고,안내`, `--unassigned 미정`, `--year 2026`으로 바꿉니다.

### 열린 PR 읽기

4번은 `origin pr list --state open`과 `origin pr list --state draft`를 따로 불러 열린 PR·초안 PR을 모으고(open 목록에는 초안 PR이 없음), 각 PR을 `origin pr diff <번호> --name-only`로 읽습니다. `--pr-number`로 준 자기 PR은 뺍니다.

- `origin` 명령이 없거나, 명령이 실패하거나, 30초 안에 끝나지 않으면 ▲로 적고 다음 항목으로 넘어갑니다. 멈추지 않습니다.
- 한 상태에서 읽어 온 PR 수가 `--limit`(상태마다 기본 1000)에 닿으면 목록이 잘렸을 수 있어 ▲입니다. 상한 안이면 잘리지 않은 것으로 봅니다.
- 다른 명령을 쓰려면 `--origin-cmd`로 이름을 줍니다. 같은 인자와 출력 모양이어야 합니다.

## 가상 예시

`example/` 폴더는 가상 입력입니다(기안 김가상, 결재 이가상).

```bash
cd example
python3 ../check.py --body body.md --title "[품의-2026-0012] 빈 이름 처리" \
  --files files.txt --forbidden forbidden.txt --terms terms.json \
  --root project --year 2026 --pr-number 12
```

`origin` 명령이 없는 곳에서 돌리면 이렇게 나옵니다.

```text
기안 전 점검
✔ 1. 문서번호·제목 형식: 품의-2026-0012, 제목과 본문이 같습니다.
✔ 2. 금지어: 금지어 2개, 걸린 곳 0개.
✔ 3. 비밀·토큰 노출: 값 모양 12가지, 걸린 곳 0개.
▲ 4. 다른 열린 PR과 파일 겹침: 'origin' 명령이 없어 열린 PR 목록을 읽지 못했습니다.
✔ 5. 본문 숫자·줄 번호: 줄 참조·건수 3곳이 실제와 같습니다.
✔ 6. 오류 코드·약속서 용어: 오류 코드 1개·용어 1개 기준으로 어긋난 곳 0개.
▲ 7. 통과 못한 항목: ▲ 1개: 4
결과: 점검 6개 중 ✔ 5 / ▲ 1
```

## ▲가 나오면

- 고칠 수 있는 것(번호, 줄 번호, 금지어, 용어)은 고치고 다시 돌립니다.
- 비밀·토큰이 걸리면 그 값을 지우는 것만으로 끝내지 않습니다. 이미 커밋했다면 그 값을 폐기하고 새로 발급합니다.
- 확인할 수 없는 것(명령이 없음, 다른 환경)은 PR 본문에 `▲` 항목으로 사유와 함께 적습니다. 통과로 적지 않습니다.

## 하지 않는 것

- 점검(`check.py`)은 파일을 고치거나 PR을 열지 않습니다. 읽기만 합니다.
- 결재선·결재 상태는 보지 않습니다. 결재선은 `approval-line` 스킬이 봅니다.
- 비밀값 점검은 값 모양만 봅니다. 모양이 다른 비밀값은 잡지 못할 수 있습니다.

## MCP로 기안 올리기 (`draft_document`)

봇은 기안을 MCP 도구 `draft_document`(결재 문서 기안)로 올립니다. 봇은 자기 몫으로 받은 **봇별 키**로 부릅니다.

### 순서

1. 위의 기안 전 점검을 먼저 돌려 ▲를 고칩니다. 점검할 때만 `--title`에 `[종류-연도-미부여] 제목`을 줍니다. 번호가 없으니 1번이 ▲로 남는 것은 괜찮습니다.
2. `draft_document`에는 제목 앞의 `[…]`를 떼어 낸 제목과, `문서번호:`·`기안:` 줄을 뺀 본문을 보냅니다. 그 자리는 서버가 채웁니다.
3. 서버가 초안 PR 하나를 엽니다. 그 뒤 일은 사람이 PR을 보고 승인(머지)하는 것뿐입니다.

※ 서버는 문서 본문과 입력을 저장하지 않습니다. 열린 초안 PR은 지울 수 없고 닫기만 됩니다.

### 부르는 법

- 서버의 MCP 주소(끝이 `/mcp`)로 JSON-RPC 요청을 POST합니다.
- 머리글에 `Authorization: Bearer <봇별 키>`를 넣습니다.
- 키 값과 실제 주소는 문서·본문·대화 어디에도 적지 않습니다. 이 글의 `<봇별 키>`, `<서버 MCP 주소>`는 자리표시입니다.

※ 브라우저에서 부르지 않습니다. 요청에 `Origin` 머리글이 있으면 서버가 403으로 거부합니다.

### 입력 4칸 (모두 필수)

| 칸 | 넣는 것 |
|---|---|
| `drafter` | 기안자 이름. 조직도에 적힌 이름과 글자까지 같아야 합니다. 봇별 키의 주인과 같은 사람(봇)이어야 합니다. |
| `kind` | 문서종류 키. `approval-line` 스킬 `rules.json`의 `docNumber.kinds` 키(예: `proposal`, `report`)입니다. |
| `title` | PR 제목 한 줄. 줄바꿈·제어문자는 안 됩니다. 서버가 앞에 `[종류-연도-미부여]`를 붙이니 `[…]` 없이 보냅니다. |
| `body` | 마크다운 본문(`문서번호:`·`기안:` 줄 없이). 서버가 문서번호·결재선 블록을 맨 위에 붙이고, 본문은 그 아래에 그대로 둡니다. |

- 이 4칸 말고 다른 칸(예: `files`)을 넣으면 거부됩니다.
- 본문 첫 10줄에 `문서번호:`·`기안:` 줄이나 결재선 블록 표지를 넣지 않습니다. 그 자리는 서버가 채웁니다.
- 제목·본문이 너무 길면 `title_too_long`·`body_too_long` 응답의 `limit` 값을 따릅니다.

### 결과

- 성공: `ok`가 `true`, `code`가 `created`, `pullNumber`(PR 번호)가 옵니다. `branch`, `docNumber`, `url`(없을 수 있음)도 옵니다.
- 실패: `ok`가 `false`이고 `code`와 `status`가 옵니다. 경우에 따라 `field`, `limit`, `step`, `upstreamStatus`가 더 옵니다.

자주 보는 `code`:

| code | 뜻 | 할 일 |
|---|---|---|
| `invalid_arguments` | 입력 칸이 빠졌거나, 모양이 틀렸거나, 없는 칸이 있음 | `field`가 가리키는 칸을 고칩니다 |
| `forged_block_line` | 본문 첫 10줄에 문서번호·기안 줄이나 블록 표지가 있음 | 그 줄을 지웁니다 |
| `title_too_long` · `body_too_long` | 제목·본문이 한도보다 김 | `limit` 안으로 줄입니다 |
| `drafter_not_in_org_chart` | `drafter` 이름이 조직도에 없음 | 조직도의 이름과 똑같이 씁니다 |
| `drafter_not_key_member` | 요청의 `drafter` 이름이, 키가 가리키는 조직도 구성원과 다름 | 그 구성원의 조직도 이름을 씁니다. 키는 누구인지 가리킬 뿐이고, 본문에 다른 이름을 적어도 작성자가 되지 않습니다 |
| `member_ambiguous` | 같은 이름이 조직도에 여럿 | 조직도 담당자에게 알립니다 |
| `kind_not_in_rules` | `kind`가 문서종류 키 목록에 없음 | `rules.json`의 키를 씁니다 |
| `already_exists` | 같은 기안자가 같은 종류·제목·본문으로 이미 기안함 | 열린 초안 PR이 있으면 그것을 씁니다. 닫힌 기안을 다시 올리려면 제목이나 본문을 바꿔 부릅니다 |
| `branch_name_conflict` | 저장소에 이미 있는 브랜치(`draft` 또는 `draft/…`) 때문에 서버가 새 브랜치를 만들 수 없음 | 봇이 고칠 수 없습니다. 저장소 관리자에게 그 브랜치 정리를 부탁합니다 |
| `origin_error` | 저장소 서버를 부르다 실패함(`step`·`upstreamStatus`로 단계 표시) | 잠시 뒤 다시 부르고, 계속되면 알립니다. 다시 부르고 `already_exists`가 오면 앞 호출로 초안 PR이 이미 열렸는지 확인합니다 |
| `caller_unverified` | 키가 없거나 틀림(401) | 자기 봇별 키를 머리글에 바르게 넣었는지 확인합니다 |
| `rate_limited` | 호출 한도를 넘음(429) | 잠시 뒤 다시 부릅니다 |

※ `caller_unverified`·`rate_limited`는 도구 결과가 아니라 JSON-RPC 오류의 `error.data.code`로 옵니다.

### 가짜 예시

아래 이름·제목·본문은 모두 가짜입니다.

```http
POST <서버 MCP 주소>
Authorization: Bearer <봇별 키>
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "draft_document",
    "arguments": {
      "drafter": "홍길동",
      "kind": "proposal",
      "title": "회의실 예약 규칙 바꾸기",
      "body": "## 요지\n\n회의실 예약을 하루 전까지 하도록 바꿉니다.\n\n## 까닭\n\n당일 예약이 겹치는 일이 잦습니다."
    }
  }
}
```

성공하면 도구 결과가 이렇게 옵니다.

```json
{"ok": true, "code": "created", "pullNumber": "12", "url": null, "branch": "<서버가 정한 브랜치>", "docNumber": "품의-2026-미부여"}
```

키 주인과 `drafter`가 다르면 이렇게 옵니다.

```json
{"ok": false, "code": "drafter_not_key_member", "status": 403}
```

기안은 봇이 MCP(`draft_document`)로 올리고, 서버가 그 위에 문서번호·결재선 블록을 붙입니다. 사람은 승인(머지)만 합니다(승인은 결재선의 각 칸에서 하고, main 머지는 마지막 칸의 사람이 합니다).
