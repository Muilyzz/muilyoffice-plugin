# Korean groupware documents

Print-ready Korean groupware documents in black, white, and gray. Four skills: a report (`report-format`), a proposal (`proposal-format`), an org chart (`org-chart`), and the shared approval line (`approval-line`).

Version 0.1.0. Install: copy this repository into `~/.cursor/plugins/local/muilyoffice-korean-groupware-documents`, then restart Cursor.

버전 0.1.0입니다. 설치는 이 저장소를 `~/.cursor/plugins/local/muilyoffice-korean-groupware-documents`에 복사하고 Cursor를 다시 켭니다.

스킬 4개(`report-format`, `proposal-format`, `org-chart`, `approval-line`)가 들어 있습니다. Cursor와 Grok Bot에서 각각 무엇이 확인됐는지는 아래 "Cursor and Grok Bot" 절, 외부로 나가는 호출과 필요한 자격 증명은 "External calls and credentials" 절에 적습니다.

Privacy policy and terms of service: not yet published. Their links go here once they are.

MuilyOffice also offers a separate paid service, the MuilyOffice web app. This plugin works without it and contains no call to the web app or to any MuilyOffice server; its only outside call is your own `origin` CLI (see "External calls and credentials").
This plugin is a separate product from the web app and needs no MuilyOffice account or purchase.

개인정보처리방침·이용약관: 아직 게시 전입니다. 게시되면 이 자리에 링크를 둡니다.

MuilyOffice에는 별도 유료 서비스인 MuilyOffice 웹앱이 있습니다. 이 플러그인은 웹앱 없이 동작하며, 웹앱이나 MuilyOffice 서버로 보내는 호출이 들어 있지 않습니다. 외부로 나가는 호출은 사용자가 로그인해 둔 `origin` CLI뿐입니다("External calls and credentials" 절).
이 플러그인은 웹앱과 별개 제품이며, MuilyOffice 계정이나 구매가 필요 없습니다.

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

- Cursor: this is a Cursor Plugin (manifest `.cursor-plugin/plugin.json`). The manifest has no path fields, so Cursor uses default folder discovery: each `skills/<name>/SKILL.md` is a skill, and `.md`/`.mdc`/`.markdown` files in `rules/` are rules ([Plugins reference](https://cursor.com/docs/reference/plugins.md)). ▲ Not yet tested in the Cursor app.
- Grok Bot: Connect apps lists apps and packaged skills, and follows the team's Cursor connector policy set in the Team Marketplace ([settings](https://cursor.com/docs/grok-bot/settings.md), [teams](https://cursor.com/docs/grok-bot/teams.md)). ▲ The Grok Bot docs do not say which plugin folders Grok Bot reads or whether plugin rules apply. Not tested.
- Most of the approval-line rule is also written in `skills/approval-line/SKILL.md`, so a host that reads skills but not rules still gets most of it.

○ Cursor: 매니페스트에 경로 필드가 없어 기본 탐색을 씁니다. `skills/` 아래 `SKILL.md`가 있는 폴더는 스킬, `rules/`의 `.md`·`.mdc`·`.markdown` 파일은 규칙입니다. ▲ Cursor 앱에서 실제로 시험하지 않았습니다.
○ Grok Bot: '앱 연결(Connect apps)'에서 앱과 묶인 스킬(packaged skills)을 찾고, 팀 마켓의 Cursor 커넥터 정책을 따릅니다. ▲ Grok Bot 문서에는 어느 플러그인 폴더를 읽는지, 플러그인 규칙(`rules/`)이 적용되는지에 대한 문장이 없습니다. 시험하지 않았습니다.
○ 결재선 규칙 대부분은 `skills/approval-line/SKILL.md` 본문에도 있습니다. 규칙을 읽지 않고 스킬만 읽는 환경에서도 대부분이 전달됩니다.

## External calls and credentials

| Where | What it calls | Credential |
|---|---|---|
| `skills/approval-line/approval.py`, only with `--pr N` (used by `render_proposal.py`, `render_result.py`) | Runs the local `origin` CLI: `origin pr view N --json url,mergedAt,mergedBy` and `origin pr view N --json reviews`. The server address is whatever that CLI is set up for; no address is written in this repository. | The user's existing `origin` CLI login. The script reads no token and stores none. |
| `skills/approval-line/SKILL.md` (agent steps) | `origin pr create`, `origin pr reviewer request` | Same `origin` CLI login |
| `skills/report-format/template/make_report.py` (all PDF renders) | Local programs only: headless Chrome on a `file://` page, and `pdfinfo`, `pdffonts`, `pdftoppm` | None |

- No MCP server, no hooks, no `variables` in the manifest. The plugin needs no secret of its own.
- `https://example.com/review` in the samples is a link printed in the document, not fetched.

○ 외부로 나가는 호출은 `origin` CLI 하나입니다. 렌더할 때 `--pr N`을 준 경우에만 `origin pr view`로 리뷰·머지 기록을 읽고, 결재 PR을 열 때 에이전트가 `origin pr create`, `origin pr reviewer request`를 씁니다. 인증은 사용자가 이미 로그인해 둔 `origin` CLI의 것을 쓰고, 이 저장소의 코드는 토큰을 읽거나 저장하지 않습니다.
○ 그 밖의 프로그램(Chrome, poppler)은 이 컴퓨터 안에서만 돕니다. 규칙 파일에는 호출이 없습니다.
○ 이 플러그인에 넣어야 하는 비밀값은 없습니다.

## Plugin bundle

The distributed plugin is these paths only: `.cursor-plugin/plugin.json`, `LICENSE`, `README.md`, `skills/`.

○ 배포 묶음은 위 4개 경로뿐입니다.

## License

MIT. The manifest `license` field and the `LICENSE` file both say MIT. Names and logos are not licensed under the license; all rights reserved.

플러그인 라이선스는 MIT입니다. 매니페스트 `license` 값과 `LICENSE` 파일이 같은 MIT입니다. 이름과 로고는 이 라이선스 대상이 아니며 권리는 유보됩니다. ▲ 법률 자문이 아닙니다. 법무 확인이 필요합니다.
