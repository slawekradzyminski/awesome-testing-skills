# Dispatch Desk administrative API release assessment

## Session

**Recommendation: hold release of the administrative API until F01–F03 are repaired and retested.** Three confirmed state-integrity defects violate explicit business requirements: over-refunding, lost address updates, and non-atomic service batches. Routine tests pass but do not cover these failure paths.

Assessed on 2026-09-12 against the assigned runtime, `http://127.0.0.1:58282`, using only this candidate's source, existing tests, requirements and HTTP calls. Fixture identities were selected through `X-Test-User`; this is the specified demo identity mechanism. Supplied artifacts are identified by SHA-256 in [source-manifest.json](source-manifest.json); no runtime build identifier was exposed, so exact runtime/source equivalence is not independently established. Runtime results corroborate the relevant source paths.

Scope: order visibility, administrative refunds, address updates, service batches, note validation and persistence, malformed input, and state preservation on rejection. No supplied source, tests, requirements or guidance were changed. No external services, delegation or browser sessions were used. Browser journeys, production authentication, real payments, performance SLAs and documentation defects were outside this assessment.

Executed **83 API requests**, zero browser actions, and four existing unit tests. The HTTP harness recorded 84 assertions: 77 passed and seven failed assertions support the three findings below; these counts are not a measure of complete coverage. See [summary.json](summary.json), [checks.json](checks.json), [existing-tests.txt](existing-tests.txt), and the complete [HTTP request/response log](http.jsonl). Evidence and reporting were completed within the six-minute assessment budget.

## Findings

### F01 — Repeated refunds can exceed the original payment

