# Bilingual README and GitHub presentation

Date: 2026-09-29. [Goal](../goal/readme-positioning/GOAL.md). Source baseline `ff7b1c6`; README publication `e2424cc`, Chinese rendering repairs `b164b15` and `6fc5948`. Primary authored and published the pages; a separate reviewer inspected content and supplied the [independent report](../reports/readme-positioning/review.md).

## Observed result

Both READMEs now explain the target audience, management gap, delegated authority, accountable resolution, independent acceptance, capability allocation and checkpoint learning. Both provide a bounded first-use prompt, all four skills, management source maps, and the existing evidence boundary. No skill or service behavior changed.

GitHub's description/About now reads:

> Give your AI team a mission, authority, and accountability. Four Markdown skills for delegated decisions, coordinated execution, independent QA, and checkpoint learning. Codex-native; adaptable to Claude Code and OpenCode.

About's website points to the [installation guide](https://github.com/stancsz/northstar/blob/main/docs/misc/install.md). The 15 Topics are `agent-governance`, `agent-orchestration`, `agent-skills`, `ai-agents`, `autonomous-agents`, `claude-code`, `codex`, `codex-skill`, `decision-making`, `human-ai-collaboration`, `markdown`, `multi-agent`, `opencode`, `quality-assurance`, and `task-delegation`. Removed legacy `python`, `collaboration-protocol`, `risk-management`, and `ai-governance` discovery tags.

Seven Issue Labels were added with scoped descriptions and colors: `skill:northstar`, `skill:qa`, `skill:subagents`, `skill:advisor`, `installation`, `field-report`, and `needs-evidence`. All nine default labels remain. No issue was relabeled. Primary read back the metadata and labels through `gh` after writing them; snapshots are disposable scratch under `tmp/readme-positioning/`.

## Rendered inspection and repair

Inspected actual public GitHub rendering in the in-app browser. The default 517×884 viewport shows naturally wrapped English/Chinese text, legible navigation and badges, and readable tables. Desktop 1280×900 inspection exposes the About panel and the native expanded Mermaid viewer; the temporary viewport override was reset afterward.

- [English opening](assets/readme-positioning/english.png): title, positioning, primary links and problem statement are visible and unclipped.
- [Chinese opening](assets/readme-positioning/chinese.png): natural wrapping and matching hierarchy.
- [Initial Chinese failure](assets/readme-positioning/chinese-diagram.png): punctuation beside closing bold markers caused literal `**` in four use-case labels. The same issue was subsequently found in the evidence summary. Both were repaired with spacing and checked again.
- [Repaired use cases](assets/readme-positioning/chinese-repaired.png) and [repaired evidence summary](assets/readme-positioning/chinese-evidence.png): exact published revision `6fc5948` renders all five labels in bold without literal markers. GitHub's Markdown API output also contains no literal `**` tokens for the Chinese README.
- [Expanded Mermaid diagram](assets/readme-positioning/chinese-flow-expanded.png): all nodes, repair/evidence paths, optional advice and learning return are visible. The narrow inline viewer has small labels and native pan/zoom controls; use GitHub's expanded viewer for detailed inspection. Desktop captures have lower text sharpness than the default-width captures; no pixel-fidelity or all-device claim is made.
- [GitHub About](assets/readme-positioning/github-about.png): description, website and topic pills appear beside the new README.

Primary exercised English → 中文 successfully. Chinese installation clicks timed out in the browser automation; inspection confirmed the correct rendered href, and direct navigation to that exact destination displayed “Install and use the Northstar package” and “Install all four.” This verifies the destination, not a successful Chinese installation-link click. Local link checking covers both language directions and installation paths. No fresh installation or Advisor call was made.

## Checks, decision and learning

Primary's initial whole-repository check resolved 467 local Markdown links and 123 anchors across 76 files after preserving the historical Chinese `#避免重复绕圈` anchor. Independent source review separately checked 35 local links in each README. Final checks include the added goal, report and evaluation records and `git diff --check`.

**Final independent verdict: READY** for the inspected publication scope at `6fc5948`. The nonauthor reviewer inspected the repaired visual evidence and full expanded diagram, then independently exercised live English → 中文 navigation and inspected About. Primary records and accepts that verdict; source checks alone were not treated as a visual pass. The task evaluates presentation and claim fidelity, not increased adoption, less supervision, lower cost, unattended execution, or a completed efficacy pilot. Advisor code is unchanged; its offline regressions were not rerun.

Learning: lead with the owner's delegation problem and concrete management mechanisms, then let readers inspect source and evidence. Keep historical anchors when reorganizing entrypoints. GitHub-rendered inspection caught Chinese emphasis defects that path/whitespace checks could not catch; inspect the rendered text before treating bilingual copy as finished. Metadata uses “delegated decisions” to communicate authority more precisely in a short standalone field.
