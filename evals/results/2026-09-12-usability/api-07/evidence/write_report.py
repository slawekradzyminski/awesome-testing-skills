import json
from pathlib import Path
records=json.loads(Path('evidence/http.json').read_text())
meta=json.loads(Path('evidence/session.json').read_text())
Path('evidence/source-review.txt').write_text('Source inspection only; no existing test files were supplied or run.\nCandidate file inventory before evidence creation: TASK.md, REPORTING.md, requirements.md, app/app.py, app/domain.py, app/requirements.md, skills/api-exploratory-testing/* (guidance), app/__pycache__/domain.cpython-314.pyc.\nSource revision: no supplied revision identifier; no parent directory or parent repository inspected. SHA-256 identifiers in session.json.\n\n'+''.join(f'{path}:\n'+''.join(f'{i:3} {line}\n' for i,line in enumerate(Path(path).read_text().splitlines(),1))+'\n' for path in ('app/domain.py','app/app.py')))
checks=[]
for r in records:
    if r['id']==1: expected='Availability: HTTP 200; capture advertised build independently of source.'
    elif r['expected_status']==422: expected='AUTH-1: length-valid credentials return 422 with Invalid username/password supplied; AUTH-4 ignores extra fields and accepts objects within 8192 bytes.'
    elif r['expected_status']==413: expected='AUTH-4 allows objects up to 8192 bytes; over-limit rejection is appropriate, but its exact status is not specified.'
    elif r['id'] in (33,34,35,36): expected='AUTH-4: malformed JSON or a non-object returns 400.'
    else: expected='AUTH-1: invalid username/password type or length rejected with 400; out-of-range feedback identifies the field and 4–255 range.'
    checks.append({'name':r['name'],'basis':'runtime','status':'passed' if r['passed'] else 'failed','expected':expected,'actual':f'HTTP {r["status"]}; '+json.dumps(r['body'],ensure_ascii=False),'evidence':['evidence/http.json']})
checks.append({'name':'Sign-in validation and parsing source reviewed','basis':'source','status':'passed','expected':'Inspect supplied routing, validation, error handling and existing relevant tests.','actual':'Read app/app.py and app/domain.py. No supplied test files discovered; tests unavailable, not executed. Source hashes captured; deployed-source correspondence unknown.','evidence':['evidence/source-review.txt','evidence/session.json']})
limitations=['Focused on sign-in validation and corrective feedback; signup, lookup, deletion, and registration persistence were not exercised.','Unicode username probes were omitted to honor the URL-safe username constraint; Unicode password coverage used single-codepoint non-BMP characters, not combining sequences.','No existing tests supplied; none executed. No UI was used, and no UI usability conclusions or screenshots are claimed.','Source revision and deployed-source correspondence are unknown. The runtime advertises validation-fixture-1; local source hashes identify the inspected files only.','This bounded session does not establish exhaustive correctness. Login success, production authentication, normalization, concurrency and password strength are outside the fixture contract.']
risks=[{'area':'Unicode username and compound Unicode handling','reason':'URL-safe username constraint prevented non-ASCII username probes. Only non-BMP single-codepoint passwords were exercised; source uses Python len(). No failure observed.','priority':'low','next_probe':'If permitted and the meaning of Unicode characters is clarified, test Unicode usernames and combining-sequence password boundaries.'},{'area':'Existing regression protection and build identity','reason':'No existing tests or explicit source revision supplied; runtime build label alone does not prove exact source correspondence.','priority':'low','next_probe':'Obtain the deployed source revision and existing validator tests, then retain focused ASCII/Unicode boundary and corrective-sequence regression cases.'}]
submission={'source_access':True,'runtime_exercised':True,'runtime_status':'tested','checks':checks,'findings':[],'risks':risks,'observations':[{'method':r['method'],'path':r['path'],'status':r['status'],'action':f'#{r["id"]}: {r["name"]}','evidence':'evidence/http.json'} for r in records],'limitations':limitations,'cleanup':'No registrations or other stateful resources created. No browser opened. Fixture service left running for its owner. Only report/submission/evidence files created in this candidate directory.','accounting':{'api_requests':39,'availability_requests':1,'functional_requests':38,'browser_actions':0,'http_start':meta['started'],'http_end':meta['ended']}}
Path('submission.json').write_text(json.dumps(submission,ensure_ascii=False,indent=2))
Path('report.md').write_text('''# Sign-in validation exploration

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
''')
print(json.dumps({'checks':len(checks),'findings':len(submission['findings']),'requests':len(records),'all_passed':all(r['passed'] for r in records)}))
