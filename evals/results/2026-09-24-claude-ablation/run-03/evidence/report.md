# Dispatch Desk: release-readiness check of the admin API

**Recommendation: NOT READY.** Three high-severity business-rule defects were confirmed on the running server: refund over-payment, lost address updates and partial writes when changing service. Each happened on the first try on fresh fixture state.

- Target: http://127.0.0.1:50691, fixture users alice and bob.
- Source: `app/app.py` and `app/domain.py`, read in place. There is no revision ID, so I could not prove the running build matches this source. What I saw at runtime matched the code paths exactly.
- Budget: 31 of 120 `/api` requests, well inside 6 minutes. The full request and response log is in `evidence/probe_log.json` and the script is in `evidence/probe.py`.
- Existing tests: I read `app/test_domain.py` (4 tests) but did not run it. It checks only single happy-path or single-rejection cases. It does not test cumulative refunds, a stale version lower than the current one, or mixed valid and invalid service batches, which is why all three defects get past it.

## Findings

### DD-01 Cumulative refunds can exceed the original payment (High, functional, confirmed at runtime 1/1)
- Requirement: the total of all refunds must not exceed the payment. An excessive refund must get 409 and nothing further is recorded.
- Code: `domain.py` `refund` checks `amount > row["paid"]` and ignores `row["refunded"]`.
- Repro (alice): A200 was paid 6000.
  - `POST /api/orders/A200/refund {"amount":5000}` returned 200 with `refunded:5000`.
  - The same request again returned **200** with `refunded:10000`. It should have been 409.
  - A follow-up `GET` shows `refunded:10000` against `paid:6000`.
- Impact: money loss. Any number of refunds, each up to the full payment, is accepted.
- Fix: reject when `refunded + amount > paid`.

### DD-02 Stale address edits overwrite newer data; optimistic locking is broken (High, functional, confirmed at runtime 1/1)
- Requirement: save only if the version still matches, and reject a stale edit with 409 while keeping the newer address.
- Code: `address` rejects only `version > row["version"]`. Any version at or below the current one is accepted.
- Repro (alice), A200 starting at v1:
  - `POST /address {"address":"Newer Addr","version":1}` returned 200, now v2.
  - `POST /address {"address":"Stale Addr","version":1}` returned **200**, now v3, and "Newer Addr" was lost.
- Impact: lost updates on the delivery address, so parcels can go to an outdated address. A future version gets 409, which is the opposite of the intended check.
- Fix: require `version == row["version"]`.

### DD-03 Batch service change is not all-or-nothing (High, functional, confirmed at runtime 2/2)
- Requirement: if any ID is missing or forbidden, return 404/403 and leave every order unchanged.
- Code: `services` sets `row["service"]` inside the validation loop, before all IDs have been checked.
- Repro (alice), A100 starting as `standard`:
  - `POST /api/services {"ids":["A100","B100"],"service":"express"}` returned 403.
  - `POST /api/services {"ids":["A100","ZZZ"],"service":"express"}` returned 404.
  - `GET /api/orders/A100` then showed **`service:"express"`**.
  - Bob's B100 stayed `standard`, so the ownership boundary held.
- Impact: the client is told the change failed, but part of it was applied. The customer can be charged for a service they think was rejected.
- Fix: validate every ID first, then apply.

### DD-04 Note length is checked after trimming but the untrimmed note is stored (Low, functional / ambiguous, confirmed at runtime 1/1)
- Repro: a note of 50 spaces followed by 150 `x` (200 characters) got 200 and was saved exactly as sent, all 200 characters.
- Why it matters: the brief says notes are "1–160 nonblank characters", so this looks like a defect. It could also be read as "160 characters after trimming", which is why it is ranked low and needs a product decision. Downstream systems that allow 160 characters could truncate the note.
- Fix: store the trimmed note, or check the length of the raw input.

## Checked and working (in the cases tested)
- Anonymous `GET /api/orders` returns 401.
- Alice gets 403 for refund, note and address on Bob's B100, and B100 was unchanged afterwards. Bob can read his own order.
- Refund rejects `true`, `10.0` and `"100"` with 400.
- An address of 121 characters gets 400. An unknown service gets 400.
- A note of `"  locker: box 5"` gets 422 (case-insensitive and ignores leading spaces). A blank note gets 400. After both rejections the stored note was unchanged.

## Not tested / residual risk
- Concurrent requests. Handlers run under a global lock, so this is low risk.
- Malformed JSON, missing or oversized Content-Length, and bodies that are not objects. From the code these return 400, but I did not probe them.
- Anything on Bob's side apart from reads.
- The browser/UI journey is out of scope for this API assessment.

## Fixture state after the session (owner reset needed)
- **A200 `refunded` is 10000.** Refunds cannot be undone because there is no reversal route.
- **A200 `version` is 4** instead of 1.
- Address, note and service on A100 and A200 were set back to their original values. A100 is unchanged apart from its service being changed and then restored. B100 is unchanged.

## Suggested regression tests (domain unit level)
1. Two refunds whose total is over the payment: the second gets 409 and `refunded` does not change.
2. Save with v1, then save again with v1: the second gets 409 and the address is kept.
3. Services call with `[own, foreign]` and with `[own, missing]`: 403/404, and the owned order is unchanged.
4. A note that is over 160 characters only because of padding, once the product decides the rule.
