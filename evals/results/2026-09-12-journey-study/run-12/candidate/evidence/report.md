# Dispatch Desk administrative API release assessment

**Recommendation: release the assessed administrative API surface. No confirmed release-blocking defect was found.** This is a bounded assessment of the supplied disposable application, not certification of its browser experience or production infrastructure.

Assessed on 2026-09-12 against `http://127.0.0.1:57710`, using the business requirements and implementation in `app/`. All **118 recorded checks passed across 97 API requests**. The **four supplied unit tests also passed**. No browser session was created, no external service was contacted, and supplied source, tests, requirements, and guidance were not edited.

## Evidence and coverage

Request numbers below refer to the `request` field in [http.jsonl](http.jsonl); concurrent requests can appear out of numerical order. Each entry records the identity, method, path, payload, response status, and response body. Detailed assertions are in [results.json](results.json).

| Release risk | Observed behavior | Evidence |
| --- | --- | --- |
| Access to another customer's data or administrative operations | Alice and Bob lists contained only their own orders. Cross-customer detail reads, refunds, address edits, notes, and services returned 403 in both directions. Missing/unknown identities returned 401 on reads and all four write operations. Missing orders returned 404. Complete fixture snapshots were unchanged after rejected access attempts. | Requests 1–32 |
| Malformed data accepted or causing an error instead of 400 | Rejected zero/negative/fractional/boolean/string/null refund amounts; blank, oversized, or incorrectly typed addresses; boolean/string/fractional versions; empty/blank/oversized/non-string notes; invalid service and ID collections. Representative transport checks rejected broken JSON, arrays, null, scalar JSON, empty body, invalid UTF-8, and an oversized body with 400. Complete state remained unchanged. | Requests 33–64 |
| Partially applied service batches | `[A100, B100]` and `[A200, B100]` returned 403; `[A100, MISSING]` returned 404. In each case the permitted order appeared first, exposing potential early mutation. The following complete snapshots matched baseline. A valid two-order express change returned both updated orders and persisted on a separate GET. Restoring standard also succeeded. | Requests 65–71, 94–97 |
| Rejected notes overwrite saved instructions | Notes of 1 and 160 characters succeeded. `LOCKER: 1` and a whitespace-prefixed lowercase variant returned 422 with actionable error text. A subsequent GET retained the previous 160-character note. | Requests 72–76 |
| Lost address updates | A 120-character address saved and advanced version 1 to 2. A subsequent version-1 edit returned 409 and preserved the newer address. Two synchronized clients then submitted different addresses at version 2: exactly one received 200, one received 409; GET returned the winner at version 3. | Requests 77–82 |
| Refunds exceed the original payment | Sequential 1,000- and 2,000-cent refunds accumulated to 3,000. A 7,001-cent request returned 409 and a subsequent GET still showed 3,000. Refunding exactly the remaining 7,000 succeeded; an additional cent returned 409. | Requests 83–88 |
| Concurrent refunds bypass the cumulative cap | Two synchronized 4,000-cent refund requests against A200's 6,000-cent payment produced one 200 and one 409. A subsequent GET showed exactly 4,000 refunded. | Requests 89–91 |
| Verification leaves avoidable fixture changes | Original addresses, notes, and services were restored and checked through final reads. Bob's complete order remained unchanged. Irreversible effects are listed below. | Requests 92–97; [baseline.json](baseline.json), [final-state.json](final-state.json) |

Source inspection supports the observed behavior: ownership checks precede domain writes (`app/domain.py:18–24`); refunds compare against the remaining balance (`:26–36`); address version checks precede mutation (`:38–49`); services validate every selected order before changing any (`:51–63`); note validation precedes saving (`:65–75`). The HTTP server holds its shared lock across domain checks and writes (`app/app.py:77–85`), supporting serialization of concurrent updates. These observations supplement the runtime evidence.

## Actions for the team

1. Retain the negative and concurrency cases as regression coverage, particularly cumulative refund rejection without mutation, competing same-version addresses, and permitted-first mixed service batches. The supplied four tests cover routine domain calls and do not establish these guarantees on their own.
2. Have the fixture owner/controller reset this instance before another assessment. Final balances and counters are below; all reversible fields have already been restored.
3. Keep the browser journey as a separate release check if shipping the UI with this API. Order-selection consistency, draft retention, visible feedback, keyboard access, and narrow layouts were outside this administrative API assessment and were not tested.

| Order | Refunded before → after (cents) | Address version before → after |
| --- | --- | --- |
| A100 | 0 → 10,000 | 1 → 4 |
| A200 | 0 → 4,000 | 1 → 1 |
| B100 | 0 → 0 | 1 → 1 |

A100's third version increment came from restoring its original address. Refunds and version increments have no authorized reversal route.

## Reproduction and limits

[assess_api.py](assess_api.py) contains the exact runtime sequence, payloads, assertions, and two-client barriers. It uses only Python's standard library and the assigned loopback URL. Run `python3 evidence/assess_api.py` **only after the fixture owner resets the instance**; it assumes initial fixture balances and versions, performs real fixture refunds, and overwrites its evidence outputs. The supplied tests were run with `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s app -v`; output is in [existing-tests.txt](existing-tests.txt).

Concurrency evidence comprises one synchronized pair for each of refunds and addresses, supported by review of the shared lock; it is not a sustained load test. Malformed JSON envelope checks used the note endpoint, with source review confirming the shared POST parser. Successful changes were checked across separate HTTP requests; persistence through a server restart is neither promised nor tested. Real authentication, payments, emails, production hardening, performance SLAs, documentation-only issues, and external integrations were excluded as directed.
