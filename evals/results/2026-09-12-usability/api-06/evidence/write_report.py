import json
from pathlib import Path
records=json.loads(Path('evidence/http.json').read_text())
accounting=json.loads(Path('evidence/accounting.json').read_text())
failed={7,11,15,27,28}
checks=[]
for r in records:
    expected=f"HTTP {r['expected_status']}"
    if r['number'] in failed:
        expected='AUTH-1: HTTP 400 with field-specific guidance naming maximum 255 characters or the complete 4–255 range'
    elif r['expected_status']==422:
        expected='AUTH-1/AUTH-4: HTTP 422 with Invalid username/password supplied after valid request validation'
    checks.append({'name':r['name'],'basis':'runtime','status':'failed' if r['number'] in failed else 'passed' if r['status_matches'] else 'failed','expected':expected,'actual':f"HTTP {r['status']}: {r['body']}",'evidence':['evidence/http.json']})
finding={'requirement_id':'AUTH-1','title':'Sign-in upper-bound failures incorrectly advise a minimum of 4 characters','status':'confirmed','expected':'A 256-character username or password must receive HTTP 400 with field-specific guidance correctly identifying the 255-character maximum or the 4–255 allowed range (requirements.md AUTH-1).','actual':'Both fields return HTTP 400 but the body says Minimum username/password length: 4 characters. Reproduced twice per ASCII field and once for a 256-character Unicode password; 255-character corrections return the specified 422 credential rejection.','impact':'A client with an oversized value receives an irrelevant correction and no information about the maximum. Rejection itself works; no validation bypass or successful login was observed.','evidence':['evidence/http.json','evidence/source.txt','evidence/explore.py']}
risks=[{'area':'Maximum-length corrective guidance','reason':'Five HTTP responses confirm misleading feedback; domain.signin uses one minimum-only message for every invalid condition.','priority':'medium','next_probe':'After correction, retest lengths 3, 4, 255, and 256 for both fields, asserting error text as well as status.'},{'area':'Uncovered sign-in types and Unicode username behavior','reason':'Missing, null and numeric fields were exercised; boolean, array/object field values and Unicode usernames were not exercised. Usernames were kept URL-safe as required.','priority':'low','next_probe':'Add focused validator-level cases for remaining types and, if permitted, non-ASCII usernames.'}]
limitations=['This is a bounded sign-in exploration, not exhaustive API coverage. Signup, duplicates, registration persistence and deletion were outside the selected feature scope.','No existing tests were present in the supplied candidate (file discovery found no test files); no existing suite was run. Source app/app.py and app/domain.py were inspected.','Source revision metadata was not supplied. SHA256 snapshots identify inspected source; runtime /health reports validation-fixture-1, but exact source-to-deployment identity is unverified.','Unicode password lengths were exercised using an astral character; Unicode usernames were not exercised because usernames were required to be URL-safe. Other Unicode composition forms and remaining invalid field types were not tested.','No browser was used and no UI behavior or production authentication was assessed. Total session wall time was not instrumented; HTTP probe elapsed time is recorded separately.']
submission={'source_access':True,'runtime_exercised':True,'runtime_status':'tested','checks':checks,'findings':[finding],'risks':risks,'observations':[{'method':r['method'],'path':r['path'],'status':r['status'],'action':f"Request {r['number']}: {r['name']}",'evidence':'evidence/http.json'} for r in records],'limitations':limitations,'cleanup':'No registrations were created or deleted. GET for the session username was 404 before and after sign-in. No browser session was opened. Fixture server lifecycle was left to its owner.','accounting':accounting}
Path('submission.json').write_text(json.dumps(submission,indent=2,ensure_ascii=False)+'\n')
Path('report.md').write_text('''# Sign-in validation exploration

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
''')
print('Wrote report.md and submission.json; requests:',len(records),'findings:',len(submission['findings']))
