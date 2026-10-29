# Frozen retest worker check

Input digests:
- Skill `C:/Users/stanc/.codex/skills/bilingual-product-demo-deck/SKILL.md` SHA256: `7491D1B3B305240565AADC4BFB7582844974971C19FD045232870EBE0CC5D7B9`.
- Parent-owned `expected.md` SHA256: `AC03CAEB8893322BD3128B3FF464A2F598D2C92EA9BEBAC756913A86167CB04F` (read only; unchanged).

Actual visible body-text locations (1-based slide numbers; placeholders are image references and are not counted as body text):

| Required text | Expected slide | English | Chinese |
|---|---:|---|---|
| ToolHarbor | 1, 6 | 1, 6 | 1, 6 |
| Cedar Makerspace | 1, 2, 5 | 1, 2, 5 | 1, 2, 5 |
| Oak School | 2, 3, 5 | 3, 5 | 3, 5 |
| Jamie Lee | 3, 4 | 4 | 4 |
| Bench Room | 3, 4 | 4 | 4 |
| 8 drill kits; 12 safety sets; 20 participants; 2026-11-12; pickup 09:00; return 16:00 | 3 | 3 | 3 |

Failures against frozen expectations: Oak School is missing on slide 2 in both languages. Jamie Lee and Bench Room are missing on slide 3 in both languages. English and Chinese both have six Marp slides; all required scenario quantities/date/times appear on slide 3. No repairs were made. Explicit image references are placeholders and images were not generated or inspected. Rendering/readability remains unverified.
