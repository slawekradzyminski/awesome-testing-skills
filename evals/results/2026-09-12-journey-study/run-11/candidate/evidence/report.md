# Dispatch Desk administrative API release assessment

**Recommendation:** The scoped administrative API is a release candidate: no functional defect or release blocker was observed in this assessment. All 102 exploratory checks passed across 105 API requests, and all four supplied unit tests passed. This is bounded evidence for the tested behavior, not exhaustive certification.

## Scope and environment

Assessed on 2026-09-12, approximately 11:09–11:12 UTC, against `http://127.0.0.1:57635` only. The charter was to challenge ownership enforcement, refund conservation, optimistic address concurrency, bulk-change atomicity, and preservation of saved instructions after rejection. The oracle was [app/requirements.md](../app/requirements.md), especially lines 5–13. Followed the supplied API exploration skill and its experiment-design and reporting references.

Used fixture users Alice and Bob, anonymous requests, and one unknown fixture identity. Read the supplied routing, domain implementation, requirements, and all existing tests. No browser session was created; browser behavior was outside this administrative API assessment. No external services, delegation, product fixes, or documentation-only findings were involved. Used 105 of 120 API requests and zero of 80 browser actions; stopped when the principal risks had useful evidence and remaining probes offered diminishing value.

There is no candidate-local Git metadata, so the source revision is unavailable. Exact SHA-256 fingerprints of the four assessed files are in [summary.json](summary.json). The deployed build identifier is unknown: observed behavior is consistent with the supplied source, but their identity is not established. The first representative order-list read returned usable fixture records before mutations began.

## Risk assessment and results

The ordering prioritizes cross-customer effects and financial/state corruption over input edge cases. **No confirmed findings, suspected defects, or failing checks remain from the explored cases.** All rows below are “explored with no defect observed”; remaining coverage limitations follow separately.

Request numbers refer to the `n` field in [http.json](http.json), which records methods, paths, fixture actors, inputs, response statuses, headers, complete bodies, and timing. [checks.json](checks.json) contains the assertions and outcomes.

| Area / priority | Source evidence and plausible failure | Live probe and observation | Existing protection and next action |
| --- | --- | --- | --- |
| Ownership / highest | `domain.py:18–24`; every mutation calls the ownership lookup. A bypass could expose or alter another customer's data. | Requests 2–21: owner lists, Alice→Bob and Bob→Alice reads plus all four mutation families, and anonymous reads/writes. Cross-owner requests returned 403; anonymous requests returned 401. Follow-up lists showed all fields unchanged. Unknown identity also returned 401 (104). | Source checks ownership before mutation. Add domain authorization regressions and representative HTTP identity checks. Production authentication is outside scope. |
| Refund conservation / highest | `domain.py:26–36` validates type and remaining balance; `app.py` serializes domain calls with one lock. Multiple partial refunds or competing requests could exceed payment. | 22–39: zero, negative, bool, fractional, string, null, and missing amounts returned 400 without changing balance. Partial refunds of 1,000 then 2,000 cents accumulated to 3,000. A 3,001-cent request returned 409 and preserved 3,000. Two competing 2,000-cent requests produced one 200 and one 409, leaving 5,000. Refunding the exact remaining 1,000 succeeded; another cent was rejected, leaving 6,000. | Supplied test checks only one partial refund. Add cumulative/exact-limit/type domain tests and one bounded concurrent HTTP regression. No real payment execution was assessed. |
| Address concurrency / high | `domain.py:38–49` checks version before writing. A stale edit could replace a newer address. | 40–52: blank, null, 121-character addresses, and bool/string versions returned 400 without changes. A 120-character address saved at version 1 and advanced to 2. A stale version-1 edit returned 409 and retained the complete saved row. Two edits at version 2 produced one 200 and one 409; the winner persisted at version 3. | Existing test checks only a successful increment. Add domain stale-state preservation tests and one HTTP competing-update test. Concurrent pair was exercised once, without forced scheduling. |
| Bulk service atomicity / high | `domain.py:51–63` gathers authorized rows before writing. Early writes could survive a later missing or forbidden ID. | 53–67: valid two-order express change succeeded. Missing and forbidden IDs were tested both before and after A100 in the batch. Results were 404/403 respectively; each immediate read showed both Alice orders entirely unchanged. Invalid service, empty list, non-list IDs, and mixed ID types returned 400 without changes. Standard service was restored successfully. | Existing test checks only successful express output. Add parameterized domain tests asserting the entire state after each failed batch. |
| Notes and rejected saves / medium | `domain.py:65–75` validates length and unsupported locker instructions before writing. Rejection could silently replace the saved instruction. | 68–82: valid note persisted; `LOCKER: 1` and whitespace-prefixed lowercase `locker: 2` returned 422 with actionable instructions. Each retained the prior complete row. Blank, null, and 161-character notes returned 400 with unchanged state. A 160-character note was accepted. Missing/bool/numeric notes returned 400 (100–102). | Existing rejection test checks only status, so add state-preservation assertions and length boundaries at the domain level. Browser draft retention and feedback rendering were not assessed. |
| HTTP parsing and privileged extra fields / medium | `app.py` requires a bounded JSON object; domain mutations assign named fields. Invalid payloads or extra properties could corrupt unrelated fields. | 83–89: malformed JSON, array, null, empty body returned 400; valid mutation payloads for missing orders returned 404. 96–105: Bob could save his own note; attempted extra `owner`, `paid`, `refunded`, `version`, and `service` fields were ignored in response and follow-up read. Oversized JSON returned 400. Bob's original full row was restored. | Add representative HTTP parser tests and a domain extra-property isolation check. Additional HTTP framing, unsupported methods and deep parser stress were not explored. |

