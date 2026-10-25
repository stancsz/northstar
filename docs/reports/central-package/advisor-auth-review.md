# Advisor service authentication recovery: independent review

Date: 2026-10-21. Reviewer: `advisor_auth_review`, independent of implementation and machine configuration. Scope: Northstar working tree on `38b6bad`, installed Windows caller and existing Subroute experts endpoint. [Goal](../../goal/central-package/GOAL.md#advisor-service-authentication-recovery), [implementation](advisor-migration.md#advisor-service-authentication-recovery-2026-10-21), [evaluation](../../evals/advisor-images.md#service-authentication-recovery).

**Verdict: READY for the requested local 401 repair.** No must-fix findings remain. This verdict covers authenticated image consultation from the installed caller; it does not claim broad provider reliability, council/reader acceptance, visual design quality or publication.

## Inspected behavior and evidence

- Read caller and service authentication boundaries before implementation review. Text and image requests share the same bearer lookup; Subroute translates upstream authentication failures to 502. Its required LAN service key explains the observed public 401, while the old skill's optional-key and loopback-only wording was stale.
- Inspected the final caller/test/guidance diff. Explicit process values win, including an empty value. Registry lookup is limited to HTTP loopback port 4040 without userinfo; other origins receive no persisted-key fallback. Redirect refusal prevents forwarding the selected credential. HTTP 401 gives configuration guidance without echoing server text; other HTTP errors redact the selected key. Service authentication remains required.
- Independently ran 22 focused registry, origin, precedence, text/image bearer, error and redirect tests: **22 passed, 38 deselected**. Scratch: `tmp/advisor-auth/reviewer/pytest`. Reused primary's full **60 Python and two Node passes** for unchanged adjacent caller/reader behavior; these are offline checks.
- Independently requested the live model catalog: persisted Windows user key returned **200**, no key returned **401**. Output contained only key-presence/status booleans and numbers. This verifies recovery without disabling service authentication.
- Independently hashed installed and repository callers: both SHA256 `8cf91c70e2b212d15650972d6314e31729b0d82248a9831ce732dd69e99adf2f`. Scoped `git diff --check` passed.
- Inspected the [live installed-caller receipt](../../evals/assets/advisor-images/auth-live-2026-10-21.json), request `chatcmpl-codex-advisor-20e8debe3ffe`, and opened its actual [390 × 844 fixture](../../evals/assets/qa-suite/A-narrow-viewport.png). Advisor correctly identified “Profile settings”, “Display name”, no visible button, and panel/input clipping at the right edge. Independently computed image SHA256 matches its receipt: `3752689e6eacb5d2aee0d41bc9c82e5d297ae83d7d6375dd2321a7d5292597b7`. Primary executed this provider request with the process key absent, exercising the new user-key lookup. Reported usage: **764 tokens**, **4.777 seconds**; no additional reviewer provider call was needed.

## Limits and learning

User key rotation or explicit stale/empty process configuration can still produce a visible authentication failure; process precedence is intentional and documented. Non-Windows registry behavior was tested by simulation, not on another operating system. No service restart, upstream credential replacement, alternate gateway or model fallback was needed. No commit/push is included.

The useful recovery boundary is to distinguish frontend service 401 from upstream subscription failure, test the catalog before spending a provider call, then verify the actual installed image entry point. A persisted environment change alone would leave an already-running desktop parent stale; the scoped lookup addresses that demonstrated cause. The independent verdict accepts this repair and its evidence, not a general authentication framework.
