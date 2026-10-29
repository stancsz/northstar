# StageKit text-only trial receipt

## Scope and constraints

- Fictional concept only: StageKit sells workspace access to rental companies; event organizers may separately buy staffed delivery.
- User constraints followed: Chinese and English Marp text drafts, six slides each, shared explicitly missing image placeholders; no web, image generation, rendering, paid calls, contacts, other writes, delegation, commits, or skill edits.
- The user supplied route preflight as already passed (`127.0.0.1:4000/v1`, model `codex-luna`, text and `echo_marker` roundtrip `NORTHSTAR_SOAK_29`). No route troubleshooting or provider call was performed.
- Wrote `first-en.md` and `first-zh.md` once. They are first-pass artifacts and were not repaired after review.

## Skill provenance

- Read: `C:/Users/stanc/.codex/skills/bilingual-product-demo-deck/SKILL.md`
- SHA-256: `AC958D2DD09F61469F007006FD08B178B4B36435CDA36557FC661198B472C52E`
- Relevant exact excerpts:
  - “A mockup is not a working product or evidence of buyer demand.”
  - “Acknowledge prototype status and limitations concisely; never invent results, testimonials, integrations, security assurances or urgency.”
  - “Use one fictional scenario across screens where possible, with plausible, internally consistent numbers, dates, stages and currencies. Show sample data clearly.”
  - “Build for validation: a prospective buyer should be able to tell you whether they would use it, what is missing, who would use it and what they would pay per location per month. Ask about their existing workflow and alternatives first. Ask for an unaided amount and currency, including zero, before presenting ranges.”
  - “If rendering, font verification or image inspection cannot be performed, preserve sources and identify the missing check rather than passing it.”
  - “If another format or a different location is requested, follow it; if Marp is unavailable preserve source and report the limitation rather than pretending another renderer was Marp.”

## Checks

- Both decks contain valid Marp front matter and six `---`-separated slides.
- Both use the same fictional company, organizer, event, date, equipment quantities, handoff time/place, offer split, and narrative sequence.
- Both include all six matching image-placeholder filenames; placeholders explicitly state the images are missing/not generated.
- Both preserve concept status and avoid claiming customer proof, integrations, product performance, or delivery guarantees.
- Both ask about current workflow and users before unaided monthly per-location pricing, explicitly accept zero, and state that a hypothetical answer is not a commitment.
- First-pass SHA-256:
  - `first-en.md`: `895F9F611333E46E720904E19F4CFC702395AF42A4A16623EBCE05EAC61E63B2`
  - `first-zh.md`: `B67CE8FC5F0F0E7CE1F79D18E5D8C79D884443165CC9847674D9BA8F5851C3DF`

## Gaps

- No images were generated; all visual assets are explicitly missing placeholders.
- No rendering, PDF export, font, clipping, or visual consistency check was performed, as requested.
- No market research or incumbent comparison was performed; differentiation and willingness-to-pay are untested hypotheses.
- No buyer feedback, contact, live product, integration, or operational result exists in this fictional trial.
- The exact user-provided Chinese date/measurement semantics were kept as written; no locale-specific calendar validation was performed.
