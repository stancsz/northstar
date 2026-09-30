# Advisor image backend handoff

Goal: [central package](../../goal/central-package/GOAL.md). Author: `advisor_image_backend` worker. Date: 2026-09-30. Subroute base: `9125725` plus these uncommitted changes. Status: implemented; offline checks passed; awaiting primary integration and independent acceptance.

## Scope and result

Subroute's existing `src/subroute/handlers/codex_advisor.py` now accepts user Chat Completions `image_url` objects and Responses-style `input_image` blocks. It preserves the exact inline base64 data URL or HTTP(S) URL, image detail, separate text blocks and their order around tool-history entries. The existing Subscription transport, terminal-completion/usage validation, roles, and fail-closed behavior remain in use. No image-generation tool, reader tool execution, retry or fallback was added. `config/litellm.experts.yaml` now declares vision for its Sol and Astra Advisor aliases. Malformed image input yields a visible 400 before opening an upstream HTTP client.

Supported detail: `auto`, `low`, `high`, `original`; omitted detail becomes `auto`. Data URLs accept base64 PNG/JPEG/WebP/GIF. Unsupported roles, local-file paths, file IDs, extra image fields, invalid base64, invalid URL types/schemes and malformed detail are rejected rather than dropped. The gateway validates envelope/base64 syntax, not decoded image pixels; upstream still validates actual image content and model capability.

## Existing capability and maintenance reason

Inspected installed, locked LiteLLM **1.101.0**: its Responses/completion transformations already translate native image blocks, and its OpenAI SDK schema permits all four detail values. This dedicated `CustomLLM` bypasses those conversions and its own `build_responses_input` previously rejected images. LiteLLM's native `chatgpt` provider additionally rewrites instructions and owns a different authenticator. The repair therefore extends only this existing adapter's content conversion. Reconsider the helper when the dedicated Advisor uses the existing native Responses conversion/transport without changing the established authentication and instruction contract; do not add another transport.

## Checks and observations

- From Subroute, `.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider --basetemp=tmp/advisor-images/backend/pytest tests/test_codex_advisor.py`: **69 passed, 1 existing Pydantic ReadOnly warning**. `PYTHONDONTWRITEBYTECODE=1`; scratch stays under `tmp/advisor-images/backend/`.
- Added causal regressions for mixed image/text/tool ordering, image-only turns, default/all explicit detail values, nonmutation, unsupported roles/envelopes, malformed base64/URLs/detail, 400 before upstream dispatch, and exact upstream image bytes plus reasoning. Both direct CustomLLM dispatch and actual locked LiteLLM `acompletion` dispatch are tested against HTTPX MockTransport.
- `git diff --check` passed. Subroute was clean at assignment start; only the three assigned source/config/test files were changed by this worker. No commits, pushes, provider calls, service restarts or additional delegation.

These are offline regressions. They do not establish live provider vision, deployed service support, image-based taste quality or end-to-end Northstar caller behavior. Primary owns service integration/live verification and any further runtime authorization.

## Skill learning and next action

Expected versus observed: native LiteLLM supports images, but the dedicated Advisor content builder was the concrete rejecting boundary. Extending that boundary and testing actual LiteLLM dispatch preserves pixels without a parallel transport. Reuse this approach only while that CustomLLM still bypasses native conversion; avoid assuming generic framework vision capability proves a custom handler accepts images. Primary should inspect the diff, test the Northstar caller through this backend, and obtain the independent verdict before acceptance.
