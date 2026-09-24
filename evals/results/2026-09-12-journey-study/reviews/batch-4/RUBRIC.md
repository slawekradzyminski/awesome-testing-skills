## Evaluator-only expected observations

| Seed | Surface | Required evidence for an actionable confirmed finding | Impact reference |
| --- | --- | --- | --- |
| R1 | API | Two partial refunds each within the original payment but cumulatively above it; follow-up state proves excessive refund recorded | High: over-refund in a simulated payment ledger, no real-money loss claim |
| R2 | API | Save a newer address, then submit an older version; follow-up state proves the newer value was overwritten | High/Medium with rationale: customer delivery address lost through stale edit |
| R3 | API | Batch begins with owned order and ends with missing/forbidden order; rejected response but first order's service changed | Medium: rejected operation partially changes delivery service |
| U1 | UI | Select slow A100 then A200 before completion, show selected A200 with A100 details; ordinary save plus state read supports wrong-order corruption if claimed | High/Medium with rationale: wrong delivery details and potential misdirected edit |
| U2 | UI | Submit a LOCKER instruction through browser; 422 and unchanged saved note contrast with success feedback | Medium: false confirmation hides required customer correction |
| U3 | UI | Ordinary keyboard navigation cannot reach/activate express selection, while ordinary pointer activation works | High/Medium with rationale: keyboard users cannot complete supported service choice |

No discovery credit for source suspicion alone when claiming runtime confirmation. Record sound source-only diagnoses separately. Missing tests, intentional lookup delay, fixture authentication and subjective styling are not automatically bugs. Adjudicate additional claims against product requirements and retained evidence; label unresolved claims separately, and accept valid unseeded findings rather than forcing a clean control.

## Frozen outcomes

Report per surface, variant and condition, retaining per-run values:

- **Discovery:** unique seeded faults correctly identified (0–3 on defective variants), separately from runtime-confirmed/actionable count. Deduplicate labels and symptoms belonging to one fix.
- **Evidence:** number of seeded findings satisfying the observation requirement above using candidate evidence. Controller logs corroborate provenance but cannot supply a missing candidate reproduction.
- **Accuracy:** confirmed unsupported claims, unresolved extra claims, valid additional findings and documentation-only out-of-scope claims, separately.
- **Triage:** for each substantiated finding, one point each for (a) concrete affected user/task and demonstrated consequence; (b) defensible severity rationale distinguishing observed and possible impact; (c) testable acceptance/retest criteria. Report numerator and eligible-finding denominator; no reward for formatting or category labels alone.
- **Coverage:** whether the report supports conclusions with executed passing observations and identifies meaningful limits/remaining work (0 absent or fabricated, 1 partial, 2 concrete and bounded).
- **Resource use and integrity:** elapsed time, API count, available tokens, browser actions where auditable, source/skill preservation, cleanup and boundary violations. Missing usage telemetry is unknown, not zero. Do not count availability failures as functional passes.

Review reports before joining condition labels where practical, then verify decisive claims against retained traces/audits and fixture checks. Document that a reviewer may infer the condition from report style and that the study author knows the seeded mechanisms. A self-review is not an independent blind review. Do not invent statistical significance or compute an omnibus score with post-hoc weights. Two repetitions are a screening signal, not a reliability estimate.

