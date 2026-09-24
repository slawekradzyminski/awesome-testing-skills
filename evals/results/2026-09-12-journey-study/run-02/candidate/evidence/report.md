# Dispatch Desk administrative API release assessment

## Session

**Recommendation: hold release.** Three confirmed defects violate required financial and data-integrity guarantees: refunds exceed the original payment, stale address saves overwrite newer data, and rejected bulk service requests partially commit changes.

Assessed the supplied Python source, business requirements and existing tests against **http://127.0.0.1:55995**, on 12 September 2026 (UTC). Build identity is captured by [source hashes](build-context.json). Only the assigned runtime and candidate directory were used. No application source, supplied tests or requirements were edited; no fixes were applied.

The assessment used **89 API requests and zero browser actions**. All four existing domain tests passed. The additional assessment made 93 assertions: 86 passed and seven failed, representing the three independent defects below, not seven bugs. See [test output](existing-tests.txt), [assessment results](results.json), [HTTP transcript](http-transcript.jsonl), and [assessment script](assess_api.py). The script mutates disposable fixtures and expects an owner reset before reuse; it also replaces its output files.

Scope was administrative API operations, including their backing note endpoint. Browser journeys, rendering, accessibility, real payments and production authentication were not assessed. `X-Test-User` is the explicitly supported fixture identity mechanism. No actual money movement or production exploit is claimed.

## Findings

### F-01 — Cumulative refunds can exceed the original payment

**Type:** functional / financial integrity. **Evidence:** confirmed through HTTP and persisted readback. **Status:** open. **Severity: High.** The API records more refunded cents than were paid, violating the core refund ceiling; repeated individually allowed requests can continue increasing the total according to the source.

**Preconditions:** Alice owns A200, initially `paid: 6000`, `refunded: 0`. Use `X-Test-User: alice` and JSON bodies.

**Minimal reproduction:**

1. `POST /api/orders/A200/refund` with `{"amount":5000}` → 200, `refunded: 5000`.
2. Repeat with `{"amount":1000}` → 200, `refunded: 6000`.
3. Repeat with `{"amount":1}` → **200, `refunded: 6001`**.
4. `GET /api/orders/A200` confirms the excessive total persists.

**Expected:** The third request returns 409 and leaves `refunded` at 6000. The [refund requirement](../app/requirements.md) explicitly limits cumulative refunds to the original payment. **Actual:** The total becomes 6001; an individually excessive request of 6001 does return 409, showing that only the single-request ceiling is checked. [Requests 62–66](F-01-refund.md).

**Affected users and impact:** Customers and administrators issuing multiple partial refunds. Demonstrated impact is an over-refunded fixture ledger by one cent; real payment processing is out of scope. No reliable API-enforced workaround exists. Temporarily suspend repeated refunds or serialize and reconcile them through a single trusted operator; client prechecks alone cannot guarantee correctness.

**Repair direction:** In [domain.py](../app/domain.py), lines 26–36, compare the amount against `paid - refunded` within the existing mutation lock, before recording it.

**Acceptance criteria:** Multiple valid partial refunds up to exactly the paid amount succeed; any request taking the total above it returns 409 with the complete order unchanged. Verify a positive remaining balance exceeded by one cent, zero remaining balance, and competing refund requests. Invalid amounts continue returning 400.

**Retest:** Not fixed or retested against a repair. Current behavior reproduced and confirmed by readback.

### F-02 — Stale address versions overwrite newer addresses

**Type:** functional / lost-update protection. **Evidence:** confirmed through HTTP and persisted readback. **Status:** open. **Severity: High.** An ordinary delayed save can silently replace a customer's newer delivery destination and reports success.

**Preconditions:** Alice owns A200; two clients have read version 1. Sequential requests with the same version reproduce this without timing dependencies.

**Minimal reproduction:**

1. `POST /api/orders/A200/address` with `{"address":"Assessment newer address","version":1}` → 200, version 2.
2. Submit the other client's stale edit: `{"address":"Assessment stale overwrite","version":1}` → **200, version 3**.
3. `GET /api/orders/A200` returns `Assessment stale overwrite`, version 3.

**Expected:** The second save returns 409, preserving the newer address and version 2. The [address requirement](../app/requirements.md) permits saving only when the submitted version matches the current one. **Actual:** A lower version succeeds; a future version is rejected correctly. [Requests 67–70](F-02-address.md).

**Affected users and impact:** Customers or administrators editing an address from multiple clients, tabs or old reads. Loss of the newer address is demonstrated; misdelivery is a possible downstream consequence, not an observed shipment. A single designated editor reduces exposure, but reload-before-save alone cannot eliminate a competing write.

