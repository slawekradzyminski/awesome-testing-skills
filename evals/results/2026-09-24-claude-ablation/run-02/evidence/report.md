# Dispatch Desk: are the admin API operations ready to release?

**Decision: NO-GO.** Three business rules are broken, and I saw each one fail on the running server. Two of them lose money or data: refunds can exceed the amount paid, and a stale address edit overwrites a newer one.

## Session summary
- **Scope:** refund, address, services and note operations, plus the related auth and input checks. Out of scope: the UI journey, documentation, general hardening and performance.
- **Environment:** http://127.0.0.1:50690, on 2026-09-24. Fixture users were `X-Test-User: alice` and `bob`. I read the source in `app/`, but I could not verify that it matches the running build. The runtime behaviour I saw matched the source's logic every time.
- **Contract:** `app/requirements.md`
- **Budget:** 49 of 120 /api requests (43 scripted, 3 wrong-header restore attempts, 3 restores), about 6 minutes.
- **Evidence:** `probe.py` is the script. `probe_output.txt` and `probe_log.json` hold the requests and responses, and step numbers below refer to them (#n). `restore.txt` shows the cleanup.

## Findings index
| ID | Title | Type | Severity | Evidence state |
|---|---|---|---|---|
| API-01 | Cumulative refunds can exceed the original payment | FA / financial | Critical | Seen on the server (1 run) + found in code |
| API-02 | Stale address version accepted: lost update | FA / data integrity | High | Seen on the server (1 run) + found in code |
| API-03 | `POST /api/services` is not all-or-nothing | FA / data integrity | High | Seen on the server (2 variants) + found in code |

### API-01: Refunds can add up to more than the payment (Critical)
- **Steps:** as alice, send `POST /api/orders/A200/refund {"amount":4000}` → 200, refunded=4000 (#8). Send the same request again → **200, refunded=8000** against paid=6000 (#9). A GET confirms refunded=8000 (#10).
- **Expected:** the second request returns 409 and no refund is recorded.
- **Cause:** `domain.py` `refund` compares `amount > row["paid"]` instead of `row["refunded"] + amount > row["paid"]`. Only a single refund larger than the payment is rejected (#11 returned 409 as it should).
- **Impact:** an order can be refunded any number of times, which directly loses money.
- **Regression test:** a domain unit test that refunds 4000 twice on a 6000 order and expects 409 with refunded still 4000. Also test that a refund exactly equal to the remaining amount succeeds.

### API-02: Stale address edits overwrite newer ones (High)
- **Steps:** send `POST /api/orders/A200/address {"address":"21 Pine Street","version":1}` → 200, version 2 (#18). Then send `{"address":"STALE edit","version":1}` → **200**. The address becomes "STALE edit" and the version becomes 3 (#19, #20).
- **Expected:** 409, with "21 Pine Street" kept.
- **Cause:** the check is `version > row["version"]`, so it only rejects versions from the future (#21). It should reject any mismatch (`!=`).
- **Impact:** concurrent edits silently lose data. A delivery could go to an address that was already superseded.
- **Regression test:** a unit test that saves with v1 and then saves again with v1, expecting 409 and the first address kept.

### API-03: A failed bulk service change still changes some orders (High)
- **Steps:** as alice, send `POST /api/services {"ids":["A200","B100"],"service":"express"}` → 403 (#25), yet **A200 is now express** (#26). B100 did not change (#27). Then send `{"ids":["A100","ZZZ"],"service":"express"}` → 404 (#28), yet **A100 is now express** (#29).
- **Expected:** no order changes when the request is rejected.
- **Cause:** `services()` sets `row["service"]` inside the check loop, before every ID has been validated.
- **Impact:** the error response tells the caller nothing changed, but orders were changed anyway. Service level (and possibly price) ends up inconsistent. Another customer's order was not changed, so this is not an authorization breach.
- **Regression test:** unit tests with [own, foreign] and [own, missing] IDs that expect 403/404 and all services unchanged.

## Checked with no defect found
| Area | Probes | Result |
|---|---|---|
| Auth / ownership | anonymous GET and POST; alice GET, refund and note on B100 (#3–7) | 401 / 403, no change |
| Refund validation | 0, -5, "100", 1.5, true, null, 1e3 (#12–17, #43) | 400 |
| Address validation | blank, 121 characters, version as a string (#22–24) | 400 |
| Services validation | unsupported service, empty id list (#30–31) | 400 |
| Note rules | `LOCKER: 12` and `  locker: 12` return 422; blank, 161 characters and a number return 400; 160 characters returns 200 (#32–38) | as specified |
| Malformed body | invalid JSON, array, non-UTF-8 bytes (#40–42) | 400 |

**Observation (not a defect):** the length check trims whitespace, but the note is stored untrimmed. A note of 160 characters plus padding was accepted and stored as 164 characters (#37). This is harmless unless the 160-character limit is a storage constraint, so the product owner should decide.

## Not tested / remaining risks
- Concurrent requests (for example, two refunds racing). A single lock covers each POST, so this is low risk, but I did not test it.
- Refunds on A100 and on Bob's order, and a note rejection immediately after a successful save. The code path is the same, and I saw the note kept after a rejection on A100.
- The browser/UI journey, which is outside this assessment.

## Changes left on the fixtures (owner reset needed)
- **A200 refunded = 8000 (paid 6000).** This cannot be undone because there is no reset route.
- **A200 version is 4 (was 1).** Its address is back to "20 Pine Street".
- A100 note, A100 and A200 service, and A100 address are back to the original values. B100 was never changed.

## Next steps
1. Fix API-01, API-02 and API-03 in `domain.py` and add the unit tests above to `test_domain.py`. The existing tests only cover the successful paths.
2. Add one API-level check for each finding (a double refund, a stale version, a mixed-owner services call) as integration coverage, then retest this session's steps.
