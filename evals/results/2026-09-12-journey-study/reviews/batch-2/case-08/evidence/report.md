# Dispatch Desk administrative API release assessment

**Recommendation:** The tested ownership, money, concurrency and atomicity rules show no release blocker. One **Low-severity functional defect** remains: surrounding whitespace bypasses the stored delivery-note length limit. Fix it before a release that promises strict input bounds, or explicitly accept this limited deviation. This bounded assessment does not certify the entire application.

## Scope and evidence

Assessment on 2026-09-12, approximately 11:26–11:29 UTC, against **http://127.0.0.1:59662**, using disposable fixture identities Alice and Bob. Charter: challenge administrative authorization, cumulative refunds, stale address writes, service-batch atomicity and rejected-note persistence, stopping after important risks have discriminating evidence within six minutes and 120 API requests.

Executed **97 API requests**, **0 browser actions**, and all **4 supplied unit tests** (all passed). No external services, product changes, issue filing or delegation. The API was available; no outage blocked exploration. Requirements oracle: [product brief](../app/requirements.md). Source and tests were inspected before selecting probes. Source revision metadata is unavailable in the candidate; [environment.json](environment.json) records SHA256 fingerprints. The deployed build is not exposed, so source/deployment identity is unverified, although observed behavior agrees with the inspected implementation.

Evidence: [HTTP requests, responses, headers and timings](http.jsonl), [initial representative read](baseline-read.json), [probe checks](checks.json), [follow-up checks](followup-checks.json), [unit-test execution record](unit-tests.txt), and [unchanged-artifact check](integrity.txt). There are 85 recorded checks: 83 passed and two failed assertions demonstrate the same note-length defect. These counts are observations, not a coverage percentage. Request numbers below refer to the `n` field in the HTTP evidence.

## Risk map and outcomes

Money and ownership were prioritized for direct customer impact; stale updates and partial batch writes followed because they silently lose or partially apply changes. Validation boundaries were selected from the actual parsing and persistence paths.

| Area / plausible failure | Evidence and existing protection | Runtime observation | Status / next action |
| --- | --- | --- | --- |
| Refunds exceed original payment | Domain checks remaining balance; supplied test covers only one partial refund | #19–33: invalid types/values rejected; 6000 accepted, 4001 rejected with 409 leaving 6000, exact remaining 4000 accepted, next cent rejected. Two competing 2500 refunds on Bob's 4000 payment yielded 200/409 and total 2500 | No defect observed. Add cumulative and competing-refund regression cases |
| Another customer's data is read or changed | Shared ownership check in domain; HTTP fixture identity gate; no supplied ownership tests | #4–14, #83–89: anonymous and unknown identities rejected, cross-owner reads and all write types denied, before/after snapshots unchanged | No defect observed. Preserve two-role API tests, including mixed-owner service batches |
| Stale address silently overwrites newer edit | Version comparison and increment under server lock; supplied test covers only successful save | #34–45: invalid types and overlength rejected; version 1 save produced 2; stale version returned 409 and preserved address. Two version-2 edits yielded one success and one conflict; read matched winner | No defect observed. Add stale-state preservation and competing-write checks |
| Failed service batch partially changes earlier orders | All rows selected before write loop; supplied test covers only all-valid batch | #46–55, #86–89: missing and forbidden IDs after an allowed ID rejected with 404/403; reverse ownership order also checked; every service remained unchanged. Valid express batch persisted; standard restored later | No defect observed. Add a late-invalid-ID atomicity regression |
| Failed note replaces saved instructions; length limit bypass | Validation precedes write, but validates trimmed text and stores original; supplied test checks only locker status | #56–67, #90–94: empty/blank/161 nonspace characters rejected; 1 and 160 accepted; LOCKER and padded lowercase locker returned 422 with previous note preserved. Padded 161/162-character notes persisted | **API-01 confirmed**. Repair length validation and test persisted value |
| Malformed request reaches mutation | HTTP parser bounds JSON body and requires object; domain validates fields | #15–18, #78–89: malformed JSON, arrays, null, empty body, missing required fields and oversized body returned 400; follow-up snapshots unchanged | No defect observed in selected cases. Retain representative integration checks |

