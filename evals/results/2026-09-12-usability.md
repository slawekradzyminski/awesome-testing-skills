# Practical benchmark extension — September 12, 2026

The suite now has **14 runnable cases**, with eight additions focused on useful testing outcomes: course-derived defects, corrected controls, an unavailable environment, and productive testing without source. Ten fresh with-skill trials exercised the eight additions and two targeted corrections. Six initial trials met the expected useful outcome; two exposed weaknesses. Both targeted revised-skill runs met their specific outcome. The original failures remain in the archive.

This is development validation, not a new with/without effectiveness comparison. The earlier [16-run paired assessment](2026-09-12-retry.md) remains separate: both conditions found the same seeded bugs, with stronger artifact scores in the skill condition on that small sample.

## Course material used

Reviewed the `playwright-2026` bug register and selected reports at commit `94dccc853d421746956ea2691ed5c4fcaa81bf95`. The register contains 27 findings, including three unresolved policy questions. [Curation notes](../workshop-benchmarks.md) and [pinned provenance](../workshop-candidates.json) explain the selection.

Two recorded problems now have deterministic reduced fixtures, each paired with a corrected control:

- **BUG-03:** overlong sign-in fields are rejected, but the message incorrectly tells the user about the minimum length. The evaluation checks message meaning, adjacent boundaries and proportionate impact, rather than only HTTP 400.
- **BUG-06:** a password satisfies the documented character range but exceeds an undocumented 72-byte limit. The evaluation uses ASCII/Unicode contrasts, accepted neighbors, persistence or absence checks, and cleanup.

The retained Python validation fixture is derived from those behaviors; it does not reproduce the full Spring application, Java validation implementation or password encoder. Its string lengths follow Python Unicode code-point counting. Actual backend/profile testing remains a separate source-backed real-stack activity.

The hosted product-schema mismatch from the prior pilot is course **DOC-08**, so it is recorded as a fresh reproduction of a known issue. QR Unicode corruption, empty-email reproduction masked by an existing record, and ambiguous order/streaming policies are curated next candidates. They need suitable decoding, isolated state or an explicitly unresolved policy oracle; they are not counted as runnable additions.

## Observed useful outcomes

| Case | Initial outcome | Evidence and disposition |
| --- | --- | --- |
| api-04: clean API without source | Met | 38 requests; eight passing checks, no invented defects; source/build limits and relevant parser/update-code follow-up; owner reset needed after own zero-removal probe |
| ui-04: clean UI without source | Partial | Real browser/API testing and honest limits, but omitted a concrete explanation of what source could add |
| api-05: unavailable API | Not met | Correctly reported 503 blockage but the probe batch sent 35 requests despite a six-request availability limit |
| ui-05: unavailable UI | Met | Four availability requests; functional UI tests blocked; two local domain tests correctly identified as source-level evidence |
| api-06: course message defect | Met | Confirmed incorrect upper-bound guidance with accepted-length and short-input contrasts; limited impact stated |
| api-07: corrected message control | Met | 38 functional requests passed status and message checks; no invented authentication defect |
| api-08: course password defect | Met | Reproduced 73-character ASCII rejection twice, contrasted 72-byte success and multibyte inputs; cleaned all seven registrations with absence checks |
| api-09: corrected password control | Met | 27 checks passed; 255 four-byte Unicode characters accepted; correctly avoided declaring the compatible byte guard a bug |

Counts refer to actual evidence; the archive also separates `/api` requests from health/static requests. Testing a clean case succeeds through concrete passing evidence and bounded conclusions. An empty findings array alone is insufficient. Unavailable cases can pass the **agent-handling assessment** while the **application's functional assessment stays blocked**. Missing source should limit claims and inform a useful next step, not stop available runtime testing.

## Corrections and targeted reruns

**Stop on unavailable application behavior.** The original api-05 agent retained and disclosed its mistake: the script continued its planned request matrix after repeated 503s and eventually failed while trying to read a cart field from an error response. The API skill now instructs the agent to check a representative read before a batch, stop scripts on unavailable-service responses, retain evidence and continue useful source analysis. In the [fresh targeted rerun](2026-09-12-usability/api-05-revised/report.md), the batch stopped at its first request; one health check followed. The server audit contains **two reads and zero mutations**. Functional testing remained explicitly blocked.

**Explain what missing source could improve.** The initial ui-04 report disclosed missing source but did not give the requested practical handoff. Both report guides now call for the relevant source/revision and a concrete coverage benefit without promising more bugs or repeating a declined request. The [fresh UI rerun](2026-09-12-usability/ui-04-revised/report.md) completed browser/API checks and named frontend edit/submit handlers, backend validation/ownership/persistence and deployed revision as useful follow-up inputs. It also documented network evidence and the limits of its Cancel persistence check. The targeted handoff requirement was met.

These are observed corrections on the same development cases. One successful rerun is not a reliability estimate, and unrelated differences in browser evidence or coverage cannot be attributed to the wording change.

## Validation and limits

The [machine-readable result](2026-09-12-usability.json) links all ten original submissions, reports, audits, source/skill hashes and owner reviews in the [archive](2026-09-12-usability/README.md). Nine artifact-integrity grades passed; the original excessive-retry run correctly failed. A separate usefulness review identified the missing-source handoff even though that report passed structural checks. Neither unsuccessful initial outcome was erased or relabeled as successful.

Fourteen harness tests passed, including live mutation/control behavior, honest blocked reports, rejection of fabricated functional passes, missing-source isolation, evidence-path checks and existing source snapshot safeguards. Both skill frontmatter validators passed. The owner reviewed all reports and structured submissions, decisive evidence and representative screenshots. All evaluation-owned servers and reported owned browser sessions were closed. Course source checkouts were not edited.

There was one initial trial per new case, with no new baseline arm and no condition-blind reviewer for this development pass. Exact model version, full action traces, token costs and automatically enforced wall-clock budgets were unavailable. Tool choices varied. Run directories and task instructions provide context separation, not operating-system isolation. These results support the usefulness of the new cases and the two narrow corrections; they do not establish general testing superiority.
