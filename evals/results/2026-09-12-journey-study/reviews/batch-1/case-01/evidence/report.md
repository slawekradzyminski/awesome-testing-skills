# Dispatch Desk release assessment

**Recommendation: hold release until the overlapping service-save defect is fixed and verified.** The ordinary customer journey and tested administrative safeguards pass, but a confirmed race can show a delivery service that differs from the saved order. Two additional browser recovery issues merit repair before release.

Assessment performed on 2026-09-12 against only `http://127.0.0.1:58780`, using the supplied requirements, source, four existing tests, HTTP probes, and Chromium through the assigned Playwright CLI session. No supplied files were changed. Documentation defects and production hardening were excluded.

## Confirmed findings

### 1. High — overlapping service saves display stale success

**Reproduce:** Start with A200 on standard delivery. Click express; hold its real HTTP response after the server processes it. Click standard and allow that response through. Then release the express response. Both calls return 200. This uses response scheduling against the real server, with no fabricated response bodies.

**Expected:** The displayed service and success feedback agree with the persisted, latest service choice.

**Observed:** The server processes express, then standard. The page subsequently displays `express` and `Delivery service saved`. Reloading A200 displays `standard`. This was reproduced twice, including a second run that explicitly synchronized response completion.

**Impact:** Customers can leave the desk believing an incorrect delivery service is active. This is a correctness issue, independent of the intentional lookup latency.

**Cause and repair:** `app/static/app.js:38–45` allows simultaneous service writes and guards responses only by order ID. Serialize service changes or disable both service buttons during a write; ensure a response cannot overwrite a newer result. Merely ignoring older responses is insufficient if writes can also reach the server out of order. Reconcile displayed state with the final committed choice.

**Verification gate:** A browser regression should exercise reordered service responses and rapid alternating choices, then compare displayed state with a fresh read. Include switching away and back while a save is pending.

Evidence: [synchronized reproduction and actual server responses](service-race-confirmed.txt), [reproduction script](service_race_confirm.js), [screenshot](service-race.png).

### 2. Medium — instructions typed during a lookup are silently discarded

**Reproduce:** With A200 loaded, select A100 and immediately type `New draft entered while loading` into the instruction field during its normal approximately 700 ms lookup.

**Expected:** The editor is unavailable until the selected order loads, or the new draft is preserved without being confused with the previous order.

**Observed:** The selector shows A100 while the previous A200 details and an editable instruction field remain visible. Typing succeeds, but lookup completion replaces the draft with A100's saved `Leave with reception` without feedback. Save and service buttons are disabled during loading; the textarea is not.

**Impact:** Ordinary typing during the known loading interval loses customer work. No wrong-order write was observed.

**Cause and repair:** `app/static/app.js:9` disables only buttons; line 17 unconditionally replaces the textarea value. Disable or make the editor read-only during lookup, and clearly associate loading details with the selected order. If editing during loading is intentional, maintain drafts per order and protect them from lookup completion.

**Verification gate:** Switch orders, attempt keyboard editing before completion, and verify that the interface either prevents editing or preserves the correct draft.

Evidence: `draftDuringLookup` and `draftAfterLookup` in [browser risk results](browser-risks-results.txt); [script](browser_risks.js).

### 3. Medium — interrupted instruction save leaves no feedback or retry

**Reproduce:** Load A100, enter a draft, abort the next note POST at the browser network layer, and click Save instruction.

**Expected:** Actionable connection-failure feedback, preserved draft, and an available retry once the failure is known.

**Observed:** An uncaught `Failed to fetch` error occurs. Feedback stays empty and Save instruction remains disabled. The draft remains in the field, but reloading to recover loses it. This is an injected transport failure; the real server's 422 rejection path works correctly.

**Impact:** A transient request failure leaves customers unable to retry in place. This is a resilience finding beyond the explicitly specified locker-rejection case.

**Cause and repair:** `app/static/app.js:23–36` has no exception handling/finally around fetch and JSON parsing. Handle failure with useful feedback and safely restore controls for the active order while preserving the draft. Apply the same recovery design to lookup and service requests, which also lack exception handling; those transport-failure paths were not separately reproduced.

**Verification gate:** Abort a save, confirm error feedback and draft retention, restore connectivity, and save successfully without reloading. Test lookup/service recovery separately.

Evidence: `failedSave`, `errors`, and `recoveredByReload` in [browser risk results](browser-risks-results.txt); [screenshot](network-failure.png).

## Passing evidence

- All four supplied domain tests passed: partial refund, address save, bulk service, and locker-note rejection. [Output](existing-tests.txt).
- 47 direct API requests produced expected statuses, with state assertions and recorded responses. Covered Alice/Bob order visibility, anonymous rejection, foreign-order reads and refund/address/note writes, missing orders, refund type validation and cumulative limit, stale address protection, bulk service atomicity for forbidden and missing IDs, supported service changes, invalid notes, locker rejection, and malformed JSON/non-object bodies. Rejected mutations preserved tested state. [Results](api-results.json), [script](api_checks.py).
- Browser locker rejection showed actionable feedback, retained `LOCKER: 1`, and did not claim success. Correcting and saving an instruction survived reload.
- The intentional A100 delay followed by a faster A200 lookup settled on consistent A200 selection/details. Saving and reloading confirmed the A200 target. Buttons were disabled during lookup.
- Keyboard Tab reached instruction editing, Save, express, and standard in sequence, each with a visible 3 px focus outline. Enter activated both service choices successfully.
- At 320 px width, all controls stayed within the viewport and document width remained 320 px. Visual inspection found readable content and usable controls; scrolling was required normally. Desktop browser flows also worked. [Browser results](browser-results.txt), [script](browser_checks.js), [narrow screenshot](narrow.png).

## Limits and handoff

This is a focused release assessment, not exhaustive certification. No additional browsers, real devices, screen reader testing, concurrent administrative callers, or full boundary-value matrix were exercised. Existing tests alone do not cover browser sequencing or transport recovery. Controlled response delay establishes the service race deterministically; its frequency on a real network was not measured.

After repairs, run targeted browser regressions for the three findings and the already passing instruction rejection/persistence and order-switch journey. Retain the API evidence for unchanged administrative code; broaden API checks if those surfaces change.

Reversible fixture changes were restored and verified by final HTTP reads: both Alice notes, both service choices, and A200's original address are back to their starting values; Bob is unchanged. **Owner reset is needed for A100's cumulative refund of 2 cents and A200's address version, which advanced from 1 to 3.** No reset route was used. [Final Alice state](final-alice.json), [final Bob state](final-bob.json).

The only created browser session, `journey-run-18`, was closed. Approximately 75 API attempts were made, including the intentionally aborted save, within the 120-request limit. Browser interactions stayed below 80. Evidence scripts mutate disposable fixtures and some assume the documented starting state; reset before rerunning the API script.
