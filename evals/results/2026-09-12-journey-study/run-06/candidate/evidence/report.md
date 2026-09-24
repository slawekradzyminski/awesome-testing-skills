# Dispatch Desk release assessment

## Session

**Recommendation: hold release until DD-01 is corrected; resolve DD-02 or explicitly accept its recovery limitation.** Routine customer flows and the administrative integrity checks passed, but overlapping service saves can display a service different from the stored order. A transport failure also strands the instruction editor without feedback.

Assessed the supplied `app/` source, four existing domain tests, and `app/requirements.md` against **http://127.0.0.1:56486**, on 12 September 2026, approximately 11:00–11:03 UTC. Used the isolated Chromium session `journey-run-06`, desktop and a 320px viewport. No supplied application, tests, requirements, or guidance were changed. No external service or other runtime was used.

The assessment prioritized order targeting, persistence, rejected-save recovery, keyboard access, money limits, ownership, optimistic concurrency, and atomic bulk changes. Network scenarios used browser interception against the assigned runtime only: DD-01 delayed a real successful response without changing its contents; DD-02 aborted one request. Their production frequency was not measured. This is a bounded release assessment, not full device/browser or accessibility certification.

## Findings

### DD-01 — Older service response overwrites the displayed latest service

- **Type / evidence / status:** Functional concurrency defect; confirmed with real backing API responses and controlled response delay; open.
- **Severity: Medium.** Customers making successive service choices can receive success feedback alongside an incorrect service display. This can mislead delivery planning; the demonstrated server value remains the last processed choice. No financial loss or cross-order write was demonstrated.
- **Preconditions:** A200 selected, standard delivery initially saved. Both service buttons remain usable during a save.
- **Minimal reproduction:** Delay delivery of the response to an express service POST by one second, after the server has processed it. Click **Use express delivery**, then approximately 100ms later **Use standard delivery**. Let the standard response arrive first, then the older express response. Read `/api/orders/A200`, then reload and select A200.
- **Expected / basis:** The displayed service and success feedback should represent the saved order and latest completed customer choice. This follows the product brief's consistent-details and persistent-edit requirements; it does not require faster order lookups.
- **Actual:** Both POSTs returned 200. The server processed express then standard; responses reached the UI standard then express. The screen ended on **express**, while a fresh API read returned **standard**. Reload displayed standard. See [captured response sequence and values](service-race-results.txt), [screenshot](service-race.png), and [reproduction script](service_race.js).
- **Likely cause / owner:** Frontend, `app/static/app.js:38–45`: `setService` checks only order identity, accepts overlapping writes, and renders each request's service as its response arrives.
- **Workaround:** Wait for each service save to complete before choosing again; reload to confirm the stored value after overlapping changes.
- **Acceptance criteria:** With either response order, successive express/standard choices leave the UI consistent with the persisted order and defined latest-choice behavior. Serialize service mutations or otherwise coordinate writes and responses; a response token alone does not control server processing order. Include switching away and back while a mutation is pending in regression coverage.
- **Retest:** Reproduced on the supplied build; no fix supplied or retested.

### DD-02 — Failed instruction request leaves Save disabled without feedback

- **Type / evidence / status:** Functional recovery defect; confirmed under an injected transport failure; open.
- **Severity: Medium.** A transient connection failure blocks further instruction saves in the current view. The draft stays visible initially, but ordinary reload recovery discards it. No saved instruction was corrupted.
- **Preconditions:** A200 loaded with note `Ring twice`; Save enabled.
- **Minimal reproduction:** Enter a new instruction; abort its POST to `/api/orders/A200/note` with a network failure. Click **Save instruction**, then restore connectivity. Edit the draft again and observe Save. Reload and select A200.
- **Expected / basis:** Surface an actionable failure and allow retry while retaining the draft. This applies the brief's failed-instruction recovery intent to transport failures; the brief does not separately specify offline behavior or durable offline drafts.
- **Actual:** Feedback stayed empty and Save stayed disabled. After interception was removed, a GET to A200 returned 200, but Save was still disabled even after further editing. Reload re-enabled Save and replaced the draft with `Ring twice`. See [state evidence](network-recovery-results.txt), [screenshot](network-failure.png), and [reproduction script](network_recovery.js).
- **Likely cause / owner:** Frontend, `app/static/app.js:23–36`: the handler disables Save before `fetch`, with no exception handling or recovery for a rejected fetch promise.
- **Workaround:** Copy the draft, reload or reselect the order, paste it back, and save after connectivity returns.
- **Acceptance criteria:** An aborted request displays a useful failure message, preserves the draft, and restores a usable retry control. Retrying after network recovery successfully persists the instruction. If the request outcome is uncertain, feedback must avoid claiming a definite save or failure without reconciliation.
- **Retest:** Reproduced on the supplied build; no fix supplied or retested.

