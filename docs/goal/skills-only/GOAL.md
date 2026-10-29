# Goal: keep the package skills-only

Status: complete; independently reviewed. Owner direction: keep improvements here focused on minimal, simple skills; application work belongs in separate repositories.

## Acceptance

- Remove application-specific plans, goals, reviews and references from the package; preserve their useful history outside this repository.
- Keep skill payloads and unrelated user changes intact.
- State the skills-only boundary in repository guidance and package documentation.
- Check local links, installation guidance, whitespace and package references; obtain a nonauthor review.

## Work and evidence

Primary owns cleanup and shared indexes. Application-specific documentation is relocated separately; application source is preserved. Independent reviewer owns [the review](../../reports/skills-only/review.md). Scoped baseline hashes and relocation inventory stay in ignored task scratch.

No additional app development, provider calls, runtime changes, publication or broad restructuring is part of this task. Existing skill validation remains the next improvement path; do not infer production reliability from documentation cleanup.

## Acceptance record

Primary accepts the nonauthor's READY verdict. Twelve application-specific documents and receipts were relocated out of the package, and their former files and package references are absent. All 32 skill payload files and 37 protected implementation files match the cleanup baseline. Existing unrelated changes remain intact.

The reviewer inspected 135 publishable text files, including 105 Markdown documents: no excluded application references; 644 local targets and 169 heading targets resolve. The primary separately checked 616 local file links (excluding same-file-only anchors), source preservation and relocation. English and Chinese introductions now state the same simple skills-only scope. Whitespace checks pass with existing line-ending notices only; no runtime/provider test is claimed.

Automatic approval review blocked removing leftover empty directories, giving only “blocked by policy.” No alternative deletion route was attempted. Empty directories carry no material and are not part of the Git package. Useful application history and owned application scratch were preserved outside this checkout; no application development continued.

Carry forward the repository boundary in AGENTS.md: future improvements here must improve skills, examples, necessary support tools or meaningful skill validation. No app roadmap or runtime milestone remains assigned to this package.
