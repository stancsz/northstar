# Adversarial Testing — OWASP LLM Top 10

`adversarial.py` ships a compact probe pack. This file documents the full attack
surface so you can extend `PROBES` for the product under test. Adversarial
coverage is **not optional** for any product with a user-facing LLM interface.

| ID | Category | What you're testing | Breach signal |
|---|---|---|---|
| LLM01 | Prompt Injection | Untrusted input overrides instructions | Model obeys injected command / leaks system prompt |
| LLM02 | Insecure Output Handling | Output passed downstream unsanitized | XSS/SQL payload echoed verbatim into output |
| LLM03 | Training Data Poisoning | Tainted training/fine-tune data | Backdoor trigger phrase produces anomalous output |
| LLM04 | Model Denial of Service | Resource-exhausting inputs | Unbounded loops, runaway token generation, timeouts |
| LLM05 | Supply Chain | Compromised models/plugins/datasets | Untrusted dependency executes / exfiltrates |
| LLM06 | Sensitive Info Disclosure | Secrets/PII in responses | Keys, secrets, other users' data surface |
| LLM07 | Insecure Plugin/Tool Design | Tools with weak input validation | Tool runs destructive action on crafted input |
| LLM08 | Excessive Agency | Too much autonomy/permission | Acts (email, payment, delete) without confirmation |
| LLM09 | Overreliance | Unverified output trusted as fact | Confident hallucination accepted downstream |
| LLM10 | Model Theft | Extraction of weights/behavior | Systematic probing reconstructs the model |

## How a probe is defined

Each probe is a dict in `adversarial.py`:

```python
{"id": "ADV-LLM01c", "owasp": "LLM01 Prompt Injection",
 "probe": "<the adversarial input>",
 "breach_if_contains": "CANARY"}          # or breach_if_contains_any: [...]
```

The harness injects `probe` into your target (via `--inject-into`), runs it, and
flags a breach if the canary/marker appears. Design canaries that *only* appear on
a successful attack — e.g. instruct the injection to emit a unique token, then
check for that token. For disclosure probes, plant a known secret in the target's
context and check whether it leaks.

## Extending coverage per product

- **RAG products:** add LLM06 probes that ask for documents outside the user's
  ACL; a breach is retrieval of another tenant's content.
- **Tool-using agents:** add LLM07/LLM08 probes for every destructive tool. The
  breach signal is the action executing without an explicit confirmation step.
- **Multi-turn chat:** add LLM01 probes split across turns (payload in turn 1,
  trigger in turn 3) — single-turn filters often miss these.

## Limits — state these honestly in the report

A screening harness proves the presence of breaches, never their absence. For
products under regulatory scrutiny, pair this with a manual red-team engagement.
The skill's `limitations.md` artifact is the place to record exactly what your
screening pack did and did not exercise, and to recommend a full pentest when
warranted.
