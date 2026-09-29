# Proportionate autonomy: independent scenario review

- Goal: [Coordinated delivery follow-up](../../goal/coordinated-delivery/GOAL.md#follow-up-proportionate-process-and-bounded-autonomy)
- Author/date: independent review agent, 2026-09-29
- Status: review complete; one finding repaired and targeted recheck passed
- Revision/environment: Windows working tree based on `1bb158a`; reviewed the current skill, template, and reference edits against that base.

## Finding

**P2: The deployment example still requires repeated approval.** [Examples](../../../skills/northstar/references/examples.md), production-deployment bullet (line 11 at review), says to prepare and verify, then "stop for explicit approval before deploy." Unlike the updated [protocol](../../../skills/northstar/references/protocol.md) and [routing rubric](../../../skills/northstar/references/routing-rubric.md), it does not distinguish an already-authorized deployment from missing authorization. In the concrete case of explicit authorization for the exact release, target, and limits, an agent following this example can recreate the approval loop this increment removes. Make the stop conditional on missing authorization or materially changed consequences; retain preparation and verification. This leftover was already present at the base, but remains relevant to the changed authority guidance. The primary agent owns the repair.

**Disposition: resolved.** The primary changed that same bullet to permit deployment within existing explicit authorization for the action and target, ask for missing authority or materially changed consequences, and clarify that rollback availability is not permission. I reread the changed line independently; it retains preparation/verification and now agrees with the protocol and rubric. This was a targeted wording recheck, not an executed deployment.

## Scenario observations

Read `AGENTS.md`, direction, the active goal, report/evaluation indexes, earlier coordinated-delivery review/evaluation, both changed skills, role briefs, changed references, the goal template, and companion QA guidance. Inspected the diff and these cases:

| Case | Written behavior and assessment |
| --- | --- |
| Worker internal refactor | Northstar permits internal structure and verification choices within acceptance, authority, and ownership boundaries. Codex Subagents explicitly allows worker internal refactoring. No automatic architecture escalation remains. |
| Coordinated shared-interface change | Workers can clarify interfaces through authorized communication; supervisors coordinate affected owners within existing authority. Unresolved cross-goal tradeoffs escalate. This preserves coordination without making every technical question a manager decision. |
| Peer asks to expand permission or take over files | Peer agreement expressly cannot expand authority or transfer write ownership. Transfers require the former writer to stop and its diff to be inspected. No peer bypass found. |
| Tiny single-agent change | One active-goal handoff/acceptance entry is sufficient by default; one agent does not simulate sequential role approvals. The explicit repository exception preserves this repository's separate worker-report requirement. Evidence can be linked instead of copied. |
| Progress at default investigation window | Evidence-backed progress permits another bounded step. Progress has concrete acceptance/failure/hypothesis criteria, and a checkpoint preserves the history. This is not an automatic user approval gate. |
| Exhausted recovery or explicit cap | Default guidance cannot override explicit limits or restart exhausted recovery. A blocked investigation requires a changed condition to resume. Reassignment and context changes do not reset attempts. |
| GUARD with existing versus missing authorization | Protocol and rubric correctly distinguish these cases and preserve action/target/limit boundaries. The deployment example inconsistency was repaired and reread as recorded above. |
| Partial dependency blocker | Worker guidance and recovery explicitly require continuing independent authorized work. The blocked portion retains its precise dependency and unmet criterion. |

No other material contradiction or unnecessary approval stage was identified in this bounded pass. Integration inspection, required evidence, consequential-action authority, and human acceptance where required remain intact.

## Checks, limits, and handoff

`git diff --check` passed during review (Git emitted LF/CRLF conversion notices). This report's relative file links were checked locally. This is independent scenario review of written instructions, not behavioral proof, an execution trial, or a claim of long-session reliability. No agent behavior, production action, installed copy, or runtime limit was tested; global link/installation validation and the separate local trial remain the primary agent's responsibility.

Only this report was written by the reviewer. No material review finding remains open. Next action: primary inspects trial evidence and records final acceptance in the existing goal/evaluation.

## Preflight follow-up review, 2026-09-29

Independently read the new entry guidance and record-mapping changes in Northstar, Codex Subagents, Northstar QA, the lifecycle/protocol references, goal template, and installation guide against the working tree based on `1bb158a`. The separate skill-feedback changes were excluded from this review. No material contradiction was found in the assigned cases:

- **Tiny one-turn task without documentation folders:** the request and handoff can supply acceptance and result; direct implementation and relevant verification do not depend on creating Northstar folders or choosing a process mode.
- **Existing issue or plan:** the skill maps goal/report/evaluation responsibilities to existing records, adds missing information, and expressly prohibits duplicate records or parallel indexes. The template is an optional fallback.
- **Explicit repository record requirements:** the entry guidance, ownership mapping, lifecycle and installation guide preserve repository requirements. This repository's `AGENTS.md` therefore continues to require its assigned report and goal/evaluation records.
- **External tracker:** existing-record mapping does not grant write authority; the core skill and installation guide explicitly retain the authorization requirement for external tracker writes.
- **Visible change:** reduced recording overhead does not waive QA. The core still requires relevant workflow/visual inspection; QA still requires opening the rendered artifact, inspecting screenshots, executing functional checks, and reporting evidence and limitations. A small task can put the result in its handoff.

Disposition: no repair requested for this preflight scope. This was a bounded documentation scenario review, not runtime testing, proof of future compliance, or review of the separate skill-feedback work. The primary agent owns final staged-scope validation and commit.
