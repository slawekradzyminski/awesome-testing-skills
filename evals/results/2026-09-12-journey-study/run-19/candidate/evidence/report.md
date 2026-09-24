# Dispatch Desk release assessment

**Recommendation: hold release.** Three browser defects violate explicit journey requirements, including a confirmed save to the wrong order. The assessed administrative API behavior passed. Passing routine domain tests do not cover the browser failures.

Assessment used the supplied source and requirements, the assigned runtime `http://127.0.0.1:59088`, and only the created Playwright session `journey-run-19`. No supplied files were edited. No external services, issue filing or delegation were used.

## Confirmed release blockers

### 1. High — delayed lookup displays one order while saving to another

**Reproduce:** Load the desk, select A200 and let it finish. Select A100, then immediately select A200 before A100's intentional 700 ms lookup completes. Wait about one second. Click **Save instruction** without changing the displayed note.

**Observed:** The selector remains A200, but the heading is `Order A100`, address is `10 Oak Street`, and note is `Leave with reception`. Save sends `POST /api/orders/A200/note` with that A100 note. The 200 response confirms that A200's previously saved `Ring twice` was overwritten with `Leave with reception`. This was reproduced twice using the real runtime, without network mocking.

**Expected / impact:** Selected order, displayed details and save target must agree regardless of response order. A customer can unknowingly overwrite instructions for a different delivery.

**Cause and repair:** In `app/static/app.js:5–19`, `readOrder` creates a generation token but never checks it before rendering or enabling controls. Ignore stale responses, including their loading/error updates, and bind editability to the currently loaded selection. Keep service and note saves consistent with the rendered order.

**Regression gate:** Force A100's response to finish after a later A200 response; assert selector, heading, address, note and service all remain A200, then save and verify A200 receives only its own intended draft while A100 remains unchanged. Include switching away and back while requests are outstanding.

Evidence: [browser results and reproduction script output](browser-check.txt), [desktop screenshot](race.png), [repeatable browser script](browser-check.js).

### 2. High — rejected delivery instruction is reported as saved

**Reproduce:** On a fully loaded A200, enter `LOCKER: 1` and click **Save instruction**.

**Observed:** The API responds 422 with `Locker delivery is unavailable; enter another instruction`. The UI instead announces `Delivery instruction saved`. The rejected draft remains in the textarea, and a separate API read confirms the previously stored note is unchanged. A separate reproduction with a consistent selection confirms this is independent of defect 1.

**Expected / impact:** Show actionable rejection feedback, retain the draft and never announce success. Customers currently believe an unsupported delivery arrangement has been recorded.

**Cause and repair:** `app/static/app.js:22–30` parses the response but unconditionally writes success. Check `response.ok`, show the returned error on rejection, retain the draft and permit correction/retry. Handle request failures without leaving the save button permanently disabled.

**Regression gate:** For 422 and malformed-note 400 responses, assert actionable failure feedback, draft preservation, unchanged persisted note and absence of success text. Correct the draft, save, reload and verify persistence.

Evidence: [isolated rejection and persistence results](persistence-layout.txt), [isolated rejection screenshot](rejected-note-isolated.png), [422 response capture](browser-check.txt).

### 3. Medium — express delivery cannot be selected with ordinary keyboard navigation

**Reproduce:** Start at the order selector and repeatedly press Tab. Focus moves through the instruction textarea, Save instruction and Use standard delivery, then returns to the order selector. It never reaches Use express delivery.

**Observed:** Express is a `div` with `role="button"`, computed `tabIndex: -1`, and only a click handler. Standard delivery is keyboard reachable and Enter successfully applies it. Focus outlines on the reachable controls are visible (3 px orange).

**Expected / impact:** Both delivery services must be usable with ordinary keyboard navigation and visible focus. Keyboard users cannot select express delivery.

**Cause and repair:** `app/static/index.html:9` and `app/static/app.js:41` provide button semantics without keyboard behavior. Use a native button with the existing identifier and handler. This also makes the existing loading-time `disabled` assignment effective; the current div does not have native disabled behavior.

**Regression gate:** Tab to each service choice, verify visible focus, activate using Enter and Space, and verify the saved service after reload. Check that both are inoperable while loading.

Evidence: [recorded Tab sequence](browser-check.txt), [tabIndex and keyboard activation results](persistence-layout.txt), [visible standard-button focus at narrow width](narrow.png).

## Verification and coverage

| Area | Observed result |
| --- | --- |
| Supplied routine tests | All four pass: partial refund, address save, valid bulk service update and note rejection. [Output](unit-tests.txt). |
| Successful browser edits | Corrected note saved with keyboard activation; express selected with pointer; both persisted after reload and reselecting A200. Standard subsequently applied with Enter. |
| Rejected note integrity | 422 leaves persisted note unchanged and retains browser draft; feedback fails as described above. |
| Responsive layout | Inspected desktop 1280×720 and narrow 375×812 screenshots. Narrow document width equals viewport width (375 px); controls and text fit, with vertical scrolling available. No confirmed layout defect. |
| Fixture access isolation | Anonymous list and note mutation return 401. Alice cannot read, refund, address-edit or note-edit Bob's order (403); Bob cannot read Alice's A100 (403). Bob's full final order equals its starting state. |
| Refund arithmetic | A100 accepts 6000 then 3000 cents; rejects 1001 with 409 and retains 9000; accepts the exact remaining 1000; rejects another cent and retains 10000. Boolean, zero, negative, fractional and string amounts return 400. |
| Address concurrency | A200 valid save advances version; a stale save returns 409 and preserves the newer address. Original address restored using the new version. Blank, overlong and boolean-version inputs return 400. |
| Bulk service atomicity | `[A100, B100]` returns 403 and `[A100, MISSING]` returns 404, with Alice's services unchanged after each. Valid two-order express update and restoration to standard succeed. |
| Input validation | Blank, overlong and non-string notes return 400; locker notes return 422. Malformed JSON, non-object JSON, empty IDs, non-string IDs and unsupported service return 400. |

API script completed **49 requests with all assertions passing**; its full method/path/actor/body/status/response transcript is in [api-check.json](api-check.json), with [script](api-check.py) and [result](api-result.txt). Browser and final restoration requests were additional and remained within the 120-request budget. Browser interactions remained below 80. Assessment and reporting completed within six minutes.

This is a bounded release assessment, not exhaustive certification. Concurrent refund/address writes, randomized input combinations, transport-failure recovery, assistive technology and other browser engines were not exercised. No performance finding is raised for the intentional lookup delay. Console errors associated with the exercised 422 responses are not separate defects. Authentication hardening and documentation-only issues were excluded as required.

## Fixture cleanup and handoff

The created browser session was closed. Original notes, addresses and standard service choices are restored for all orders; Bob remains unchanged. [Final state verification](final-state.json) records the result.

**Owner reset is required for two authorized, non-reversible effects:** A100's cumulative refunded amount is now **10000 cents** (originally 0); A200's address version is now **3** (originally 1, advanced once for the test save and once for restoration). Other refund totals and version counters are unchanged. Do not rerun the API script on this consumed refund fixture without a reset.

Fix the three browser findings, add the specified journey regression coverage, and rerun those affected checks against a reset fixture before release. No product fixes were made during this assessment.
