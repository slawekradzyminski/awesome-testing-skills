# Dispatch Desk release assessment

## Session

**Recommendation: hold the customer browser release.** Three confirmed browser defects violate the product brief: an order-switch race permits saving against an order different from the displayed details, rejected instructions report success, and express delivery cannot be reached by ordinary keyboard navigation. Administrative API checks passed within the tested scope.

Assessed 12 September 2026 against the assigned runtime, `http://127.0.0.1:59159`, using the supplied source, requirements and existing tests. Browser: Headless Chromium 152 on macOS, session `journey-run-20`; desktop and 375 × 812 CSS-pixel narrow viewport. No response mocking, external traffic, fixes, or modifications to supplied artifacts. Source fingerprints are in [source-hashes.json](evidence/source-hashes.json). The assessment completed within the six-minute allowance.

This was a bounded assessment, not exhaustive certification. Findings below are observed runtime failures with source corroboration. The intentional 700 ms A100 lookup is a reproduction condition, not a performance defect. Documentation-only issues and production authentication are excluded.

## Findings

### DD-01 — Late order lookup replaces details without changing the save target

- **Type:** functional / data integrity. **Evidence:** confirmed in the browser and backing requests. **Status:** open. **Severity: High.** A customer can save instructions to A200 while the details identify A100 and its address; this compromises the core delivery-editing journey.
- **Preconditions:** Alice's fixture orders; normal server latency; no network manipulation.
- **Minimal reproduction:** Load the desk and select A200. Select A100 and immediately select A200 before A100 finishes loading. Wait about one second. Observe the selector and order details. Enter a distinctive instruction and save; reload and select A200 to inspect persistence.
- **Expected:** The selected order, heading, address, draft and save destination agree, including when lookups finish out of order. This is an explicit Browser experience requirement in [requirements.md](app/requirements.md).
- **Actual:** The selector remained A200, but the heading became “Order A100”, address “10 Oak Street”, and note “Leave with reception”. Saving “Assessment race marker” issued `POST /api/orders/A200/note` and returned 200. Reloading A200 showed that marker. This demonstrates an actual persisted update under mismatched displayed identity, not just a transient loading label. See [screenshot](evidence/order-race.png) and the `out of order lookup`, `save after mismatched lookup`, and `actual target of race save` records plus requests in [browser-results.json](evidence/browser-results.json).
- **Affected users / workaround:** Customers switching orders quickly. Wait for each lookup to finish, and verify selector, heading and address agree before saving. Reload if they disagree. This requires the customer to notice the defect.
- **Repair direction:** In [app.js](app/static/app.js), `readOrder` creates a generation token but never checks it before updating the DOM or enabling controls (lines 5–19). Ignore obsolete lookup responses and bind editable details and saves to the latest resolved selection.
- **Acceptance / retest:** Repeat rapid A200 → A100 → A200 changes with normal latency. After both responses finish, all displayed fields must belong to A200; a saved marker must change only A200. Repeat while a lookup is pending and with the opposite final selection; stale responses must not replace the draft or enable controls for obsolete details. **Not retested after repair; no fix was applied.**

### DD-02 — Rejected delivery instructions display a success message

- **Type:** functional / failure feedback. **Evidence:** confirmed browser response and persisted-state checks. **Status:** open. **Severity: Medium.** Customers receive a false assurance that instructions were accepted and may leave the journey with the previous instructions still active.
- **Preconditions:** A100 loaded with “Leave with reception”.
- **Minimal reproduction:** Enter `LOCKER: 1` and click Save instruction. Observe feedback, then reload.
- **Expected:** The API rejects locker instructions with 422. The browser must display actionable failure feedback, retain the draft for correction, preserve the previous saved instruction, and never claim success, per [requirements.md](app/requirements.md).
- **Actual:** The API returned 422 with “Locker delivery is unavailable; enter another instruction”, but the UI showed “Delivery instruction saved”. The draft remained `LOCKER: 1` until reload; reload showed the unchanged “Leave with reception”. Draft retention and server preservation passed; the false success and missing failure explanation are the defect. Empty instructions also produced the same success message. See [screenshot](evidence/rejected-note.png), the rejected-note records in [browser-results.json](evidence/browser-results.json), and [empty-input follow-up](evidence/browser-followup-results.txt).
- **Affected users / workaround:** Customers entering rejected instructions. Correct the draft to a supported, nonblank instruction, save, and reload to verify persistence; current feedback alone cannot establish success.
- **Repair direction:** The note-save handler in [app.js](app/static/app.js), lines 22–30, parses the response but unconditionally reports success. Check `response.ok` and expose the returned error while preserving the draft and allowing correction.
- **Acceptance / retest:** A locker submission must show the actionable rejection and no success message; an empty submission must show validation feedback. Both must preserve the saved note and editable draft. Correcting to a valid instruction must show success and survive reload. The valid correction/persistence path passed on the current build, but **the defective rejection path remains open; no repair retest.**

