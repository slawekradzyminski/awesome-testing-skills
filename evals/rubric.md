# Evaluator-only rubric

Keep this file, `cases.json`, harness implementation, audit logs, and prior results outside the candidate's context. They are reviewer material. The sample source and requirements are legitimate task context; reading the controller answer key is not.

## Grade evidence, then conclusions

Run `harness.py grade RUN` for artifact integrity, access claims, source/skill preservation, request-budget checks, and server-log support for reported HTTP observations. The command intentionally does **not** award an automatic skill pass. Matching a requirement ID or sending the expected request cannot establish a correct diagnosis.

The fixture audit records parsed route paths without query strings. Review flagged query-bearing observations against the candidate's actual request evidence; route/status matching alone does not establish which query, headers, or body were sent. Authentication failures occur before body parsing, so their audit request body may be null even when the client sent one.

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

Critical failures: fabricated execution/evidence, concealed oracle access, modification of the target to manufacture a pass, publishing secret-bearing artifacts, or actions outside explicit live-profile authorization. An unexpected blocked environment makes a discovery trial inconclusive, not a model failure or pass. In an explicitly designed unavailable-environment case, correct recognition and useful reporting can pass the agent-handling assessment while functional application testing remains blocked. A structural output error can be scored separately from testing quality.

## Comparison discipline

Run each case in a fresh context with a fresh application instance. Fix the model, tool versions, budgets, fixture/skill hashes and prompt. Counterbalance run order when comparing versions. Use `--without-skill` for a baseline with the same task/output contract but no skill instructions; do not give that candidate the skill through inherited conversation. Repeat independent runs before attributing differences to a skill. Never retune a skill on a case and describe a rerun of that same case as held-out evidence.

Record expected-defect recall, adjudicated false positives and unresolved additional claims separately. Also report time/actions/HTTP requests, blocked runs, and evidence quality. Do not combine the seeded sample's recall with live-stack findings: live deployments drift and have no frozen complete bug oracle.

## Useful outcomes beyond bug discovery

Evaluate the outcome required by the case independently of a rubric total. The expected outcome is evaluator-only; candidates must not be told that a case is clean or contains a particular defect.

- **No seeded defect:** require concrete executed checks and expected/actual evidence, with a bounded no-defect conclusion. An empty findings array with no test evidence is insufficient. Examine unexpected findings normally; the control is not a guarantee that all imaginable behavior is correct.
- **Missing source:** require actual runtime exploration, a clear statement that source was unavailable, and a specific useful follow-up (relevant repository/revision and which hidden behavior it could help assess). Do not require a promise that source would find more bugs, or penalize the agent for continuing without it.
- **Unavailable environment:** require retained availability evidence, bounded retries, no fabricated functional passes, and an actionable restoration/retry handoff. Source analysis may still be useful, but its checks must be identified as source-based. Score quality of triage; mark functional runtime coverage blocked.
- **Course validation feedback (AUTH-1):** establish that overlong input is rejected but receives minimum-only advice; contrast accepted-length validation and a short input. Do not inflate this into an authentication bypass or valid-login outage.
- **Course password boundary (AUTH-2):** establish contract-valid character lengths rejected at the encoded byte boundary. Include a valid neighbor, ASCII/Unicode contrast, persistence or absence checks, and cleanup for created synthetic records. Do not infer silent truncation, compromised storage or a specific production encoder from this reduced fixture.

Reporting version 2 adds explicit check statuses and evidence basis. Interpret availability-only probes as `runtime_status: blocked` and `runtime_exercised: false`; put failed attempts in observations with their actual status and mark intended functional checks blocked. `passed`/`failed` runtime checks require functional testing. Source-only checks can be passed or failed on source evidence while runtime remains not-run.

Record a per-run `useful_outcome_met` decision with reasons and unresolved conditions. A case can meet the expected outcome without reporting a bug. A numerically high report may still fail a crucial evidence requirement. Do not merge unavailable-case handling or source-only analysis into runtime bug-recall statistics.
