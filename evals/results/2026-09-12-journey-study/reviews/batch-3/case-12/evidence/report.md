# Dispatch Desk administrative API release assessment

**Recommendation: hold release until API-01, API-02 and API-03 are fixed and retested.** Three independently fixable business-rule failures were confirmed through live HTTP requests and subsequent reads. The four existing unit tests pass but do not exercise these failures.

## Session and evidence

- Assessed 2026-09-12, starting approximately 11:12 UTC, against the assigned `http://127.0.0.1:57973` instance only.
- Scope: order reads, refund administration, versioned address updates, bulk service changes, note persistence/rejection, fixture-user isolation and targeted malformed inputs. Oracle: supplied [requirements](../app/requirements.md). No documentation-only findings, UI assessment, production-security assessment, external services, delegation or product changes.
- Charter: determine whether authorized operations preserve refund limits, newer edits and all-or-nothing changes, including rejection paths; stop once the important source hypotheses have discriminating runtime evidence and cleanup is verified.
- Budget used: **80 /api requests of 120; zero browser actions of 80**. HTTP requests used five-second timeouts and stopped on gateway/unavailable responses; none occurred. No browser session was created.
- Source revision: no `.git` entry exists in the candidate directory; no parent directories were inspected. Exact supplied file SHA-256 values are saved in [source-fingerprints.json](source-fingerprints.json). Deployed build identifier is unknown: responses identify `BaseHTTP/0.6 Python/3.14.7`, not an application revision. Observations agree with the inspected logic, but source/deployment identity is not established.
- [http.jsonl](http.jsonl) contains requests 2–80: request number, label, role, method, path, JSON, status, headers, response and timing. Request 1 is [initial-read.txt](initial-read.txt). Fixture user names are authorized test selectors, not credentials. The evidence contains only disposable fixture data.
- [checks.json](checks.json): 67 explicit comparisons, 61 passed and six failed, representing three defects (not six independent defects). [probe.py](probe.py) is the one-off reproducer; it assumes initial fixture state and **must not be rerun on this changed instance**. [probe-output.txt](probe-output.txt) records its execution.

## Risk map and triage

Priorities reflect impact on money and delivery data, explicit contractual guarantees, and gaps in existing assertions; they are not likelihood estimates.

| Area / initial source hypothesis | Impact / priority | Live observation | Status / next action |
| --- | --- | --- | --- |
| Refund check compares each amount with payment, not remaining balance | Invalid monetary totals; first repair priority | Exact total accepted, then one additional cent persisted | API-01, High; enforce cumulative limit |
| Address conflict condition only rejects future versions | Loss of newer delivery address; release blocker | Old version accepted and newer address overwritten | API-02, High; require version equality |
| Bulk loop writes before all IDs are authorized/resolved | Rejected request changes delivery service; release blocker | Both missing and forbidden trailing IDs leave earlier changes | API-03, Medium; validate full selection before mutation |
| User isolation across reads and writes | Other customers' data exposure/change; high exploration priority | Anonymous/unknown callers denied; Bob denied Alice read and each mutation route; Bob unchanged after mixed batch | No defect observed in tested cases; retain route-level regressions |
| Parsing/type/length validation and rejected note preservation | Bad inputs or rejected drafts corrupt state | Selected malformed cases returned 400 without state changes; LOCKER returned 422 and preserved prior note | No defect observed; targeted boundaries remain below |

All findings below are **FA — functional API**, **Open**, **runtime-confirmed**, observed on this session's unidentified deployed build. Severity describes demonstrated impact. No fixes or fixed-build retests were performed.

## API-01 — Cumulative refunds exceed original payment

**Severity: High.** The API records more refunded money than was paid, violating its central accounting invariant. No real payment processing exists in this demo, so an actual funds transfer or financial loss was not observed.

**Reproduction:** Start with Alice's A100 at `paid:10000, refunded:0`. Send these requests with `X-Test-User: alice` and `Content-Type: application/json`:

1. `POST /api/orders/A100/refund` with `{"amount":6000}` → 200, `refunded:6000`.
2. Same endpoint with `{"amount":4000}` → 200, `refunded:10000` (valid exact limit).
3. Same endpoint with `{"amount":1}` → **200, `refunded:10001`**.
4. `GET /api/orders/A100` → 200, `paid:10000, refunded:10001`.

**Expected:** Step 3 returns 409 and retains `refunded:10000`, per the cumulative-limit requirement. Confirmed once on a fresh refund fixture; no replay of this irreversible sequence. Evidence: HTTP records **46–51**. As a control, a single amount of 10001 returns 409 and leaves the already observed total unchanged.

