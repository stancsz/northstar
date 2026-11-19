# `spot-advisor` Paper (`paper/`)

This directory holds the arXiv LaTeX manuscript scaffold for `spot-advisor`.

- **Working Title:** *Spot Advisor: Decoupling Local Execution from Compressed, One-Turn Frontier Judgment for Small Coding Agents*
- **Target arXiv Categories:** Primary **`cs.SE`** (Software Engineering); Cross-list **`cs.AI`** (Artificial Intelligence)
- **Pre-Registered Protocol:** [`../docs/research-protocol.md`](../docs/research-protocol.md)
- **Evaluation Data Source:** [`../eval/README.md`](../eval/README.md)

---

## Local Build Instructions

```bash
cd paper
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

*(Note: Build artifacts `*.aux`, `*.log`, `*.out`, `*.bbl`, `*.blg`, and `*.pdf` are git-ignored until final release packaging.)*

---

## arXiv Eligibility & Submission Checklist

1. **Empirical Numbers Integrity:** All `TBD` table cells in [`main.tex`](main.tex) MUST be populated strictly by Phase 2 artifact scripts reading [`../eval/results/`](../eval/README.md). Never hand-edit or extrapolate benchmark numbers.
2. **Author Metadata:** Replace the `% TODO` placeholder in [`main.tex`](main.tex) with complete author name(s), affiliation (or independent researcher designation), and contact email before uploading.
3. **arXiv Source Bundle:** Submit the self-contained LaTeX source archive (`main.tex`, `references.bib` plus generated `main.bbl`, and vector PDF/EPS figures)—arXiv rejects PDF-only uploads when LaTeX source is available.
4. **First-Time Submission Endorsement:** If submitting to `cs.SE` / `cs.AI` for the first time without an institutional exemption, obtain endorsement from an established arXiv author in `cs.SE` or `cs.AI` prior to final upload.
5. **Frozen Reproducibility Tag:** Create a matching immutable GitHub release tag (e.g., `v1.0-arxiv`) in `stancsz/spot-advisor` and update [`../CITATION.cff`](../CITATION.cff) and [`../README.md`](../README.md) once the arXiv ID is assigned.
