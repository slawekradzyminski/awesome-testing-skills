# Dispatch Desk release assessment

**Recommendation: address UI-01 and UI-02 before releasing the customer journey.** The routine flow works, but service feedback can contradict persisted state, and a failed instruction request can strand the draft with Save disabled. Both findings were demonstrated through ordinary UI controls under explicitly controlled network conditions; neither was observed as a spontaneous loopback failure.

## Scope and environment

Assessed Alice's order selection, instruction editing, service selection, their backing API calls, desktop/narrow presentation, and selected keyboard interactions on 2026-09-12, approximately 11:16–11:20 UTC. Runtime: `http://127.0.0.1:58432/`. Browser: Headless Chromium 152.0.0.0 on macOS; CSS viewports 1280×720 and 375×812, device scale factor 1. No device emulation or general throttling. Only the named `journey-run-16` session was used.

Charter: establish successful persisted edits, then challenge asynchronous order/service transitions, rejection recovery, keyboard access, and customer data boundaries; stop within six minutes and the 120 API-request/80 browser-action caps. Administrative refunds/address changes, documentation-only issues, external services, production authentication, and real-device certification were excluded.

Requirements basis: [product brief](../app/requirements.md), especially “Browser experience” and service/note operation rules. Source revision/branch and backend deployed build identifier are unavailable. All three served frontend files match the supplied files byte-for-byte; hashes are in [build-match.json](build-match.json). This does not establish backend revision identity.

## Prioritized risk map

| Journey / risk | Evidence and impact | Protection / observation | Status and next action |
| --- | --- | --- | --- |
| Concurrent service choices | Both buttons remain enabled during requests; completion handler checks only order identity. Incorrect displayed delivery arrangement undermines customer decisions. | Delayed earlier response overwrote the newer visible choice; fresh GET disagreed. | **UI-01**, repair and test reordered completions. |
| Instruction transport failure | Save is disabled before fetch; no exception recovery. Customer cannot retry the draft. | Injected connection reset left Save disabled and stale service-success feedback. | **UI-02**, add recovery and retest. |
| Out-of-order order reads | A100 intentionally takes about 700 ms; old data could target another order. | Generation guard worked for A200 → A100 → A200; final selection/details remained A200. | Explored without defect in this sequence; retain regression. |
| Successful/rejected instructions | Persistence and draft loss matter more than toast appearance. | Valid A100 edit survived reload. LOCKER draft stayed editable with actionable 422 feedback; backing API rejection retained saved state. | Explored without defect in tested cases. |
| Keyboard/narrow layout | Both service choices and note controls must be reachable. | Tab order: order, note, Save, express, standard; all exposed visible focus. Enter activated express; Space activated standard. 375 px document width equaled viewport width. | No sampled barrier; keyboard text-entry/save sequence and assistive technology remain untested. |
| Customer boundaries / bulk backing call | Forbidden member could partially change permitted orders. | Anonymous list 401; foreign read/note write 403; mixed Alice/Bob service change 403 with both customers unchanged. | No defect in these probes; broader API administration outside this browser assessment. |

## UI-01 — Earlier service response overwrites the displayed latest choice

**Type:** FUI / NET. **Severity:** Medium. **Status:** Open. **Evidence:** runtime-confirmed with controlled response reordering, 1/1 experiment. Recommended release repair priority: first.

**Reproduction:** Load A200 and allow its details to settle. Intercept only `/api/services`, forwarding each request to the real server unchanged. Click **Use express delivery**; hold its successful response after the server has processed it. Click **Use standard delivery** and deliver that successful response. Then release the held express response. The reproducible interception and normal clicks are in [service-ordering.js](service-ordering.js).

**Actual:** The server processed express then standard (both HTTP 200). The UI first showed standard, then regressed to express with “Delivery service saved.” An independent GET immediately afterward returned `service: standard`. See [ordered request/response evidence](service-ordering-output.txt), [fresh persisted read](service-race-persisted.json), and [opened desktop screenshot](service-race-desktop.png).

**Expected:** Selected order, displayed details, and saved delivery arrangement should remain consistent, as required by the browser brief. An older completion must not replace the current authoritative result.

**Impact:** Customers can believe express is active when the order actually remains standard. This probe establishes incorrect display/feedback; it does **not** establish incorrect server ordering, a charge, or an actual delivery failure. Reloading/reselecting can recover authoritative details. Ordinary sequential keyboard changes were a contrasting successful case.

**Cause evidence:** [app.js](../app/static/app.js), lines 38–45: requests overlap; the completion guard checks only `id !== selected`; the service text is set from the request's captured service. No per-operation ordering/reconciliation protects the same order.

