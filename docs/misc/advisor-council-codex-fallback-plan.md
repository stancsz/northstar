# Add a Direct Codex Fallback to Advisor Council

## Summary

Save this plan first and read it back, then implement a direct Codex transport in the shared Advisor Council caller. Codex and Claude Code can invoke the same Python script, which uses the local Codex sign-in when the configured Advisor gateway is unavailable.

Direct requests to `gpt-6.1-terra` and `gpt-6.1-sol` completed with provider usage. The direct token-count endpoint returned HTTP 404, so the fallback uses a request-size cap instead of claiming an exact preflight count.

## Implementation changes

- Add `--transport {auto,gateway,codex}`. In `auto`, try the configured gateway first and use Codex only when the URL is unset or the input-token preflight cannot connect or times out. Preserve HTTP, authentication, malformed-count, and inference errors as visible failures. Record the selected transport and fallback reason.
- For direct requests, support one text-only consultation with `gpt-6.1-terra` or `gpt-6.1-sol` at low reasoning effort. Read the existing Codex auth file, stream the response to completion, and report requested and actual model, response ID, and validated provider usage. Cap the full UTF-8 request body at 24,000 bytes. Report missing or expired sign-in clearly.
- Keep direct Codex limited to simple consultations. Image requests, multi-model council calls, and reader mode require the configured gateway. Update the shared skill and installation guidance while retaining existing model defaults and council behavior.
- Preserve the existing staged Advisor Council changes. Inspect the older Claude Code skill copy, merge any local-only content, and sync the completed shared skill to the active `.agents` and `.claude` directories.

## Verification

- Extend the Advisor caller regressions for route selection, connection-failure fallback, explicit transport selection, Unicode byte limits, unsupported modes, malformed or incomplete streams, usage validation, and credential redaction.
- Run `python -B -m pytest -q -p no:cacheprovider tests/test_codex_advisor.py` and `node --test tests/test_pi_reader.mjs`.
- Exercise the installed skill from Codex and Claude Code with a synthetic text packet and unavailable gateway. Confirm completed direct Terra advice and provider usage. Confirm the healthy gateway path still works.
- Inspect documentation links and install paths, run `git diff --check`, and compare both installed skill copies with the repository skill.

## Assumptions

- Claude Code invokes the Advisor skill from a running session. This change does not reconfigure Claude Code's own model route.
- Fallback occurs only before inference, when the gateway URL is absent or the token-count request has a connection failure or timeout.
- The direct fallback retains the existing 6,000-character packet limit as well as the 24,000-byte request cap.
