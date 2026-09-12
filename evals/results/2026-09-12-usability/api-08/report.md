# Registration exploration

One runtime-confirmed functional defect: signup rejects valid passwords above 72 UTF-8 bytes despite AUTH-2 allowing 8–255 Unicode characters. Severity: **Medium, provisional**; registration is materially impaired for affected passwords.

## Session and evidence

Explored registration validation, persistence, duplicates and cleanup against `http://127.0.0.1:49530`, using only invented data and URL-safe usernames. Contract: supplied `requirements.md`, matching `app/requirements.md`. Deployed health response identifies `validation-fixture-1`; source revision is unavailable and its exact relationship to the deployed build is unknown. Source SHA-256 values are in [session metadata](evidence/session.json). No test files were supplied within this candidate; none were executed. Read relevant routing, validation and in-memory persistence source, captured in [app evidence](evidence/app.py.txt) and [domain evidence](evidence/domain.py.txt).

Used **60 HTTP requests**, including one health request; **zero browser actions**. No retries hidden by the HTTP client or availability failures occurred. Work stopped at the request limit within the five-minute session. [Complete HTTP evidence](evidence/http.json) records request bodies, byte counts, response headers/bodies, timing and numbered actions. All passwords there are invented fixture values. The scripts in `evidence/` preserve the executed experiments; they are exploratory evidence, not an added regression suite.

## Finding: signup applies an undocumented password byte limit

**Requirement:** AUTH-2 requires acceptance of otherwise valid unique registrations with 8–255 Unicode character passwords.

**Reproduction:** POST `/api/v1/users/signup` with a fresh URL-safe username, a unique `@example.test` email and a password constructed as `"A" * 73`. Expected 201 and GET of the username returning username/email. Actual: 400, JSON `{"error":"password cannot be more than 72 bytes"}`, then GET 404. Requests 11–12 preserve the first failure.

The ASCII 73-character case reproduced on **2/2 fresh registrations** (11–12 and 19–20). A 255-character ASCII password also failed (13–14). An 18-emoji password, 72 UTF-8 bytes, succeeded and persisted (15–16); a 19-emoji password, 76 bytes, failed and remained absent (17–18). A 72-character ASCII control succeeded (9–10). These bodies are all below the 8192-byte request ceiling, with independent synthetic usernames/emails; duplicates and payload size do not explain the failures.

**Demonstrated impact:** Users cannot register with passwords explicitly permitted by the contract. The effective character ceiling depends on UTF-8 encoding. No sensitive storage, data corruption or broader authentication consequences were observed.

**Source evidence:** `app/domain.py:4` declares `MAX_ENCODED_PASSWORD_BYTES = 72`; lines 18–19 enforce it after the declared character check. Runtime boundary behavior matches this branch, although deployment provenance cannot be verified. This is one independently fixable problem, not separate ASCII and Unicode defects.

**Next action:** Align password validation with AUTH-2. Recommend domain tests at 8/72/73/255/256 ASCII characters and representative multibyte boundaries; retain representative API checks for acceptance and persistence. No fix was made or verified.

## Results and risk map

| Area | Risk and priority | Evidence and outcome | Next action |
| --- | --- | --- | --- |
| Password lengths | High exploration priority: source conflicts with contract | Confirmed defect above; 8-character password succeeds (57–58); 7, 256 and null reject without writes (21–26) | Focused corrective tests and retest |
| Persistence and ignored fields | Medium: returned data might differ from stored state | Successful POST/GET contain exactly username/email; password and extra admin/displayName fields absent (3–4). Exact 8192-byte body with ignored padding succeeds (43–44) | No defect observed in tested cases |
| Duplicates | Medium: retry might overwrite or create a second record | Duplicate username returns 409 and original stays unchanged (5–6); duplicate email returns 409 with new username absent (7–8) | No defect observed in tested cases |
| Username/email validation | Medium: invalid data might persist | Username lengths 3/256 reject and remain absent; 4/255 succeed. Missing email local/domain and array-valued email reject and remain absent (27–40) | Missing-field and other type permutations remain untested |
| JSON parsing/size | Low after observed controls | Malformed JSON and array root return 400 (41–42); 8192-byte object accepted | 8193 bytes and other root types remain untested |
| Cleanup | Medium: records or uniqueness claims might remain | Seven successful registrations deleted with 204 and individually confirmed absent via GET 404 (45–56,59–60). A deleted email is reusable (57–58) | No disposable registrations remain |

Structured results contain **29 checks: 25 passed, 4 failed**, with all four failed checks supporting the single password finding. Passing cases do not establish exhaustive coverage.

## Limitations and closeout

Sign-in is outside this registration charter. Production authentication, full email syntax, normalization, concurrency, password strength and login success are outside the fixture contract. Restart behavior, all missing/type permutations, additional Unicode classes and over-limit body rejection were not tested. No browser was opened, so there is no browser cleanup or UI evidence. The fixture owner retains server lifecycle control.

All seven successful registrations were deleted and confirmed absent; identified rejected registrations also returned 404. No application, requirements, skills or existing tests were changed. Remaining work is the password validation fix followed by the focused retest above; no exploration cleanup remains.
