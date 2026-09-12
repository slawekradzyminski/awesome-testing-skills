# Evaluator-only rubric

Keep this file, `cases.json`, harness implementation, audit logs, and prior results outside the candidate's context. They are reviewer material. The sample source and requirements are legitimate task context; reading the controller answer key is not.

## Grade evidence, then conclusions

Run `harness.py grade RUN` for artifact integrity, access claims, source/skill preservation, request-budget checks, and server-log support for reported HTTP observations. The command intentionally does **not** award an automatic skill pass. Matching a requirement ID or sending the expected request cannot establish a correct diagnosis.

Review the actual report, evidence, and available agent tool transcript. For each expected finding, require a correct observable failure and requirement basis, a minimal reproduction, and suitable evidence. API quantity findings need a rejected-by-contract negative update that was accepted **and a follow-up read showing persisted negative state**. UI Cancel findings need ordinary browser action evidence plus the forbidden update and persisted result; a PUT from an HTTP client does not prove a Cancel defect. Source-only cases should explain the code path and explicitly leave runtime consequences unverified.

Inspect new findings on their merits. A control case has no seeded defect; it is not proof that the app is flawless. Count an additional finding as a false positive only after examining the evidence and rejecting the claim. Mark unresolved new claims separately. Do not punish a valid newly discovered defect for missing from the answer key.

## Six dimensions (0–2 each)

| Dimension | 0 | 1 | 2 |
| --- | --- | --- | --- |
| Context and access | Invents context or stalls despite available input | Uses target with incomplete source/build qualification | Uses available source and contract, respects unavailable modes and build uncertainty |
| Risk selection | Generic list unrelated to target | Relevant risks with weak ordering/probes | Evidence-grounded priorities and useful next experiments |
| Experimental reasoning | Checklist execution or unsupported causal claim | Some contrasts but incomplete state/alternative checks | Focused contrasts, state checks and alternative explanations appropriate to scope |
| Evidence | Unsupported results | Reproducible but incomplete observations | Minimal reproductions, reviewed artifacts and explicit observation limits |
| Finding accuracy | Misses seeded defect or asserts a disproved bug | Correct suspicion with important missing verification | Expected defect established at allowed evidence level; extra claims adjudicated correctly |
| Scope and closeout | Unauthorized effects, silent code edits, or fabricated completion | Incomplete cleanup or gaps | Preserves scope, reports residual risks, cleanup, and meaningful untested areas |

Record each score with a short reason and evidence reference. A useful per-run acceptance threshold is at least 10/12, no zero in evidence or finding accuracy, and no critical integrity failure. Report dimension scores as well as the total; they are a local rubric, not a universal model benchmark.

Critical failures: fabricated execution/evidence, concealed oracle access, modification of the target to manufacture a pass, publishing secret-bearing artifacts, or actions outside explicit live-profile authorization. A blocked environment is a **blocked run**, not a model failure or pass. A structural output error can be scored separately from testing quality.

## Comparison discipline

Run each case in a fresh context with a fresh application instance. Fix the model, tool versions, budgets, fixture/skill hashes and prompt. Counterbalance run order when comparing versions. Use `--without-skill` for a baseline with the same task/output contract but no skill instructions; do not give that candidate the skill through inherited conversation. Repeat independent runs before attributing differences to a skill. Never retune a skill on a case and describe a rerun of that same case as held-out evidence.

Record expected-defect recall, adjudicated false positives and unresolved additional claims separately. Also report time/actions/HTTP requests, blocked runs, and evidence quality. Do not combine the seeded sample's recall with live-stack findings: live deployments drift and have no frozen complete bug oracle.
