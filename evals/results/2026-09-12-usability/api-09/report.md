# Registration exploration report

No defects were observed in the tested cases. All 27 runtime checks passed; this is bounded evidence, not a claim that the application is defect-free.

## Session and environment

- Charter: challenge registration validation, duplicate handling, persistence and disposal using source-informed HTTP probes against AUTH-2, AUTH-3 and AUTH-4 in `requirements.md`.
- Runtime: `http://127.0.0.1:49532`, tested 2026-09-12. Health reported `validation-fixture-1`.
- Scope limits: five minutes, 60 API requests; actual 58 requests including one health request, zero browser actions. HTTP experiment elapsed 0.03 seconds; inspection and reporting completed within the five-minute task budget. No service was started or repaired.
- Synthetic disposable values only; no authentication was needed for the fixture's public lookup/cleanup routes. Passwords in HTTP evidence are represented by type, character count and byte count; the replay script contains only invented test values.
- Source reviewed: `app/app.py` routing/parsing/persistence/cleanup and `app/domain.py` validators. Source hashes and independent runtime identity are in [session metadata](evidence/session.json). No revision metadata was supplied; source-to-deployment identity remains unknown.
- Existing tests: no test files present in the supplied app directory. None run. [Numbered source evidence](evidence/source.txt).

## Risk-led exploration

| Area | Initial concern and priority | Observation and disposition |
| --- | --- | --- |
| Password limits | High exploration priority: Unicode byte guard could disagree with the declared character range. | ASCII 7/255/256 and four-byte Unicode 7/8/255/256 tested; all matched AUTH-2. The 255-character Unicode case is 1020 UTF-8 bytes and succeeds. No defect observed. |
| Persistence and duplicates | High: invalid or duplicate writes could leave records or overwrite an existing email. | Rejected candidates read as 404; duplicate username/email returned 409, original state survived, and alternate username remained absent. |
| Username/email validation | Medium: boundary and type handling could bypass validation. | Username lengths 3/4/255/256, missing email parts, absent @, empty email, and selected wrong types all behaved as required. |
| Parsing and envelope | Medium: malformed input and body limits could bypass checks. | Malformed JSON and array body returned 400. Exactly 8192 encoded bytes succeeded; 8193 returned 413 with no record. Extra fields were ignored. |
| Cleanup | Medium: deleting one record could damage others or leave state. | All successful creates received DELETE 204. Baseline survived other deletes, then its own DELETE was followed by GET 404. |

## Checks and evidence

Actual request/response headers, bodies, timings, actions and monotonically numbered request IDs are preserved in [HTTP evidence](evidence/http.json). The [check ledger](evidence/checks.json) records requirement expectations and actual outcomes. The [experiment script](evidence/explore.py) documents exact inputs; it was executed once.

| Check | Result | HTTP request IDs |
| --- | --- | --- |
| valid baseline and ignored fields | passed | 2, 3 |
| duplicate username preserves record | passed | 4, 5 |
| duplicate email creates no record | passed | 6, 7 |
| ascii7 | passed | 8, 9 |
| ascii255 | passed | 10, 11, 12 |
| ascii256 | passed | 13, 14 |
| unicode7 | passed | 15, 16 |
| unicode8 | passed | 17, 18, 19 |
| unicode255 | passed | 20, 21, 22 |
| unicode256 | passed | 23, 24 |
| name3 | passed | 25, 26 |
| name4 | passed | 27, 28, 29 |
| name255 | passed | 30, 31, 32 |
| name256 | passed | 33, 34 |
| emaillocal | passed | 35, 36 |
| emaildomain | passed | 37, 38 |
| emailat | passed | 39, 40 |
| emailempty | passed | 41, 42 |
| pwnull | passed | 43, 44 |
| namelist | passed | 45, 46 |
| emailnumber | passed | 47, 48 |
| malformed | passed | 49 |
| nonobject | passed | 50 |
| 8192 byte envelope | passed | 51, 52, 53 |
| 8193 byte envelope | passed | 54, 55 |
| cleanup isolation | passed | 56 |
| delete then absent | passed | 57, 58 |

## Findings

None confirmed, code-evidenced or suspected within this exploration. The UTF-8 guard is compatible with the tested maximum Unicode length; its presence alone is not a defect. The intentionally public fixture routes and storage model are not evaluated as production security behavior.

## Limitations and next useful checks

This bounded session exercised registration, lookup and deletion; signin was outside the chosen registration charter and was not exercised. 58 API requests total including one successful availability request; zero browser actions, no browser session opened. No requests were made to other runtimes. No existing tests were found in the supplied app directory; none were run. The recorded script is a one-off experiment, not a regression suite. No concurrent registration, normalization, full email syntax, production authorization, password strength, delivery, or successful login testing; these are outside the fixture contract. Not every omitted field, invalid JSON shape, Unicode sequence, or wrong-type combination was tested. Oversized body rejection was observed as 413; the contract does not prescribe its exact status. Source revision metadata unavailable in the allowed directory; source hashes recorded independently from deployed health version. State absence after DELETE was explicitly read back for the baseline; other successful creations each received DELETE 204.

Residual risk is low within the tested scope. A useful next step is focused validator regression coverage for omitted fields, representative type errors and mixed Unicode values, plus one integration lifecycle test covering invalid-write absence, duplicate preservation and delete/readback. No test suite or application changes were made.

## Cleanup and handoff

All 7 registrations created by this session received DELETE 204. Baseline GET after deletion returned 404. No owned registrations remain. No browser was opened; the fixture service was left running for its owner. No unfinished execution or cleanup remains. The remaining checks above are explicitly unperformed coverage suggestions. Deliverables are `report.md`, `submission.json` and the linked evidence files.
