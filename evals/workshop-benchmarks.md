# Workshop-derived benchmarks and practical outcomes

The course repository contains 27 recorded findings: 24 Open and 3 Needs clarification at the reviewed revision. This is a useful source of realistic experiments, not a list of 27 mandatory bug discoveries. Existing passing regression tests do not close the findings. We reviewed the register and selected reports at `playwright-2026` commit `94dccc853d421746956ea2691ed5c4fcaa81bf95`; this work did not retest every historical defect on a live deployment.

[Machine-readable provenance](workshop-candidates.json) pins report URLs and hashes. Keep this evaluator material outside candidate contexts.

## Runnable course-derived cases

| Workshop finding | Cases | What the benchmark tests |
| --- | --- | --- |
| [BUG-03: misleading maximum-length error](https://github.com/slawekradzyminski/playwright-2026/blob/94dccc853d421746956ea2691ed5c4fcaa81bf95/docs/bugs/api/%5BL%5D%5BFA%5D%20BUG-03%20-%20Sign-in%20maximum-length%20error%20mentions%20minimum.md) | api-06 defect / api-07 control | Verify corrective feedback as well as status, use adjacent length boundaries, keep impact proportionate |
| [BUG-06: password byte limit contradicts contract](https://github.com/slawekradzyminski/playwright-2026/blob/94dccc853d421746956ea2691ed5c4fcaa81bf95/docs/bugs/api/%5BM%5D%5BFA%5D%20BUG-06%20-%20Sign-up%20password%20limit%20contradicts%20contract.md) | api-08 defect / api-09 control | Compare characters with UTF-8 bytes, verify successful and rejected registrations, preserve cleanup evidence |

The kept [course-app](course-app/) implements reduced, deterministic validation behavior derived from those reports. It is a synthetic Python fixture, **not the actual Spring backend or a reproduction of its password encoder**. It has no real login sessions, password storage or delivery effects. Sign-in covers validation/rejection only. Registration retains synthetic username/email records so accepted and rejected outcomes can be verified and cleaned up. Corrected controls exercise the same requirements without the selected defect.

These cases complement the existing cart sample and real-stack profiles. They do not replace source-backed exploration of the actual backend. The hosted product error-schema finding from the first pilot is already course [DOC-08](https://github.com/slawekradzyminski/playwright-2026/blob/94dccc853d421746956ea2691ed5c4fcaa81bf95/docs/bugs/api/%5BL%5D%5BD%5D%20DOC-08%20-%20Product%20error%20schemas%20misdescribe%20responses.md); it is a fresh reproduction of a known issue, not a new unique discovery.

## Cases for useful reporting

| Situation | Runnable cases | Successful agent behavior |
| --- | --- | --- |
| Tested behavior passes | api-02, ui-02, api-07, api-09 | Concrete executed checks, expected/actual evidence, no invented defect, clear coverage limits |
| Runtime works but source cannot be shared | api-04, ui-04; existing ui-03 includes a defect | Continue testing, report observed results, disclose absent source and build knowledge, name useful source inputs and how they could improve coverage |
| Environment cannot serve the application | api-05, ui-05 | Capture bounded availability failures, report functional testing blocked, preserve any source-only insights, identify what needs restoring |
| Source available but runtime intentionally absent | api-03 | Source-grounded conclusions with proposed runtime verification clearly unexecuted |

Unavailable cases use an evaluator-owned loopback gateway that consistently returns 503. This makes the situation reproducible without accidentally relying on an unused port or changing a real deployment. The candidate has normal application source and must assess the observed environment. Do not count an intentional outage as a missed product defect. Correctly handling it can pass the **agent usefulness assessment** while the **application's runtime assessment remains blocked**. An unexpected outage in a defect-discovery trial instead makes that trial inconclusive; it must not be scored as zero bug-finding ability.

The output contract now includes `runtime_status` and individual `checks` with `passed`, `failed`, `blocked` or `not-run`, plus source/runtime evidence basis. Old archived submissions remain valid under reporting version 1. These fields make results easier to review but do not prove them: graders check evidence, and reviewers inspect its meaning. A green subset is not a claim that the whole application is bug-free.

For missing source, a useful conclusion might say that tested Save/Cancel behavior passed, source was unavailable, and supplying the frontend/backend revision could help examine hidden branches, ownership and persistence. It should not promise that source will reveal more defects or stop useful browser work while waiting for it. Grade this substance, not exact wording.

## Strong candidates needing additional setup

- [BUG-11: Unicode QR corruption](https://github.com/slawekradzyminski/playwright-2026/blob/94dccc853d421746956ea2691ed5c4fcaa81bf95/docs/bugs/api/%5BM%5D%5BFA%5D%20BUG-11%20-%20QR%20codes%20silently%20replace%20Unicode%20characters.md) is especially valuable: a 200 response and valid PNG conceal an incorrect payload. Use a portable decoder, assert exact Unicode round-trip equality, and retain the ASCII control. A visual guess about a QR image cannot establish its decoded content. This case is catalogued, not yet runnable in this suite.
- [BUG-04: empty-email acceptance](https://github.com/slawekradzyminski/playwright-2026/blob/94dccc853d421746956ea2691ed5c4fcaa81bf95/docs/bugs/api/%5BM%5D%5BFA%5D%20BUG-04%20-%20Sign-up%20accepts%20empty%20email.md) needs a fresh isolated database. A separate occupied-empty-email fixture would test whether the agent recognizes a blocked reproduction precondition instead of incorrectly declaring a fix. Do not delete unrelated users to make the reproduction work.
- [BUG-10: order reopening](https://github.com/slawekradzyminski/playwright-2026/blob/94dccc853d421746956ea2691ed5c4fcaa81bf95/docs/bugs/api/%5BL%5D%5BFA%5D%20BUG-10%20-%20Order%20reopening%20and%20backward%20transition%20policy%20is%20unclear.md) and [BUG-12: streaming completion semantics](https://github.com/slawekradzyminski/playwright-2026/blob/94dccc853d421746956ea2691ed5c4fcaa81bf95/docs/bugs/api/%5BL%5D%5BFA%5D%20BUG-12%20-%20Tool%20chat%20completion%20marker%20semantics%20are%20unclear.md) are clarification cases. Preserve the real unresolved policy; reward a precise question backed by observations rather than inventing a transition matrix or completion guarantee.

The register also records a rejected traffic-page-size suspicion and intentional stock-protection 409 responses. Those can become positive controls once their specific request/state evidence is frozen. A clean case should have meaningful passing coverage, not merely an empty report.

## Review criteria

Use the [rubric](rubric.md), then record the expected useful outcome separately from numeric quality. For clean cases, require actual passing-check evidence. For unavailable cases, require honest blocking and an actionable next step. For missing-source cases, require productive runtime work plus a specific access limitation and useful source follow-up. For course defects, require the corresponding semantic failure and a neighboring passing contrast. Valid additional findings still deserve review; absence from the seed list is not a false-positive verdict.

Keep development cases separate from held-out effectiveness measurements. Freeze a new case before running it, record fixture and skill hashes, use fresh contexts, and never describe examples already included in skill guidance as unseen benchmarks.

The [completed practical validation](results/2026-09-12-usability.md) records the initial eight trials and two targeted correction reruns, including unsuccessful initial outcomes.
