# Dispatch Desk release assessment

**Recommendation: hold the customer browser release.** Three runtime-confirmed defects violate the browser requirements: stale order details can cause an edit to reach a different order than the displayed heading, rejected instructions falsely report success, and express delivery is unavailable through ordinary keyboard navigation.

Assessment: 12 September 2026, approximately 11:22–11:26 UTC. Target: `http://127.0.0.1:59252/`; browser role Alice. Headless Chrome 152 on macOS, desktop 1280 × 720 and narrow 390 × 844 CSS pixels, default zoom, no emulation or injected network conditions. Source commit and deployed build identifiers were not supplied. Served HTML, JavaScript and CSS were byte-compared with the supplied files and matched; [source hashes](source-hashes.json) and [runtime comparisons](http-probes.json) identify the assessed artifacts. Backend revision equivalence is not established by that asset comparison.

The charter was to verify that customers can select the intended order, save or correct instructions, and select either delivery service without losing consistency or keyboard access. Scope included backing API rejection and ownership checks. Requirements: [product brief](../app/requirements.md). Documentation-only defects, product fixes, external services and delegation were excluded. Exploration stopped after reproducing the principal failures and checking contrasting successful paths, within the six-minute budget. There were 41 `/api` requests, including setup, browser traffic, readbacks and cleanup; browser interactions remained below the 80-action limit.

## Prioritized findings

All findings are **Open**, **runtime-confirmed**, and not fixed or retested against a repaired build. Severity uses High for severe/core-flow impact and Medium for material impairment.

| ID | Type | Severity | Failure | Release action |
| --- | --- | --- | --- | --- |
| UI-01 | FUI / NET | High | Late A100 response overwrites A200 details; save still targets A200 | Block release; enforce latest-selection consistency |
| UI-02 | FUI / UX | High | A rejected instruction reports “Delivery instruction saved” | Block release; handle unsuccessful save responses |
| UI-03 | A11Y | High | Express delivery is skipped by keyboard navigation | Block release; make both service choices keyboard-operable |

### UI-01 — Order selection, details and save target diverge

**Reproduction:** As Alice, select A200 and wait for its details. Select A100, then select A200 before A100's approximately 700 ms lookup completes. Wait for both responses. The selector reads **A200 — Pine Street**, but the heading, address and instruction show **A100 / 10 Oak Street**. Enter an instruction and click Save instruction.

**Observed:** The mismatch reproduced twice, once at each sampled width, without response interception or artificial delay. In the first occurrence, saving `Journey assessment: wrong target proof` sent one successful POST to `/api/orders/A200/note` while A100's heading was displayed. A fresh order-list read confirmed that A200 received the text and A100 retained its own saved text. This is a demonstrated wrong-context write within Alice's orders, not evidence of a cross-customer write.

Evidence: inspected [desktop mismatch](order-mismatch-desktop.png), inspected [narrow mismatch](order-mismatch-narrow.png), [save request](mismatch-save-request.txt), [save response](mismatch-save-response.txt), [independent persisted read](after-browser-alice.json), and [second reproduction with selected/heading values](keyboard-and-retest.log). The [network log](browser-network-final.txt) associates requests 21–23 with the first occurrence and 32–33 with the repeated lookup sequence; its listing order alone is not used as evidence of response completion order.

**Expected:** Selected order, displayed details and save target remain consistent regardless of lookup completion order, as explicitly required by the browser brief. Ordinary A200 selection with its response allowed to finish displayed A200 correctly, providing the contrasting case.

**Cause and impact:** In [app.js](../app/static/app.js), lines 5–19, `generation` and `token` are incremented but never checked before updating the DOM. The note handler uses `selected` at lines 23–26, so the old response's displayed order differs from the mutation target. A customer can unintentionally change another delivery arrangement; silently successful feedback makes discovery harder. Waiting for one lookup at a time avoids the observed trigger but is not a reliable release mitigation.

**Acceptance / regression:** Permit only the latest lookup to render or enable actions. Exercise A200 → A100 → A200 with A100 completing last; assert selector, heading, address, note and service all describe A200. Save and independently read both orders, proving only the displayed/selected order changed. Repeat the converse ordering and service selection during loading. Preserve the intentional lookup latency.

### UI-02 — Rejected delivery instructions falsely claim success

**Reproduction:** Load A100, enter `LOCKER: 1`, and click Save instruction. Repeated with `LOCKER: 2` after a successful keyboard save.

**Observed:** Both POSTs returned 422 with `Locker delivery is unavailable; enter another instruction`. The live feedback instead read **Delivery instruction saved**. The draft remained in the textarea, but there was no actionable rejection message. Reload after the first rejection restored the previously successful instruction. API readback confirmed the backend preserved that saved instruction.

Evidence: inspected [desktop false success](rejected-save-desktop.png), inspected [narrow false success](rejected-save-narrow.png), [422 request](rejected-request.txt), [response body](rejected-response.txt), [readback](after-browser-alice.json), and [repeat including response and visible state](keyboard-and-retest.log). Network requests 15 and 30 are the two rejected saves. The associated resource-load console errors reflect the deliberate 422 responses, not separate defects.

**Expected:** The brief requires actionable rejection feedback, a retained draft, preservation of the old saved note, and no success claim. Draft and persisted-state preservation passed; feedback failed. A normal instruction returned 200 and survived reload, providing the contrasting success case.

