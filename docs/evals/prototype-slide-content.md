# Prototype presentation content correction

2026-10-29. Scope: instruction review, not a newly generated deck or a repeatability test. Parent executor inspected the installed skill and recent conversation records directly. This extract makes the evidence reviewable inside this repository.

## Inspected sources

- Current request: “don't just create a marp pdf, 演讲稿的内容要在slides里面。”
- Chat `01a18699-39b3-7812-b292-8187f6460b77`, “研究北美医美行业痛点”: recent user messages read from the local session transcript after the chat reader exceeded its size limit.
- Chat `01a188d9-2f1a-7c92-b10c-c4e86c1c7137`, “设计长寿健康管理产品原型”: user messages read through `read_thread`.
- Installed `C:/Users/stanc/.codex/skills/bilingual-product-demo-deck/SKILL.md`: read before modification and reread in full after modification. This is a separate installed skill, not a directory shipped in Northstar.
- [Northstar entrypoint](../../skills/northstar/SKILL.md): scoped diff inspected.

## Correction coverage

| User correction, quoted or summarized | Current installed skill coverage |
| --- | --- |
| Current request: presentation content belongs on slides | New “Put the sales narrative on the slides” section requires visible buyer, problem, promise, workflow, reason to buy, offer and next decision; notes and separate scripts are supplementary. |
| Medical-aesthetics chat: “don't academic the pdf slides, sell. market the product.” | Existing Quality bar requires sales framing; new section requires selling and comprehension rather than an academic report or a wall of speech text. |
| “我要你先用image generation来做图片，只要图片。” | Make the product visible, item 1, preserves the images-only stage and image-generation requirement; the new section reiterates sequencing. |
| Every page needs corresponding, consistent left navigation and better alignment | Make the product visible, item 2, requires exact shared navigation, complete labels, order, spacing and the correct active tab, with inspection and repair. |
| “做两个marps，中英文（用同样截图）” | Item 5 requires a shared screenshot set and natural copy in each language; the new section requires a complete narrative in both versions. Editable Marp sources and matching PDF exports remain required. |
| AI embedded where useful; owner options for local inference | Item 4 embeds AI in the workflow and describes feasible cloud/local options when requested, without claiming verified privacy or integrations. |
| Longevity chat: show core functions and selling points across institution, clinical and patient perspectives | Quality bar selects concrete high-value workflows; new section connects screenshots to user actions, intended results and buyer value. It does not prescribe these three audiences for unrelated products. |
| Longevity chat: standard practices and packages bought by institutions, with patient subscriptions | New section requires service/subscription offers to explain what is delivered, by whom, and value to buyer and end user. This supports that business model without making it universal. |

## Current installed instruction excerpts

> Put the substance of the presentation visibly on the slides: who buys and uses it, the costly moment, the core promise, how the demonstrated workflow solves it, why the buyer would choose it over their current approach, what they receive, and the next decision.

> Speaker notes, a separate speech script, research notes or the final chat message may supplement this story but must not hold essential selling content that is absent from the slides.

> Before accepting the deck, read the rendered slides in order without speaker notes or companion documents.

> A screenshot gallery, slogans alone, or a complete separate speech script with missing slide content fails this check.

Original screen inspection, fictional-data consistency, price-discovery ordering, full PDF rendering, Chinese fonts, clipping checks, source packaging and customer-contact boundaries remain present. The current installed text was compared with the pre-edit read; changes were additive and confined to the delivery section.

## Checks and acceptance

- Installed skill: `python -B C:/Users/stanc/.codex/skills/.system/skill-creator/scripts/quick_validate.py C:/Users/stanc/.codex/skills/bilingual-product-demo-deck` returned exit 0, “Skill is valid!”. This checks structure, not behavior.
- Repository change: `git diff --check -- skills/northstar/SKILL.md` returned exit 0. The scoped diff adds routing and the visible-narrative acceptance requirement.
- Parent acceptance: the requested instruction correction is present and compatible with the inspected recent corrections. No new demonstration was generated; improved future output quality and repeatability remain untested. This is author/parent evidence, not an independent behavioral verdict.
