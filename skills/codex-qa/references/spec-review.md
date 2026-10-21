# Three-pass independent spec and implementation review

Use for a requested spec-driven workflow or the [Spec Kit bridge](../../northstar/references/spec-kit.md). Review the actual project schema and constitution. The optional [eight-section profile](../templates/spec-profile.md) supplies FR / KE / SC / A / Q identifiers when needed; do not reject upstream specs for lacking that custom layout.

The author supplies evidence and runs development checks. An uninvolved reviewer runs these passes in order and reports directly to the accepting owner. The same nonauthor may run all three; a fresh context does not erase authorship. A reviewer writes findings and probes, never repairs the spec or product while certifying it. If reassigned to repair, another reviewer checks that scope.

## Run the passes

| Pass | Checklist sections | Decision and evidence |
| --- | --- | --- |
| 1 — Structural | §1 | Does this conform to the adopted schema? Record spec revision, schema/version, missing sections, identifiers and broken references. |
| 2 — Evidence and privacy | §2 + §5 | Is each required claim supported and each criterion measurable? Inspect sources and scrub the intended release surface; unavailable sources remain unverified. |
| 3 — Adversarial | §3 + §4 | What broken implementation could still pass? Challenge every FR/SC and strengthen the proposed check through findings to the author; never silently rewrite acceptance. |

Store the three outcomes once in the existing feature review/checklist record: pass, reviewer/non-authorship, artifact revision, checks actually performed, findings by requirement ID, disposition and next action. Use the [compact receipt practice](skill-effectiveness.md) only when evaluating the skill itself. A single reviewer can record all passes together; three labels without inspected evidence are not three reviews.

Resolve structural blockers within a spec before treating its evidence review as complete, and its evidence/privacy blockers before declaring its adversarial review complete. Evaluate independent specs separately: a blocker in one does not block another unless they share the affected requirement or dependency. Useful later probes may be prepared while a blocker is being repaired; that spec's stage remains pending. Record material questions in the project's question section (section 8 in the custom profile), with owner and unblock condition. An open question about required behavior, unsupported mandatory claim, privacy defect or missing verification blocks acceptance; merely listing it never resolves it. A later optional question may remain explicitly outside accepted scope.

## Checklist

### 1. Structure

- Identify the adopted template and actual constitution; check its required sections, stable IDs, internal links, and requirement-to-criterion mapping. For the custom profile, check all eight sections and FR / KE / SC / A / Q references; explicitly mark inapplicable entity sections rather than inventing entities.
- Distinguish requirements, assumptions and unresolved decisions. Check citation-per-claim when the adopted profile requires it. A plausible citation string is only structural evidence until pass 2 opens it.

### 2. Evidence and measurability

- Open each FR's source and each material factual claim's evidence; verify exact support, version and scope. An owner request can support desired behavior; it cannot establish an external fact. Missing sources and inference stay labeled.
- For every SC, identify observable output, inputs, environment, threshold and a judging method. Test whether a reasonable independent reviewer could decide pass/fail. Vague words such as fast, secure or reliable are insufficient alone.
- Map each FR to at least one SC or direct acceptance check and each SC back to intended value. Identify contradictions, orphan criteria, unsupported assumptions and material unanswered questions.

### 3. Attack the functional requirements

- For **each FR**, propose a concrete broken implementation that might satisfy the current wording or superficial check. Examine the applicable failure boundary: empty/invalid/long input, duplicate/replayed action, interruption, persistence, dependency failure, stale state or authority crossing.
- State the invariant and an observable discriminator. For example, a saved-toast requirement can pass while data is lost; reload and inspect the stored result. The author repairs the spec/check; the reviewer rechecks the same finding and its affected mappings.

### 4. Attack success criteria and verify implementation

- For **each SC**, ask how a fake, hardcoded, partial or happy-path-only result could pass. Challenge denominators, time windows, fixtures, environment differences and the asserted downstream effect.
- Before building, record proposed checks and residual uncertainty as **spec evidence**. After building, execute the relevant checks through the real entry point and inspect resulting data/output, including applicable failure/recovery cases. Link results by FR/SC and artifact revision; never convert a proposed test or stub success into a live-integration pass.
- Record READY only for the inspected scope with all required checks and material repairs independently verified. A ready spec still needs separate implementation acceptance. Missing required execution is UNVERIFIED; an observed blocker is NOT READY even when other evidence is missing.
- Name both scopes when reviewing them together: a spec can be READY while its implementation is NOT READY. A shared implementation defect blocks each affected implementation verdict; it does not invalidate an otherwise verified spec's wording, evidence or proposed adversarial checks.

### 5. Privacy and release safety

- Inspect spec, source excerpts, examples, attachments, evidence links and the proposed public report for credentials, private paths/identities, customer data and restricted source contents. Follow actual project rules; use its Article IV/IX only if those rules exist there.
- Keep sensitive evidence in authorized local storage and use a minimal sanitized summary. Do not treat a dead private link or invented redaction as evidence of the original claim. If necessary evidence cannot be safely shared, name the gap and authorized review route; do not publish first and scrub later.
- Check that publication, external messages and operational actions are within inherited authority. Review approval grants no new permission.

After a relevant change, rerun affected passes and downstream checks; retain unaffected evidence with its revision. Follow [Codex QA's repair limits](../SKILL.md#finish-without-a-review-loop) and preserve failed-attempt history across reviewers. Do not create a new review round just to rename an unresolved defect.
