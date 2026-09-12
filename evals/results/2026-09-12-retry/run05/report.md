# Cart API exploration

No confirmed defects were found in the explored API behavior. This is a bounded exploration, not an exhaustive coverage claim.

## Charter and environment

Investigate whether updating an existing item preserves caller isolation, validates quantities before mutation, enforces the stock boundary, and returns/persists correct totals. Scope: existing carts and product data; requirements.md CART-1–CART-4. UI-1/UI-2 were not exercised. No application, requirement, skill, or test source changes were made.

- Runtime: http://127.0.0.1:64179; `/health` returned `sample-1` (HTTP evidence #1).
- Source: supplied `app/app.py`, `app/domain.py`, and `app/test_domain.py` inspected. Revision was not supplied. SHA-256 fingerprints of source and contract are in [session metadata](evidence/session.json). The deployed version label agrees with the literal in source, but it does not prove source/build equivalence.
- Roles: public disposable Alice/Bob fixture identities, anonymous, and an invalid token. Evidence names roles and omits Authorization headers.
- Budget: 49 of 60 HTTP requests, 0 browser actions. Approximately three minutes total; exact end-to-end timing was not instrumented. The automated HTTP portion measured 0.027 seconds. Six shell/tool invocations were used through artifact creation; no token-usage metric is available.
- Requests used a five-second timeout. All returned HTTP responses; no ambiguous write outcomes occurred.

## Evidence and results

[HTTP evidence](evidence/http.json) contains every request's method, path, role, body, response status, response headers, full response body, purpose, sequence number, and duration. State reads surrounding writes establish the before/after result. The [exploration script](evidence/explore.py) records the actual sequence; rerunning its terminal removal requires a fresh fixture.

| Requirement / risk | Source-based hypothesis and priority | Actual exploration | Conclusion |
| --- | --- | --- | --- |
| CART-1 identity isolation | High initial priority: route must derive ownership from authenticated actor, ignoring client identity fields. `app.py:40–45,60–64,72–82` selects actor before domain calls. Existing test covers domain-level isolation only. | #2–12: Alice starts at 1, Bob at 2; anonymous reads/write and invalid token return 401; rejected write preserves Alice; Alice update to 3 leaves Bob at 2. #37–39: Alice supplies Bob in query/body; only Alice changes to 4, Bob remains 2. | No defect observed. Authentication and spoofing controls exercised through real HTTP. |
| CART-2 validation and failed-write atomicity | High initial priority: Python booleans resemble integers; validation must precede writes. `domain.py:24–25` uses exact type; handler passes missing quantity as null. No existing invalid-type tests. | #13–32: negative, fractional, null, string, true, false, array, object, floating-point 3.0, and omitted quantity all return 400. Follow-up reads retain quantity 3 and total 36 after every rejection. | No defect observed. Decimal-encoded 3.0 was rejected; the contract explicitly rejects fractions but does not separately define integral JSON floats, so this observation is not labeled a discrepancy. |
| CART-3 stock and atomicity | High initial priority: boundary rejection must not overwrite previous state or reserve stock. Guard precedes mutation in `domain.py:31–36`; existing domain test checks rejection of 6. | #33–36: 5 succeeds with total 60; 6 returns 409; subsequent GET retains 5. Product stock stays 5. #49 confirms stock after removal. | No defect observed. Inclusive boundary and stock invariance confirmed. |
| CART-4 totals | Medium initial priority: totals derive from stored quantities; price is hardcoded in `domain.py:21`. | Catalog #4 reports price 12; quantities 1,2,3,4,5 produce totals 12,24,36,48,60 across reads/updates. #47–48: empty cart has both totals 0. | Correct for current product data. Price-change behavior was not tested. |
| CART-2 zero transition | Medium initial priority: deletion follows a separate branch at `domain.py:33–34`; no existing test covers it. | #47 Bob quantity 0 returns 200, empty items, totalItems 0, totalPrice 0; #48 confirms persistence. | No defect observed. Terminal probe performed once on disposable Bob. |
| Parser and missing-item boundaries | Medium initial priority: parsing and domain errors must preserve existing cart. | #40 malformed JSON returns 400; #41 array root returns 400; #42 preserves Alice at 4. #43 unknown item returns 404; #44 preserves Alice. | No defect observed. Exact 404 is implementation behavior rather than a separately specified requirement. |

## Existing tests and residual risks

The two existing domain tests were inspected and executed with `python3 -m unittest discover -s app -p 'test_*.py' -v`. Both passed; [test output](evidence/unit-tests.txt). They assert updated total price and unchanged Bob quantity, plus stock rejection status and preserved Alice quantity. They do not protect the HTTP authentication/parser boundary, invalid input types, or removal. Missing tests are coverage gaps, not product defects.

1. **Medium — Concurrent cart transitions:** `ThreadingHTTPServer` shares the Store, and the lock protects audit writing only. Sequential observations do not establish concurrent read/update/removal consistency. Next useful experiment: a bounded synchronized read and removal on a fresh disposable fixture, with a defined acceptable outcome and final state check. No race was reproduced or claimed.
2. **Low — Current-price coupling:** totalPrice multiplies by literal 12 rather than looking up product price. The actual catalog also has price 12, and no product mutation API is in scope. Next useful action: if configurable pricing is introduced, add a domain test with a different product price and compare cart/catalog consistency. This is a future-data risk, not a current demonstrated discrepancy.
3. **Low — Durable HTTP regression protection:** domain tests bypass authentication and JSON parsing. Add a small representative API integration test for anonymous rejection, boolean/missing quantity rejection with unchanged state, and actor isolation. Keep type permutations and zero behavior primarily at domain level.

UI behavior, keyboard/narrow-width operation, transport failures, concurrency, oversized request framing, restart persistence, and changing catalog prices were not tested. Checkout, adding removed items, and production authentication are explicitly out of scope. No screenshots were taken and no UI finding is asserted.

## Cleanup and handoff

Alice was restored to original quantity 1 and total 12 (#45–46). Bob remains empty after the authorized zero-removal probe (#47–48); the API has no supported re-add operation. The fixture/process owner can restart the application to restore Bob to quantity 2. Stock remains 5 and price remains 12 (#49). The server was left running. No browser session was created. No outstanding check is necessary to substantiate the reported sequential results; the residual probes above remain unperformed.
