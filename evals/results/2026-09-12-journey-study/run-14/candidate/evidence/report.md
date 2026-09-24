**Release recommendation: hold the administrative API release.** Three confirmed defects violate required money, concurrency-control, and bulk-update invariants. All reproduce with ordinary sequential HTTP requests; none requires browser timing or production authentication. Fix all three and add regression coverage before release.

Assessed the supplied `app/requirements.md`, `app/domain.py`, `app/app.py`, and existing tests against `http://127.0.0.1:58128` on 2026-09-12. Used 76 API requests and zero browser actions, within the assigned limits. Supplied source, tests, requirements, and guidance were not edited. The four existing unit tests pass; the assessment recorded 72 checks, with 66 passing and six failed assertions representing the three defects below. Passing routine tests therefore do not establish release readiness.

**1. High — cumulative refunds exceed the original payment.**

Starting with Alice's A100 at `paid=10000, refunded=0`, send these JSON bodies in sequence to `POST /api/orders/A100/refund`, with `X-Test-User: alice` and `Content-Type: application/json`:

1. `{"amount":6000}` returns 200 with `refunded=6000`.
2. `{"amount":4000}` returns 200 with `refunded=10000` (the exact permitted total).
3. `{"amount":1}` incorrectly returns 200 with `refunded=10001`.
4. `GET /api/orders/A100` confirms that the excessive total persisted.

Expected: step 3 returns 409 and leaves `refunded=10000`. Actual: an over-refund is recorded. This breaks the financial limit; repeated individually acceptable refunds can continue increasing the total, as inferred from the source. No real payments were exercised.

Evidence: [HTTP transcript](http.jsonl), requests 65–68. A separate request for 10001 cents returns 409 (request 69), showing the distinction between the original-payment check and the missing cumulative check. Root cause: `app/domain.py:33` compares only `amount` against `paid`, then increments `refunded` at line 35. Repair: validate against `paid - refunded` before mutation, within the existing server lock. Regression gate: multiple partial refunds, exact remaining balance, remaining balance plus one cent, refund after full exhaustion, and unchanged total on every rejection. Also exercise concurrent refunds competing for the same remaining balance.

**2. High — stale address versions overwrite newer edits.**

Starting with Alice's A200 at version 1:

1. `POST /api/orders/A200/address` with `{"address":"<120 x characters>","version":1}` succeeds and returns version 2. The exact body is in the transcript.
2. Send `{"address":"Stale overwrite","version":1}` to the same endpoint.
3. The second save incorrectly returns 200, stores `Stale overwrite`, and advances the version to 3; a subsequent GET confirms it.

Expected: step 2 returns 409, preserving the first address and version 2. Actual: a customer working from an older read can silently destroy a newer delivery address, risking incorrect delivery. This sequential test models two clients that both read version 1; simultaneous requests are unnecessary to trigger the defect.

Evidence: [HTTP transcript](http.jsonl), requests 61–63. A future version is correctly rejected with 409 (request 64). Root cause: `app/domain.py:45` rejects only versions greater than the stored version. Repair: reject every unequal version before modifying either the address or counter. Regression gate: equal version succeeds once, stale and future versions return 409 with the complete stored state unchanged, and two saves using the same version produce one success and one conflict.

**3. High — rejected bulk service operations partially mutate orders.**

Starting with A200 on `standard`, as Alice:

1. `POST /api/services` with `{"ids":["A200","MISSING"],"service":"express"}` returns 404.
2. `GET /api/orders/A200` nevertheless reports `service=express`.
3. Restore A200 to `standard`, then send `{"ids":["A200","B100"],"service":"express"}`.
4. That request returns 403, but A200 again changes to `express`. Bob's B100 remains unchanged, verified using Bob's identity.

Expected: both failed operations leave every order unchanged. Actual: an error response conceals a committed service change on the valid prefix of the batch. Callers cannot rely on the promised all-or-nothing operation, potentially leaving delivery arrangements inconsistent. This is an atomicity failure; the test did not show unauthorized modification of Bob's order.

Evidence: [HTTP transcript](http.jsonl), requests 54–60. Root cause: `app/domain.py:60` mutates each row during validation, before later IDs have passed existence and ownership checks. Repair: resolve and authorize the entire selection first, then apply all changes under the existing lock. Regression gate: missing and forbidden IDs at the beginning, middle, and end of batches; verify all affected orders after failure; retain successful standard/express coverage.

**Other evidence and limits.**

The live checks verified owner-filtered listing; anonymous and unknown-identity rejection on listing and a mutation; foreign reads and refund/address/note/service denials in both Alice/Bob directions; missing-order mutation rejection; malformed JSON and non-object body rejection; invalid amount types, zero and negative amounts; blank, oversized, and invalid-type address/note values; invalid versions and service payloads; successful two-order service updates; acceptance of 120-character addresses and 160-character notes; and 422 locker-note rejection with the saved note retained. Full order reads confirmed state preservation after the initial negative-input and authorization checks. Coverage and actual responses are retained in [checks.json](checks.json) and [http.jsonl](http.jsonl); [existing-tests.txt](existing-tests.txt) records the supplied unit-test run.

This was a focused API assessment, not exhaustive input fuzzing or simultaneous-request testing. Browser journeys, layout, accessibility, production security, real payments, external systems, and performance SLAs were outside this assessment. The server source serializes mutations with a lock, but that does not correct the demonstrated domain-rule errors. No browser session was created.

**Fixture cleanup and handoff.** All original addresses, notes, and services were restored and verified through final GETs. A100's refund total changed irreversibly from 0 to **10001 cents**. A200's version advanced from **1 to 4**, including restoration of its original address. A100's version remains 1; A200 remains unrefunded; B100 is unchanged. The fixture owner must reset the instance to clear the refund and version counter. Compare [baseline.json](baseline.json) with [final-state.json](final-state.json).

The executable [assessment script](assess_api.py) and [assertion summary](assessment-output.json) support reproduction. The script performs fixture mutations; use a freshly owner-reset instance before rerunning its refund scenario. No product fixes were applied, as instructed. After repair, require the three regression gates above and rerun the routine suite and relevant HTTP checks before approving release.