**Cause and impact:** [app.js](../app/static/app.js), lines 25–30, parses the response but unconditionally sets success feedback without checking `response.ok`. Customers can leave believing delivery instructions were accepted when they were not. The backend validation does not prevent this misleading customer outcome.

**Acceptance / regression:** Show success only after an accepted save. For 422 and 400, expose actionable server feedback, retain the editable draft, re-enable correction, and leave persisted data unchanged. Test a valid save, `LOCKER:` rejection, blank rejection, correction and reload. Transport failure/recovery also needs a dedicated follow-up check.

### UI-03 — Keyboard users cannot choose express delivery

**Reproduction:** Reload and wait for A100. Press Tab to Order, Tab to Delivery instruction; enter text, Tab to Save instruction, Enter to save, then Tab again. Focus moves directly to **Use standard delivery**, skipping **Use express delivery**.

**Observed:** The exact sequence and focused element IDs are in [keyboard evidence](keyboard-and-retest.log). Express is a `DIV` with `role="button"` and `tabIndex: -1`; it is not in ordinary sequential keyboard navigation. The inspected [focus screenshot](keyboard-focus-desktop.png) shows visible focus on standard delivery. Enter successfully saved the instruction and activated standard delivery. Mouse activation of express succeeded and survived reload, isolating the impairment to keyboard operation. One full keyboard sequence was exercised.

**Expected:** Both service choices and instruction editing must work with ordinary keyboard navigation and visible focus, per the browser requirements. No screen-reader behavior or comprehensive standards conformance is claimed.

**Cause and impact:** [index.html](../app/static/index.html), line 9, supplies a non-focusable div; [app.js](../app/static/app.js), line 41, attaches only a click handler. Keyboard-only customers cannot complete the express-selection task. This is High because a required core choice is blocked for that interaction mode.

**Acceptance / regression:** Prefer a native button with appropriate pending/disabled behavior. Verify Tab reaches each service control, focus is visible, and Enter and Space activate it once. Read persisted service after reload and confirm keyboard selection changes only the intended order. Retest both sampled widths.

## Risk map and passing evidence

| Journey / risk | Evidence and priority rationale | Experiment / status | Next action |
| --- | --- | --- | --- |
| Switching while lookups overlap | Unused generation token; core target consistency | Runtime-confirmed UI-01, 2/2 reproductions | Repair and test response-order permutations |
| Rejected instruction feedback | Unconditional success text; customer relies on acceptance | Runtime-confirmed UI-02, 2/2 reproductions | Test rejection and correction in the browser |
| Keyboard service choice | Div used as button; explicit keyboard requirement | Runtime-confirmed UI-03 | Native keyboard-operable control and manual retest |
| Successful note/service persistence | Baseline for distinguishing UI-only feedback from stored success | Valid mouse note and express saves survived reload; keyboard note and standard saves succeeded | Retain these as regression baselines |
| Customer boundaries and atomic services | Browser backing operations must not change forbidden orders | Anonymous list 401; Alice read/note against B100 403; mixed allowed/forbidden service batch 403 and mixed allowed/missing batch 404; all preserved state | Broaden to other administrative endpoints in a separate API assessment |
| Malformed instruction data | Prior saved note must survive rejection | Empty, whitespace, 161-character and numeric notes returned 400 with state unchanged | Add live browser blank-feedback case to UI-02 regression |
| Narrow layout / focus visibility | Explicit desktop/narrow support | Opened screenshots at 1280 × 720 and 390 × 844; narrow document width equaled viewport width; no sampled clipping or horizontal overflow observed | Check other widths, zoom and real devices separately |

Backing API evidence: [13-request probe results](http-probes.json) and [probe source](http-probes.py). A first local helper run failed after one read because it used the wrong Python request-method accessor; that helper was corrected and the complete probe then passed. This was a tooling error, not an application defect.

The supplied four domain tests were inspected and executed: **4 passed** ([output](unit-tests.txt)). They cover one partial refund, one address save, one successful service batch and a note rejection status. They do not exercise browser response ordering, visible rejection feedback, keyboard access, or persisted-state invariants across UI transitions; their passing result does not establish customer-journey readiness.

## Limits and closeout

Visual review covered the saved screenshots, including failure states and visible keyboard focus. No additional visual defect was established. UX and network review focused on the three customer consequences above. No performance SLA was assessed; A100's intentional delay was used as a naturally occurring ordering condition. No screen reader, real device, alternate browser, zoom/reflow sweep, offline/transport failure, double-click save, or delayed mutation-response ordering check was performed. Refund accumulation and address version conflicts were not live-tested because this assessment prioritized the browser journey and its backing calls; existing routine unit results are not a substitute for those API assessments. Documentation-only auditing was excluded.

Prioritized residual checks after repairs: controlled lookup and mutation response ordering; rejected-save correction and transport recovery; keyboard Enter/Space behavior and focus during loading; then broader browser/device and administrative API coverage. No claim of exhaustive coverage is made.

Alice's notes and services were restored through the API. Fresh reads show **both Alice and Bob exactly match their original baselines**, including addresses, refund totals and version counters: [cleanup evidence](cleanup.json). No refunds or address-version increments were made. Only the created `journey-run-21` browser session was closed ([close result](browser-close.txt)); no interceptors were installed. Supplied source, tests, requirements and guidance were not edited. Local exploratory scripts and evidence remain here for the team.
