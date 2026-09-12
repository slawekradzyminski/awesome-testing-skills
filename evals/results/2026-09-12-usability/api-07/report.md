# Sign-in validation exploration

No defects were observed in the scoped runtime checks. All 38 functional requests produced the expected status and feedback; a separate availability request succeeded. This is a bounded result, not an assertion that the application is defect-free.

## Scope and environment

Charter: challenge `POST /api/v1/users/signin` validation and determine whether its corrective feedback guides a caller from invalid fields to the specified credential rejection. The oracle was the supplied `requirements.md`, chiefly AUTH-1 and AUTH-4. Tests used synthetic URL-safe usernames and invented passwords; the only email was `example@synthetic.test` in an ignored extra field. No registration was created.

Runtime: `http://127.0.0.1:49531`. `GET /health` returned 200 and advertised `validation-fixture-1`. No explicit source revision was supplied, and exact deployed-source correspondence is unknown. Inspected source SHA-256 identifiers and HTTP timestamps are in [session metadata](evidence/session.json). The source routing/parser and sign-in validator were read; no existing test files were supplied, so none were run. The application and supplied instructions were not changed.

## Evidence and outcomes

Full sanitized request descriptions, status codes, response headers, JSON bodies and timings appear in [HTTP evidence](evidence/http.json), with request numbers below. Invented string passwords are represented by lengths and UTF-8 byte counts in the evidence; the [probe script](evidence/explore.py) documents synthetic construction for reproduction. Source excerpts with line numbers are in [source review](evidence/source-review.txt).

| Behavior | Evidence | Result |
| --- | --- | --- |
| Representative valid lengths | #2 | 422 with exactly `Invalid username/password supplied` |
| Username/password ASCII lengths 0, 3, 4, 255, 256 | #3–7, #14–18 | 4 and 255 accepted for credential evaluation; 0, 3 and 256 returned 400 and field-specific 4–255 guidance |
| Missing, null, numeric, boolean, array and object fields | #8–13, #19–24, #37 | 400; correct field identified |
| Unicode password lengths 3, 4, 255, 256 | #25–28 | Same character boundaries as ASCII; 255 non-BMP characters (1020 UTF-8 bytes) returned 422 |
| Corrective sequence | #29–31 | Both short → username guidance; username corrected → password guidance; both corrected → specified 422 |
| Extra fields | #32 | Ignored; 422 unchanged |
| Malformed JSON and array/null/string bodies | #33–36 | 400 with parser/object feedback |
| 8192-byte object, then 8193-byte object | #38–39 | 8192 reached normal credential validation; 8193 rejected with 413 `Request too large`. Exact over-limit status is unspecified by AUTH-4. |

Each listed variation was executed once; the corrective sequence independently repeats the minimum-length transition with different synthetic values. No suspicious behavior required a reproduction loop. The source uses `len(value)` and validates username before password (`app/domain.py:6–11`), consistent with the observed response sequence. The contract does not require aggregation of all errors, so sequential guidance is not classified as a defect. Returned bodies and headers were preserved, rather than judging status codes alone.

## Risk map and remaining scope

| Area / plausible risk | Priority and reason | Observation / next action |
| --- | --- | --- |
| Off-by-one boundaries or misleading guidance | Initially high: core requested behavior | Explored with no defect; retain focused boundary and corrective-sequence regression cases |
| Byte versus character counting | Initially medium: Unicode contract | Non-BMP password boundaries passed; Unicode usernames omitted under URL-safe restriction |
| Parser bypass or extra-field influence | Initially medium: shared request entry point | Invalid shapes rejected, extras ignored, encoded size boundary checked |
| Existing regression protection / build identity | Residual low: tests and exact revision unavailable | Request tests and deployed revision before assessing regression coverage |
| Compound Unicode semantics | Residual low: untested and no observed failure | Clarify intended character unit before testing combining sequences; do not infer a defect from ambiguity |

Signup, lookup, deletion and registration persistence were outside this sign-in charter and were not exercised. No UI/browser work was performed and no UI observations or screenshots are claimed. Production authentication, login success, normalization, concurrency and password strength remain outside the fixture contract.

## Accounting and cleanup

39 API requests total: 1 availability request and 38 functional sign-in requests, below the 60-request limit. Browser actions: 0. Work completed within the five-minute task budget. HTTP start/end and timing are recorded in session metadata. No registrations or connections require cleanup; no browser was opened. The fixture service remains under its owner's lifecycle control. Deliverables are this report, `submission.json`, and `evidence/`. There are no unfinished mandatory checks within the selected charter.
