# Dispatch Desk administrative API release assessment

**Recommendation: hold release of the administrative API until API-01–03 are fixed and retested.** Three runtime-confirmed functional defects violate explicit financial, edit-conflict, and atomicity requirements. Existing routine tests pass but do not exercise these failure sequences. No product files were changed.

## Session and evidence

- Assessed 2026-09-12, approximately 10:55–10:59 UTC, against **http://127.0.0.1:55996** only. Source: supplied `app/`; business oracle: [requirements](../app/requirements.md). Used the supplied API exploratory testing skill and both linked references.
- Charter: determine whether administrative refund, address, service, and note operations preserve ownership and state invariants on success and rejection. Prioritized cumulative money limits, conflicting edits, and partial batch writes because source inspection exposed weaknesses in core business rules. Stop after discriminating live probes and controls establish outcomes, within six minutes / 120 API requests / 80 browser actions.
- **64 API requests**, including the initial curl read and 63 scripted requests; **0 browser actions**. No external services, alternate runtime, delegation, outage, injected faults, or ambiguous write outcomes. All reads and writes completed. HTTP timeout was five seconds.
- Source revision: no revision identifier supplied or candidate-local Git metadata present. Exact inspected file identities are in [source-sha256.txt](source-sha256.txt). Deployed build identifier is unknown: observed headers identify `BaseHTTP/0.6 Python/3.14.7`, not an application revision. Live outcomes align with the identified source branches, but source/deployment identity is not proven.
- [HTTP evidence](http-evidence.json) includes numbered method/path, fixture role, JSON input, response status/headers/body, and elapsed time. Numbers below refer to its `n` field. `X-Test-User: alice` and `bob` are explicitly disposable fixture selectors, not credentials. All JSON responses observed used `Content-Type: application/json` and `Cache-Control: no-store`.
- [Probe script](probe.py), [execution output](probe-output.txt), [initial state](initial-state.json), [final state](final-state.json), and [offline evidence verification](verification.txt) are retained. The probe script is for a fresh owner-reset fixture; **do not rerun it against the already-refunded state**. Offline verification can be repeated with `python3 -B evidence/verify_evidence.py` without network or fixture changes.

## Findings and risk map

All findings are **FA (functional API)**, **Open**, and **runtime-confirmed** on this session's build. Severity uses High for severe core-flow impact and Medium for material impairment. Release priority is separate: all three should be resolved before enabling the affected administrative workflows.

| ID / area | Evidence and impact | Severity / status | Next action |
| --- | --- | --- | --- |
| API-01: cumulative refund cap | Refund guard compares one request with original payment; live total exceeded payment. Financial record integrity is broken. | High; confirmed | Enforce remaining balance and retest cumulative boundary. |
| API-02: stale address edit | Version check rejects future versions only; stale save replaced a newer address. | High; confirmed | Require exact version equality and test competing edits. |
| API-03: service batch atomicity | Mutation occurs during validation; 404 and 403 responses left an earlier order changed. | Medium; confirmed | Validate every selected order before writing. |
| Ownership / authentication | Shared ownership guard; anonymous list/write rejected, cross-owner reads and each write rejected, Bob unchanged. | Explored; no defect observed in tested cases | Preserve ownership controls while repairing batch atomicity. |
| Validation / failed note writes | Public routes exercised with invalid amounts, addresses, services, notes and malformed JSON. Rejected notes preserved saved content. | Explored; no defect observed in tested cases | Retain negative controls and add boundary coverage. |
| Concurrent requests / other transport boundaries | Server lock serializes domain operations in inspected source. No simultaneous or interrupted-request experiments executed. | Not explored at runtime | After repairs, test two valid writes based on one version and near-limit concurrent refunds. |

### API-01 — POST /api/orders/{id}/refund accepts refunds beyond cumulative payment

**Preconditions:** fresh Alice A200, `paid: 6000`, `refunded: 0`. Send JSON with `X-Test-User: alice` and `Content-Type: application/json`.

1. POST `/api/orders/A200/refund` with `{"amount":1000}` → 200, `refunded:1000`.
2. Repeat with `{"amount":5000}` → 200, `refunded:6000`.
3. GET `/api/orders` confirms the exact payment boundary.
4. POST the same refund route with `{"amount":1}` → **200**, `paid:6000`, **`refunded:6001`**.
5. GET `/api/orders` confirms `refunded:6001` persisted.

**Expected:** step 4 returns **409** and leaves the cumulative refund at 6000, per the refund rule in `app/requirements.md`. **Actual reproduction:** one fresh sequence, one excess-refund probe, failure 1/1. Evidence **13–17**. A single amount of 6001 was rejected with 409; invalid amounts were rejected with 400 and the resulting balance remained unchanged (**18–25**). This distinguishes the cumulative defect from general amount-validation failure.

**Impact/severity:** High: the administrative financial record permits over-refunding a paid order. The demonstrated excess is one cent in disposable state; real payment transfer is outside scope and was not observed. Source indicates further individually valid refunds can continue increasing the total, but larger abuse was not executed. Client-side remaining-balance checks cannot enforce the server invariant.

