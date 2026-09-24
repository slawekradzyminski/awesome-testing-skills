# Dispatch Desk release assessment

## Session

**Recommendation: hold release.** Three confirmed customer journey defects remain open: a delayed lookup can cause a save to overwrite another order's instructions, rejected instructions claim success, and express delivery is inaccessible through ordinary keyboard navigation.

Assessed on 12 September 2026 using the supplied source and requirements, the existing four domain tests, and Chromium through the assigned `journey-run-07` session at `http://127.0.0.1:56981`. The browser uses Alice's disposable orders. HTTP checks also used Bob and anonymous requests. No source, supplied tests, requirements, or guidance were changed. No external services or delegation were used.

The six-minute assessment prioritised order identity, saved-state integrity, rejection recovery, keyboard access, narrow layout, and administrative API safeguards. This is a sampled release assessment, not exhaustive certification. The intentional 700 ms A100 lookup is not itself a defect.

## Findings

### DD-01 — Late lookup displays A100 while Save modifies A200

- **Type / evidence / status:** Functional data integrity defect; confirmed in the live browser and backing HTTP response; open.
- **Severity: High.** Ordinary rapid order switching silently overwrites delivery instructions on a different order from the displayed heading and address. This can cause the customer to give incorrect instructions for a delivery.
- **Preconditions:** Alice's two orders have different notes; A100 retains its normal lookup delay.
- **Minimal reproduction:** Load A200 and wait for its details. Select A100, then select A200 before A100 finishes. Wait for the pending A100 response, then click Save instruction without editing the displayed note.
- **Expected / basis:** The browser requirements explicitly require the selected order, details, and save target to remain consistent when lookups finish out of order.
- **Actual:** The selector showed A200, but the heading showed Order A100 and the editor showed A100's `Assessment delivery note`. Save posted that note to `/api/orders/A200/note`; the 200 response confirmed A200 now contained it. See [browser results](evidence/browser-results.txt), steps `out of order response` and `save mismatched displayed note`, and [screenshot](evidence/wrong-order.png). The [reproduction script](evidence/browser-check.js) uses the real lookup latency without mocked responses.
- **Affected users / workaround:** Customers switching orders before lookups settle. Wait for each selection to finish and verify the selector and heading agree before saving; if they disagree, reselect the intended order and wait.
- **Repair direction:** In `app/static/app.js:5–19`, `token` is generated but never checked. Ignore superseded lookup results before updating details, loading indicators, or button state; gate edits on the currently loaded order matching the selection.
- **Acceptance / retest:** Repeat A200 → A100 → A200 with overlapping responses. Once settled, selector, heading, address, note, and service must all belong to A200. A subsequent save must update only A200 with its intended draft. Test both completion orders and initial-load switching. No fix supplied; retest pending.

### DD-02 — Rejected delivery instructions display success

- **Type / evidence / status:** Functional error-feedback defect; confirmed in browser and HTTP; open.
- **Severity: High.** The application explicitly tells customers an unsupported delivery instruction was saved when the server retained an older instruction, creating a credible risk of incorrect delivery arrangements.
- **Preconditions:** An order has an existing saved note.
- **Minimal reproduction:** Enter `LOCKER: 1` and click Save instruction. Observe the status and then reload.
- **Expected / basis:** The requirements mandate actionable failure feedback, preservation of the rejected draft for correction, and no success claim on rejection. Locker instructions must return 422 and retain the old saved note.
- **Actual:** The API returned 422 with `Locker delivery is unavailable; enter another instruction`, but the UI displayed `Delivery instruction saved`. The draft remained available immediately after rejection; reloading showed the prior saved note. See [browser results](evidence/browser-results.txt), rejection and reload steps, and [screenshot](evidence/rejected-note.png). Draft preservation and server rejection passed; the defect is the false success and missing reason.
- **Affected users / workaround:** Customers submitting unsupported instructions. Until repaired, avoid locker instructions and reload to verify persistence; reloading discards an unsaved draft, so retain its text first.
- **Repair direction:** In `app/static/app.js:22–30`, branch on `response.ok` and display the returned error when rejected. Keep the draft editable and restore the Save control on failure.
- **Acceptance / retest:** A 422 locker rejection and a 400 blank-note rejection must show actionable failure, never success, preserve the draft, and leave the saved note unchanged. Correcting the draft must then save successfully and survive reload. No fix supplied; retest pending.

### DD-03 — Keyboard users cannot select express delivery

