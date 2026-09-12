# Sign-in validation exploration

One runtime-confirmed AUTH-1 defect was found: oversized usernames and passwords receive minimum-length guidance instead of the applicable maximum. Input rejection itself works.

## Scope and environment

The charter was to assess `POST /api/v1/users/signin` validation and actionable correction, stopping after meaningful boundary contrasts and reproduction. The supplied limits were five minutes, 60 API requests and 45 browser actions. Only `http://127.0.0.1:49527` and files within this candidate were used. All credentials were invented; usernames were URL-safe. No registration mutations were needed.

Runtime build: `/health` reported `validation-fixture-1`. UTC timestamps are in [HTTP evidence](evidence/http.json). Source revision metadata was unavailable; [source evidence](evidence/source.txt) records complete inspected files with SHA256 fingerprints and line numbers. Correspondence to the deployed build is not independently established. The requirements supplied in `requirements.md` are the behavioral oracle. No existing test files were found in the supplied candidate; no existing suite was run.

## Finding: upper-bound errors give the wrong correction

**AUTH-1; functional contract defect; runtime-confirmed; provisional Low severity.** The impact is misleading feedback in an otherwise working rejection path.

Minimal reproduction: POST a JSON object to `/api/v1/users/signin`, with `username` set to 256 copies of ASCII `u` and an invented 4–255-character password. The result is HTTP 400, `Content-Type: application/json`, and `{"username": "Minimum username length: 4 characters"}`. Alternatively, use the URL-safe username `probe_c_0612` and a password of 256 ASCII `p` characters; the response is `{"password": "Minimum password length: 4 characters"}`. Both examples have values already above the stated minimum, and the responses do not identify the required maximum.

AUTH-1 requires field-specific guidance correctly identifying the allowed 4–255 range or violated boundary. The expected error should therefore identify maximum 255 characters or the complete range. A caller cannot learn from the current message how to correct an oversized value. No bypass, successful login, or downstream harm was demonstrated.

Evidence: [HTTP requests 7, 11, 15, 27, 28](evidence/http.json) show five occurrences: username ASCII twice, password ASCII twice and password Unicode once. Adjacent valid lengths of 255 return the specified HTTP 422 `Invalid username/password supplied`, including the correction in request 29. The first failures were preserved before repeat probes. [Source `app/domain.py`, lines 6–10](evidence/source.txt) explains the likely cause: every invalid type or length follows the same minimum-only response branch. The source behavior agrees with the observed responses, though deployment identity remains unverified.

Retest after correction: assert status and applicable guidance for 3 and 256 characters, with accepted validation at 4 and 255. Add direct `signin` unit tests for the text in each boundary branch and a small representative HTTP integration check. No application, tests, requirements, or skill files were changed.

## Explored behavior and risk map

| Behavior / initial risk | Priority and reason | Observed evidence | Outcome / next action |
| --- | --- | --- | --- |
| Misleading upper-bound guidance | Medium: code uses minimum-only feedback | Requests 7, 11, 15, 27, 28 | Confirmed defect; correct message and retest |
| Off-by-one validation | Medium: affects every sign-in | ASCII lengths 3, 4, 255, 256 for both fields | Statuses correct; 3 rejected, 4/255 reach credential rejection, 256 rejected |
| Unicode password length counted as bytes | Medium: contract explicitly counts Unicode characters | Astral-character password lengths 3, 4, 255, 256 | Correct length decisions; upper-error text remains defective |
| Missing or invalid field types | Medium: potential validation bypass | Missing/null/numeric values independently for each field | All HTTP 400 and field-specific; no bypass observed |
| Invalid envelope and extra fields | Low: parser boundary | Malformed `{`, array `[]`, nested unknown field | Invalid envelopes HTTP 400; unknown field ignored |
| Encoded body-size boundary | Low: parser boundary | Exactly 8192 and 8193 encoded bytes | 8192 reaches HTTP 422; 8193 rejected with HTTP 413. Contract gives no exact above-limit status requirement |
| Unexpected sign-in state creation | Low: no successful account in fixture | Own username GET before and after | Both 404; no created record observed for this username |

Every HTTP status matched the planned status. Five checks nevertheless fail because their response guidance violates AUTH-1. A green status-only subset would miss this defect. Full request/response semantics, headers, timings and the complete 30-request accounting appear in [HTTP evidence](evidence/http.json). Password values are represented by synthetic placeholders and character/byte counts in that evidence; the [reproduction script](evidence/explore.py) generates only invented values and documents the exact byte-sized bodies.

## Limits and cleanup

Signup, duplicates, registration lifecycle, production authentication and UI behavior were outside this sign-in charter. Unexplored sign-in variants include boolean/list/object field values, additional Unicode composition forms and non-ASCII usernames (the task required URL-safe usernames). These are residual coverage gaps, not additional defects. A next useful probe is focused validator coverage of those types and, if authorized, Unicode usernames.

**Accounting:** 30 API requests, including one health/availability request and two lookup requests; zero browser actions and zero browser sessions. No retries were implicit. The probe script records its own elapsed execution time in [accounting](evidence/accounting.json); total session wall time was not instrumented. No accounts were created, no cleanup deletion was necessary, and no browser connection remains. The server was neither started, repaired nor stopped. No further checks are needed to complete this bounded report; proposed regression checks require a subsequent correction task.