- **Type:** financial state integrity. **Evidence:** confirmed through HTTP and persisted readback. **Status:** open. **Severity: High.** A caller can record more refunded money than was paid, breaking the central refund invariant. No real payment transfer was tested or claimed.
- **Precondition:** Alice's A100 has `paid: 10000`, `refunded: 0` on a fresh fixture.
- **Minimal reproduction:** With `X-Test-User: alice`, POST `/api/orders/A100/refund` with `{"amount":6000}`, then `{"amount":4000}`, then `{"amount":1}`. GET `/api/orders/A100`.
- **Expected:** The first two refunds succeed; the last returns 409 and leaves `refunded` at 10000. Basis: the refund requirement explicitly caps cumulative refunds at the original payment and requires no further refund on rejection.
- **Actual:** All three POSTs returned 200; the last response and subsequent GET showed `paid:10000, refunded:10001`. [Requests 52–55](reproductions.md#request-52-refund-first-partial) show the complete sequence. A standalone request for 10001 cents correctly returned 409 earlier, demonstrating that the missing check is cumulative.
- **Affected users / workaround:** Any customer order with previous refunds. Suspend repeated refunds or serialize them behind a trusted remaining-balance check until repaired; a client-side check alone cannot enforce this under concurrent requests.
- **Repair direction:** In `app/domain.py:33`, compare the amount with `paid - refunded`, with validation and mutation in the same critical section. The current code only compares each request with `paid`.
- **Acceptance criteria:** Partial refunds totaling exactly the payment succeed; the next positive cent returns 409 and preserves the total. Requests individually exceeding the payment still return 409. Concurrent refunds whose sum exceeds the remaining balance cannot both succeed. Preserve rejection of zero, negative, noninteger and boolean amounts.
- **Retest:** Not performed after repair; no product fixes were authorized. Sequential runtime failure confirmed; concurrent refund behavior remains untested.

### F02 — Stale address edits overwrite newer saved addresses

- **Type:** concurrency control / data loss. **Evidence:** confirmed through HTTP and persisted readback. **Status:** open. **Severity: High.** An ordinary second editor with an older snapshot silently replaces a newer delivery address, creating a delivery correctness risk.
- **Precondition:** Alice's A200 is at version 1; two editors hold that version.
- **Minimal reproduction:** POST `/api/orders/A200/address` with `{"address":"Current dispatch address","version":1}`. Then submit `{"address":"Stale dispatch address","version":1}` with the same Alice header. GET `/api/orders/A200`.
- **Expected:** First save returns 200 and version 2. Second save returns 409, retaining `Current dispatch address` and version 2. Basis: saves are allowed only when the supplied version matches; stale edits must preserve the newer address.
- **Actual:** First save returned version 2. Stale save returned 200, changed the address to `Stale dispatch address`, and advanced the version to 3. GET confirmed both changes. [Requests 56–58](reproductions.md#request-56-address-editor-one-saves). A future version was separately rejected with 409.
- **Affected users / workaround:** Customers or administrators editing the same order from multiple tabs or sessions. Restrict address editing to one active editor per order as an interim operational measure. Refreshing immediately before saving reduces but does not eliminate the race.
- **Repair direction:** In `app/domain.py:45`, reject every version unequal to the stored version. Keep the comparison and save atomic. The current condition rejects only greater versions.
- **Acceptance criteria:** Exact current version succeeds and increments once. Lower and higher versions return 409 with address and version unchanged. Two saves using the same initial version produce one success and one conflict, including concurrent submissions.
- **Retest:** Pending repair. Sequential competing-editor scenario confirmed; simultaneous submissions were not exercised.

### F03 — Failed service batches leave earlier orders changed

- **Type:** transaction atomicity. **Evidence:** confirmed for both missing and forbidden order IDs, with persisted readback. **Status:** open. **Severity: Medium.** A failed administrative operation silently changes part of the requested delivery service selection, leaving callers unable to rely on the failure response. Foreign order access itself remained denied.
- **Precondition:** A200 uses `standard`; Alice does not own B100; `MISSING` does not exist.
- **Minimal reproduction:** As Alice, POST `/api/services` with `{"ids":["A200","MISSING"],"service":"express"}`. After the 404 response, GET `/api/orders/A200`. Restore `standard` and repeat with `["A200","B100"]`, which returns 403.
- **Expected:** Respectively return 404 or 403 and leave every order unchanged. Basis: the service batch requirement explicitly mandates all-or-nothing behavior for missing or forbidden members.
- **Actual:** Both failing batches changed A200 to `express` despite the error response. [Requests 60–61](reproductions.md#request-60-f03-mixed-batch-missing) and [65–66](reproductions.md#request-65-f03-mixed-batch-forbidden). Putting the invalid ID first preserved A200, demonstrating input-order dependence. B100 remained fully unchanged.
- **Affected users / workaround:** Callers submitting batches with an invalid, unavailable or unauthorized order later in the list. Temporarily avoid mixed batches; single-order calls limit the partial-update problem but do not provide batch atomicity. If a batch fails, reread all accessible members before reconciling state.
- **Repair direction:** In `app/domain.py:56–63`, resolve and authorize the entire selection before mutating any row. Remove the assignment during validation at line 60; commit only after all entries pass, within the existing lock.
- **Acceptance criteria:** Mixed valid/missing and valid/forbidden batches return the required error and preserve all orders regardless of member order. Test invalid members at beginning, middle and end. A fully valid batch updates all selected orders; both supported services continue to work.
- **Retest:** Pending repair. Both failure variants and reversed-order controls were verified on the supplied runtime.

## Coverage and handoff

Verified passing behavior:

- Existing four tests: single partial refund, current-version address save, valid service batch, and locker-note rejection.
- Alice and Bob list only their own orders. Cross-customer GET, refund, address, note and single-order service requests return 403 in both directions; before/after lists confirm no mutation. Missing and unknown fixture identity calls return 401 on list and representative mutation routes.
- Invalid refund types, zero/negative amounts and an individually excessive refund are rejected. Missing-order refund, address and note routes return 404.
- Blank, nonstring and overlength addresses; missing, boolean and string versions; malformed service selections; blank, nonstring and overlength notes are rejected with 400. Malformed JSON, nonobject JSON, empty bodies and oversized bodies also return 400. Readback after the rejection matrix showed Alice's state unchanged.
- A 120-character address, 1- and 160-character notes, and a valid two-order express batch succeed. Later GETs confirm persisted values. Both service values were exercised during updates and restoration.
- `LOCKER:` instructions, including whitespace and lowercase variants, return 422. Rejection after saving a 160-character note preserves that note.

Limitations and next work: This was a bounded source-informed API assessment, not exhaustive testing. No simultaneous request races, load, transport fuzzing, process-restart persistence or browser behavior were tested. Add focused regression tests for F01–F03 to the supplied suite, then retest the repaired runtime, including simultaneous refund/address requests and all batch failure positions. API/domain maintainers should own the repairs; release validation should verify rejection responses **and subsequent stored state**.

Cleanup: Address text, notes and services were restored to their initial values. Bob's entire fixture is unchanged. Final owner-read snapshots are in [final-state.json](final-state.json), with initial values in [baseline.json](baseline.json). **Owner restart/reset is still required:** A100's `refunded` changed from 0 to **10001 cents**, and A200's version changed from 1 to **5**, including restoration of its address. These cannot be restored through the supplied API. No reset route was attempted. No browser session requires closing.

Supporting harness: [assess_api.py](assess_api.py) and [reproductions.md](reproductions.md). The harness expects a fresh fixture and mutates refund totals and version counters; use the recorded evidence now, and reset the instance before a later rerun. Findings remain open; no source repair or post-fix retest occurred.
