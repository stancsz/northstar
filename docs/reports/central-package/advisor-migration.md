# Codex Advisor migration

Goal: [central package](../../goal/central-package/GOAL.md). Status: complete for the assigned advisor files. Date: 2026-09-29. Source: `D:\github\subroute\skills\luna-advisor-escalation` and its two advisor-specific tests. No Subroute files were changed.

## Delivered

- Added `skills/codex-advisor/SKILL.md` with `name: codex-advisor`, Codex Advisor guidance, contents links, explicit task-wide consultation ceilings and Northstar recovery constraints. The current Codex worker keeps ownership. The file links to Northstar expert practice, the reader reference, and Subroute's current Compose configuration for the external experts service.
- Added `skills/codex-advisor/references/reader.md` and `agents/openai.yaml`. Both caller examples resolve the installed `codex-advisor` directory and use the same `$codexAdvisor` variable; neither assumes the working directory or names a particular user. The reader reference retains the separate expert `:4040` and Pi worker `:4000` endpoints, isolation/call limits, and final-response tool-disable requirement.
- Copied `ask_expert.py`, `expert_reader.py` and `pi_reader.mjs` byte-for-byte. Source and destination SHA-256 values match respectively: `9165164ED4974AF1F86E506686BDD2EDAE5CEBD2D5B248E3CD910927C2570C0F`, `520DD9FA5C9870C1BC7E8909DA6A43516E85D67E7F92D0DF27D695B8AC7E4E6C`, and `1F06B87A195C2C5AD4A6C4293F38952471C14BC8F724D78E209463D178443B13`.
- Migrated the Python suite to `tests/test_codex_advisor.py` and Node suite to `tests/test_pi_reader.mjs`. Their only code changes are the new skill script paths and Python loader module name; behaviors and historical fixtures remain intact.

## Checks and limits

- `py -m pytest -p no:cacheprovider --basetemp tmp/central-package/advisor/pytest tests/test_codex_advisor.py`: **24 passed** in 4.91 seconds. `PYTHONDONTWRITEBYTECODE=1`; temporary files stayed under `tmp/central-package/advisor/`.
- `node --test tests/test_pi_reader.mjs`: **2 passed**, including the native Pi reader line-number check. `TEMP`/`TMP` pointed at the same scoped scratch directory. The existing Pi package was used; no dependency was installed.
- Whitespace scan on the assigned Markdown, YAML and test files found no trailing whitespace. Script hashes were compared with Subroute source. No paid/live provider call or service startup occurred.
- The local tests verify caller and reader boundaries only. They do not establish live expert or gateway availability, provider quality, cost savings, deployment behavior, or human acceptance. Northstar install integration and Subroute redirect/source removal remain with the primary owner.

## Mandatory visual Advisor follow-up

Historical documentation-only result; the later caller image-delivery increment supersedes its transport limitation. See the [current goal](../../goal/central-package/GOAL.md#caller-image-delivery-and-advisor-directed-reading).

2026-09-30, base `0b751ab`, primary implementation; separate nonauthor documentation review READY, inspected and accepted by primary. Added the mandatory art/image/aesthetic consultation loop in [Codex Advisor](../../../skills/codex-advisor/SKILL.md#mandatory-visual-and-aesthetic-guidance), with discoverable metadata and Northstar/QA routing. Advisor receives actual images, chooses further inspection, directs concrete repairs and sees repaired views. Ordinary blocker prerequisites and call ceilings cannot truncate required visual feedback; authority, resource and no-progress recovery limits still apply. Advisor direction cannot self-certify the resulting design.

Source inspection confirms `ask_expert.py` accepts only text and the Pi snapshot excludes binary images. The skill requires an authorized image-capable channel and leaves visual consultation unverified if none exists; no runtime/image-transport support was added. No service, provider, installed-copy or Git publication change. Development validation and the independent verdict will be linked from the [evaluation](../../evals/central-package.md#mandatory-visual-advisor-follow-up).
