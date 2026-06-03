# Compliance, PII & Data Governance Testing

Layer 6 can fold a compliance checklist into the readiness score. Produce a
`compliance.json` in the run directory; `score_release.py` reads it and turns any
failed check into a defect (default severity `high`).

## compliance.json shape

```json
{
  "frameworks": ["GDPR", "PIPL", "SOC2-TypeII", "ISO-25010"],
  "checks": [
    {"name": "PII not logged in plaintext", "framework": "GDPR",
     "passed": true,  "severity": "critical",
     "how_to_verify": "grep application logs for email/phone patterns",
     "detail": "no matches in 10k log lines"},
    {"name": "Data subject deletion honored end-to-end", "framework": "GDPR",
     "passed": false, "severity": "high",
     "how_to_verify": "delete account, confirm removal across stores within SLA",
     "detail": "record persisted in analytics warehouse after deletion"}
  ]
}
```

## Framework starter checklists

**GDPR / PIPL (personal data):** lawful basis recorded · data minimization ·
PII never logged in plaintext · right-to-access export works · right-to-deletion
propagates to all stores · consent withdrawal honored · cross-border transfer
controls (PIPL is stricter on export from China).

**SOC 2 Type II (operational controls over time):** access control enforced &
least-privilege · audit logging on sensitive actions · change management on
production · encryption in transit and at rest · incident response runbook ·
vendor/subprocessor review.

**ISO/IEC 25010 (product quality model):** functional suitability ·
reliability · performance efficiency · security · maintainability · usability ·
compatibility · portability. Map your coverage map to these characteristics so
the report shows quality-in-use, not just pass counts.

## PII leakage & data-masking detection (automatable)

Run these as `cli`/`predicate` test cases against logs, API responses, and the
LLM's own outputs. Detector regexes (extend per locale):

- Email: `[\w.+-]+@[\w-]+\.[\w.-]+`
- Phone (NA): `\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b`
- Credit card (Luhn-eligible): `\b(?:\d[ -]?){13,16}\b`
- Canadian SIN: `\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b`
- API keys: `\b(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b`

A passing data-masking test means these patterns are **absent** from
user-facing output and logs (or appear only as masked tokens like `****`).

## Access-control testing

For multi-tenant or role-gated products, generate negative cases that attempt to
read/write across the authorization boundary. A correct system returns 403/empty;
a breach (cross-tenant read) is a `critical` compliance + safety defect.