### DD-03 — Express delivery is absent from the keyboard tab sequence

- **Type:** accessibility / keyboard interaction. **Evidence:** confirmed keyboard traversal and element inspection. **Status:** open. **Severity: Medium.** Keyboard-only customers cannot choose one of the two required service options.
- **Preconditions:** An order has finished loading; ordinary Tab navigation.
- **Minimal reproduction:** Focus the Order selector and press Tab repeatedly. Focus moves to Delivery instruction, Save instruction, then Use standard delivery, skipping Use express delivery.
- **Expected:** Both service choices and instruction editing must be usable with ordinary keyboard navigation and visible focus, as required by [requirements.md](app/requirements.md).
- **Actual:** Recorded traversal was `note → save → standard → body → order`. Express is a `DIV` with `role="button"` and `tabIndex=-1`, and has only a click listener. It never receives focus through Tab. The other controls have a visible 3 px orange focus outline. See the keyboard record in [browser-results.json](evidence/browser-results.json), [HTML evidence](evidence/index.html.numbered.txt) line 9, and [handler evidence](evidence/app.js.numbered.txt) line 41.
- **Affected users / workaround:** Keyboard-only customers. Pointer activation works, but there is no ordinary keyboard workaround in the supplied UI.
- **Repair direction:** Use a native button for express, retaining the focus styling and proper disabled state while loading.
- **Acceptance / retest:** Tab reaches express with visible focus; Enter and Space activate it and persist express for the selected order. Standard must remain reachable and operable, and loading must prevent premature activation. Pointer express and keyboard standard passed on this build. **Express keyboard access remains open; no repair retest.**

## Coverage and handoff

**Passing evidence:** All four supplied domain tests passed ([test output](evidence/existing-tests.txt)). The independent HTTP assessment made 48 requests and passed 43 explicit checks ([summary](evidence/api-summary.txt), [request/response evidence](evidence/api-results.json), [assessment script](evidence/api-assessment.py)). These covered:

- Alice/Bob list ownership, anonymous read/write denial, cross-owner order read denial, and forbidden note/refund/address writes with Bob's state preserved.
- Service-batch atomicity when a valid first ID is followed by a forbidden or missing order; malformed service inputs.
- Positive integer refund validation, multiple partial refunds, cumulative excess rejection without mutation, exact remaining refund, and rejection after full refund.
- Address type/length/nonblank validation, a valid update with version increment, stale-update rejection, and preservation of the newer address.
- Invalid note types/length/blank inputs, locker rejection with the previous saved note retained, and malformed JSON/non-object rejection.

The browser verified initial A100 details, ordinary A200 selection, successful note and pointer express changes surviving reload, keyboard instruction entry/save surviving reload, and keyboard standard selection. Desktop and narrow layouts were inspected; at 375 px the document width was 375 px, with no horizontal overflow and usable wrapping. Evidence: [desktop](evidence/desktop.png), [full narrow page](evidence/narrow-full.png), [main browser results](evidence/browser-results.json), [follow-up results](evidence/browser-followup-results.txt). Browser scripts are retained beside those results for reproduction.

**Limits and next work:** One Chromium environment only; no Firefox/WebKit, real-device or screen-reader certification. No exhaustive input matrix, concurrent HTTP mutation stress, transport-failure simulation, or pending-save/service-response race exploration. Valid multi-order service mutation was exercised by the supplied domain test, not independently against the runtime. Passing administrative checks do not establish complete API correctness. Prioritize DD-01, then DD-02 and DD-03; add focused browser regression checks using the acceptance criteria before reassessing release readiness.

**Cleanup:** All modified notes and services were restored, and Bob's address was restored. Final readbacks show Alice's orders unchanged from their initial values: [Alice state](evidence/final-alice.json). Bob B100 now has `refunded: 4000` and `version: 3` (originally 0 and 1); these are irreversible through the supported operations and **require the fixture owner's reset**. Bob's address is again “30 Elm Street”, note “Side entrance”, and service “standard”: [Bob state](evidence/final-bob.json). Do not rerun the refund script on this exhausted fixture without owner reset. Only the created `journey-run-20` browser session was closed ([closure evidence](evidence/browser-close.txt)). No product fixes were authorized or applied.
