**Release recommendation: hold the administrative API release.** Three confirmed high-priority defects violate explicit financial integrity, address concurrency, and bulk atomicity requirements. Each was reproduced against the assigned runtime and verified using subsequent reads. No product fixes were made.

Assessment performed on 2026-09-12 against `http://127.0.0.1:55994`, using only the supplied candidate source, requirements, existing tests, and that runtime. There were 92 API requests and zero browser actions. The four existing unit tests passed. The assessment recorded 132 assertions: 125 passed and seven failed, representing the three defects below; these counts include status and state assertions, not 132 independent scenarios.

**F1 — High / release blocker: cumulative refunds can exceed the original payment.**

Precondition: Alice's A100 has `paid: 10000` and `refunded: 0`. With `X-Test-User: alice`, send these requests to `POST /api/orders/A100/refund`:

1. `{"amount":6000}` → 200, refunded 6000.
2. `{"amount":4000}` → 200, refunded 10000.
3. `{"amount":1}` → **200, refunded 10001**.

The third request must return 409 and leave the cumulative refund at 10000. A subsequent order-list read confirms the excessive total persisted. This permits over-refunding; the source also indicates that further positive requests no larger than the original payment would continue to accumulate, although that additional repetition was unnecessary to reproduce the defect.

Evidence: [HTTP transcript](http.json), request IDs 47–51; [failed assertions](checks.json), names beginning `F1`. In [domain.py](../app/domain.py), lines 33–35 compare the new amount with the original payment without subtracting refunds already recorded.

Recommended repair: reject when `amount > paid - refunded`, keeping the check and increment in the same protected operation. Add regression cases for several partial refunds, exact exhaustion, one cent over the remaining balance, and unchanged state after rejection. Include simultaneous refund attempts in release verification to ensure the invariant remains protected under concurrent requests. The existing single-partial-refund test does not exercise accumulation.

**F2 — High / release blocker: stale address edits overwrite newer data.**

Precondition: Alice's A200 is at version 1. With Alice's header, send to `POST /api/orders/A200/address`:

1. `{"address":"New address from current editor","version":1}` → 200, saved address and version 2.
2. `{"address":"Stale editor overwrite","version":1}` → **200, stale address saved and version 3**.

The second request must return 409, retain the first address, and retain version 2. Subsequent reads show the stale address persisted. Two editors using the same previously read version can silently lose the newer change, potentially redirecting delivery to an obsolete address. This sequential replay reproduces the stale-editor failure without requiring a timing-sensitive race.

Evidence: [HTTP transcript](http.json), request IDs 52–55; [failed assertions](checks.json), names beginning `F2`. In [domain.py](../app/domain.py), line 45 rejects only versions greater than the saved version, accepting older ones. A future-version request did correctly return 409 in request 56.

Recommended repair: require exact equality between supplied and current versions before changing either the address or version. Add tests for current, older, and future versions, asserting complete preservation after rejected saves; exercise two saves based on the same read. The existing address test covers only the first successful edit.

**F3 — High / release blocker: failed bulk service requests partially change orders.**

Precondition: A200 uses `standard`. As Alice, call `POST /api/services` with `{"ids":["A200","MISSING"],"service":"express"}`. The response is 404, but a subsequent read shows A200 now uses **express**. After restoring standard, repeat with `{"ids":["A200","B100"],"service":"express"}`. The response is 403, and A200 again changes to **express**. Bob's B100 remains unchanged.

The errors are appropriate, but both requests must leave every order unchanged. A caller receiving failure cannot safely infer that nothing was saved. Putting the invalid or foreign ID first preserved state in both tested cases, confirming that behavior depends on list order.

Evidence: [HTTP transcript](http.json), IDs 57–74 cover before/after reads, both reproductions, restoration, and reversed-order controls. Specifically, failed writes are requests 59 and 68; persisted partial changes appear in 60 and 69. [Failed assertions](checks.json) begin `F3`. In [domain.py](../app/domain.py), line 60 mutates an order while the validation loop is still checking subsequent IDs.

Recommended repair: resolve and authorize the entire selection before mutating any order, with validation and commit under the existing server lock. Remove the mutation from the validation loop. Add missing-ID and foreign-ID tests with invalid entries at the beginning, middle, and end; assert every order remains identical after failure. The existing bulk test covers only an entirely valid selection.

**Passing evidence and coverage limits.**

- Anonymous list/detail reads and all four write operations returned 401. Alice and Bob were denied foreign detail reads and every foreign write operation with 403; full snapshots confirmed no changes from these denied operations. Lists contained only the caller's orders.
- Malformed JSON, non-object JSON, and empty bodies returned 400. Tested refund validation rejected null, boolean, zero, negative, fractional, and string amounts; a single amount exceeding the original payment returned 409 without changing state.
- Address validation rejected missing fields, blank and 121-character addresses, and boolean/string versions. Service validation rejected missing fields, an empty ID list, an unsupported service, and mixed-type IDs. Full snapshots remained unchanged after these invalid-input checks.
- Valid bulk express selection persisted for both Alice orders. Notes of lengths 1 and 160 persisted through subsequent reads; null, empty, blank, and 161-character notes were rejected. `LOCKER:` and whitespace-prefixed lowercase `locker:` instructions returned 422 and preserved the previously saved note.
- [Existing test output](existing-tests.txt) shows all four supplied tests passing despite the release blockers. [Assessment script](assess_api.py), [assertions](checks.json), and [run summary](run-summary.json) provide reproducible evidence. The script expects fresh fixture data and performs irreversible refunds; do not rerun against the current fixture without an owner reset.

This assessment covers administrative API behavior. Browser journeys, layout, keyboard access, and UI response ordering were not assessed. No browser session was created. Concurrent requests were not dynamically exercised; source inspection shows a server lock around domain operations, but the reproduced business-rule defects occur even with sequential requests. Validation coverage is targeted, not exhaustive. Production authentication, actual payments, external integrations, and documentation-only defects were outside scope.

**Fixture restoration and release follow-up.** All addresses, notes, and services were restored to their initial values and verified through final reads. Two persistent differences require the fixture owner's reset: A100 `refunded` changed from **0 to 10001 cents**, and A200 `version` changed from **1 to 4** (including the restoration save). B100 is unchanged. See [baseline](baseline.json), [final state](final-state.json), and [remaining changes](remaining-changes.json).

Before release, repair F1–F3, add the stated regression tests, and repeat the affected HTTP scenarios on a fresh fixture. Acceptance requires rejection without mutation for cumulative excessive refunds, stale address saves, and every invalid bulk selection ordering.
