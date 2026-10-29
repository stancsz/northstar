# Subroute tool preflight guard — 2026-10-23

## Outcome

Updated the Codex and Claude Code Subagents skills to require a harmless function/tool-result roundtrip when the assigned CLI needs tools and its project requires that gate. The guidance now requires parsing the actual protocol response blocks, treats `supplemental_advisor_failed` with “base request was not sent” as a gateway pre-inference failure, and stops before CLI launch without an unchanged retry or provider/credential substitution.

## Evidence

The unique-marker Responses request succeeded after inspecting `output[].content[]`; PowerShell's automatic `output_text` projection was null even though the marker appeared in the message's `output_text` content block. The subsequent forced function-call request returned HTTP 502 `supplemental_advisor_failed`, explicitly saying the base request was not sent. No Codex worker was launched for that attempt. The Subroute source at `D:\github\subroute\src\subroute\plugins\advisor_plugin.py` corroborates that the configured supplemental call runs before the base request and raises on failure.

This proves the observed failure occurred before Codex CLI inference; it does not prove a general gateway outage or a CLI defect. No model, route, provider, credential, global setting, or gateway source was changed. Claude was not launched; no authorized Subroute inference key is currently available to its process.

## Validation and limits

The parent reran `py -3 -B -m pytest -q -p no:cacheprovider tests/test_codex_subagents_helper.py`; **26 passed**. This helper regression suite does not prove live route availability or Claude tool behavior. A prior accepted Codex native smoke and one scoped documentation writer remain a separate positive trial, not a reliability claim. Resume a tool-using CLI task only after the required same-route tool-result roundtrip passes. Keep the goal Active until Codex and Claude tasks demonstrate bounded tool use and accepted handoffs on their configured Subroute paths.

## Gateway log diagnosis and Council decision

The sanitized gateway log for request `aa3df7b2-9487-4d4a-9fc2-5957e0755651` identifies the supplemental call as `claude-opus-5-5-low` via Antigravity. The bridge returned `BadGatewayError` after four output retries were blocked by content safety filters. The log does not show whether the trigger was the synthetic marker/tool wording or a broader provider condition; this single failure is not proof of a systemic outage.

Advisor Council (GPT-6.1 Sol and Gemini review; 3,772 tokens reported) recommends a hard stop and gateway-owner repair before further route probing. It notes the safety-filter cause remains uncertain. This advice does not authorize disabling the supplemental call, changing route/model/provider, substituting credentials, or contacting anyone. No message was sent. Re-run a full preflight only after owner-side repair is established.