- **Type / evidence / status:** Accessibility and functional access defect; confirmed by browser Tab traversal and DOM inspection; open.
- **Severity: Medium.** Keyboard-only customers cannot perform one of the two required delivery service choices, though instruction editing and the standard-service control remain reachable.
- **Preconditions:** An order is fully loaded.
- **Minimal reproduction:** Focus the Order selector and press Tab repeatedly. The sequence is Order → Delivery instruction → Save instruction → Use standard delivery → page body; express is skipped.
- **Expected / basis:** Both service choices must be usable through ordinary keyboard navigation with visible focus, as required in the browser experience brief.
- **Actual:** Express is a `DIV` with `role="button"`, `tabIndex=-1`, and only a click handler. It cannot be reached through Tab. Pointer activation did work and persisted after reload. Standard delivery was keyboard-activated with Enter and worked. See the keyboard traversal and service steps in [browser results](evidence/browser-results.txt); [narrow screenshot](evidence/narrow.png) shows visible focus on the standard button.
- **Affected users / workaround:** Keyboard-only users; pointer input is a workaround only for customers able to use it. There is no demonstrated keyboard-only route to express in the UI.
- **Repair direction:** Replace the express `div` in `app/static/index.html:9` with a native button, preserving styling and its handler. This also gives the existing loading-state `disabled` assignment native behavior.
- **Acceptance / retest:** Tab must reach express with visible focus. Enter and Space must each activate it; the service must persist after reload. Verify both service buttons remain correctly disabled during loading. No fix supplied; retest pending.

## Coverage and handoff

**Passing evidence:**

- All four supplied domain tests passed: [unit test output](evidence/unit-tests.txt). These routine tests alone do not cover the confirmed browser defects.
- Valid browser note save survived reload; a rejected note left the prior server note unchanged; pointer express selection survived reload; Enter activated standard delivery. Normal sequential order selection worked. See [browser results](evidence/browser-results.txt).
- At 375 × 812, the page had no horizontal overflow (`scrollWidth=375`), controls and text were visible in the full-page capture, and a native button had visible focus. See [narrow screenshot](evidence/narrow.png). This is a single narrow viewport check, not real-device certification.
- The [API check](evidence/api-check.py) completed 54 HTTP calls with expected status codes and state assertions: [full request/response evidence](evidence/api-results.json), [summary](evidence/api-summary.txt). Checked Alice/Bob list separation; anonymous rejection; forbidden reads and note/address/refund writes; missing orders; service batches with a valid order followed by forbidden/missing IDs preserving all state; valid multi-order service changes; invalid services and IDs; nonpositive, boolean, fractional, and string refund amounts; cumulative refunds to exactly the paid amount followed by 409 without another refund; address version increment and stale 409 preserving the newer address; invalid address lengths/version type; blank, oversized, and locker notes preserving the saved note; malformed JSON and non-object bodies; and Bob's state remaining unchanged.

**Additional check limitation:** An exploratory keyboard-only correction script timed out while trying to change the native order selector with ArrowDown; no A200 lookup or save was made in that attempt. This is inconclusive and is not reported as another product defect. Full keyboard-only correction remains unverified. See [attempt script](evidence/keyboard-recovery.js) and [timeout output](evidence/keyboard-recovery.txt). The earlier successful Tab traversal and standard-service Enter activation remain valid.

**Limitations and next work:** Prioritise the three repairs and add browser regressions that exercise the real order-switch race, rejection feedback and correction, and keyboard service selection. Error transport failures, interrupted connections, repeated overlapping writes, multiple browsers/tabs, screen-reader announcements, broader viewports, and concurrent API requests were not exhaustively assessed. No production authentication, payments, email, or performance SLA assessment was attempted, as excluded by the brief.

**Cleanup:** Notes, addresses, and delivery services were restored to their original values; Bob remained unchanged. A200 now has `refunded=6000` (two authorised test refunds of 1000 and 5000 cents) and `version=3` (test address update followed by restoration). These cannot be restored through the supported API: the fixture owner must reset the instance. A100 remains at `refunded=0`, `version=1`. See [original Alice state](evidence/alice-before.json), [original Bob state](evidence/bob-before.json), and [post-check fixture state](evidence/fixture-after.json).

Only the created `journey-run-07` browser session was closed: [closure evidence](evidence/browser-close.txt). The recorded browser traffic includes 14 API requests; together with 54 scripted API checks and two baseline reads, the assessment used 70 API requests, below the 120-request cap. Browser interactions remained below the 80-action cap.
