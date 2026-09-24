# Three-condition Dispatch Desk assessment — September 12, 2026

**This stronger screening study still does not demonstrate a substantial effectiveness advantage for the full skills.** A normal request, a reporting template and the full skill each established every seeded fault with actionable evidence. Severity calibration differed modestly. Full-skill runs used fewer API requests, took longer and generated more model output.

All **24 candidate runs** and **six artifact-review sessions** completed. The [machine-readable results](2026-09-12-journey-study.json) retain per-run scores, raw and adjudicated summaries, resource use and review reasons. The [evidence archive](2026-09-12-journey-study/README.md) links every report, runtime audit, runner trace, reviewed skill snapshot and fixture check. These results are separate from the original pilot and 18-case harness.

## What changed from the first pilot

The new self-authored Dispatch Desk application offers administrative API operations and a customer browser journey. Its defective API variant contains cumulative over-refunding, stale address overwrites and partial changes from rejected batches. Its defective UI variant contains stale order details, false success on rejected instructions and an express-service control inaccessible through ordinary keyboard navigation. Matching variants remove those seeds.

Candidates received broad release-readiness tasks, source, existing tests, business requirements and their own loopback instance. The normal condition received a minimal deliverable location instead of the previous detailed reporting contract. The template condition additionally received a compact report template. The skill condition received the complete frozen API or UI skill, including its reporting references, and explicit invocation. This tests the full package against a small output template, not a precise word-for-word ablation.

Four surface/variant cells × three conditions × two fresh repetitions produced 24 runs. Model identifier and effort were fixed to **gpt-6-astra / high**, using Codex CLI **0.153.4** and Playwright CLI **0.1.19**. The preflight confirmed that only the shared Playwright helper remained in the available-skill catalog; the testing skill was supplied only to its assigned condition. User configuration and AGENTS intake were disabled equally through per-process overrides. No permanent user settings changed.

The [protocol](2026-09-12-journey-study/protocol.md), cases, skills, template and schedule were frozen before candidate execution. Six minutes included reading and reporting, with limits of 120 API requests and 80 browser actions. Up to three isolated candidates ran concurrently. All candidate source/skill preservation checks passed, frozen inputs and controller hashes matched afterward, and every candidate completed within the recorded six-minute and API-request limits. Exact complete browser-action counts were not independently reconstructed.

## Results

There are twelve seeded opportunities per condition: three API and three UI mechanisms, each encountered twice. Repeated observations of the same mechanism are not independent new bug types.

| Measure | Normal request | Report template | Full skill |
| --- | ---: | ---: | ---: |
| Candidate runs | 8 | 8 | 8 |
| Seeded faults identified | 12 / 12 | 12 / 12 | 12 / 12 |
| Seeded findings with actionable evidence | 12 / 12 | 12 / 12 | 12 / 12 |
| Triage points for those seeded findings | 32 / 36 | 35 / 36 | 34 / 36 |
| Additional valid finding instances | 5 | 3 | 4 |
| Unresolved additional claims | 1 | 1 | 1 |
| Adjudicated unsupported confirmed claims | 0 | 0 | 0 |
| API requests across eight runs | 666 | 669 | 536 |
| Median elapsed seconds per run | 249.78 | 267.58 | 285.25 |
| Output tokens across eight runs | 54,611 | 58,310 | 62,468 |

Triage awarded one point each for concrete impact, defensible severity and testable acceptance/retest criteria. The differences above came from severity judgments: several reports called false instruction-save feedback High without establishing harm beyond the rubric's Medium reference; normal API reports also overstated the failed-batch service change. The full skill did not eliminate severity inflation. These small subjective differences do not establish a reliable ranking.

Across all eligible seeded and additional findings, triage totals were **47/51**, **44/45** and **46/48** respectively. The denominators differ because additional discoveries differ. All conditions received **16/16** on the coarse coverage/handoff dimension: reports retained executed passing observations and meaningful limits. That dimension reached a ceiling and does not establish equivalent exhaustive coverage.

