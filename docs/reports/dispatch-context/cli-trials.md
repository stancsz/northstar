# CLI dispatch trial handoff

## Setup and route evidence

Used isolated `CODEX_HOME` and `CLAUDE_CONFIG_DIR` values for local CLI processes; neither CLI edited the repository. Both were invoked with model alias `default` through `http://localhost:4000` and a read-only task boundary. Codex used the existing dedicated `subroute-subagents` profile and low reasoning effort. Claude used `ANTHROPIC_BASE_URL=http://localhost:4000`, `ANTHROPIC_MODEL=default`, `--model default`, plan mode and only the Read tool. A unique-response smoke request succeeded in each CLI. Codex identified provider `subroute` and model `default`; Claude returned its unique response. Claude also emitted `[claude-code:unrecognized_model]` for its SDK title request `default[1m]`; task requests returned through the configured local endpoint. No provider key or global CLI configuration was changed.

## Matched Claude replication

The two fixture directories contained byte-identical `README.md`, `history.md` and `items.csv` (SHA-256 hashes checked). Both assignments were read-only, used absolute paths to their separate but identical fixtures, and requested the same three-line text handoff. Control directed the worker to start with `README.md`; treatment put the acceptance criteria and first action (`items.csv`) directly in the brief and identified history as background. The actual criteria were identical to the README in both fixtures. Unlike the native trials, this CLI trial did not ask for a `summary.md` file, so it evaluates response completion rather than file creation.

The prompt variants were:

- **Control:** “Prepare a concise current inventory summary from the fixture at `<control-dir>`. Start with README.md, then inspect source files as needed. Return exactly three lines: SKUs with quantities; available-item count; total quantity. Do not edit files.”
- **Treatment:** “Prepare a concise current inventory summary from the fixture at `<treatment-dir>`. First inspect `<treatment-dir>/items.csv`. Acceptance: include only rows with status available; list SKUs in ascending order with quantities; report available-item count and sum of available quantities; exclude archived rows. Return exactly three lines: SKUs with quantities; available-item count; total quantity. README.md is supporting context and history.md is older background. Do not edit files.”

| Condition | Result | Read tool calls | Turns | Input / output / cache-read tokens | Duration |
| --- | --- | ---: | ---: | --- | ---: |
| Treatment | Correct ascending available SKUs A-08 (3), A-17 (4), A-31 (2); count 3; total 9 | 3: items, README, history | 4 | 1,106 / 341 / 2,138 | 5.3 s |
| Control | No handoff; hit maximum-turn error after attempting an extra read of the fixture directory | 4: README, items, history, directory | 4 | 1,168 / 501 / 1,792 | 10.6 s |

Both conditions read the same three source files; treatment completed without the extra failed directory read. Provider-reported output tokens were lower for treatment in this pair, but one pair does not establish typical token savings. Both emitted the non-blocking `default[1m]` SDK title diagnostic.

## Earlier exploratory Claude pair

In an earlier pair, the control used relative filenames and repeatedly failed to resolve them before reaching the turn limit. Treatment returned the correct result. This pair was not treated as clean causal evidence because its path handling was not matched. Usage was control 946 input / 654 output / 1,920 cache-read tokens and treatment 856 / 319 / 1,920; results are retained as exploratory only.

## Codex CLI task runs

The control and treatment both used isolated profile-backed Codex CLI invocations with model alias `default`, provider `subroute`, low effort and a read-only sandbox. A unique-response smoke request had succeeded on the same route. In both task runs, the worker drifted into troubleshooting an unavailable `functions.exec`-style wrapper and did not inspect the inventory fixture or produce a task handoff. The low-level failures differed: control repeatedly misparsed wrapper input; treatment repeated that parsing issue, then received policy denials for PowerShell, `cmd.exe` and `bash.exe` shell attempts and made a malformed `apply_patch` probe. The calls were interrupted after repeated drift. No useful per-run usage receipt was available. These failures do not compare the two brief styles and leave Codex CLI effectiveness unresolved.

## Acceptance and limits

The Claude replication shows a bounded improvement in task completion for this inventory task: the treatment succeeded where control did not, with identical source files and unchanged output criteria. The earlier exploratory pair points in the same direction but has a path confound. Codex CLI did not produce a usable comparison. These observations justify keeping the concise wording change for now; they do not establish a general reduction in drift or total token cost. Re-test Codex CLI separately after diagnosing its tool-wrapper behavior.
