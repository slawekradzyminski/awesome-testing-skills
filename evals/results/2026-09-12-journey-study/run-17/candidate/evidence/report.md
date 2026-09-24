# Dispatch Desk release assessment

## Session

**Recommendation: fix DD-001 before release.** The main customer journey and tested API safeguards passed, but overlapping service saves can display a service that differs from the stored order while claiming success. This is a confirmed Medium defect, reproduced twice under controlled response ordering.

Assessed on 12 September 2026, approximately 11:16–11:21 UTC, against the supplied source in `app/` and the assigned runtime `http://127.0.0.1:58576`. Browser: headless Chromium 152 on macOS, session `journey-run-17`; desktop and 320px-wide layouts. Context: product requirements, server/domain implementation, frontend, four supplied routine tests, and report template. No source, tests, requirements, or guidance were changed. No external application traffic or delegation was used.

This was a time-boxed assessment, not exhaustive certification. The core HTTP suite made 43 requests; cleanup made five, with additional browser backing calls remaining within the 120-request budget. Browser interactions remained within the 80-action budget. Evidence scripts are assessment artifacts, not additions to the supplied test suite. Re-running the API script mutates refunds and version counters; use a fresh fixture.

## Findings

### DD-001 — A late service-save response overwrites the displayed result of a newer save

- **Type:** Functional correctness / asynchronous browser state.
- **Evidence state:** Confirmed in the assigned runtime; reproduced twice using actual server responses with controlled delivery delay.
- **Status:** Open; no product fix applied.
- **Severity:** **Medium.** Customers who change service again while a save is pending receive a false view of their delivery arrangement. The displayed service and success feedback disagree with persisted data. No payment loss or cross-customer mutation was demonstrated.

**Preconditions and minimal reproduction**

1. Open Alice's A100 and wait for its details to load.
2. Delay delivery of the response to an Express service save by 900ms, while forwarding the request to the real server unchanged.
3. Click **Use express delivery**. After the server has saved Express, but before its response reaches the page, click **Use standard delivery** (100ms later in the reproduction).
4. Allow the Standard response to arrive first, followed by the delayed Express response.
5. Observe the service and feedback, then reload A100.

**Expected:** The displayed service and save feedback remain consistent with the final stored service, including when saves overlap. The product brief requires consistent order details and successful edits that survive reloading. In this reproduction the server processes Express then Standard, so the settled page should display Standard.

**Actual:** Both requests return 200. Standard is stored and its response arrives first. When the earlier Express response arrives, the page changes the service to `express` with `Delivery service saved`. Reloading displays `standard`. The captured response bodies establish the server's write order; this is not an inferred failure from a screenshot alone.

Evidence: [first reproduction and request/response chronology](service-race-results.txt), [independent repeat](service-race-repeat.txt), [page showing the incorrect service](service-race-before-reload.png), [reproduction script](service-race.js). The script delays only delivery of an unchanged real response; it does not fabricate response data. Reproduction under unmodified natural network timing was not established.

**Affected users / workaround:** Customers making successive service choices before prior feedback completes. Wait for each save to finish before making another selection; reload to verify the stored service after overlapping saves.

**Implementation pointer and suggested repair:** `app/static/app.js`, lines 38–45, checks only whether the order ID is still selected before applying each response. Both service buttons remain available while requests are pending. Serialize service changes, or track mutation order and reconcile the displayed result with server state. Ensure the approach also handles the server receiving writes out of order; merely suppressing an old response may not solve that case.

**Acceptance criteria:** Under delayed and reordered service responses, rapid Express → Standard changes must settle with the UI matching the persisted order; reload must preserve the displayed service. If changes are serialized, a pending save must prevent a competing service request with clear pending feedback. Verify the reverse choice order and switching orders during a pending service save. Existing keyboard operation and sequential persistence must remain working.

**Retest:** Original behavior reproduced twice. Fix verification pending.

## Coverage and handoff

### Checked and passed

| Area | Evidence and result |
| --- | --- |
| Existing routine tests | [Four tests passed](unit-tests.txt): refund, address, batch service, locker-note rejection. These alone do not exercise browser behavior. |
| Customer isolation | Alice/Bob order lists; anonymous list and mutation rejection; Alice denied Bob's read, refund, address and note operations; Bob's order unchanged after forbidden operations. |
| Refund integrity | Invalid types, boolean, zero and negative amounts rejected; two partial refunds accumulate; excessive cumulative refund returns 409 and preserves the total. |
| Address concurrency | Successful save increments version; stale save returns 409 and preserves newer address; blank, overlong and boolean-version inputs rejected. |
| Batch service atomicity | Valid batch persists for both Alice orders; allowed order followed by forbidden or missing order rejects without partial change; invalid/empty service inputs rejected. |
| Note and request validation | Blank/overlong notes rejected; locker prefix, including case/leading-space variant, rejected without changing saved note; malformed JSON and non-object bodies rejected. |
| Browser order switching | Natural delayed A100 lookup completes after A200; A200 selection/details stay consistent and subsequent note save targets A200. Saving is disabled while the lookup is pending. |
| Browser note recovery/persistence | Valid A200 edit survives reload, A100 is unchanged; locker rejection retains draft and actionable error without success claim; reload reveals prior saved note. |
| Keyboard and layout | Tab order reaches selector, editor, save, Express and Standard with 3px visible focus; both services activate via keyboard; Express persists reload. Note editing and saving also completed by keyboard at 320px. Narrow screenshot shows readable, stacked controls without horizontal overflow. |

Detailed results: [41 passing HTTP checks with requests and responses](api-results.json), [HTTP script](api-checks.py), [14 passing main browser checks](browser-results.txt), [browser script](browser-checks.js), [keyboard note save](keyboard-edit.txt), [rejection screenshot](rejected-note.png), [narrow layout and keyboard focus](narrow-keyboard.png). Screenshots were visually inspected for the narrow layout. The later console capture reported no messages; it is not a complete session-wide console audit.

### Limits and useful next work

Firefox, WebKit, physical mobile devices, screen-reader behavior, concurrent administrative writes, exhaustive validation boundaries, transport failures, and all permutations of overlapping note/service saves were not tested. No claim of complete accessibility or production security coverage is made. Those excluded production concerns are not findings.

Prioritize DD-001 with frontend ownership and a regression test that controls response order. Then exercise pending saves while switching away from and back to the same order, and network-failure recovery. The supplied routine tests passing should not substitute for these browser checks.

One initial attempt at the service-delay harness failed because `setTimeout` is unavailable in the CLI execution sandbox. The local harness was corrected to use Playwright's wait method; the subsequent two reproductions completed. This harness error is not a product defect.

### Cleanup

All fixture notes, services, and addresses were restored to their initial values and verified through final order lists. **Owner reset is still required for B100: `refunded` is 2000 cents (initially 0), and `version` is 3 (initially 1).** Refunds are irreversible through the supplied API; restoring the address increments its version. Alice's final orders match the initial fixture. See [initial state](initial-state.json) and [cleanup requests, final state and remaining differences](cleanup-results.json).

Only the created browser session, `journey-run-17`, was closed. The temporary response route was removed before final checks. No external issues were filed or product fixes made.
