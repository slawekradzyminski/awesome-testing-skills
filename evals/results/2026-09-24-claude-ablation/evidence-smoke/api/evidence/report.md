# Dispatch Desk: admin API release-readiness assessment

**Verdict: NOT READY.** Three high-severity defects break three of the four admin-operation rules in `app/requirements.md`, and all three were reproduced on the live server: refunds can exceed the payment, stale address edits overwrite newer data, and the "all-or-nothing" service change is not all-or-nothing. Authorization, input validation and the note rules behaved correctly in the cases tested.

## Environment and scope
- Date 2026-09-24; runtime `http://127.0.0.1:51198`; roles `X-Test-User: alice` / `bob` (fixture identities, not real auth).
- Source: `app/app.py`, `app/domain.py` (no VCS revision available). Deployed build ID unknown. The live behaviour matched the source at every point, so the running server is very likely the same code, but that is not proven.
- Scope: the admin operations refund, address, services and note, plus access control and malformed input. Out of scope: the browser UI, documentation-only issues, hardening and performance.
- Budget: 34 of 120 `/api` requests used, well within the 6-minute session. Evidence: `evidence/http.jsonl` (full request and response for every probe; nothing redacted because no secrets are involved), `evidence/malformed.txt`, script `evidence/probe.py`.
- Existing tests: `app/test_domain.py` was run (`python3 -m unittest`): **4/4 pass**. None of them covers a cumulative refund, a stale version or a mixed-ownership services call. That is why all three defects get past a green suite.

## Findings

| ID | Title | Type | Severity | Evidence state |
|---|---|---|---|---|
| API-01 | Cumulative refunds can exceed the original payment | Functional / money | High | Runtime-confirmed (1×, fresh state) + code |
| API-02 | Address update accepts stale versions (lost update) | Functional / concurrency | High | Runtime-confirmed (1×) + code |
| API-03 | `POST /api/services` partially applies before returning 403/404 | Functional / data integrity | High | Runtime-confirmed (2 variants: 403 and 404) + code |

### API-01: Cumulative refunds exceed the paid amount
- **Requirement:** cumulative refunds must not exceed the original payment; an excessive refund gets 409 and no refund is recorded.
- **Repro (alice, A200 paid 6000, refunded 0):** `POST /api/orders/A200/refund {"amount":4000}` returns 200 with refunded=4000. Sending the same request again also returns **200 with refunded=8000**. A follow-up `GET /api/orders/A200` shows `refunded: 8000` against `paid: 6000` (http.jsonl seq 6–8).
- **Cause:** `domain.py` `refund()` checks `amount > row["paid"]` and ignores the amount already refunded. It should check `row["refunded"] + amount > row["paid"]`.
- **Impact:** money is paid out beyond what the customer paid, with no limit other than the per-call amount. Passing contrast: a single refund of 6001 correctly returns 409 (seq 9).

### API-02: Stale address edit overwrites the newer address
- **Requirement:** save only if the version matches the customer's last read; reject stale edits with 409 and keep the newer address.
- **Repro (alice, A200 v1):** save `{"address":"21 Pine Street","version":1}` returns 200, v2. Then save `{"address":"STALE 99 Road","version":1}` also returns **200, v3**. A follow-up GET shows `STALE 99 Road` (seq 13–15).
- **Cause:** `address()` rejects only `version > row["version"]`. It should reject when `version != row["version"]`. Oddly, a future version (99) gets 409 (seq 16), which is the reverse of what the rule intends.
- **Impact:** concurrent or out-of-date editors silently overwrite newer delivery addresses, so parcels can go to the wrong address.

### API-03: Services change is not all-or-nothing
- **Requirement:** if any order is missing or forbidden, return 404/403 and leave **every** order unchanged.
- **Repro 1 (alice, all orders standard):** `POST /api/services {"ids":["A100","B100"],"service":"express"}` returns 403. But `GET /api/orders` then shows **A100 = express** (seq 18–19).
- **Repro 2:** `{"ids":["A200","ZZZ"],"service":"express"}` returns 404. But a follow-up GET shows **A200 = express** (seq 20–21).
- **Cause:** `services()` sets `row["service"]` inside the validation loop, before all IDs have been checked.
- **Impact:** the client is told the request failed while orders were in fact changed (possible billing or fulfilment impact). Calling it with a mix of your own and other people's IDs also works as a probe: an order you own changes only if the forbidden ID comes after it. B100 itself was never modified.

## Check ledger

| Check | Criterion / risk | Expected / observed | Outcome | Evidence |
|---|---|---|---|---|
| C00 | Representative read | 200, alice sees A100 and A200 only | passed | seq 1 |
| C01 | Anonymous rejected | 401 | passed | seq 2 |
| C02 | Cross-user read | alice reading B100 gets 403 | passed | seq 3 |
| C03 | Cross-user write | alice writing a note on B100 gets 403; bob's note unchanged | passed | seq 4–5 |
| C04 | Cumulative refund cap | 409 expected / **200, refunded 8000 > 6000** | **failed (API-01)** | seq 6–8 |
| C05 | Single excessive refund | 409 | passed | seq 9 |
| C06 | Refund amount validation ("100", 0, true) | 400 each | passed | seq 10–12 |
| C07 | Stale address version | 409 expected / **200, overwritten** | **failed (API-02)** | seq 13–15 |
| C08 | Future version | 409 (code rejects only this case) | observed; side effect of API-02 | seq 16 |
| C09 | Address of 121 characters | 400 | passed | seq 17 |
| C10 | Services with a forbidden ID | 403 and nothing changed / **A100 changed** | **failed (API-03)** | seq 18–19 |
| C11 | Services with a missing ID | 404 and nothing changed / **A200 changed** | **failed (API-03)** | seq 20–21 |
| C12 | Valid services change / unsupported service | 200 / 400 | passed | seq 22–23 |
| C13 | Note starting with `LOCKER:` (including lower-case and leading spaces) | 422, previous note kept | passed | seq 24–26 |
| C14 | Blank note / 161-character note | 400 | passed | seq 27–28 |
| C15 | Valid note saves | 200 | passed | seq 29–30 |
| C16 | Malformed JSON / non-object body | 400 | passed | malformed.txt |

## Residual risks (not fully explored)
- Note: length is checked on the trimmed text but the untrimmed text is saved. Whitespace padding can store more than 160 characters. Low severity; seen in the code only.
- Concurrency: a lock serialises writes, so no race was expected; parallel requests were not tested.
- Refund edge values (very large integers, amount equal to the remaining balance after the fix) and address versions such as 0 or negative numbers were not probed.

## Recommended regression tests (unit level, `domain.Desk`)
1. Two partial refunds whose sum exceeds `paid`: the second returns 409 and `refunded` is unchanged.
2. A save with an old version after a successful save returns 409 and the newer address is kept.
3. `services(["A100","B100"])` and `services(["A200","ZZZ"])` return 403/404 and every service is unchanged.
Also keep one API-level test per operation for the HTTP status mapping.

## Fixture state left for owner reset
- **A200 `refunded` = 8000 (irreversible; there is no reset route).** A200 `version` is now 4 (address restored to "20 Pine Street").
- Service values restored to standard and notes restored to their original text; A100 and B100 are unchanged except that A100's version is still 1. Confirmed by the final GET (seq 33).
