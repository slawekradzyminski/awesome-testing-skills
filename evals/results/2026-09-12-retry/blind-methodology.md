# Blind artifact review methodology

All twelve reports were read against requirements.md and the same six rubric dimensions. Access conditions and seeded requirement IDs came only from cases.json. Experimental condition labels were not provided or inferred. Review stayed inside this directory; no application, tests, original runs, or new exploration were executed.

Decisive negative-quantity request/read sequences, source-only handler/domain paths, Cancel reproductions and available browser network records were inspected. Six representative screenshots were opened (B, D, F, G, J, K); images were used only for visible state. Other screenshots and the complete original action transcripts were not verified. The supplied artifacts support assessment, not independent provenance certification. No harness grade, server audit, or original before/after target snapshots were available. Integrity, access preservation, time and action counts therefore remain provisional.

| Case | Context | Risk | Reasoning | Evidence | Accuracy | Closeout | Total |
|---|---:|---:|---:|---:|---:|---:|---:|
| case-A | 2 | 2 | 2 | 2 | 2 | 1 | 11/12 |
| case-B | 1 | 2 | 2 | 1 | 2 | 2 | 10/12 |
| case-C | 1 | 2 | 2 | 2 | 2 | 2 | 11/12 |
| case-D | 2 | 2 | 2 | 1 | 1 | 2 | 10/12 |
| case-E | 2 | 2 | 2 | 2 | 2 | 2 | 12/12 |
| case-F | 1 | 2 | 2 | 1 | 1 | 2 | 9/12 |
| case-G | 2 | 2 | 2 | 2 | 2 | 2 | 12/12 |
| case-H | 2 | 2 | 2 | 2 | 2 | 2 | 12/12 |
| case-I | 1 | 2 | 2 | 2 | 2 | 1 | 10/12 |
| case-J | 1 | 2 | 2 | 1 | 1 | 2 | 9/12 |
| case-K | 2 | 2 | 2 | 2 | 2 | 2 | 12/12 |
| case-L | 2 | 2 | 2 | 2 | 2 | 2 | 12/12 |

The primary source+runtime set contains eight reports: four with a seeded requirement and four without one. All four seeded defects were identified, but only C, H and K meet the rubric’s full evidence criterion. F has persisted changes and a convincing captured source mechanism, but no forbidden browser PUT capture. B likewise lacks a network trace for its qualified no-PUT conclusion. K supplies browser network deltas, request/response bodies and persisted state. API findings in C and H supply accepted negative writes followed by negative persisted reads.

The four supplementary fallback cases remain separate. E and L fully establish their source-only code findings at the allowed evidence level and explicitly leave runtime predictions unverified. D and J strongly support Cancel-related persisted changes but lack the required browser mutation capture; D also lacks a separate saved-state read for its keyboard repeat. These evidence deductions do not penalize the absence of source access. A and I lose a closeout point for a documented but outstanding owner reset after Bob removal, not for an unauthorized action.

No adjudicated false positive or unresolved additional product finding was found. Hardcoded pricing, asynchronous races and transport recovery were reported as risks, not established bugs. No-seed cases are not known-bug-free controls, and a lack of additional reported defects does not establish the absence of unseeded bugs.

This suite supports a narrow demonstration of artifact quality on one small fixture, not broad exploratory-testing performance or a causal skill benefit. Limitations include only two seeded mechanisms, one simplified Python/JavaScript application, tiny per-scenario samples, unknown independent repeats/order counterbalancing/model and tool controls, unverified source/runtime equivalence, heterogeneous browser tooling and instrumentation, inconsistent action/request accounting, and incomplete original execution evidence. A scalar threshold can be met even when a seeded defect is only partially verified; retain the dimension scores and the separate defect-verification result. Source fallback scores must not inflate runtime recall.

For a comparative claim, join these frozen blind scores to condition labels only after review, obtain external integrity grades, normalize time/actions/HTTP accounting, repeat independent fresh-context trials, counterbalance order, freeze fixture/prompt/model/tool/skill versions, and test genuinely held-out tasks across more applications and failure classes. Any tuning on these cases must be described as development evidence. Use a second reviewer or adjudication to quantify scoring subjectivity.
