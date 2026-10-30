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

2026-09-30, base `0b751ab`, primary implementation; separate nonauthor documentation review READY, inspected and accepted by primary. Added the mandatory art/image/aesthetic consultation loop in [Codex Advisor](../../../skills/advisor-council/SKILL.md#mandatory-visual-and-aesthetic-guidance), with discoverable metadata and Northstar/QA routing. Advisor receives actual images, chooses further inspection, directs concrete repairs and sees repaired views. Ordinary blocker prerequisites and call ceilings cannot truncate required visual feedback; authority, resource and no-progress recovery limits still apply. Advisor direction cannot self-certify the resulting design.

Source inspection confirms `ask_expert.py` accepts only text and the Pi snapshot excludes binary images. The skill requires an authorized image-capable channel and leaves visual consultation unverified if none exists; no runtime/image-transport support was added. No service, provider, installed-copy or Git publication change. Development validation and the independent verdict will be linked from the [evaluation](../../evals/central-package.md#mandatory-visual-advisor-follow-up).

## Gemini 4 council route recovery

2026-10-16 follow-up to the Gemini 4 skill update. The installed caller and Northstar source target `gemini-4-argon-advisor`; Subroute's experts config maps it to `antigravity/gemini-4-argon-low`. At inspection, the local experts container had already loaded this config, and `/v1/models` listed the Gemini 4 alias. One live council invocation through the installed caller completed Gemini 4 Argon followed by GPT-6.1 Sol with no retry or fallback. Gemini usage was 2,798 tokens; Sol usage was 672 tokens. [Evaluation](../../evals/central-package.md#gemini-4-council-route-recovery) records request IDs and limits.

The Advisor's recommendation matched the already planned live smoke check, so `decision_changed: false`. Offline caller regressions passed: 38 in Northstar and 76 in Subroute. No container restart was needed in this follow-up because the service was already serving the updated route. No commit or push was made. This verifies one live call through the configured route; it does not establish ongoing provider availability or general advice quality.

## Installed skill check

2026-10-16 follow-up at the owner's request. The installed helper's `--help` resolved and showed only the supported Sol choice plus council, image and reader options; its SHA-256 matched the Northstar source caller. One default live Sol consultation completed through `codex-gpt-6.1-sol-advisor` in 8.436 seconds, returned a 74-word evidence-bounded answer and reported 535 provider tokens. It correctly distinguished local readiness from publication and ongoing reliability. Northstar caller tests passed 38, Subroute caller tests passed 76, and `node --test tests/test_pi_reader.mjs` passed 2. Usage was recorded; `decision_changed: false`. This is functional smoke evidence, not general advice-quality proof; live image and reader consultations were not exercised.

## Advisor service authentication recovery, 2026-10-21

Owner request: fix image consultations returning 401. Primary implemented the scoped repair; independent acceptance is in [advisor-auth-review.md](advisor-auth-review.md), with the [goal](../../goal/central-package/GOAL.md#advisor-service-authentication-recovery) and [evaluation](../../evals/advisor-images.md#service-authentication-recovery).

The failure was service authentication shared by text and image calls. The caller process and Windows user/machine environments lacked `EXPERTS_API_KEY`; the running Subroute experts service required it after LAN exposure. A catalog request without it returned 401, while the existing `.env` service key returned 200. The key was configured in the Windows user environment without printing it or creating a credential file. No service configuration, authentication policy, upstream credentials or gateway route changed.

Caller repair: explicit process configuration wins (including an empty value); only the default HTTP loopback origin on port 4040 can read the persisted Windows user key. Other origins require explicit process configuration. This removes the stale-parent-environment problem for already-open desktop sessions. Redirects fail visibly so credentials cannot follow them. A 401 gives configuration guidance without echoed server details, and other HTTP errors redact the selected key. No automatic retry or model fallback was introduced. Repository and installed caller SHA256 match: `8cf91c70e2b212d15650972d6314e31729b0d82248a9831ce732dd69e99adf2f`. Only the authentication section of the installed skill was replaced, preserving its other local guidance.

Checks: 60 Python tests, two Node tests (no skips), authenticated catalog and one installed-caller image request passed. Initial Python run had 33 passes and 27 fixture setup errors because its scratch parent was missing; creating that directory resolved the setup error without code changes. Live receipt identifies the image heading/label and clipping correctly; 764 provider-reported tokens, 4.777 seconds. No source-reader or council completion was needed to repair missing credentials. `decision_changed: false`: the diagnostic image feedback confirmed pixel transport and did not change implementation. No advice-quality or general provider-reliability claim follows.

Learning applied: distinguish service 401 from upstream auth failures, verify configuration using a catalog request first, and test the installed caller from a process that still lacks the variable. Merely setting a persisted environment variable would not update an existing desktop parent. The scoped fallback fixes that demonstrated boundary while keeping other endpoints explicit. No commit or push performed.
