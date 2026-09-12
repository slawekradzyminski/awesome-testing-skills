# Cart quantity API exploration

No discrepancies were observed against CART-1 through CART-4 in the tested cases. This is a bounded runtime assessment, not a defect-free certification. No findings are asserted.

## Charter and environment

Assess whether existing cart updates respect identity isolation, quantity validation, stock and totals, including read-after-write and rejection atomicity. API scope only; checkout, re-adding removed items, production authentication and service lifecycle excluded.

Target: `http://127.0.0.1:49528`; date: 2026-09-12. Requirements: supplied `requirements.md` (CART-1–4; UI-1–2 noted as untested). Source access explicitly unavailable. Source revision, deployed build and their relationship are unknown. Public disposable fixture identities Alice and Bob were used; evidence contains role names rather than authorization headers.

Accounting: 38 actual HTTP requests, 0 browser actions, 0 failed availability requests. HTTP exploration ran 2026-09-12T09:10:09Z to 2026-09-12T09:10:42Z. The complete task stayed within five minutes and the 60-request ceiling; no automatic retries or browser-generated requests. The runtime responded immediately, so the six-request availability-failure stop condition was not triggered.

## Results and evidence

Each numbered ID refers to one line/record in [HTTP evidence](evidence/http.jsonl), which captures method/path, role, submitted JSON, status, response headers/body, timestamp, duration and intent. The one-off client is `explore.py`; it is not a regression suite.

| Check | Expected | Observed |
| --- | --- | --- |
| Authenticated product data | Fixture notebook price 12 and stock 5 | GET returned product 1, Workshop notebook, price 12, stockQuantity 5 (request IDs 5) |
| CART-1: anonymous access and mutation | Anonymous API access is rejected | Products/cart GET and item PUT returned 401; follow-up Alice read unchanged (request IDs 1,4,23,24) |
| CART-1: identity isolation | Caller sees and changes only own cart | Separate initial Alice/Bob quantities; Alice update left Bob unchanged; Bob update carrying username=alice changed only Bob; zero removal left Bob unchanged (request IDs 2,3,6–8,28–30,35–37) |
| CART-2: valid quantities and persistence | Non-negative integers accepted within stock | Quantities 3 and 5 persisted on Alice, 4 on Bob; successful restore updates also persisted (request IDs 6,7,25,26,28,30–34) |
| CART-2: invalid quantity atomic rejection | Negative, fractional, missing, null, string and boolean quantities return 400 and leave cart unchanged | -1,1.5,missing,null,string 2,true each returned 400; each immediate GET retained Alice quantity 3 and totals 3/36 (request IDs 9–20) |
| CART-3: stock boundary and failure atomicity | Above five returns 409 without mutation; five accepted; stock not reserved/decremented | 6 returned 409 and quantity stayed 3; 5 accepted; product stock stayed 5 across updates and removal (request IDs 21,22,25–27,38) |
| CART-4: calculated persisted totals | totalItems sums quantities and totalPrice uses price 12 | Read-after-write totals matched 3/36,5/60,4/48,1/12,2/24,0/0; client totalPrice=1 did not override Bob total 48 (request IDs 7,26,28,30,32,34,36) |
| CART-2: zero removal | Quantity zero removes existing item | Alice PUT returned empty items and zero totals; subsequent GET confirmed removal (request IDs 34–36) |

The negative input probes each ran once from quantity 3, with an immediate state read after every rejection. No failure needed reproduction. The ownership extra-field contrast ran once: Bob submitted `{"quantity":4,"username":"alice","totalPrice":1}`; the response and follow-up read remained Bob-owned with totalPrice 48, while Alice stayed at quantity 5. This supports the specific tested isolation boundary, not every possible authorization surface.

## Prioritized residual risks

| Area | Evidence / uncertainty | Priority and next useful probe |
| --- | --- | --- |
| UI-1 and UI-2 browser behavior | API-only charter; browser was not used. Server behavior cannot establish provisional edits, Cancel, visible feedback or keyboard/narrow-width usability. | high: With a fresh fixture, exercise edit/cancel/reopen/save with browser network evidence and desktop/narrow keyboard checks. |
| Malformed JSON and retry/concurrent outcomes | Only valid JSON objects and sequential requests were exercised; no source or deployed build identity supplied. | medium: Inspect relevant parser/update code when available, then test one malformed JSON request and controlled repeated/concurrent updates against an agreed ordering contract. |

No missing test or unimplemented out-of-scope feature is classified as a defect. Existing tests were unavailable and not run. Further broad sequential probes were stopped after the scoped core risks had evidence and no promising anomaly remained. If building regression coverage later, favor validator/domain tests for the invalid classes and representative API integration checks for identity separation, rejected-write atomicity and zero-removal persistence.

## Limitations

- Source unavailable by task instruction; source revision, deployed build identifier and source/build relationship unknown. No application code or existing tests inspected or executed.
- UI-1/UI-2 were not tested; no browser opened and no screenshots claimed.
- Sequential bounded exploration of one product and two disposable identities; no concurrency, malformed JSON, service failure injection or production authentication assessment.
- Checkout, adding removed items and service lifecycle are out of scope.

## Cleanup and handoff

Bob restored to quantity 2 and totalPrice 24, verified by requests 32 and 37. Alice was restored to 1 before the final zero-removal test, then left empty (request 36). Re-adding removed items is explicitly not implemented/in scope, so owner reset is required to recover Alice initial fixture. Product stock remains 5. No service lifecycle action taken; no browser session opened.

Outstanding work: a fresh fixture is needed for Alice-based UI coverage. UI checks listed above remain unexecuted; this report makes no visual or accessibility claims. No application, requirements, skill or existing test files were changed.
