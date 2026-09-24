# Dispatch Desk evidence archive — September 12, 2026

See the [assessment](../2026-09-12-journey-study.md) and [machine-readable results](../2026-09-12-journey-study.json) for the conclusions and limitations.

- [Frozen protocol](protocol.md), [schedule](schedule.json), [input hashes and model/tool configuration](freeze.json), and [evaluated controller](evaluated-controller.py).
- [Evaluated skill snapshots](evaluated-skills/) include the reporting/accessibility/UX refinements. These exact copies were unchanged throughout the candidate study.
- [Infrastructure checks](infrastructure/results.json) verify all six seeded mechanisms and their corrected variants. Browser screenshots were captured and opened. These are fixture checks, not agent-performance scores.
- [Run metadata](run-results.json) records all 24 attempts, usage and source preservation. Every run completed; no failed attempt was replaced.
- [Review inputs and raw decisions](reviews/) contain six fresh artifact-review sessions. [Condition mapping](reviews/condition-map.json) stayed outside reviewers' assigned batch directories. Text can reveal guidance use, so the review is only partially masked.
- [Owner adjudications](owner-adjudications.json) apply one whitespace-boundary ambiguity consistently to the template and skill reports. The normal report was already marked unresolved by its reviewer. Raw reviews are preserved; the result JSON includes both raw and adjudicated summaries.
- Independent author reproductions of [service response ordering](additional-service-race/adjudication.md) and [draft/transport recovery](additional-recovery/adjudication.md) corroborate additional observations in corrected variants.

Each run contains the original candidate source, scripts, report and evidence, plus the controller's events, audit and metadata. Incidental `.playwright-cli` logs and Python bytecode are excluded from this curated copy; primary evidence links in all 24 designated reports resolve. Review copies normalize known candidate-directory prefixes to their case directory and remove TASK/template/skill inputs that explicitly identify the condition; original candidate records remain unchanged here. Some report prose still reveals skill use.

The original controller's `report_exists` field checks only the candidate root. The shared output wording also permits `evidence/report.md`; every run has a report in one of those locations. This collector limitation is not scored as missing work. Use the root report when it delegates to or duplicates the evidence report.

All owned fixtures and browser sessions were closed. Archived scripts refer to stopped disposable instances: use the [study preparation commands](../../journey-study/) for a new run. No product deployment or external issue filing is involved.

## Per-run results

Counts are finding instances across repeated runs, not distinct product bugs. A control's 0/0 means no seeded opportunity; it is not a perfect-recall score.

| Run | Surface / variant | Condition | Seeded actionable | Additional valid / unresolved | Time (s) | API requests | Report |
| --- | --- | --- | --- | --- | --- | --- | --- |
| run-01 | api / defects | normal | 3/3 | 0 / 0 | 212 | 92 | [report](run-01/candidate/evidence/report.md) |
| run-02 | api / defects | template | 3/3 | 0 / 0 | 233 | 89 | [report](run-02/candidate/evidence/report.md) |
| run-03 | api / defects | skill | 3/3 | 0 / 0 | 247 | 64 | [report](run-03/candidate/evidence/report.md) |
| run-04 | ui / control | normal | 0/0 | 2 / 0 | 293 | 73 | [report](run-04/candidate/evidence/report.md) |
| run-05 | ui / control | skill | 0/0 | 2 / 0 | 327 | 60 | [report](run-05/candidate/evidence/report.md) |
| run-06 | ui / control | template | 0/0 | 2 / 0 | 312 | 80 | [report](run-06/candidate/report.md) |
| run-07 | ui / defects | template | 3/3 | 0 / 0 | 283 | 70 | [report](run-07/candidate/report.md) |
| run-08 | ui / defects | normal | 3/3 | 0 / 0 | 249 | 79 | [report](run-08/candidate/evidence/report.md) |
| run-09 | ui / defects | skill | 3/3 | 0 / 0 | 337 | 43 | [report](run-09/candidate/evidence/report.md) |
| run-10 | api / control | template | 0/0 | 0 / 0 | 197 | 90 | [report](run-10/candidate/report.md) |
| run-11 | api / control | skill | 0/0 | 0 / 0 | 240 | 105 | [report](run-11/candidate/evidence/report.md) |
| run-12 | api / control | normal | 0/0 | 0 / 0 | 226 | 97 | [report](run-12/candidate/evidence/report.md) |
| run-13 | api / defects | skill | 3/3 | 0 / 0 | 224 | 80 | [report](run-13/candidate/evidence/report.md) |
| run-14 | api / defects | normal | 3/3 | 0 / 0 | 205 | 76 | [report](run-14/candidate/evidence/report.md) |
| run-15 | api / defects | template | 3/3 | 0 / 0 | 233 | 83 | [report](run-15/candidate/evidence/report.md) |
| run-16 | ui / control | skill | 0/0 | 2 / 0 | 313 | 46 | [report](run-16/candidate/evidence/report.md) |
| run-17 | ui / control | template | 0/0 | 1 / 0 | 300 | 76 | [report](run-17/candidate/report.md) |
| run-18 | ui / control | normal | 0/0 | 3 / 0 | 258 | 74 | [report](run-18/candidate/report.md) |
| run-19 | ui / defects | normal | 3/3 | 0 / 0 | 251 | 74 | [report](run-19/candidate/evidence/report.md) |
| run-20 | ui / defects | template | 3/3 | 0 / 0 | 263 | 71 | [report](run-20/candidate/report.md) |
| run-21 | ui / defects | skill | 3/3 | 0 / 0 | 286 | 41 | [report](run-21/candidate/evidence/report.md) |
| run-22 | api / control | normal | 0/0 | 0 / 1 | 287 | 101 | [report](run-22/candidate/evidence/report.md) |
| run-23 | api / control | skill | 0/0 | 0 / 1 | 284 | 97 | [report](run-23/candidate/evidence/report.md) |
| run-24 | api / control | template | 0/0 | 0 / 1 | 272 | 110 | [report](run-24/candidate/report.md) |
