# Korean groupware documents

Print-ready Korean groupware documents in black, white, and gray. Five skills: a report (`report-format`), a proposal (`proposal-format`), an org chart (`org-chart`), the shared approval line (`approval-line`), and a self-check before opening a pull request or draft (`pre-draft-check`).

Version 0.2.0. Install: copy this repository into `~/.cursor/plugins/local/muilyoffice-korean-groupware-documents`, then restart Cursor.

버전 0.2.0입니다. 설치는 이 저장소를 `~/.cursor/plugins/local/muilyoffice-korean-groupware-documents`에 복사하고 Cursor를 다시 켭니다.

스킬 5개(`report-format`, `proposal-format`, `org-chart`, `approval-line`, `pre-draft-check`)가 들어 있습니다. Cursor와 Grok Bot에서 각각 무엇이 확인됐는지는 아래 "Cursor and Grok Bot" 절, 외부로 나가는 호출과 필요한 자격 증명은 "External calls and credentials" 절에 적습니다.

**Privacy.** The plugin files themselves send nothing: they have no telemetry and no MCP server of their own, and none of their scripts calls a MuilyOffice server. An optional skill instruction, described below, tells your bot how to call a MuilyOffice server. The scripts' only outside call is your own `origin` CLI on your computer. With `--pr N`, `skills/approval-line/approval.py` reads the PR's URL, merge time, merger, base branch, and reviews, and prints those names into the document on your computer. `skills/pre-draft-check/check.py` reads the list of open and draft PRs and their changed file names. When you open an approval PR, the agent steps in `skills/approval-line/SKILL.md` use the same CLI to open it and request reviewers. Separately, the "MCP로 기안 올리기" section of `skills/pre-draft-check/SKILL.md` tells your bot how to send a drafter, document kind, title, and body to the MuilyOffice server's MCP tool `draft_document` with its own bot key. If your bot does that, the server receives at least those four fields and the bot key used to sign in, and opens a draft PR in the repository the MuilyOffice server is configured for (by default the server operator's own repository; a customer's repository only if your bot key is registered to one), and its description contains the document body. The server code does not store the body anywhere except the draft PR. Its logs record result codes, failure stages and error names, and the draft branch name contains a short hash of the input. Hosting-platform logs may exist separately and are not described here. This section is not a privacy policy.

**Terms.** Use of this plugin is governed by the MIT License in `LICENSE`, and the plugin is provided "AS IS".

MuilyOffice also offers a separate paid service, the MuilyOffice web app. This plugin works without it. The plugin files contain no call to the web app or to any MuilyOffice server, and the scripts' only outside call is your own `origin` CLI. The `pre-draft-check` skill does tell your bot how to call the MuilyOffice server's MCP tool `draft_document` with its own bot key (see "External calls and credentials").
This plugin is a separate product from the web app. In this version, the core features need no MuilyOffice account or purchase; only the optional bot call to the MuilyOffice server needs a bot key issued by that server.

**개인정보.** 플러그인 파일 자체는 아무것도 보내지 않습니다. 원격 수집(텔레메트리)과 자체 MCP 서버가 없고, 스크립트는 MuilyOffice 서버를 부르지 않습니다. 다만 선택 기능으로, 봇이 MuilyOffice 서버를 부르는 방법을 안내하는 스킬 절이 있습니다(아래). 스크립트가 밖으로 부르는 것은 사용자 컴퓨터의 `origin` CLI뿐입니다. `skills/approval-line/approval.py`에 `--pr N`을 주면 PR 주소·머지 시각·머지한 사람·대상 브랜치·리뷰를 읽어, 그 이름을 사용자 컴퓨터의 문서에 넣습니다. `skills/pre-draft-check/check.py`는 열린 PR·초안 PR 목록과 바뀐 파일 이름을 읽습니다. 결재 PR을 열 때는 `skills/approval-line/SKILL.md`의 에이전트 단계가 같은 CLI로 PR을 열고 리뷰를 요청합니다. 이와 별도로 `skills/pre-draft-check/SKILL.md`의 "MCP로 기안 올리기" 절은 사용자의 봇이 자기 봇별 키로 MuilyOffice 서버의 MCP 도구 `draft_document`에 기안자·문서종류·제목·본문을 보내는 방법을 안내합니다. 봇이 그렇게 부르면 서버는 최소한 이 네 칸과 로그인에 쓰는 봇별 키를 받고, MuilyOffice 서버가 설정된 저장소에 초안 PR을 엽니다(기본은 서버 운영자의 저장소이고, 봇별 키가 고객 저장소에 등록된 경우에만 그 저장소입니다). 그 PR 본문에는 문서 본문이 들어갑니다. 서버 코드는 초안 PR 밖에는 본문을 저장하지 않습니다. 로그에는 결과 코드·실패 단계·오류 이름이 남고, 초안 브랜치 이름에는 입력의 짧은 해시가 들어갑니다. 호스팅 플랫폼의 기록이 별도로 있을 수 있으며 여기서는 설명하지 않습니다. 이 절은 개인정보처리방침이 아닙니다.

