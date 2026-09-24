# Dispatch Desk admin API: release readiness assessment

**Date:** 2026-09-24. **Runtime:** http://127.0.0.1:50688. **Source:** app/ (no VCS revision available; the deployed build was not identified separately. Every observed behaviour matched the source, so the runtime appears to run this code).
**Scope:** refund, address, services and note operations, plus the auth/ownership and malformed-input handling around them. UI, docs and hardening were out of scope.
**Budget used:** 44 of 120 /api requests (38 probes and 6 restore/verify). Existing unit tests were read but not run.

## Verdict: NOT READY. Three confirmed high-severity defects break explicit requirements.

| # | Severity | Operation | Defect (confirmed live) |
|---|---|---|---|
| 1 | **High (money)** | `POST /refund` | Cumulative refunds are not limited. Each refund is only checked against the original payment. |
| 2 | **High (data loss)** | `POST /address` | The optimistic-lock check is inverted. Stale versions are accepted and overwrite newer addresses. |
| 3 | **High (integrity)** | `POST /services` | The change is not all-or-nothing. Orders listed before a missing or forbidden ID are changed, even though the call returns 403/404. |
| 4 | Low | `POST /note` | The length check uses the trimmed text, but the note is stored untrimmed. A note longer than 160 characters can be saved. |

### 1. Over-refund: cumulative refunds exceed the payment
- Requirement: "cumulative amount must not exceed the original payment. Reject an excessive refund with 409."
- Code: `domain.py` `refund` checks `amount > row["paid"]`. It should check `amount > row["paid"] - row["refunded"]`.
- Repro (B100 paid 4000): as bob, `POST /api/orders/B100/refund {"amount":3000}` returns 200 (refunded=3000). Repeating it returns **200 with refunded=6000**. A GET afterwards confirms `refunded: 6000` on a 4000 payment (probe_log #5-8). A single refund above the payment (4001) is correctly rejected with 409.
- Impact: repeated calls can refund money that was never paid, with no upper bound except the per-call cap.

### 2. Stale address edits overwrite newer data (lost update)
- Requirement: "Save only if the version still matches ... Reject stale edits with 409 and preserve the newer address."
- Code: `address` rejects only `version > row["version"]`. It should reject whenever `version != row["version"]`.
- Repro (A200): after a read, version=1. `POST address {"Newer Street 1", version:1}` returns 200 (v2). Then `POST address {"STALE Street", version:1}` **returns 200 (v3) and replaces the newer address** (probe_log #16-20). Only versions from the future (51) get a 409, which is the opposite of what the requirement asks for.
- Impact: when two agents edit the same order, one agent's change is silently lost. The protection exists in name only.

### 3. Bulk service change is only partly applied when it fails
- Requirement: "all-or-nothing ... if any order is missing or forbidden, return 404 or 403 and leave every order unchanged."
- Code: `services` sets `row["service"] = service` inside the validation loop, before later IDs have been checked.
- Repro: as alice, `POST /api/services {"ids":["A100","B100"],"service":"express"}` returns **403**, but A100 is now `express`. `{"ids":["A200","NOPE"]}` returns **404**, but A200 is now `express` (probe_log #21-25). Bob's B100 stayed unchanged, so the ownership check does protect the other customer's order.
- Impact: the client is told the request failed, but the data has changed. Clients that retry or show an error will show the wrong service level.

### 4. Note length limit can be bypassed with whitespace (low)
- `"y" + 300 spaces` returns 200 and the full 301-character string is stored (probe_log #31-32). The requirement says 1-160 characters. Unlike address, the note is not trimmed before it is saved. The impact is small (storage, and the display of notes further along).

## Checked and working as required
- Anonymous requests get 401. Alice gets 403 when reading or changing Bob's B100, whether by GET, refund or note (#2, #3, #15, #33).
- Refund amounts of 0, -1, "100", 1.5, true and null each return 400 (#9-14).
- Notes: `"  locker: 5"` returns 422 (the check ignores case and leading spaces). 161 characters and whitespace-only notes return 400 (#28-30).
- Malformed JSON, a JSON array, an 8 KB nested array and invalid UTF-8 each return 400, and the server keeps responding (#34-38).
- A failed services call did not change another customer's order.

## Test gaps (source tests inspected, not run)
`test_domain.py` covers only happy paths and one 422 case. No test covers cumulative refunds, stale versions, services rollback or cross-user access. That is why all three high-severity defects would pass the existing tests. Add regression tests for each repro above.

## Not explored / residual risk
- Concurrent requests: all writes run under one global lock, so I judged races low risk and did not probe them.
- Services with duplicate IDs, unusual Content-Length values, and route variants such as `/api/orders/x/A100` on GET. The code takes the last path segment, so this looks like loose routing but not an auth bypass. None of these were probed.
- 403-versus-404 responses reveal whether an order ID exists. The requirements allow either status, so I did not report this.

## Fixture state changes (for the owner reset)
- **Irreversible:** B100 `refunded` = **6000** (paid 4000), caused by defect 1. There is no way to undo a refund.
- **Version counter:** A200 address restored to "20 Pine Street", but `version` = **4** (was 1).
- Restored: A100/A200 service back to `standard`, A200 note back to "Ring twice". A100 is untouched apart from its service, which is restored.

## Evidence
- `evidence/probe.py`: the probe script. `probe_output.txt` and `probe_log.json` hold every request and response.
- `evidence/restore_output.txt` and `restore_log.json`: the restore actions and a final state check.