**Acceptance/retest:** Serialize conflicting changes or reconcile them with authoritative state so displayed service, latest accepted choice, and a fresh GET agree after all requests settle. Test both response orders and switching away/back while requests are pending. Verify no unintended writes to the other order. No fix or fixed-build retest was performed.

## UI-02 — Failed instruction request leaves Save disabled without recovery feedback

**Type:** FUI / NET / UX. **Severity:** Medium. **Status:** Open. **Evidence:** runtime-confirmed with an injected connection reset, 1/1 experiment. Recommended release repair priority: second.

**Reproduction:** On A100, first complete a service change so “Delivery service saved” is visible. Enter a valid instruction. Abort only its note POST with `connectionreset`, then remove the interceptor. All data entry and submission use normal controls; [network-failure.js](network-failure.js) records the setup.

**Actual:** After the request failed, the draft remained onscreen, Save stayed disabled, and feedback still said “Delivery service saved.” No actionable note failure or retry option appeared. After removing the route, a successful independent GET confirmed the old note (`Leave with reception`) remained persisted. See [failure/state/read evidence](network-failure-output.txt), [opened narrow screenshot](failed-save.png), and [console](console.txt). The console's connection-reset/fetch error was induced; its missing UI recovery is the defect. The earlier 422 console message was an expected server rejection, not another finding.

**Expected:** The customer should receive actionable failure feedback, retain the draft, and be able to retry once connectivity recovers. This follows the brief's rejected-edit recovery outcome, applied here to a transport failure rather than an HTTP validation response.

**Impact:** A transient connection failure prevents saving the current draft in place. Reloading or switching orders can re-enable controls but risks losing the unsaved text; copying the draft before reloading is a workaround. The old message describes a service save, not a falsely observed successful note POST.

**Cause evidence:** [app.js](../app/static/app.js), lines 23–36: fetch/JSON exceptions bypass every path that re-enables Save. There is no catch/finally recovery. The HTTP 422 branch did recover normally in the contrasting test.

**Acceptance/retest:** Handle transport/response parsing failures, replace stale feedback with an actionable error, preserve the draft, and restore retry capability for the correct active order. Test retry success and failure after navigation without enabling a Save against unsettled order details. Read-after-write must confirm the eventual result. No fix or fixed-build retest was performed.

## Passing evidence and limits

- Four supplied domain tests passed: [captured test output](unit-tests.txt). They cover routine refund/address/service success and LOCKER status only; they do not exercise UI code, asynchronous ordering, keyboard use, or persisted rejection invariants.
- [Clean browser journey output](core-clean.txt) records valid note persistence after reload, actionable LOCKER rejection with retained draft, and the natural delayed-read sequence. [Rejection screenshot](rejected-desktop.png) was opened and inspected.
- [Backing API checks](backing-checks.json) capture ownership rejection, mixed-owner service atomicity, blank/LOCKER note rejection, and state comparisons. These are selected browser-backing checks, not a comprehensive administrative API certification.
- [Keyboard output](keyboard-output.txt), [express focus screenshot](keyboard-express.png), and [narrow screenshot](narrow.png) were reviewed. Controls wrap without horizontal overflow at 375 px, and service buttons visibly indicate keyboard focus. Vertical scrolling is required and is not itself a defect.
- No screen reader, browser-engine matrix, intermediate width, zoom, real mobile keyboard, long-text reflow, performance SLA, request-arrival reordering, or save/navigation/save timing matrix was tested. Fetch/JSON failure handling for order reads and service writes remains a source-evidenced residual risk, not an additional confirmed finding.

An initial evidence listener used an unavailable `URL` global and produced tool errors; it did not stop browser actions. That run and the next run were not used as clean happy-path proof. The owned session was closed/reopened, A200's temporary note restored, and the journey rerun successfully from A100. [core-output.txt](core-output.txt) retains the intermediate evidence for transparency; [core-clean.txt](core-clean.txt) is the final verified run.

## Closeout and regression handoff

All interceptors were removed. The owned browser session was closed. Alice's final orders exactly match the saved baseline, including notes, services, refunded amounts, addresses and version counters: [baseline](baseline-alice.json), [final](final-alice.json). Bob remained unchanged in the backing checks. No refunds or address/version changes were made, and no source, supplied test, requirement, or guidance files were edited.

Add a small regression set around: (1) reordered service completions with authoritative state comparison; (2) failed note POST followed by successful retry with retained draft; (3) A200 → A100 → A200 with delayed A100 and a save targeting only A200; (4) rejected LOCKER edit preserving both draft and persisted note, followed by correction/reload; and (5) keyboard-only note editing and both service choices at desktop and narrow widths. Keep forbidden side effects on other orders explicit in assertions.
