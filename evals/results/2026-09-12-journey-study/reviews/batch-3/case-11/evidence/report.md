# Dispatch Desk release assessment

**Recommendation: hold release.** Three runtime-confirmed browser defects violate the product brief: a stale lookup can cause a note to be saved to the wrong order, rejected instructions claim success, and express delivery is unavailable through ordinary keyboard navigation. All findings are open; no product fixes were authorized or made.

## Scope and environment

Assessed 2026-09-12, approximately 11:05–11:09 UTC, within the six-minute budget, against `http://127.0.0.1:57088`. Charter: verify Alice can select the intended order, save instructions, recover from rejection, and choose delivery service; prioritize persisted correctness, response ordering, and keyboard access. Supporting ownership and bulk-service backing calls were sampled. Documentation-only issues and administrative refund/address journeys were excluded from this browser assessment.

Browser: Chromium 152.0.7977.84, dedicated `journey-run-09` session; desktop 1280×720 and narrow 390×844 CSS pixels, default zoom, no emulation or network throttling. Only the assigned runtime was accessed. The intentional approximately 700 ms A100 lookup delay was used without interceptors. Source revision and backend deployed build identifier are unknown: this candidate has no Git repository metadata. Served HTML, JavaScript, and CSS match supplied files byte-for-byte; [hash evidence](build-match.json). This establishes frontend identity, not backend revision provenance.

Requirements basis: [product brief](../app/requirements.md), particularly “Browser experience” and note/service API contracts. Read the supplied exploratory skill, browser-experiment/reporting references, and Playwright CLI skill with its custom-code reference. Source, tests, requirements and guidance were left unchanged.

## Prioritized risk map

| Journey / state | Evidence and initial concern | Impact / priority | Observation and next action |
| --- | --- | --- | --- |
| Rapid order switching → save | `readOrder` generates a token but never checks it | Wrong-order persisted instructions; first priority | UI-01 confirmed twice; guard rendering and saving against stale loads |
| Rejected instruction → correction | Save handler ignores HTTP status | Customer believes rejected instructions are saved; high priority | UI-02 confirmed in two valid probes, including a fresh session; display API error and retain draft |
| Keyboard service selection | Express is a div with only a click listener | Keyboard users cannot choose express; high priority | UI-03 confirmed; use a keyboard-operable native control |
| Ordinary successful edit / reload | Persistence must outlive displayed feedback | Core journey baseline | Note and express service survived reload; retain regression coverage |
| Ownership / service atomicity | Client always uses Alice, backend must enforce boundary | Other-customer mutation; high priority | Anonymous list 401, Alice read/note to B100 403, mixed A100/B100 service request 403 with both users unchanged |
| Narrow layout | Required narrow-screen support, no pixel reference | Hidden controls / unreadability | Inspected screenshot at 390×844; width equals scroll width, controls readable; no defect observed in sampled state |
| API-only administration and transport failures | Existing tests are routine domain tests | Residual coverage uncertainty | Refund accumulation, stale address, offline/5xx recovery not exercised live; separate targeted follow-up |

## UI-01 — Stale order lookup displays A100 while save targets A200

**Type:** FUI / NET. **Severity:** High. **Status:** Open. **Evidence:** runtime-confirmed.

**Reproduction:** Start with distinct notes for A100 and A200. This session saved `Journey 09 reception test` on A100; A200 initially contained `Ring twice`. Select A200 and wait for its details. Select A100, then select A200 before the slower A100 lookup completes. Once both responses finish, click **Save instruction** without changing the displayed note.

**Actual:** The dropdown selects A200 — Pine Street, while the heading says Order A100, the address is 10 Oak Street and the textarea shows A100's note. Save sends `POST /api/orders/A200/note` with `{"note":"Journey 09 reception test"}`, returning 200. A fresh orders read confirms A200 now contains that note. The stale display reproduced in two deliberate probes; the wrong-order save was verified once in the retained primary reproduction. In the repeat probe, response order was A200 then A100. Ordinary selection of A200 with its lookup completed produced consistent A200 details.

**Expected:** Selected order, displayed details and mutation target remain consistent regardless of lookup completion order, explicitly required by the browser brief.

**Impact:** Customers can overwrite delivery instructions on another of their own orders while seeing the wrong address/order details. This is within Alice's account; it is not demonstrated cross-customer access. Reloading or waiting for a fresh selection before editing is a workaround, but the UI gives no warning that it is needed.

**Cause evidence:** [app.js](../app/static/app.js), lines 5–19: `token` is unused and every successful response renders details. Lines 23–26 use the separate `selected` value for the save target.

**Evidence:** [inspected desktop screenshot](race-state.png), [state and sequence](race-state.txt), [save request/response](race-save.txt), [persisted orders](race-persisted.json), [repeat with response ordering and ordinary contrast](race-repeat.txt).

**Acceptance / regression:** Delay A100, switch A100→A200, resolve A200 first and A100 last, then edit/save. Every displayed field and target must be A200; A100 must remain unchanged. Test the opposite response order and switching during save. Ignore obsolete responses and keep mutation controls tied to the currently loaded order. No repaired build has been retested.

## UI-02 — Rejected instructions display successful-save feedback

**Type:** FUI / UX. **Severity:** High. **Status:** Open. **Evidence:** runtime-confirmed.

**Reproduction:** Wait for A100 to finish loading. Enter `LOCKER: 09`, then click **Save instruction**.

