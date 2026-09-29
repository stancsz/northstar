# Independent source review: README positioning

Date: 2026-09-29. Reviewed revision: `ff7b1c6` plus the current working-tree drafts. Reviewer: independent of README authorship. Scope: `README.md`, `docs/misc/README.zh-CN.md`, linked installation/skill guidance, and the four cited evaluation summaries. Scratch probes: `tmp/readme-positioning/reviewer/probes.txt`.

## Review probes and observations

- **First use and package:** Both pages lead to the shared installation guide, show a bounded `$northstar` example, and map all four sibling skills. The install guide confirms the four directories must be installed together and explains host-specific loading. The Advisor service and optional reader prerequisites are called out separately; the pages do not imply that installation starts services or calls a provider.
- **Delegated authority and management:** Standing authority is presented as mandate-bounded; outside decisions and indispensable human dependencies return to the owner. The manager's integration/remedy responsibility, worker ownership, independent review, and bounded recovery language match the current Northstar, Codex QA, and Subagents guidance. The reviewer separation wording correctly includes experience/taste review and manager repairs.
- **Evidence and portability:** The example is explicitly identified as a usage example, not a benchmark. Efficiency prose counts total effort and says cheaper models or larger teams do not establish savings. The evidence section accurately frames the trials as limited and leaves comparative gains, reduced owner intervention, savings, sustained business outcomes, and broad host integration unproven. Cross-host use is framed as Markdown guidance requiring host adaptation, rather than tested integration. Design-source references link to the project's existing maps and explicitly disclaim endorsement and efficacy proof.
- **English/Chinese parity:** Both pages cover the same audience, management gap, authorized initiative, integration accountability, independent acceptance, checkpoint learning, first action, four-skill map, service boundary, use cases, evidence boundary, and installation/feedback path. The Chinese is idiomatic and reorganizes a few phrases naturally rather than translating literally. No material scope or caveat mismatch found.
- **Links and whitespace:** A local-link/approximate-heading check found 35 links per page and no missing targets or fragments. `git diff --check -- README.md docs/misc/README.zh-CN.md` returned no whitespace errors; Git printed only expected LF-to-CRLF working-copy notices.

## Findings

**Must fix:** None found in source.

**Suggestion:** For the standalone GitHub description, consider changing “autonomous decisions” to “authorized decisions” or “delegated decisions.” The fuller README accurately says Northstar guides behavior and is neither runtime enforcement nor a guarantee of autonomy, so this is not a blocker; the shorter About field may be read without that context.

## Decision and remaining evidence

**Source review: READY.** The reviewed copy meets the content and claim-boundary criteria in the [readme-positioning goal](../../goal/readme-positioning/GOAL.md). Local link and whitespace checks passed.

**Overall publication review: UNVERIFIED.** I did not inspect GitHub-rendered English/Chinese pages, responsive layout or navigation in the browser, nor the resulting About fields, Topics, and issue-label state. Those checks remain pending the primary agent's rendered captures and metadata result. This source verdict does not authorize or attest to publication.

## Rendered review and metadata readback (2026-09-29)

I opened the provided original-resolution captures from `docs/evals/assets/readme-positioning/`:

- **English opening (`english.png`, 517×884):** Clear title, promise, package definition, language/install/evidence navigation, badges, audience statement, and problem framing. Line wrapping is readable at the captured width. No visible clipping or overlapping controls in this portion.
- **Chinese opening (`chinese.png`, 517×884):** Clear Chinese positioning, subtitle, navigation, badges, audience statement, and problem framing. Chinese wraps naturally at the captured width. No visible clipping or overlap in this portion.
- **Chinese lower page (`chinese-diagram.png`, 517×884):** The four bold labels in the use-case list rendered their Markdown `**` characters literally, making the content visibly unfinished. The embedded diagram is partly obscured by GitHub's on-screen zoom controls in this capture, so its complete presentation cannot be judged here.

The primary reports repairing the four list lines by adding a space after each closing `**`. I independently checked the current source at lines 120–123; all four labels now use `- **label:** ` followed by a space and the text. This is the correct Markdown form for GitHub rendering. The defect remains in the earlier screenshot and is preserved as failed visual evidence; a fresh post-repair capture and inspection are required before marking publication READY. No current rendered pass for the repaired lines is claimed.

The provided readback files `tmp/readme-positioning/github-after.json` and `tmp/readme-positioning/labels-after.json` show the final description using “delegated decisions,” the installation guide as homepage, 15 repository topics, all seven proposed labels, and all nine default labels retained. This confirms the captured readback contents; it does not independently authenticate the command or the live GitHub state. The primary reports that clicking English → 中文 succeeded; I did not repeat that interaction in the browser.

**Provisional checkpoint decision: UNVERIFIED for publication.** At that review point, the source-level review was READY and the two opening captures met the inspected readability checks at 517×884. The lower Chinese rendered defect had been fixed in source but awaited visual recheck, and the diagram needed an unobscured view. The final visual closeout below supersedes this checkpoint.

## Final visual closeout — published revision `6fc5948`

This final section supersedes the provisional publication status above. I opened the new original-resolution captures and checked the live GitHub page at the current `main` revision:

- **`chinese-repaired.png`:** At the inspected narrow width, all four use-case labels are rendered as bold Chinese text. The literal Markdown markers are gone. Paragraph wrapping and the adjacent evidence table remain readable at 517×884.
- **`chinese-evidence.png`:** The evidence summary label “仍待证明” is bold and renders without literal markers. The summary table and closing links are visible and readable at 517×884.
- **`chinese-flow-expanded.png`:** At the captured 1280×900 desktop view, the expanded Mermaid viewer displays the full topology. Every node and connection is present; native pan/zoom controls sit beside the diagram without covering its nodes.
- **English opening:** The earlier 517×884 GitHub capture remains representative: the positioning, first-use links, badges and problem framing are readable. English content was unchanged in the final Chinese punctuation repair.
- **Language navigation and live publication:** In Chrome, I opened `https://github.com/stancsz/northstar` at `6fc5948`, clicked the rendered **中文** link, and confirmed navigation to the rendered Chinese README and its Chinese headline. The live About panel showed the updated delegated-decisions description, installation-guide homepage and current 15 topics. The supplied `labels-after.json` readback contains the seven requested labels and all nine defaults.

**Limitations:** The narrow inline Mermaid view uses GitHub's pan/zoom controls and its labels appear small at the captured width; the expanded viewer is the clear way to inspect the complete diagram. Evidence covers the actual 517×884 page views and 1280×900 expanded diagram, not every device size. The expanded screenshot has some capture softness, although node text and topology are inspectable. These limits do not obscure the reviewed content or indicate a remaining defect.

**Final decision: READY for the reviewed publication scope.** The initially observed literal-asterisk defect in the Chinese use-case labels, and the subsequently corrected evidence-summary emphasis, remain recorded above as historical failures. Fresh GitHub renders at `6fc5948` verify both repairs; the source and live English-to-Chinese navigation also check out.
