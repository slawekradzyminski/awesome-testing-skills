# Dispatch Desk release assessment

**Recommendation: hold release for two browser timing defects.** Routine journeys and the tested API business rules pass, but customers can lose newly typed instructions or see a delivery service that differs from the saved service. Both findings are medium severity (P2); neither demonstrates cross-customer access or incorrect refund accounting.

Assessment conducted on 12 September 2026 against **http://127.0.0.1:56415**, using the supplied source, requirements, four existing unit tests, direct HTTP checks and Chromium through the assigned `journey-run-04` Playwright CLI session. No supplied files were edited.

## Confirmed findings

### DD-1 — An older service response overwrites the current saved service in the UI

**Impact:** The desk reports “Delivery service saved” and displays express while the server stores standard. Reloading changes the displayed service back to standard. Customers cannot reliably tell which service is active after overlapping choices.

**Reproduce:**
1. Load A100 with standard delivery.
2. Click Use express delivery. Allow its real POST to commit, but hold delivery of that response.
3. Click Use standard delivery while express remains pending. Allow the second POST and response to complete.
4. Release the first response.
5. Compare the displayed service with `GET /api/orders`, then reload.

**Observed:** Both writes returned 200; the server recorded express followed by standard. After the older response arrived, the UI displayed express and success feedback. The server still returned standard, and reload displayed standard.

**Evidence:** [Runnable reproduction](browser-races.js), [captured response bodies and UI/server states](browser-races-results.txt), [screenshot](service-mismatch.png).

**Test condition:** Response delivery was deliberately reordered with a Playwright route using `route.fetch()` and the genuine server response. No response bodies or statuses were fabricated. This establishes the failure under response reordering; it does not measure how often that occurs on an ordinary connection.

**Cause and action:** `app/static/app.js:38–45` leaves both service buttons usable during a write and accepts every response for the selected order. Serialize service changes or disable both buttons until completion; ensure rendering reflects the authoritative final state. A latest-response token alone does not ensure server write ordering. Add a regression that reverses response completion and checks both the UI and persisted service, including after reload.

### DD-2 — The enabled instruction editor silently discards typing during an order lookup

**Impact:** A customer can enter a new draft in an apparently usable editor and lose it without saving or receiving an explanation.

**Reproduce:**
1. Load A200.
2. Select A100 and immediately type `Draft typed during loading` into Delivery instruction during the normal approximately 700 ms lookup.
3. Wait for the lookup to finish.

**Observed:** During loading, the selector was A100, the heading still showed A200 and the textarea was enabled. The typed draft was then replaced by `Leave with reception`. No artificial delay was needed for this reproduction.

**Expected:** Prevent editing until the selected order's details are ready, or preserve and correctly associate text entered during loading. A usable editor should not silently overwrite the customer's current input.

**Evidence:** [Runnable reproduction](browser-races.js), [before/after editor states](browser-races-results.txt), [resulting screen](draft-after-lookup.png).

**Cause and action:** `app/static/app.js:9` disables save and service buttons but leaves the textarea enabled; line 17 unconditionally replaces its value on completion. Include the editor in the loading state or explicitly handle dirty drafts. Add a regression for typing during the normal A100 lookup. The intentional lookup latency itself is not a defect.

## Verified coverage

| Area | Result and evidence |
| --- | --- |
| Existing tests | All four pass: partial refund, address save, successful service batch and locker rejection. [Output](routine-tests.txt). |
| Fixture access | Alice and Bob lists contain only their own orders. Anonymous list/mutation return 401. Alice cannot read or mutate Bob's order through note, address or refund endpoints. Bob's final order remains unchanged. |
| Refund accounting | Invalid numeric types, zero and negative amounts return 400. A100 partial refunds of 6000 and 4000 reach exactly 10000; another cent returns 409 without changing the total. |
| Address concurrency | Invalid addresses/version types return 400. Successful edit increments version; stale version returns 409 and preserves the newer address. |
| Service atomicity | Valid batch persists both changes. A batch containing an owned order followed by a forbidden or missing order returns 403/404 and preserves all Alice orders. Invalid selections/services return 400. |
| Note/API validation | Blank, oversized and non-string notes rejected; locker instructions, including mixed case and leading whitespace, return 422. Prior note retained. A 160-character note succeeds. Malformed JSON and non-object bodies return 400. |
| Browser note journey | Locker rejection shows actionable feedback, keeps the draft and does not claim success. Corrected note saves and survives reload. Notes restored afterwards. [Rejected draft screenshot](rejected-draft.png). |
| Order lookup race | A200 → A100 → A200, followed by completion of the slower A100 lookup, retains A200 details. A subsequent note save updates A200 and leaves A100's note unchanged. |
| Keyboard | Tab reaches order, instruction, save, express and standard in order; each has a 3px solid visible focus outline. Both services work using keyboard activation. Instruction entry and save also complete entirely by keyboard with a 200 response. [Keyboard evidence](keyboard-note-results.txt). |
| Layout | At 320px width there is no horizontal page overflow and all controls fit horizontally. [Full-page screenshot](narrow-keyboard.png) also shows visible keyboard focus. Desktop exercised at default viewport and 1280 × 900. |

The API matrix used 47 requests. [Script](api_assessment.py), [pass results](api-results.txt) and [full request/response transcript](api-transcript.json) provide exact inputs and results. Browser checks are in [the assertion script](browser-assessment.js) and [its successful CLI execution](browser-results.txt); that CLI output echoes the script rather than printing its console-based result array. No assertion error was reported. [Browser request log](browser-requests.txt) records 24 API requests. Two final read-only requests verified fixture cleanup: **73 total API requests**, below the 120-request cap. Interaction/navigation/viewport/screenshot actions remained below 80.

## Fixture cleanup and release follow-up

All addresses, notes and services were restored to baseline. **Owner reset is required for A100 refunded: 0 → 10000 cents, and A200 address version: 1 → 3.** These are the only final differences; see [final fixture comparison](final-fixture.json). The created browser session was closed; no other sessions were touched.

Fix DD-1 and DD-2, add the targeted browser regressions above, and repeat the affected persistence/lookup/keyboard checks before release. The API findings provide passing evidence for the unchanged administrative implementation; the four supplied unit tests alone do not cover these browser failures.

This is a time-bounded assessment, not exhaustive certification. Cross-browser/device coverage, screen-reader operation, transport-failure recovery, and exhaustive concurrent mutation interleavings were not tested. Production authentication, real payments, external integrations and documentation-only defects were excluded as required. No external services, product fixes or delegation were used.