**이용 조건.** 이 플러그인의 이용은 `LICENSE`의 MIT 라이선스를 따르며, "있는 그대로(AS IS)" 제공됩니다.

MuilyOffice에는 별도 유료 서비스인 MuilyOffice 웹앱이 있습니다. 이 플러그인은 웹앱 없이 동작합니다. 플러그인 파일에는 웹앱이나 MuilyOffice 서버로 보내는 호출이 들어 있지 않고, 스크립트가 밖으로 부르는 것은 사용자가 로그인해 둔 `origin` CLI뿐입니다. 다만 `pre-draft-check` 스킬은 봇이 자기 봇별 키로 MuilyOffice 서버의 MCP 도구 `draft_document`를 부르는 방법을 안내합니다("External calls and credentials" 절).
이 플러그인은 웹앱과 별개 제품입니다. 이 판에서는 핵심 기능에 MuilyOffice 계정이나 구매가 필요 없습니다. 선택 기능인 서버 호출에만 그 서버가 발급한 봇별 키가 필요합니다.

The plugin id is the `name` field in `.cursor-plugin/plugin.json`. That field is the only place the publisher prefix is defined. Change it there to rename the plugin.

## Operating rules

The operating rules applied to all documents are kept outside the plugin bundle. They have mandatory and optional rules:
- Mandatory: approval line structure, document numbering, merge permission, release tagging
- Optional: team name format, drafter display

The approval line part of them is in `skills/approval-line/SKILL.md`.

## English

Install this repository as a Cursor plugin. The manifest is `.cursor-plugin/plugin.json`.

Ask for a Korean result report (결과 보고서) or review report (검토 보고서). The agent follows `skills/report-format/SKILL.md`.

Render the checked-in sample from the repository root:

```bash
python3 skills/report-format/template/make_report.py \
  skills/report-format/template/example_content.py \
  sample.pdf
```

The sample is a render check. A new report carries that document's own title, date, author, and link. Format rules are in `skills/report-format/template/README.md`.

A proposal (품의서), a result report (결과보고서), and an org chart (조직도) are rendered the same way from a JSON data file. Each writes a PDF and an HTML file next to it.

```bash
python3 skills/proposal-format/render_proposal.py skills/proposal-format/example_proposal.json out/proposal.pdf --number 42
python3 skills/report-format/render_result.py skills/report-format/example_result.json out/result.pdf --number 42
python3 skills/org-chart/render_org_chart.py skills/org-chart/example_organization.json out/org.pdf
```

The approval procedure shared by the proposal and the result report is `skills/approval-line/SKILL.md`.

## 한국어

이 저장소를 Cursor 플러그인으로 설치합니다. 매니페스트는 `.cursor-plugin/plugin.json`입니다.

결과 보고서나 검토 보고서를 요청하면 `skills/report-format/SKILL.md`를 따릅니다.

저장소 루트에서 예시 보고서를 렌더합니다.

```bash
python3 skills/report-format/template/make_report.py \
  skills/report-format/template/example_content.py \
  sample.pdf
```

예시는 렌더 확인용입니다. 새 보고서에는 에이전트가 그 문서의 제목, 날짜, 기안자, 링크를 넣습니다. 규격은 `skills/report-format/template/README.md`입니다.

품의서, 결과보고서, 조직도도 같은 방식으로 데이터 파일(JSON)에서 렌더합니다. PDF와 같은 폴더에 HTML도 생깁니다. 명령은 위 English 절과 같습니다.

품의서·결과보고서가 함께 쓰는 결재 절차(기안·검토·결재)는 `skills/approval-line/SKILL.md`입니다.

## Cursor and Grok Bot