Full-skill runs made about 20% fewer API requests than the other conditions, while their median session took about 14% longer than normal-request sessions. Fewer calls can reflect different coverage choices; it is not automatically greater efficiency. Some UI runs exercised refund and address administration beyond the requested browser journey, consuming budget and leaving additional fixture counters for owner reset. That scope drift occurred across conditions, including skill runs.

Token totals are recorded by the CLI. Cumulative input includes repeatedly submitted context and cached input; it is not unique context size or a monetary bill. No price or general cost-effectiveness claim is made. Shared-host contention and model latency also limit speed comparisons.

## Useful discoveries in the corrected variants

The variants with seeds removed still contained real additional problems. Across the six UI control runs, agents reported twelve valid finding instances representing **three distinct mechanisms**:

- A delayed earlier service-save response can leave the UI showing express while a fresh read and reload show standard. All three conditions found it in both repetitions. Responses came from real server writes; tests controlled only their delivery order.
- The enabled instruction editor can accept typing while an order lookup is pending, then discard that draft when the lookup completes. Both normal-request repetitions found it. The reproduction used the fixture's ordinary documented latency.
- An aborted instruction-save request can leave Save disabled without useful recovery feedback; a reload restores the control while discarding the draft. Both skill repetitions, one template repetition and one normal repetition found it. The connection failure was explicitly injected.

The author reproduced all three on fresh corrected instances without changing application source and opened the resulting screenshots. They are conditional client-state/recovery findings, not evidence of spontaneous network failures or measured production frequency. The loading-draft and transport-recovery expectations interpret the brief's usable-editing/recovery intent; that judgment and the evidence are retained for review.

Normal requests found the broadest additional set in this small sample. Additional findings did not increase the seeded-recall denominator. Their presence is also why a corrected control must not be assumed to be a flawless application.

## An ambiguous boundary stayed unresolved

All three second-repetition API controls found that surrounding whitespace permits saved notes longer than 160 total characters. The requests and persisted values are established. The brief, however, specifies “1–160 nonblank characters” without defining whether the bound applies before or after trimming, and no further impairment was demonstrated.

One reviewer marked this unresolved; two accepted it under a literal stored-length interpretation. The final author adjudication applies the same requirement-uncertainty rule to all three conditions: retain the observation as a product clarification, with no confirmed discovery credit and no disproved-finding penalty. [Raw reviews](2026-09-12-journey-study/reviews/) and [explicit adjudications](2026-09-12-journey-study/owner-adjudications.json) remain available. This is a useful example of why AI artifact grading still needs consistency review.

## Review and integrity limits

Six fresh AI review sessions each assessed four reports against the frozen outcome criteria, inspecting decisive artifacts, source, supplied runtime audits and relevant screenshots. Condition labels and their mapping were withheld from the assigned directories. Report wording sometimes reveals guidance use, so this is **partially masked artifact review**, not guaranteed blinding or an independent research replication. The study author authored the fixture and knew the seeds, checked review consistency, and performed the separately identified additional reproductions.

All primary report links resolve. Incidental browser logs are absent from the curated archive where candidates did not preserve them, and some cleanup statements lack a separate candidate closure artifact. The controller nevertheless closed its owned fixtures and named browser sessions. The original root-only report detector missed reports saved under `evidence/`; the shared prompt permits that interpretation, so the collector limitation does not count against testing quality.

Candidate/controller separation was a context boundary, not an operating-system sandbox. Per-run source hashes were preserved, and a scan of executed commands found no explicit references to the evaluator paths checked. That scan is not proof against all possible access. The study records the requested model identifier and installed tools, not an unavailable immutable backend model revision.

## Decision

The new study is more informative, but its discovery result remains a tie. With this small application's source and business context, the ordinary agent already finds and verifies the seeded faults. A reporting template provides comparable outcomes with less instruction material; the full skill has no demonstrated additional effectiveness benefit here.

The skills can still be published as inspectable, adaptable workflows, with these results visible. This evidence supports neither a claim that they generally find more bugs nor that every project can dispense with them. One self-authored application, six seeded mechanisms, two repetitions and a coarse rubric remain a narrow test. Future studies should use materially different, independently curated project tasks and freeze the next comparison before tuning. These results should not be extended selectively until a preferred winner appears.