## Coverage and handoff

| Area | Evidence and result |
|---|---|
| Existing tests | All four domain tests passed: partial refund, address save, service change, locker rejection. [Output](existing-tests.txt). |
| Ownership and access | Anonymous listing returned 401; Alice's read, refund, address, and note attempts against B100 returned 403. Per-user lists and Bob's unchanged record were checked. [API transcript](api-results.json). |
| Bulk atomicity | `[A100, B100]` returned 403 and `[A100, missing]` returned 404; complete Alice and Bob snapshots remained unchanged. Valid two-order service changes passed and were restored. |
| Refund accounting | Rejected zero, negative, boolean, fractional, and string amounts. A200 accepted 3500, rejected 2501 with 409 without changing the balance, accepted the exact remaining 2500, then rejected another cent. |
| Address concurrency | A200 accepted version 1 and incremented it; stale version 1 returned 409 and preserved the newer address. Blank, overlong, and boolean-version inputs returned 400. Restoring the original address advanced version to 3. |
| Input rejection | Blank/overlong notes, unsupported locker notes including mixed case/leading spaces, empty service IDs, unsupported service, and a non-object JSON body were rejected. Rejected notes preserved the saved note. These are sampled cases, not exhaustive malformed-input coverage. |
| Customer lookup and targeting | Rapid A200 → A100 → A200 selection stayed on A200 after the intentionally slow A100 response. Following note saves targeted A200. [Browser results](browser-results.txt), [request log](browser-requests.txt). |
| Rejected instruction | `LOCKER: 12` produced actionable feedback, kept the draft, and allowed correction and successful saving. [Screenshot](rejected-note.png). |
| Persistence | A valid note survived reload; a separate keyboard-entered note and express service both survived reload. [Keyboard/persistence results](keyboard-results.txt). |
| Keyboard and layout | Tab reached order selection, instruction entry, Save, express, and standard. Keyboard entry and Enter saved successfully; service buttons worked with Enter. Focused action controls had a visible 3px outline. At 320px, document width equalled viewport width; screenshot inspection found readable, reachable controls with vertical scrolling. [Narrow screenshot](narrow.png). |

The HTTP script made 40 requests, followed by two final-state reads. The browser log records 37 API attempts, including the injected failure; the assessment remained below the 120-request allowance. The four existing tests exercise fresh in-memory domain state and do not certify browser behavior.

**Remaining coverage:** Other browser engines, real mobile devices, screen-reader behavior, exhaustive validation boundaries, concurrent administrative callers, and pending mutation/order-switch combinations were not exercised. Service request processing in the reverse order and interrupted initial order lookups merit follow-up. Login, real payments, production authentication/security hardening, external messaging, and documentation defects were excluded as required.

**Next work:** Frontend owner should coordinate service mutations and implement instruction transport-error recovery, then retest the two saved reproduction scripts and the successful switching, keyboard, and persistence flows. No product fixes or new supplied tests were made during this assessment.

**Cleanup:** Notes, services, and addresses are restored to their original values; A100 and B100 are unchanged. **Owner reset is required for A200: refunded = 6000 cents and version = 3**, versus initial 0 and 1. These counters cannot be restored through the supplied API. [Final fixture state](final-fixture-state.json). All browser interception was removed, and only the created `journey-run-06` session was closed. [Close evidence](browser-close.txt).
