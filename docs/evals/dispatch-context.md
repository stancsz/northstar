# Dispatch context guidance evaluation

Goal: [Clear, economical subagent dispatch context](../goal/dispatch-context/GOAL.md). The owner reported agent drift and wasted tokens but supplied no failed dispatch transcript. We evaluated the wording with native-agent scenarios and the requested Codex CLI and Claude Code CLI routes.

## Guidance and independent review

The Codex Advisor council recommended refining the existing task brief with must-know facts, next action, acceptance and authority limits; it advised against arbitrary length caps or mandatory acknowledgment turns. An independent scenario review covered clear single-step work, ambiguous multi-step work, missing inputs and unrelated history. It found no material wording defect. See the [implementation report](../reports/dispatch-context/implementation.md) and [review](../reports/dispatch-context/review.md).

## Native matched trials

Three pairs used GPT-6 Luna at low effort and identical fixture inputs within each pair. All six outcomes met their acceptance criteria.

| Pair | Control | Treatment | Interpretation |
| --- | --- | --- | --- |
| Inventory with unrelated history | Correct; 3 files inspected; 180-character summary and 1,121-character handoff | Correct; 1 source file inspected; 153-character summary and 424-character handoff | Positive retrieval and handoff-length proxies; no token/time telemetry |
| Missing July source, original control | Correctly marked unknown despite a conflicting prompt suggestion to estimate from June; 425-character output and 1,175-character handoff | Correctly marked unknown; 128-character output and 589-character handoff | Control prompt conflict weakens causal comparison |
| Missing July source, neutral control | Correctly marked unknown; README, June file and folder listing inspected; 245-character output and 945-character handoff | Same correct result and same inspected sources; 235-character output and 581-character handoff | No retrieval reduction; handoff shorter, but output length is not cost telemetry |

No native run exposed comparable per-agent tokens or elapsed time. Correctness was already achieved in controls; these pairs alone do not prove general improvement or savings.

## CLI trials

Both clients passed unique-response smoke requests through `http://localhost:4000` using the configured `default` alias. Codex reported provider `subroute` and model `default`; Claude returned the unique response but emitted a non-blocking `default[1m]` title-request diagnostic. Task usage, stdout and errors are detailed in the [CLI trial handoff](../reports/dispatch-context/cli-trials.md).

The first Claude pair had a path confound: control used relative filenames, failed to resolve them, and hit its turn limit; treatment returned the correct summary. We do not treat that as a clean comparison. The replication used byte-identical fixtures, absolute paths, the same read-only authority and output format. Control read the README, inventory and history, then spent a turn attempting to read the fixture directory and ended at its turn limit without a handoff. Treatment read those same three files and returned the correct summary in the same reported turn count. Provider-reported output was 501 tokens for control versus 341 for treatment; input was 1,168 versus 1,106. This is a repeated response-completion advantage in one small scenario, not evidence of broad savings. This CLI trial requested a three-line text reply, not a `summary.md` file; file-creation behavior was not tested.

Codex CLI control and treatment both drifted into tool-wrapper troubleshooting and produced no task result, though their low-level tool failures differed. Since neither condition completed, the Codex CLI runs provide no comparative evidence. The task attempts were stopped after repeated drift; their token totals remain unknown.

## Conclusion

The revised brief has a limited positive signal: in the matched Claude CLI replication the treatment completed while control did not, and the native inventory pair required fewer source reads under treatment without a correctness regression. The missing-input native trials remained correct in both conditions. Keep the wording change, but claim neither general drift prevention nor measured total token savings. Codex CLI remains unresolved and requires a separate diagnosis of its tool-wrapper path before it can validate this guidance.

Documentation checks must include local Markdown links and installation paths plus `git diff --check`; no behavioral test outside the scoped trials is implied. Future evidence should preserve matched fixtures, exact CLI route/model, acceptance, tool/read counts, actual usage, attempts, interventions and time. Do not compare output length alone as a measure of total cost.