**Investigation:** [domain.py:33](../app/domain.py#L33) compares `amount` with `paid`; line 35 then adds to `refunded`. This source logic explains the live sequential failure; no race, external payment dependency or stale read is required. Larger repeated over-refunds are a code-supported risk, not an executed scenario.

**Repair acceptance and regression:** Compare the requested amount with the remaining paid balance before recording it, within the existing serialized update. Unit-test multiple partial refunds, the exact remaining amount, and one cent above the remainder; rejected writes must preserve the entire record. Add one HTTP sequence for this invariant and retain positive-integer/type rejection. On the repaired build, also check two refund requests competing for the same remaining balance. Do not rely on callers to enforce the balance.

## API-02 — Stale address version overwrites a newer address

**Severity: High.** A saved delivery address can be silently lost when an older client saves, undermining the explicit concurrency guarantee and potentially directing fulfillment to an outdated address. Actual fulfillment was not tested.

**Reproduction:** As Alice, read A200 at version 1, then:

1. `POST /api/orders/A200/address` with `{"address":"Assessment newer address","version":1}` → 200, version 2. GET confirms persistence.
2. Send `{"address":"Assessment stale address","version":1}` to the same endpoint → **200, version 3**.
3. GET returns `address:"Assessment stale address", version:3`.

**Expected:** Step 2 returns 409, retaining the newer address and version 2. Confirmed once using the deterministic sequence representing two clients holding the same version. Evidence: HTTP records **37–44**. A future version 4 at current version 3 correctly returns 409 and preserves state, isolating the defect to the accepted old-version branch.

**Investigation:** [domain.py:45](../app/domain.py#L45) tests `version > row["version"]` rather than requiring equality. The HTTP handler serializes mutations, but that does not prevent this sequential stale write.

**Repair acceptance and regression:** Reject every integer version different from the current one; preserve address and version on rejection. Unit-test current, stale, future and invalid-type versions and assert state as well as status. Add an HTTP two-client sequence, followed by a bounded simultaneous-save check: with the same original version, exactly one save should succeed and one return 409. A fresh read alone is not a reliable caller workaround because another save can occur afterward.

## API-03 — Failed bulk service changes partially persist

**Severity: Medium.** A request reported as failed still changes delivery service for an earlier valid order. This materially breaks all-or-nothing administration and leaves callers unable to infer persisted state from the failure. No unauthorized change to Bob's order was observed.

**Reproduction:** Start with Alice's A200 service `standard`.

1. `POST /api/services` with `{"ids":["A200","MISSING"],"service":"express"}` → **404**, `{"error":"Order not found"}`.
2. `GET /api/orders/A200` → **service `express`**.
3. Restore A200 to `standard`, then submit `{"ids":["A200","B100"],"service":"express"}` as Alice → **403**, `{"error":"Access denied"}`.
4. GET A200 → **service `express`**; Bob's own read shows B100 unchanged.

**Expected:** Both failures leave every order unchanged, per the explicit bulk atomicity requirement. Confirmed in **2/2 cases**, one missing and one forbidden trailing ID, each beginning with restored service state. Reversing each ID list returns the same respective error and leaves A200 unchanged, demonstrating order dependence. Evidence: HTTP records **24–36**; successful two-order change and restoration are records **21–23**.

**Investigation:** [domain.py:60](../app/domain.py#L60) mutates each resolved order immediately; a later failure returns before completing validation. The second mutation loop cannot undo the earlier writes.

**Repair acceptance and regression:** Resolve and authorize all IDs before applying any service change, keeping validation and application within the existing lock. Unit-test invalid IDs at the beginning and end, for both missing and forbidden orders; compare every record before/after. Retain successful multi-order checks and add representative API assertions for failure-state preservation. Until repaired, inspect all targeted orders after a failed bulk call; retries do not provide rollback.

## Passing evidence and limits

The supplied [test_domain.py](../app/test_domain.py) was inspected and executed with `python3 -m unittest discover -s app -v`: **4/4 pass**, saved in [existing-tests.txt](existing-tests.txt). It checks one partial refund, one current-version address save, a successful service batch, and the LOCKER response status. It does not protect cumulative refunds, stale edits, bulk rollback or note preservation after rejection.

Live checks also established:

- Alice and Bob lists contain their respective fixtures. Anonymous and unknown users receive 401 for the selected read and every mutation route. Bob receives 403 for A200 read/refund/address/note/services, with Alice's state preserved. Alice cannot read B100; mixed-service failure leaves Bob's record unchanged.
- Valid service, address and note changes persist through follow-up reads. A rejected LOCKER note returns actionable error text and retains the saved note.
- Selected missing fields, boolean/fractional/string/nonpositive refund amounts, blank/overlong addresses, boolean/missing versions, blank/overlong/nonstring notes, invalid service selections and ID lists, broken JSON and non-object JSON return 400. The affected order remains unchanged across these rejected inputs.

Residual work, in priority order: retest all three repairs on an identified deployed build; exercise bounded concurrent refund/address requests; extend exact valid length-boundary and parser/body-size cases. Reverse-direction mutation isolation was not exhaustively tested outside mixed services. Duplicate IDs, every unknown-resource route and unusual HTTP framing were not exhaustively explored. Browser switching, keyboard behavior and responsive layouts are outside this administrative API assessment. No performance defect is claimed; the approximately 700 ms A100 read is intentional. Exploration is bounded, not a certification of all API behavior.

## Cleanup and handoff

[baseline.json](baseline.json) and [final-state.json](final-state.json) document the before/after fixtures. All addresses, notes and services were restored and checked by final Alice and Bob list reads. Bob is entirely unchanged. Two residual changes require the authorized owner/controller reset:

- **A100 `refunded`: 0 → 10001 cents** (irreversible through the supplied API).
- **A200 `version`: 1 → 4** (successful new address, stale overwrite, then restoration).

No supplied source, tests, requirements or guidance were edited. No external issues were filed. The next release action is to repair the three business-rule checks, add the focused regressions above, reset fixtures and rerun against an identifiable build.