**Actual:** The API returns 422 with `Locker delivery is unavailable; enter another instruction`. The UI instead displays **Delivery instruction saved**. The draft remains in the textarea, but the corrective error is never shown. A fresh-session reproduction after cleanup returned the same 422 and success message; a subsequent HTTP read still contained the baseline saved note `Leave with reception`.

Two properly ready-state probes confirmed this behavior, including a fresh browser session. An additional intermediate attempt was inconclusive because an outstanding order lookup replaced the draft before submission; [that attempt](rejected-note-repeat.txt) returned 200 and is not counted as a rejection reproduction. The successful valid-note/reload journey provides the positive contrast.

**Expected:** The brief requires actionable failure feedback, preserved draft, and no success claim on rejection. Saved state must remain unchanged.

**Impact:** A customer can leave believing essential delivery instructions were accepted when fulfillment retains the previous instructions. Draft retention works, but the false confirmation removes the reason to correct it.

**Cause evidence:** [app.js](../app/static/app.js), lines 25–30, parses the error response but unconditionally sets successful-save feedback without testing `response.ok`.

**Evidence:** [inspected screenshot of false confirmation](rejected-note.png), [original 422 response and draft](rejected-note.txt), [fresh-session confirmation](rejected-note-fresh-session.txt), [fresh persisted-state read](rejected-note-fresh-persisted.json), [successful save/reload contrast](happy-path.txt).

**Acceptance / regression:** Submit a valid note, then a LOCKER instruction and a blank instruction. For rejection, show the corrective server message, retain the exact draft, re-enable saving, and leave the stored note unchanged. Correcting the draft must persist and survive reload. Success wording must appear only after success. No repaired build has been retested.

## UI-03 — Express delivery is skipped by keyboard navigation

**Type:** A11Y. **Severity:** High. **Status:** Open. **Evidence:** runtime-confirmed.

**Reproduction:** With an order loaded, focus the Order dropdown and close it with Escape. Press Tab repeatedly. Observed focus order: instruction textarea → Save instruction → Use standard delivery → body → Order. **Use express delivery** is skipped. The reached controls show a solid focus outline. In a contrasting keyboard probe, Tab to standard delivery and press Enter: its service request returns 200 and selects standard successfully. Mouse activation of express also succeeded and persisted through reload.

**Expected:** Both service choices must work with ordinary keyboard navigation and visible focus, explicitly required by the brief.

**Impact:** Keyboard-only customers cannot complete the express-service choice, although mouse users can. This blocks a required core operation for that interaction mode. No screen reader or real-device behavior is claimed.

**Cause evidence:** [index.html](../app/static/index.html), line 9, uses `<div role="button">` without a tab stop; [app.js](../app/static/app.js), line 41, supplies only click behavior. The corresponding standard option is a native button.

**Evidence:** [actual key sequence/focus and DOM properties](keyboard.txt), [standard keyboard activation and response](keyboard-standard.txt), [inspected narrow screenshot](narrow.png).

**Acceptance / regression:** Use a native button for express, preserve clear focus, and ensure Tab reaches it in order and Enter/Space activate exactly one service mutation. Verify native disabled behavior during loading as well. Repeat the keyboard journey at desktop and narrow widths; no repaired build has been retested.

## Verification, limitations and closeout

- Executed `python3 -m unittest discover -s app -v`: **4 passed**; [output](unit-tests.txt). Inspected assertions cover one partial refund, one address save, successful bulk services and note rejection status. They do not exercise browser rendering, feedback, keyboard operation or async ordering; passing them does not cover these failures.
- [Backing API checks and cleanup](api-checks-cleanup.json) preserve before/after records for the sampled ownership/atomicity boundaries. [Local script](check_backing_api.py) records 13 requests. These checks are limited to the listed cases, not a complete authorization audit.
- Reviewed live response bodies for the note rejection, wrong-order save and keyboard service change; [browser request list](requests-final.txt). Browser activity plus direct checks remained comfortably below 120 API requests. Exploration stayed below 80 browser actions; no exhaustive state/device matrix was attempted.
- Captured and opened the desktop rejection, desktop mismatched-order, and narrow screenshots. No clipping or horizontal overflow was observed in the narrow sample (390 px viewport and 390 px document width). The desktop screenshots are scrolled to the affected controls. Visual review is limited to these states, not every breakpoint or zoom setting.
- An initial custom response logger failed because `URL` was unavailable in its execution environment. It was removed; affected early automation was not used as proof. Essential probes were rerun and captured directly. `browser-events.txt` contains viewport measurements but no usable event history. The expected failed-request console indication accompanying 422 is not a separate defect; no broad console-cleanliness claim is made.
- No injected responses, production integrations, external traffic, delegation, issue filing or source/test edits. No refund or address mutations were made. Alice's complete orders were verified equal to the original baseline after restoration; Bob was unchanged. The final fresh-session rejection also preserved baseline A100. No refund totals or version counters changed. Both incarnations of the dedicated browser session were closed; no other sessions were touched.
- Remaining useful checks: stale in-flight writes across navigation, transport failure recovery, malformed-note boundaries, service errors and pending-state behavior, intermediate widths/zoom, and assistive technology. API-only refund/address requirements merit their own live administrative assessment. These are untested risks, not additional confirmed defects.

Release next step: repair UI-01 through UI-03, add the focused regressions above, and rerun the affected journeys with persisted-state assertions before approval.
