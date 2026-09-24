# Dispatch Desk release assessment

**Recommendation: hold release until UI-01 and UI-02 are fixed and retested, or explicitly accept these conditional risks.** The normal customer journey and sampled administrative safeguards passed. Two Medium defects were demonstrated using controlled network conditions: service feedback can disagree with persisted state, and a failed instruction request leaves saving unavailable without recovery feedback. Neither condition occurred spontaneously on the local network; their production frequency is unknown.

Assessment performed 2026-09-12, approximately 10:59–11:04 UTC, against **http://127.0.0.1:56450**. Scope: Alice's customer browser journey and the documented administrative API operations; disposable Alice/Bob fixtures. Documentation-only defects and production authentication/security were excluded. Work stayed within the six-minute, 120 API-request and 80 browser-action limits. No supplied source, tests, requirements or guidance were edited.

Browser: Chromium 152.0.7977.84, dedicated `journey-run-05` session, desktop 1280×720 and narrow 375×812 CSS pixels; default desktop browser behavior, no device emulation or intentional zoom. Normal network conditions except the explicitly labeled response-ordering and aborted-request probes. Source revision/build identifiers were not supplied. [Source fingerprints](source-fingerprints.txt) identify assessed files; [matching SHA-256 hashes](source-match.txt) establish that the served JavaScript matched the supplied JavaScript. Backend build identity remains unknown; its observed behavior was checked independently.

## Risk map and coverage

Charter: establish that customers can select the intended order, save instructions and service choices, recover from rejection, and use ordinary keyboard navigation; challenge persistence, asynchronous transitions and API data boundaries. Stop after discriminating probes, cleanup and reporting within the time budget.

| Journey / risk | Evidence and priority | Experiment / result | Status / next action |
| --- | --- | --- | --- |
| Order selection with late lookup | High priority: A100 has intentional latency; saves must target displayed order. Source uses a generation token. | A200 → A100 → A200; A200 response arrived before A100. Final selection, heading and note remained A200; save posted only to A200. Independent later read confirmed A200's changed note and unchanged A100. | No defect observed in this sequence. Preserve as a regression. |
| Instruction persistence and rejection | High priority: misleading success or lost drafts affect delivery. Existing test checks only rejection status. | Valid note survived reload. `LOCKER: 12` returned 422, preserved draft, showed actionable error and retained prior persisted note. Keyboard save succeeded. | Normal paths passed; transport recovery failed, UI-02. |
| Service selection and response ordering | High priority: displayed service informs delivery expectations. Service handler lacks the lookup generation protection. | Keyboard express/standard worked normally. Holding the first real response until the second completed produced stale service display twice. | UI-01; repair asynchronous save coordination. |
| Ownership and anonymous access | High priority: cross-customer changes forbidden. | Alice/Bob lists isolated; anonymous list and write returned 401; Alice read/note/address/refund against B100 returned 403. Bob's complete record unchanged. | No defect observed in sampled directions. Reverse Bob→Alice mutations not exercised. |
| Bulk service atomicity | High priority: partial changes forbidden. | `[A100,B100]` returned 403 and `[A100,MISSING]` returned 404. Complete Alice list stayed unchanged after each; Bob stayed unchanged. | No defect observed; add negative integration coverage. |
| Refund and stale address edits | High priority: financial and concurrent-edit integrity. | A200: 1000 accepted, 5001 rejected with 409, 5000 accepted, then 1 rejected; reads confirmed 1000 then 6000 totals. Stale address version returned 409 and preserved newer address. | No defect observed; irreversible fixture changes disclosed below. |
| Input validation | Medium priority: malformed values can bypass business rules. | Refund bool/zero/negative/fraction/string, non-object note body, blank and overlong note rejected with 400. | Sample passed; exhaustive boundary/type combinations not covered. |
| Keyboard / responsive layout | High priority: explicitly supported interaction modes. | Tab reached order, note, save, express and standard in order; 3px visible focus recorded. Enter activated express and save; Space activated standard. At 375px, document scroll width equaled client width; controls wrapped and remained readable. | No barrier observed in sampled controls/layouts. Full accessibility certification not performed. |

[API evidence](api-results.json) contains 34 requests and assertions; [API probe](api_probe.py) is an assessment helper, **not a safe reset script**: rerunning it would mutate refunds again. [Existing test results](unit-tests.txt): all four supplied domain tests passed. These tests were inspected and executed; they do not cover browser rendering, asynchronous saves, HTTP ownership, cumulative refunds, stale conflicts or bulk rollback.

## UI-01 — Service success display can contradict the saved service

**Type:** FUI / NET. **Severity:** Medium. **Status:** Open. **Evidence:** runtime-confirmed under injected response ordering, reproduced 2/2 times. Observed at 375×812 with Alice/A100 initially standard.

1. Intercept `/api/services` only to hold the response for express **after forwarding the request to the real server**.
2. Click **Use express delivery**, then **Use standard delivery** while the express response is held. Both controls are normally enabled; no forced click or DOM edit is used.
3. Let the standard response complete, then release the original express response unchanged.
4. Observe the service and success feedback, read A100 through the API, then reload.

