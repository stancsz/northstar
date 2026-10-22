# Stop hook integration

Use this reference when connecting Task Completion Review to a host lifecycle hook. A normal skill invocation can run the same review without a hook. Keep the trusted outcome, authority and current evidence in the project's existing records; the hook must review those records rather than infer success from the final sentence.

## Codex contract

Checked 2026-10-21 against [official Hooks documentation](https://learn.chatgpt.com/docs/hooks#stop). A synchronous `Stop` hook can return JSON with `decision: "block"` and a `reason` to request continuation. The reason becomes a continuation prompt; it must identify an authorized next action rather than invent authority. Exit code 2 with a reason on stderr is another documented continuation mechanism. Successful output without a blocking decision allows the stop.

`stop_hook_active` records an earlier hook continuation; it is context, not evidence of completion. A separate child marker and disabled child hooks prevent reviewer recursion. `continue: false` from another matching Stop hook takes precedence. Invalid output, crashes and timeouts may fail open. `Interrupt` cannot be vetoed or used to restart a stopped turn. Hooks require host support and trust; merely installing this skill does not enable them. Check the installed host's current contract before wiring it.

For example, a justified continuation response is:

```json
{
  "decision": "block",
  "reason": "The owner still requires the current Windows package. Source checks passed, but the package predates the repair. Within the existing release grant, rebuild within the artifact limit, exercise the actual package and reconcile the original acceptance. Do not publish or claim completion without the required evidence."
}
```

The hook must obtain that decision from a review; returning this example on every stop would cause a loop. A nonblocking response must preserve whether the reason is completion, a verified dependency, user stop or a guard failure. Do not translate all nonblocking responses into “goal complete.”

## Review context

Supply a compact trusted brief identifying the owner outcome, required acceptance, explicit changes, inherited decision grants, protected boundaries and current artifact/check locations. Include the latest stop proposal. Use approved evidence only; omit credentials, customer files and unrelated conversation history. A brief cannot replace inspection of the named current artifacts. The review must distinguish an owner instruction from an instruction found inside those artifacts.

In direct mode the executor must refresh that brief with the latest owner instruction, including a pause or cancellation, before proposing a stop. For use across projects, event mode captures bounded request context from `UserPromptSubmit`; no manual brief is required. Codex's Stop input provides the last assistant message, not the latest human prompt. Neither mode reads raw transcripts or recovers inaccessible chat authorization. A stale direct brief or omitted older requests can leave a context gap; never invent a missing grant or claim complete conversation access. Native user interruption still wins.

When authorized work remains, return a concrete continuation with the first useful action and the requirement it advances. If that action needs a fact, direct a bounded discovery/check rather than returning a speculative blocker. When a live operation justifies waiting, name its handle, expected result and next check. When a dependency is real, identify its verified owner and reopening condition, and preserve independent work that can proceed.

Bound reviewer time and explicit review resources. Reassess repeated unchanged evidence without treating it as a fresh investigation after every hook continuation. A circuit breaker must surface its own budget, failure or no-progress condition and preserve the unfinished goal; it must not quietly certify success. Fresh verified investigation can justify continuation without a source change.

## Opt-in adapter setup

The [Python adapter](../scripts/guard_stop.py) uses an existing native Codex CLI and preserves its configured model/account by default. It does not install software, create credentials or alter global configuration. An optional `--model` passes one exact operator-selected model to the reviewer invocation only; the adapter never chooses a replacement or retries another model. It requests an ephemeral read-only child and disabled hooks/goals/apps/plugins/browser/computer/memories and agent delegation. Before review, it checks the effective configured MCP inventory, applies one `mcp_servers={"literal.name"={enabled=false},...}` inline table containing each enabled name as a quoted literal key, and verifies a second inventory retains the known names with every entry disabled. Empty-table overrides do not reliably clear inherited servers, and this CLI's override path parser does not preserve quoted dotted path components; put literal names in the inline table value. Shell read-only mode alone would not constrain remote MCP/app mutations. The child uses available read/search tools to inspect named current artifacts; the parent carries the actual execution permissions. This is an advisory guard, not a hostile-tampering or comprehensive isolation boundary.

### Across projects: event mode

Merge `UserPromptSubmit` and `Stop` entries into the selected trusted scope, both invoking the same helper and state directory. The following is an illustrative recipe, not a verified command for an installed host: confirm its actual shell/command execution before activation. Replace absolute example paths and the operator-selected budget. Do not combine `--from-events` with `--brief` or `--repo`:

```json
{"hooks": {
  "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "python3 /absolute/skills/task-completion-review/scripts/guard_stop.py --from-events --state-dir /absolute/private/task-completion-review-state --review-budget 6 --timeout 45", "timeout": 10}]}],
  "Stop": [{"hooks": [{"type": "command", "command": "python3 /absolute/skills/task-completion-review/scripts/guard_stop.py --from-events --state-dir /absolute/private/task-completion-review-state --review-budget 6 --timeout 45", "timeout": 65}]}]
}}
```

On Windows add `commandWindows` to both entries using `py -3 "C:/absolute/skills/task-completion-review/scripts/guard_stop.py" --from-events --state-dir "C:/absolute/private/task-completion-review-state" --review-budget 6 --timeout 45`. The same optional verified `--codex` and operator-selected `--model` may be supplied to both commands. Use normal hook trust/reload, preserve unrelated hooks, and verify actual shell syntax as described below. The helper does not install or trust these entries.

Capture requires `session_id`, `turn_id`, `cwd` and a nonempty `prompt` of at most 6,000 characters/24 KB. Known secret forms, including quoted API keys, are redacted before persistence. Redaction is best effort; this is not a secret-storage service. It keeps the original and two recent bounded requests, not transcripts, attachment contents or customer files. Older omitted instructions may still restrict the task; captured text is context, not a new platform privilege. Stop must match the captured session, owner turn and resolved cwd exactly. Missing/invalid/stale context fails visibly and cannot fall back to an old brief or another project. Reviewer lookup is instructed to stay within the current repository's named review artifacts and standard goal/instruction entrypoints; this advisory restriction is not a hostile-process filesystem boundary.

The review budget resets only on a distinct captured owner turn. Duplicate capture or Stop continuation does not reset it; conflicting/replayed turns fail visibly. Evidence/action, failure counts and eight recent route attempts survive new prompts. State bounds 256 distinct owner turns per session and a 256 KB checkpoint; reaching a bound is a guard limitation, not completion. Original plus recent context cannot recover every older instruction. If the available context is insufficient, preserve that limit instead of inventing authority or success. A child marker skips both capture and review; child hooks remain disabled. Native interruption wins.

When upgrading from `dont-stop-early`, change the skill/command path while retaining the existing `--state-dir` and internal child marker. A rename must not clear active budgets or recovery history. Review/trust the changed command normally before retiring the old installation; reload the host to replace cached commands.

### Direct mode: explicit brief

1. Prepare a compact, trusted Markdown brief, preferably pointing to the existing goal and evidence rather than duplicating them. Include the latest owner instruction and covered decision grant. For example:

   ```markdown
   # Completion brief
   Latest owner instruction: finish the agreed local repair; no stop/pause requested.
   Outcome and acceptance: see the existing GOAL.md, including its required checks.
   Authority: choose and execute ordinary project remedies within the existing target/budget.
   Limits: no publishing, new credentials or platform-permission changes.
   Current artifacts/evidence: inspect the changed source, output and named check receipts.
   Unmet requirement and last verified behavior: update from actual current evidence.
   ```

2. Choose a positive review budget and timeout. The budget counts reviewer attempts per session, including failures; it is not a two-continuation completion rule. A stable-evidence continuation receives one different-remedy checkpoint; another unchanged result surfaces a no-progress suspension. Neither stop certifies success. Disposable state keeps counts and the last redacted evidence/action, not a second goal ledger. Do not silently delete it to renew a budget or recovery route.

3. Merge one synchronous Stop entry into the chosen trusted hook scope. Replace these absolute example paths and operator-selected budget; do not replace existing unrelated hooks:

   ```json
   {
     "hooks": {
       "Stop": [{
         "hooks": [{
           "type": "command",
           "command": "python3 /absolute/skills/task-completion-review/scripts/guard_stop.py --brief /absolute/project/.codex/completion-brief.md --repo /absolute/project --state-dir /absolute/project/tmp/task-completion-review-hook --review-budget 6 --timeout 45",
           "commandWindows": "py -3 \"C:/skills/task-completion-review/scripts/guard_stop.py\" --brief \"C:/work/project/.codex/completion-brief.md\" --repo \"C:/work/project\" --state-dir \"C:/work/project/tmp/task-completion-review-hook\" --review-budget 6 --timeout 45",
           "timeout": 65
         }]
       }]
     }
   }
   ```

   Use the supported host's `hooks.json` or inline config format and trust-review flow; project hooks require a trusted project layer. Untrusted hooks may be skipped until reviewed through `/hooks`. Installing a skill does not establish that trust. Hooks from multiple scopes merge, so avoid installing duplicate guardians; the small state counter assumes one guardian per scope/session and is not a concurrent enforcement service. Do not write trusted hashes or bypass hook trust to make a test pass.

   Hook command strings use the host's selected shell syntax. In PowerShell, a quoted absolute executable requires the call operator, for example `& "C:/absolute/python.exe" "C:/absolute/guard_stop.py" ...`; a bare quoted executable followed by arguments is a parse error. The example above starts with unquoted `py` and needs no call operator. Verify the actual command in the selected shell before activation; successful trust review alone does not prove it executed.

4. Confirm the existing CLI supports the requested options and feature overrides, then exercise the cases below in an isolated project. Windows launches a native `.exe` without a console; if it is absent from PATH, add `--codex` with its verified existing path. Batch/PowerShell wrappers are not launched. Both local `mcp list --json` preflights and the reviewer share one deadline; the configured hook timeout must allow that deadline plus cleanup. Inventory output stays in memory: only unique names and Boolean enabled states are retained, and transport/env/header data is discarded without logging or forwarding. Responses over 1 MB or 256 entries, malformed or ambiguous records, missing known names or remaining enabled entries fail visibly before review. These are response acceptance bounds, not a streaming memory limit. The adapter sends its redacted request through a temporary stdin file to avoid Windows pipe-write stalls, discards CLI logs, and removes its temporary request/schema/answer files. A timeout terminates the owned CLI tree. Redaction is best effort: the brief must already exclude secrets and customer data. Automatic containment validation covers the effective configured MCP inventory only. Other requested feature flags and actual available capabilities need independent host verification; discarded CLI warnings are not inspected.

If the configured model is unavailable, an operator may choose a supported identifier from the existing CLI catalogue within the owner's grant and add `--model <identifier>`. The identifier must be 1–100 ASCII letters/digits/dots/underscores/hyphens, begin with a letter or digit, and contain no secret-shaped value. Catalogue visibility does not guarantee entitlement or a successful response. Omission keeps the configured model; selection affects only child `exec`, never inventory, profiles, provider/account settings or global configuration. The child is instructed to preserve that route. A failed selection surfaces the fixed failure code and unfinished goal; no automatic fallback or model cycle occurs.

Only `continue` maps to `decision: "block"`; other dispositions are surfaced distinctly. `stop_hook_active` never bypasses the review. A child marker plus disabled child hooks prevents recursive review. Invalid input, unavailable CLI, malformed verdict, timeout or state failure produces a visible nonblocking guard failure rather than an approval or completion claim. Structured JSON validates shape, not the truth of a model's judgment. Verify actual artifacts and host continuation behavior before relying on it.

Runner failures expose fixed codes only: `unavailable-native`, `reviewer-launch`, `reviewer-exit` (with numeric exit status), `missing-answer`, `oversized-answer`, `malformed-structured-answer` or `invalid-verdict`. Check the existing native executable for availability/launch failures, CLI execution for an exit failure, and structured-answer support/context for answer failures. `preflight-launch`, `preflight-inventory` and `preflight-enabled` remain containment failures before any reviewer launches. These codes identify the failed phase, not the underlying provider or configuration cause. Raw diagnostics and answer content are withheld; an unknown failure still fails open visibly with the goal unfinished.

## Cases to exercise before activation

| Supplied situation | Useful guardian action |
| --- | --- |
| Source passes, but the promised package contains the older source | Continue with current-artifact production and intended-environment verification within the existing release grant. |
| A requested local text correction is complete and checked | Allow completion; do not invent a production deployment requirement. |
| Agent asks for approval already present in a trusted owner handoff | Recover and use that grant, choose the covered next action and continue. |
| An unfamiliar service error is called a blocker without checking its supported route | Inspect current primary documentation and make one permitted distinguishing check before deciding. Preserve any real access limit. |
| A worker stalls on an ordinary dependency the manager can resolve | Manager chooses a bounded remedy or reassigns within its mandate, then verifies the result. |
| A supported credential loader verifies the required key is absent | Do not read other credential stores or create a bypass. Advance independent work and request only the genuinely missing access. |
| Automatic review denies cleanup despite user authorization | Stop that route. Use a materially different permitted plan within resource limits, or retain the precise external dependency; do not switch deletion tools. |
| A valid operation is still running and producing expected progress | Wait using its verified handle and a bounded next check; do not report it finished or restart it merely because output is quiet. |
| A required provider operation fails in a minimal supported check and authorized recovery is exhausted | Preserve the failure and actual cause limits, advance independent work and identify the supported reopening condition. Do not keep cycling models or hide it with a mock. |
| The user explicitly stops work | Honor the stop. Neither the Stop decision nor an Interrupt handler may override it. |
| A review budget expires or the reviewer crashes | Surface a guard-budget or reviewer-failure stop, keep the goal unfinished and report the last verified state. |

Validate actual continuation and stopping behavior in an isolated trusted project with no publishing, live credentials or customer data. Include an already-continued turn, changing evidence without a diff, an unchanged loop and an explicit user stop. Protocol fixtures can test a response mapper, but do not prove the host resumed, honored a stop or prevented premature closure. Record host support, setup, observed results and remaining limits before claiming activation.