## Verification and evidence quality

Executed `python3 -m unittest discover -s app -v`: four tests passed (`test_address_save`, `test_note_rejection`, `test_partial_refund`, `test_services`). They exercise the domain directly, with no HTTP integration or concurrency assertions. Tests were inspected as well as executed; their passing result does not establish the untested business invariants by itself.

The live exploration checked persisted state through follow-up reads, including after error responses. Concurrent experiments used two client threads against the assigned runtime, one pair each for refunds and address updates. These demonstrate the observed outcomes under ordinary scheduling; they do not prove every possible interleaving. No load or performance SLA claim is made. HTTP evidence contains JSON content types and `Cache-Control: no-store`; no outage or transport failure occurred.

The 102 checks are assertions from one-off exploratory scripts, not 102 independent regression tests. [explore.py](explore.py) and [followup.py](followup.py) preserve the executed experiments. **They mutate fixture data and assume a fresh initial state; do not rerun them against the already-refunded fixture.** The follow-up script additionally expects the first script's evidence. No regression suite or application code was changed.

## Remaining risks and recommended action

1. Preserve the demonstrated invariants with focused regression tests: ownership and cumulative refund limits first, then stale address preservation and failed bulk atomicity. Put most cases at the domain level; retain small HTTP checks for parsing, actor propagation, and concurrency. Missing tests are a maintenance risk, not a product defect.
2. Associate the assessed source fingerprints with the actual release build before treating this session as evidence for another deployment. No build identity was supplied or exposed by the inspected application.
3. If the browser journey is part of the same release decision, assess it separately: out-of-order selection, draft retention on rejection, keyboard focus, and narrow layouts were not tested here. These are explicit scope limits, not inferred failures.
4. Persistence across process restart, retries after lost responses, larger concurrency patterns, exhaustive Unicode/whitespace boundaries, and general HTTP hardening remain untested. The demo explicitly promises fixture lifetime persistence, not durable production storage; no defect is inferred from that limitation.

## Cleanup

Restored original addresses, notes, and services, verified Alice's final state (94) and Bob's final state (105), and checked that ownership/payment fields remained unchanged. [initial-state.json](initial-state.json) and [final-state.json](final-state.json) record the principal session snapshots; Bob's final follow-up snapshot equals both.

The fixture owner must reset these authorized, irreversible session effects:

- **A200 refunded:** 0 → **6,000 cents**, fully refunded.
- **A100 version:** 1 → **4**, including the address restoration increment.

A100's address is again `10 Oak Street`; all notes and services match their initial values. Bob's entire order is unchanged. No browser session or background process needs closing. Supporting evidence contains disposable fixture identities only, with no production credentials.