**Actual:** both POSTs returned 200. The server stored standard, but the page ended with **express** and **Delivery service saved**. Reload showed standard. [First reproduction](service-race.txt), [repeat](service-race-repeat.txt), [reproduction script](service-race.js), and [opened screenshot](service-race.png) preserve the response bodies, order and visual result.

**Expected / basis:** the browser brief requires successful service edits to survive reload and a consistent customer journey. Current service display and success feedback must represent the actual persisted outcome after pending saves settle.

**Impact:** customers can leave believing they have express delivery when the saved arrangement is standard. A reload reveals the actual value but the screen gives no reason to reload. This is a material core-flow correctness issue; no charge or fulfillment consequence was tested. The timing was deliberately controlled, so natural occurrence rate is unmeasured. Ordinary sequential keyboard choices provided the passing contrast.

**Code investigation:** `app/static/app.js:38–45` permits overlapping writes and updates the display from each request's captured `service`; it checks only order ID. Late responses for the same order can overwrite newer feedback. The order-lookup generation guard does not protect these saves.

**Acceptance / retest:** coordinate service writes so an older completion cannot overwrite newer intent, and reconcile the display with persisted state. Test both response orders, rapid opposite choices, navigation during save, and a fresh read/reload. If requests can reach the server in a different order, a client display guard alone is insufficient. Add a focused browser regression asserting the final displayed **and persisted** value. No fix or post-fix retest performed.

## UI-02 — Failed instruction request disables saving without feedback

**Type:** FUI / NET, secondary UX. **Severity:** Medium. **Status:** Open. **Evidence:** runtime-confirmed with one injected connection failure; recovery state checked separately.

Preconditions: Alice/A100 loaded normally, saved note `Leave with reception`, 375×812 viewport.

1. Abort the next `/api/orders/A100/note` request to simulate connection failure before it reaches the server.
2. Enter `Assessment network draft` and click **Save instruction** normally.
3. Remove interception and inspect the screen after the failed request has settled; then reload.

**Actual:** Save remained disabled, the draft remained visible, feedback was empty and an unhandled `TypeError: Failed to fetch` occurred. Removing interception did not restore saving. API read confirmed no note mutation. Reload re-enabled Save but replaced the draft with the old saved note. [Failure evidence](network-failure.txt), [recovery and independent state read](network-recovery.txt), [opened screenshot](network-failure.png), [console history](console-history.txt).

**Expected / basis:** the browser requirements establish actionable failure feedback and preservation of instructions for correction. Transport failures should likewise leave a recoverable customer journey; this extends that stated recovery goal to a failed connection rather than a business-rule 422 response.

**Impact:** users experiencing a transient connection failure cannot retry in place and may lose entered text on reload. Manually copying the draft before reloading is a workaround. The server was not naturally unavailable; the failure was injected, and this report does not allege a server reliability problem. The successful save and actionable 422 rejection are passing contrasts.

**Code investigation:** `app/static/app.js:23–36` disables Save before awaiting fetch and lacks exception handling/finally cleanup. The observed thrown fetch skips all re-enabling and feedback paths.

**Acceptance / retest:** catch transport/response parsing failures, preserve the draft, show actionable retry feedback and restore the appropriate controls after settlement. Retest retry after connectivity returns and navigation during a pending save; assert no false success or unintended duplicate save. No fix or post-fix retest performed.

## Evidence, limits and closeout

Screenshots were captured **and opened**: [desktop rejection](rejected-desktop.png), [keyboard express focus](keyboard-express.png), [narrow successful save](narrow.png), and both finding screenshots above. Desktop service controls are below the initial viewport but visible on ordinary scrolling; this was not classified as clipping. No precise contrast-standard compliance claim is made.

[Order-switch evidence](order-switch.txt), [note evidence](browser-note.txt), [keyboard evidence](keyboard.txt), [narrow keyboard/reflow evidence](narrow-keyboard.txt), and [browser request history](browser-requests-final.txt) support the journey results. Console history contains the expected 422 resource error and the deliberately injected request failure; neither is counted as a separate defect. The final console command was empty after reload and does not erase the earlier captured error.

Remaining priorities after the two repairs: exercise service request arrival order as well as response order, save/navigation/reselection combinations, initial-load failure and retry, and narrow-layout keyboard operation across more widths. No Safari/Firefox, real mobile keyboard, screen reader, zoom matrix, formal accessibility audit, broad load/performance test, or exhaustive malformed HTTP testing was performed. Intentional A100 latency is not a defect. Observations do not establish an SLA or exhaustive release coverage.

All interceptors were removed. Only the created `journey-run-05` browser session was closed. [Final fixture reads](final-fixtures.json) confirm addresses, notes and services restored for Alice and Bob. **A200 remains refunded by 6000 cents and its address version is now 3 instead of 1**; these authorized irreversible refund/version changes require the fixture owner's reset. A100 and B100 retain their original refund/version values. No external services, issue filing, delegation or product fixes were used.