## API-01 — POST /api/orders/{id}/note persists notes over 160 characters

**Type:** FA (functional API, validation). **Severity:** Low. **Status:** Open. **Evidence:** Runtime-confirmed; two successful reproductions using different padded inputs on the same fixture. Not a fresh-fixture repetition or a post-fix retest.

**Precondition:** Alice owns A200. Read and retain its note for cleanup. At the first reproduction, the saved note contained 160 `n` characters, following a successful boundary save and rejected locker requests.

**Reproduction from the candidate directory:**

```sh
curl --max-time 5 -i \
  -H 'X-Test-User: alice' -H 'Content-Type: application/json' \
  --data-binary @evidence/API-01-request.json \
  http://127.0.0.1:59662/api/orders/A200/note
curl --max-time 5 -i -H 'X-Test-User: alice' \
  http://127.0.0.1:59662/api/orders/A200
```

The [request file](API-01-request.json) contains 160 `n` characters followed by one space: **161 total characters**. POST #64 returned **200**, JSON content type and `Cache-Control: no-store`, with all 161 characters in `note`. GET #65 returned the identical order including that note. A leading and trailing space around 160 `n` characters also returned 200 and persisted **162 characters** (#66–67). In contrast, 161 nonspace characters returned 400 (#58). [Focused evidence](API-01-evidence.json) preserves full payloads and responses.

**Expected:** Under the brief's 1–160-character note limit and malformed-input rule, reject this oversized note with 400 and preserve the saved note. The brief does not explicitly define whitespace normalization; this finding applies the stated limit to the note that is actually saved and returned. If the product intends a normalized-length rule, saving the normalized bounded value would resolve the persisted-length inconsistency; that alternative needs an explicit product decision.

**Impact:** A caller can store a delivery instruction outside the stated bound. No demonstrated financial impact, cross-customer access, rendering failure or downstream truncation. Severity remains Low because the observed impact is limited to violating the field bound.

**Cause:** [domain.py](../app/domain.py), lines 70–74, checks `len(note.strip())` but saves `note` unchanged. The HTTP route calls that method directly. The nearby address implementation both validates and stores trimmed content; #93–94 confirmed its saved address stayed at 120 characters. This contrast isolates note persistence rather than JSON parsing as the issue.

**Acceptance and regression:** Enforce the intended limit on the persisted note. With the current literal input contract, reject 161-character padded notes with 400 and no state change; keep valid 1- and 160-character notes working and preserve 422/no-write locker behavior. A focused domain test should assert status **and stored state** for the padded boundary, with one API follow-up read to protect integration. No product fix or post-fix retest was performed.

## Test gaps and residual risks

The supplied four tests assert one partial refund, a successful address version increment, successful service updates and the locker rejection status. They do not establish cumulative refund safety, concurrency, ownership, batch rollback or state preservation after rejection. The live evidence supplies bounded confidence for those cases; proposed regressions above should preserve it.

Highest-priority remaining validation is to run the focused checks against an identified release build. Each concurrency experiment used only one pair of competing HTTP requests; it is evidence for that execution, not exhaustive scheduling or load testing. Unicode length semantics, unusual transport framing, ambiguous/lost write responses and exhaustive input combinations were not explored. Browser race handling, feedback, keyboard use and layout are outside this administrative API assessment. Production authentication, payment integrations, general hardening and performance SLAs are excluded by the brief. Persistence was verified by API reads, not by restarting the in-memory server.

## Cleanup and handoff

All original addresses, notes and service choices were restored and verified through reads. [Final state](final-state.json) compared with [initial state](initial-state.json) retains only authorized, irreversible effects:

- **A100 refunded: 0 → 10000 cents.**
- **B100 refunded: 0 → 2500 cents.**
- **A200 address version: 1 → 6**, including restoration writes.

The fixture owner/controller must reset those amounts and counters. No browser session was created. Exploration scripts are retained for review; the full probe expects initial fixture state and should only be replayed after owner reset. No supplied source, tests, requirements or guidance were changed.