- Cursor: this is a Cursor Plugin (manifest `.cursor-plugin/plugin.json`). The manifest has no path fields, so Cursor uses default folder discovery: each `skills/<name>/SKILL.md` is a skill ([Plugins reference](https://cursor.com/docs/reference/plugins.md)). ▲ Not yet tested in the Cursor app.
- Grok Bot: Connect apps lists apps and packaged skills, and follows the team's Cursor connector policy set in the Team Marketplace ([settings](https://cursor.com/docs/grok-bot/settings.md), [teams](https://cursor.com/docs/grok-bot/teams.md)). ▲ The Grok Bot docs do not say which plugin folders Grok Bot reads. Not tested.
- Most of the approval-line rule is also written in `skills/approval-line/SKILL.md`, so a host that reads skills but not rules still gets most of it.

○ Cursor: 매니페스트에 경로 필드가 없어 기본 탐색을 씁니다. `skills/` 아래 `SKILL.md`가 있는 폴더는 스킬입니다. ▲ Cursor 앱에서 실제로 시험하지 않았습니다.
○ Grok Bot: '앱 연결(Connect apps)'에서 앱과 묶인 스킬(packaged skills)을 찾고, 팀 마켓의 Cursor 커넥터 정책을 따릅니다. ▲ Grok Bot 문서에는 어느 플러그인 폴더를 읽는지에 대한 문장이 없습니다. 시험하지 않았습니다.
○ 결재선 규칙 대부분은 `skills/approval-line/SKILL.md` 본문에도 있습니다. 규칙을 읽지 않고 스킬만 읽는 환경에서도 대부분이 전달됩니다.

## External calls and credentials

| Where | What it calls | Credential |
|---|---|---|
| `skills/approval-line/approval.py`, only with `--pr N` (used by `render_proposal.py`, `render_result.py`) | Runs the local `origin` CLI: `origin pr view N --json url,mergedAt,mergedBy,baseRefName` and `origin pr view N --json reviews`. The server address is whatever that CLI is set up for; no address is written in this repository. | The user's existing `origin` CLI login. The script reads no token and stores none. |
| `skills/approval-line/SKILL.md` (agent steps) | `origin pr create`, `origin pr reviewer request` | Same `origin` CLI login |
| `skills/pre-draft-check/check.py`, only for the open-PR file overlap check | Runs the local `origin` CLI: `origin pr list --state open` and `--state draft`, then `origin pr diff N --name-only` for each PR | Same `origin` CLI login |
| `skills/pre-draft-check/SKILL.md`, "MCP로 기안 올리기" (instructions for your bot; no code in the plugin makes this call) | Tells the bot to POST a JSON-RPC `tools/call` for `draft_document` (drafter, kind, title, body) to the MuilyOffice server's MCP address (ending in `/mcp`). The server opens a draft PR. No MCP address is written in the plugin. | The bot's own per-bot key in `Authorization: Bearer <key>`. The key is not written in the plugin. |
| `skills/report-format/template/make_report.py` (all PDF renders) | Local programs only: headless Chrome on a `file://` page, and `pdfinfo`, `pdffonts`, `pdftoppm` | None |

- The plugin declares no MCP server and no hooks, and has no telemetry. The manifest declares one optional variable, `webAppUrl` (the public address of the separate MuilyOffice web app, `https://{host}`); it is not a secret, and nothing in this plugin reads it or calls that address. The plugin needs no secret of its own.
- `https://example.com/review` in the samples is a link printed in the document, not fetched.
- Gothic A1 is not part of the plugin at run time. It is downloaded from `raw.githubusercontent.com` only when preparing the environment.

○ 플러그인 파일 자체는 서버를 부르지 않고, 원격 수집(텔레메트리)도 없습니다. 스크립트가 밖으로 부르는 것은 사용자 컴퓨터의 `origin` CLI 하나입니다. 렌더할 때 `--pr N`을 준 경우에만 `origin pr view`로 리뷰·머지 기록을 읽고, 기안 전 점검의 PR 겹침 항목은 `origin pr list`, `origin pr diff --name-only`를 부르며, 결재 PR을 열 때 에이전트가 `origin pr create`, `origin pr reviewer request`를 씁니다. 인증은 사용자가 이미 로그인해 둔 `origin` CLI의 것을 쓰고, 이 저장소의 코드는 토큰을 읽거나 저장하지 않습니다.
○ `pre-draft-check` 스킬의 "MCP로 기안 올리기" 절은 봇이 MuilyOffice 서버의 MCP 주소로 `Authorization: Bearer <봇별 키>`를 넣어 `draft_document`를 부르는 방법을 안내합니다. 이 호출은 봇이 하며, 플러그인 코드에는 들어 있지 않습니다. MCP 주소와 키는 플러그인에 적혀 있지 않습니다.
○ 그 밖의 프로그램(Chrome, poppler)은 이 컴퓨터 안에서만 돕니다. 규칙 파일에는 호출이 없습니다.
○ 이 플러그인에 넣어야 하는 비밀값은 없습니다.

## Plugin bundle

The distributed plugin is these paths only: `.cursor-plugin/plugin.json`, `LICENSE`, `README.md`, `skills/`.

○ 배포 묶음은 위 4개 경로뿐입니다.

## License

MIT. The manifest `license` field and the `LICENSE` file both say MIT.

The MIT License in `LICENSE` covers the code and documentation in this repository. It does not grant any right to use the names "Muilyzz Corp." (including any shortened form of it) or "MuilyOffice", or any other name or mark of Muilyzz Corp., to identify a product or service. Muilyzz Corp. reserves any rights it has in those names.

플러그인 라이선스는 MIT입니다. 매니페스트 `license` 값과 `LICENSE` 파일이 같은 MIT입니다.

`LICENSE`의 MIT 라이선스는 이 저장소의 코드와 문서에 적용됩니다. 'Muilyzz Corp.'(줄인 표기 포함)와 'MuilyOffice' 등 Muilyzz Corp.의 이름·표지를 상품이나 서비스의 표지로 쓸 권리는 이 라이선스로 허락하지 않으며, Muilyzz Corp.는 이 이름들에 대해 가진 권리를 유보합니다.

This plugin's documentation and skills were written largely with AI coding tools (such as Cursor agents).

이 플러그인의 문서와 스킬은 대부분 AI 코딩 도구(Cursor 에이전트 등)로 작성했습니다.
