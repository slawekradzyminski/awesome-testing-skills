# Dispatch Desk administrative API release assessment

## Session

**Assessment: no High or Medium release blocker found in the administrative API checks performed. One Low-severity note-validation defect should be tracked or repaired before claiming full conformance.** Refund accounting, ownership enforcement, optimistic address updates, and bulk-service atomicity passed the exercised scenarios. This is a bounded API assessment, not a production or browser release certification.

- Date: 12 September 2026; assessment began approximately 11:27:30 UTC and completed before 11:32 UTC, within the six-minute limit.
- Target: assigned disposable runtime `http://127.0.0.1:59820` only. Supplied source, tests, and requirements in `app/` were reviewed; source fingerprints and local Python version are in [build metadata](build.json). The runtime's deployment hash was not independently exposed or verified.
- Scope: order reads, fixture-user isolation, refund administration, address administration, bulk services, notes, malformed requests, and saved-state preservation. Browser work was unnecessary for this API scope; no browser session was created.
- Resources: **110 API requests, zero browser actions**. Existing tests: **4/4 passed**. Additional first-pass assertions: **108/108 passed**; supplementary status checks: **20/22 passed**, with both failures demonstrating the same defect below. These are check counts, not independent feature counts.
- Evidence: [HTTP index](http-index.md), [requests 1–88](http-evidence.json), [requests 89–110](boundary-evidence.json), [first-pass assertions](checks.json), [supplementary checks](boundary-checks.json), and [existing-test output](existing-tests.txt).

## Findings

### API-01 — Whitespace padding bypasses the saved note length limit

**Type:** functional input validation/data integrity. **Evidence:** confirmed through POST responses and subsequent GET reads. **Status:** open; reproduced twice; no product changes made. **Severity:** Low.

**Preconditions:** Alice can access A200, whose original note is `Ring twice`.

**Minimal reproduction:**

1. Send `POST /api/orders/A200/note` with `X-Test-User: alice`, JSON content type, and a JSON object whose `note` is 160 `n` characters followed by one space (161 characters total).
2. Observe HTTP **200**, with all 161 characters returned as the saved note.
3. Send `GET /api/orders/A200` as Alice. Observe that the 161-character note persisted.

Exact bodies and responses are recorded in [boundary evidence](boundary-evidence.json), requests **99–100**. A second reproduction, requests **101–102**, submits one `n` followed by 1,000 spaces and persists **1,001 characters**, also with HTTP 200.

**Expected and basis:** [the product brief](../app/requirements.md) limits notes to 1–160 nonblank characters and requires malformed inputs to return 400. A note over the maximum should return **400** and retain the previous saved note. At minimum, a normalized-input policy must not persist a value beyond the stated limit. Actual behavior accepts and persists the entire padded value.

**Cause supported by source:** [domain.py](../app/domain.py), lines 69–74, checks `len(note.strip())` but assigns the original, untrimmed `note`. Address updates normalize the value they save; notes do not.

**Affected users and demonstrated impact:** any fixture customer/API client can save an instruction beyond the supported size. The demonstrated impact is a saved-data contract violation. No downstream truncation, delivery failure, financial loss, or cross-customer effect was demonstrated; this limited impact supports Low severity. Clients can work around it by trimming notes and enforcing the 160-character maximum before submission.

**Acceptance criteria:** enforce nonblank content and the maximum against the value actually stored. Under the current rejection contract, 161-character padded notes return 400 and leave the old note unchanged; valid 1- and 160-character notes still save, and `LOCKER:` rejection still preserves the old note. If the team deliberately adopts trimming before validation, verify that both the response and subsequent reads contain at most 160 characters. Add regression cases for trailing and leading whitespace at the boundary.

**Retest:** not repaired and therefore not retested after a fix. The reproduction's changes were restored.

## Coverage and handoff

| Risk | Evidence and result |
| --- | --- |
| Cross-customer access and anonymous mutations | Alice/Bob lists and detail reads; both directions of forbidden refund/address/note updates; anonymous and unknown actors; bulk operations containing forbidden orders. Rejections returned 401/403 and checked state remained unchanged. Requests 1–17, 89–98. |
| Refund accounting | Invalid amounts including boolean, float, string, zero, negative, null and containers returned 400. Above-payment and cumulative over-refunds returned 409. A100 accepted 4,000 then exactly 6,000 cents, rejected 6,001 between them and further refund afterward. Requests 22–35. |
| Concurrent refund requests | Two synchronized clients requested 4,000 cents each against A200's 6,000 cents. One returned 200 and one 409; final total was 4,000. Requests 36–38. This is one observed competing pair, not a load or exhaustive scheduling test. |
| Address validation and lost updates | Bad address/version shapes returned 400; a 120-character address saved; a stale version returned 409 without changing the saved value or version. Two synchronized updates using version 2 produced one 200 and one 409, preserving the winner at version 3. Requests 39–52. |
| Bulk service atomicity | Owned-first/missing-later, owned-first/forbidden-later, forbidden-first, and multiple-owned/missing-last combinations returned 403/404 with no partial service changes. Valid Alice bulk and Bob single-order changes persisted; invalid service/ID shapes returned 400. Requests 53–68, 94–95, 106–108. |
| Notes and rejection preservation | Blank, wrong-type and unpadded 161-character inputs returned 400. Uppercase and whitespace-prefixed lowercase locker instructions returned 422 and retained the old note. Valid lengths 1 and 160 saved. Padding exception is API-01. Requests 69–77, 98–104. |
| Request parsing and missing resources | Invalid JSON syntax, non-object JSON, empty body, invalid UTF-8, missing operation fields and an oversized body returned 400; missing order reads and mutations returned 404. Requests 18–21, 78–82, 96–98, 105. |

**Remaining limits and next work:** no browser journey, keyboard, responsive-layout, or out-of-order UI testing was performed. Production authentication, real payments, external integrations, general hardening, documentation-only defects, performance SLAs, and exhaustive fuzz/load testing were excluded. For this API surface, add regression coverage for the demonstrated padding defect and retain the exercised accounting, stale-edit and bulk-rollback cases in the project suite. The existing four domain tests cover routine paths and do not establish these broader guarantees.

**Cleanup:** all original addresses, notes, and service choices were restored and checked through final reads (requests 109–110). Bob's entire order matches its initial state. Irreversible fixture changes requiring the owner's reset are:

- A100 refunded total: **0 → 10,000 cents**; version remains 1.
- A200 refunded total: **0 → 4,000 cents**; address version **1 → 4**, including restoration.

See [initial state](initial-state.json) and [final state](final-state.json). No reset endpoint was called, and no source, supplied tests, requirements, or guidance were edited. [The assessment script](assess_api.py) and [supplementary script](boundary_checks.py) are evidence-generating, stateful scripts; rerun the main script only after the fixture owner resets the instance.
