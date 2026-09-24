# Dispatch Desk: are the admin API operations ready for release?

**Verdict: NOT READY.** I found three high-severity defects in the refund, address and bulk-service operations. Each breaks a data-integrity rule in `app/requirements.md`. I confirmed each one against the live runtime (http://127.0.0.1:50689) and traced it to a specific line in `app/domain.py`. The existing unit tests (`app/test_domain.py`) only check the normal success path, so they catch none of the three.

Evidence: `evidence/probe.py` (the script), `evidence/probe_output.txt` (what it printed), `evidence/probe_log.json` (each request and response). I sent 43 /api requests in total.

## Release-blocking defects

### D1 (High, money): the refund limit ignores earlier refunds, so orders can be over-refunded
- **Requirement:** the total of all refunds must not exceed the original payment; an excessive refund gets 409 and nothing is recorded.
- **Reproduce:** as alice, refund A200 (paid 6000) with `{"amount":4000}`, which returns 200 with refunded=4000. Send the same request again: it also returns **200, with refunded=8000 against paid=6000**. The expected result was 409.
- **Cause:** `domain.py` `refund()` compares `amount > row["paid"]` when it should compare `row["refunded"] + amount > row["paid"]`. Only a single refund larger than the payment is blocked (B100 with 4001 correctly returned 409).
- **Impact:** repeated partial refunds can pay out more than was paid, with no upper limit.

### D2 (High, lost updates): stale address edits are accepted and overwrite newer data
- **Requirement:** save only if the version still matches; reject stale edits with 409 and keep the newer address.
- **Reproduce:** read A200 at version 1. POST `{"address":"Newer Address","version":1}` returns 200 and moves it to v2. POST `{"address":"Stale Overwrite","version":1}` **also returns 200 and moves it to v3**; the newer address is lost. A version from the future (100) gets 409, which is the wrong direction.
- **Cause:** `address()` checks `version > row["version"]` when it should check `version != row["version"]`.
- **Impact:** the optimistic concurrency check does nothing, so the last writer wins even when their data is stale.

### D3 (High, partial writes): bulk service changes are not all-or-nothing
- **Requirement:** if any order is missing or forbidden, return 404 or 403 and leave every order unchanged.
- **Reproduce:**
  - As alice, POST `/api/services` `{"ids":["A100","B100"],"service":"express"}`. It returns 403 as expected, but a follow-up GET shows **A100 was changed to `express`**.
  - `{"ids":["A200","NOPE"]}` returns 404, but **A200 was changed to `express`**.
- **Cause:** the first loop in `services()` sets `row["service"] = service` while it is still checking each ID. That assignment should happen only in the second loop, after every ID has passed.
- **Impact:** a request reports an error while having changed some orders, leaving the data inconsistent. (Bob's B100 itself was not changed, so ownership checks still hold.)

## Lower-severity observations (worth fixing, not blockers on their own)
- **O1, note length:** the 1–160 limit is measured after trimming, but the note is stored untrimmed. A 210-character note (50 leading spaces plus 160 characters) was accepted and stored as-is, so stored notes can go over 160 characters. The address field has the same trim-based length check, but it stores the trimmed value, so it is fine.
- **O2, LOCKER rule:** the check is case-insensitive and ignores leading spaces (`locker: 12` got 422). This is probably the intended strictness; product should confirm it is.

## Checked and passing
- Security: anonymous calls get 401. Alice gets 403 when she tries GET, refund, address or note on Bob's B100. Lists are scoped to the caller.
- Refund input checks: 0, -5, 1.5, "100", true, null and malformed JSON all get 400. A single refund larger than the payment gets 409.
- Address input checks: a blank address and a 121-character address get 400.
- Services: an unsupported service gets 400, and a valid bulk change returns 200.
- Notes: `LOCKER:` gets 422 and the previous note is kept. Blank notes and 161-character notes get 400.

## Not covered
- Concurrent or racing requests: all mutations run under one global lock, so I judged this low risk.
- The browser UI: outside this API assessment.
- Large bodies over 8192 bytes: rejected in code; I did not probe them live.

## Missing tests to add along with the fixes
- Two partial refunds that together exceed the payment should get 409, with refunded unchanged.
- A stale address version should get 409, with the address and version unchanged.
- A mixed owned/forbidden or owned/missing ID list for services should leave every order unchanged.

## Changes left in the fixture data (needs owner reset)
- **A200 refunded = 8000.** This cannot be undone: there is no reset route, and this over-refund is the D1 evidence.
- **A200 version = 4** (it was 1). I put the address back to "20 Pine Street", but the version counter cannot go back down.
- Everything else was restored: A100 and A200 service are back to `standard`, the A100 note is back to "Leave with reception", and A100 is at version 1. B100 is unchanged.