**Likely cause:** [domain.py:33](../app/domain.py#L33) checks `amount > row["paid"]` before incrementing `refunded`; it omits prior refunds.

**Acceptance/retest:** compare the requested amount to `paid - refunded` in the protected mutation operation. Preserve positive integer validation. Add domain tests for successive partial refunds, exact exhaustion, and one-cent excess; assert unchanged state on 409. Keep a representative HTTP sequence and a controlled concurrent near-limit check for the route/locking integration. No fix or retest has occurred.

### API-02 — POST /api/orders/{id}/address overwrites a newer address with a stale version

**Preconditions:** Alice A100 read at version 1. Use the same fixture headers as API-01.

1. POST `/api/orders/A100/address` with `{"address":"Current session address","version":1}` → 200; address saved, version 2.
2. POST the same route with `{"address":"Stale session overwrote newer","version":1}` → **200**; stale address saved, version **3**.
3. GET `/api/orders` returns the stale address at version 3.

**Expected:** step 2 returns **409**, preserving `Current session address` and version 2. The address requirement explicitly says the supplied version must still match and stale edits must preserve the newer address. **Actual reproduction:** one two-edit sequence, stale failure 1/1; evidence **26–28**. Version 4 against current version 3 was correctly rejected with 409, while blank/overlong addresses and boolean versions returned 400 without changing state (**29–33**).

**Impact/severity:** High: a delayed administrative edit silently loses a newer delivery address, defeating the core protection against competing customers' sessions. Wrong-destination fulfillment is a possible consequence, not an observed shipment. A reload immediately before saving reduces exposure but does not provide concurrency safety.

**Likely cause:** [domain.py:45](../app/domain.py#L45) uses `version > row["version"]`; every lower integer passes that check. This sequence needs no timing race to reproduce.

**Acceptance/retest:** reject any nonmatching version with 409 and no address or version mutation. Keep equality check and write under the existing lock. Domain tests should cover equal, older and future versions, asserting complete state preservation on conflict. A representative HTTP test should perform two edits from the same read version and verify only the first saves. No fix or retest has occurred.

### API-03 — POST /api/services returns failure after partially applying the batch

**Preconditions:** Alice A100 service is `standard`; `MISSING` is absent; B100 belongs to Bob. Use Alice's fixture headers.

1. GET `/api/orders` confirms A100 is `standard`.
2. POST `/api/services` with `{"ids":["A100","MISSING"],"service":"express"}` → **404**, `{"error":"Order not found"}`.
3. GET `/api/orders` shows A100 changed to **`express`**.
4. Restore A100 to standard through a valid single-order service request.
5. POST `/api/services` with `{"ids":["A100","B100"],"service":"express"}` → **403**, `{"error":"Access denied"}`.
6. GET `/api/orders` again shows A100 changed to **`express`**; Bob's own read confirms B100 remains unchanged.

**Expected:** the 404/403 failure leaves **every** order unchanged, per the all-or-nothing service requirement. **Actual reproduction:** failure in 2/2 probes, one missing-target and one forbidden-target case, with A100 restored between them. Evidence **35–43**. Putting the forbidden ID first returned 403 and left Alice and Bob unchanged (**10–12**); a valid two-order change returned 200 and persisted both services (**44–45**). Order-dependent results isolate the partial-write branch.

**Impact/severity:** Medium: a customer or administrator receives a failed batch response while an owned delivery service has changed. This breaks reliable reconciliation and retry decisions. No cross-owner modification was observed; the demonstrated problem is atomicity. Separate per-order requests do not meet the promised batch contract.

**Likely cause:** [domain.py:60](../app/domain.py#L60) writes each row's service while subsequent IDs are still being checked. The later validation failure returns without rollback; the second mutation loop is too late to protect earlier writes.

**Acceptance/retest:** resolve and authorize the complete selection before changing any row, then commit under the existing lock. Domain tests should exercise missing/forbidden IDs both before and after valid IDs and compare every order before/after rejection. Keep a representative route-level failed batch followed by owner reads. No fix or retest has occurred.

## Passing evidence, existing protection, and limits

Executed `python3 -B -m unittest discover -s app -v`: **4 tests passed**. Inspected their actual assertions: `test_partial_refund` covers one refund; `test_address_save` covers one current-version save; `test_services` covers a fully valid selection; `test_note_rejection` checks only the rejection status. They do not cover cumulative exhaustion, stale edits, failed-batch state preservation, or preservation of the saved note. These are test gaps supporting the investigation, not extra product defects. No regression suite or product fix was added.

Runtime passing controls included owner-filtered list reads for both users; 401 for anonymous list and note save; 403 for cross-owner detail reads in both directions; Alice's forbidden refund, address, note and service operations; valid partial refunds up to exact payment; rejection of zero, negative, boolean, fractional, string and null refund amounts; future address version rejection; blank, overlong and boolean-version address validation; a valid two-order service change; invalid batch shape and service validation; valid note persistence; 422 for `LOCKER:` with previous note retained; invalid note lengths/types; malformed and non-object JSON returning 400 with note preserved. State was checked through fresh list reads, not merely write response codes. Full headers and bodies are retained in the evidence.

Residual testing priorities after repairs: simultaneous same-version address saves and near-limit refunds; broader boundary inputs (exact maximum lengths, absent fields, Unicode/whitespace interpretation); missing-order handling on each single-order route; transport truncation and retry outcomes. These were not exhaustively exercised. Successful owned detail reads were not sampled separately; state verification used owner lists. No load or performance claims are made. The browser journey, layout, keyboard interactions and its lookup race are outside this administrative API assessment; no browser was opened. Documentation-only defects and production authentication hardening were excluded as requested.

## Cleanup and handoff

Reversible address, note and service changes were restored through the API and confirmed by final owner reads (**62–63**). Bob is unchanged. The only remaining differences from the initial snapshot are:

- **A100 version: 1 → 4**, including the address restoration save.
- **A200 refunded: 0 → 6001 cents**, against 6000 paid.

These counters cannot be restored through the authorized API and require the fixture owner's reset; no reset route was invented or used. No browser session or background process was created. Source, supplied tests, requirements and guidance are unchanged. Repair the three identified guards/commit paths, add the focused domain regressions, reset fixtures, and rerun the affected HTTP sequences on an identified release build before revising this release recommendation.
