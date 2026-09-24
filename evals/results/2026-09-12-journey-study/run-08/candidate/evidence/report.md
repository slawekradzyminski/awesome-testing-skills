# Dispatch Desk release assessment

**Recommendation: hold release.** Three reproduced browser defects violate the customer journey requirements: inconsistent order identity during saves, false success on rejected instructions, and an express-delivery control inaccessible through ordinary keyboard navigation. The sampled administrative API checks passed.

Assessed 2026-09-12 against `http://127.0.0.1:57078`, using the supplied source, requirements, four existing tests, HTTP checks and the `journey-run-08` browser session. No application, supplied test, requirement or guidance files were edited. No external traffic, delegation or product fixes were used.

## Confirmed defects

### F1 — High: late lookup displays A100 while selection and save target are A200

**Reproduce:** Let an order finish loading. Select A100 and immediately select A200, within the intentional 700 ms A100 lookup delay. Wait for both responses. The selector shows `A200 — Pine Street`, but the heading shows `Order A100`, with A100's address and instruction. Enter an instruction and save.

**Observed:** The browser sent `POST /api/orders/A200/note` with `Race evidence intended for displayed A100`, received 200 with order ID A200, and continued displaying heading `Order A100`. This can cause customers to change delivery instructions on an order other than the one whose details they are viewing. The mismatch also occurred when switching to A200 immediately after reload, independently of the explicit rapid-switch sequence.

**Expected:** Selected order, visible details and mutation target must agree regardless of lookup completion order. The intentional lookup delay itself is acceptable.

**Cause and repair:** `app/static/app.js:6` creates a generation token but never checks it before rendering at lines 14–19. Discard obsolete lookup responses before updating any details or enabling controls; ensure actions operate on the current, fully loaded order. Add a browser regression that delivers A100 after A200 and checks selection, heading, address, note and the actual POST target/body together.

**Evidence:** [Recorded browser results](browser-results.txt), [mismatch screenshot](order-race.png), [request log](browser-requests.txt). The response body confirms a real A200 mutation, beyond a cosmetic heading error.

### F2 — High: rejected delivery instruction reports success

**Reproduce:** On a fully loaded A200, replace the instruction with `LOCKER: 1` and click Save instruction.

**Observed:** The backing request returns 422 with `Locker delivery is unavailable; enter another instruction`, while the UI displays `Delivery instruction saved`. The rejected draft remains in the textarea, but the actionable API error is hidden. Customers are told an unsupported delivery arrangement was saved. API checks separately confirmed rejection preserves the previously saved note.

**Expected:** Display actionable failure feedback, preserve the draft for correction, and never claim success after rejection.

**Cause and repair:** `app/static/app.js:27` parses the response but line 29 unconditionally writes the success message. Branch on `response.ok`, show the returned validation message on failure, and preserve retry capability. Add browser regressions for 422 and 400, checking feedback, draft retention, unchanged persisted note, and successful correction/reload.

**Evidence:** [422 response alongside UI state](browser-results.txt), [false-success screenshot](rejected-note.png), [API rejection and preservation checks](api-results.json).

### F3 — Medium: express delivery cannot be reached by keyboard

**Reproduce:** Once loading completes, focus the Order selector and press Tab repeatedly. The observed sequence is instruction textarea → Save instruction → Use standard delivery → document body → Order selector. Express delivery is skipped.

**Observed:** Express is a `DIV` with `role="button"`, `tabIndex=-1`, and only a click handler. Ordinary keyboard users cannot choose this service. The reached controls have a visible 3 px focus outline; standard delivery and instruction saving worked with Enter in the follow-up check.

**Expected:** Both service choices and instruction editing support ordinary keyboard navigation and visible focus.

**Cause and repair:** Replace the custom control at `app/static/index.html:9` with a native button and preserve focus styling and the loading disabled state. Verify Tab reachability plus Enter and Space activation for both service choices. A native button also provides actual disabled semantics; assigning `.disabled` to the current DIV does not supply those semantics.

**Evidence:** [Tab sequence and DOM properties](browser-results.txt), [working keyboard controls](browser-positive-results.txt).

## Passing evidence and coverage

| Area | Checks and result |
| --- | --- |
| Existing tests | All four supplied domain tests passed: partial refund, address save, service batch, note rejection. [Output](existing-tests.txt). These do not exercise the browser defects. |
| Identity and ownership | Anonymous list and mutation rejected with 401; Alice/Bob lists contain only their own IDs; Alice cannot read or mutate Bob's order via note, refund or address; Bob's complete final state unchanged. |
| Refunds | Positive partial refunds of 1,000 then 2,000 cents accepted; additional 7,001 rejected with 409 and refunded total remains 3,000. Zero, negative, boolean, decimal, string and missing amounts rejected with 400. |
| Addresses | Valid save increments version; stale save returns 409 and preserves newer address/version. Blank, overlength, boolean-version and string-version inputs rejected. Original address restored. |
| Service atomicity | Mixed owned/foreign and owned/missing batches return 403/404 and preserve the entire Alice order list. Valid two-order express batch persists. Empty IDs, non-string IDs and unsupported service rejected. |
| Notes and request parsing | Locker instructions, including padded lowercase prefix, rejected with 422; blank, overlength and non-string notes rejected with 400; saved state unchanged across rejections. Broken JSON, array and null bodies rejected with 400. |
| Browser success paths | Valid instruction survives reload; express selected by pointer survives reload; standard service and instruction save activate with Enter. [Results](browser-positive-results.txt). |
| Layout and focus | Desktop inspected; 375 × 812 narrow viewport has document width 375 with no horizontal overflow. Full-page screenshot shows controls in the layout. Reached keyboard controls have visible focus. [Narrow screenshot](narrow.png). |

[API script](api-assessment.py) made 57 requests, all with expected statuses; its semantic state assertions also passed. [Full request/response evidence](api-results.json). Including four baseline/final HTTP reads and 18 browser API calls, the assessment used **79 API requests**, below the 120 limit. Browser work remained below the 80-action limit. Scripts are evidence and mutate fixtures if rerun; the API script adds refunds and advances address versions.

## Cleanup and remaining scope

Original notes, services and address text were restored and reread. A200 and B100 exactly match their baselines. A100 differs only in `refunded: 3000` (baseline 0) and `version: 3` (baseline 1), from authorized refund and address tests. These require owner reset; there is no reset route. See [baseline Alice](baseline-alice.json), [final Alice](final-alice.json), [baseline Bob](baseline-bob.json), [final Bob](final-bob.json), and [cleanup verification](cleanup-verification.json). Only the browser session created for this assessment was closed.

This was a bounded release assessment, not exhaustive certification. Cross-browser/device coverage, injected network failures, concurrent administrative mutations, and every numeric/string boundary were not exercised. No findings are based solely on documentation or visual preference. No fixes were applied. Before release, repair F1–F3 and run the specific browser regressions above alongside the existing tests and unchanged API safeguards.