**Repair direction:** In [domain.py](../app/domain.py), lines 38–49, reject every version unequal to the stored version, maintaining comparison and update under the existing lock.

**Acceptance criteria:** A matching version saves and increments exactly once. Lower and higher versions return 409 with address and version unchanged. When two edits submit the same starting version, exactly one succeeds. Preserve integer-type validation.

**Retest:** Not fixed or retested against a repair. Current behavior reproduced and confirmed by readback.

### F-03 — Failed bulk service changes leave earlier orders modified

**Type:** functional / transaction atomicity. **Evidence:** confirmed for both missing and forbidden later IDs. **Status:** open. **Severity: Medium.** A reported failure silently changes eligible orders, leaving a partially applied delivery-service selection. No change to another customer's order was observed.

**Preconditions:** Alice's A100 uses `standard`; B100 belongs to Bob; `MISSING` does not exist. Use Alice's fixture identity.

**Minimal reproduction:**

1. `POST /api/services` with `{"ids":["A100","MISSING"],"service":"express"}` → 404.
2. `GET /api/orders` shows **A100 now uses `express`**.
3. Restore A100 to `standard` with a valid single-order request.
4. Repeat the first request with IDs `["A100","B100"]` → 403; another read again shows A100 changed to `express`.

**Expected:** Each failed request leaves every order unchanged, as explicitly required by the [bulk service requirement](../app/requirements.md). **Actual:** The endpoint returns the expected error status while retaining an earlier mutation. [Requests 74–79](F-03-services.md). Final Bob readback confirms B100 remained unchanged.

**Affected users and impact:** Customers and administrators submitting batches containing an inaccessible or nonexistent later item. The demonstrated impact is an unintended service change despite failure feedback. As a temporary mitigation, re-read every requested eligible order after a failed batch and reconcile changes; a sequence of single-order requests does not provide the required atomic batch guarantee.

**Repair direction:** In [domain.py](../app/domain.py), lines 51–64, resolve and authorize the entire selection before changing any row; keep validation and mutation together under the existing lock.

**Acceptance criteria:** Missing or forbidden IDs at the beginning, middle and end return 404 or 403 with all orders unchanged. Valid multi-order batches update every selected order together. Foreign orders remain unchanged and inaccessible.

**Retest:** Not fixed or retested against a repair. Both failure variants independently reproduced and read back.

## Coverage and handoff

**Passed checks:**

- Four supplied routine domain tests, run with `python3 -m unittest discover -s app -v`.
- Alice/Bob listing isolation; anonymous and unknown identities rejected with 401 for listing, detail and all mutation routes.
- Both directions of foreign-order access rejected with 403 for detail, refund, address, note and single-order service requests. Missing detail/refund/address/note targets returned 404. Full state snapshots confirmed authorization attempts changed nothing.
- Malformed JSON, non-object JSON and empty request bodies returned 400 on the refund endpoint. Refund null, boolean, zero, negative, fractional and string amounts were rejected.
- Blank, non-string and overlength addresses and non-integer versions rejected; a 120-character address saved. A future version returned 409.
- Empty/malformed service ID selections and unsupported service values rejected. A valid two-order express change succeeded; standard restoration succeeded.
- Blank, non-string and overlength notes rejected. One- and 160-character notes saved. `LOCKER:` and a whitespace-prefixed lowercase variant returned 422; readback after rejection preserved the previous saved 160-character note.
- Full snapshots before and after invalid-input checks showed no mutations. Successful edits and the three faulty mutations were verified using subsequent API reads.

**Limitations and next work:** No browser session was created. Browser race handling, feedback, keyboard use and layouts remain outside this administrative API assessment. Concurrent request stress, transport framing/oversized-body boundaries, exhaustive Unicode/whitespace boundaries, and invalid batch IDs in every position were not exercised. These are coverage gaps, not asserted defects. No external services were contacted. Prioritize the three repairs and add regression tests for the stated acceptance criteria; retain the existing passing checks. The current routine tests omit cumulative refunds, stale versions and mixed-validity batch failures.

**Cleanup:** Addresses, notes and services were restored and verified for all fixtures. A100 and B100 match their initial states. **Owner reset remains required for A200:** `refunded` changed from **0 to 6001 cents**, and `version` from **1 to 5**. These cannot be restored through the documented API. Compare [initial state](initial-state.json) with [final state](final-state.json). No browser cleanup is needed. No product fixes, issue filing or delegation were performed.
