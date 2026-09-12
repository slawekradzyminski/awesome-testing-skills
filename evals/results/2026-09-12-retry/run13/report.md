# Public API contract and authentication exploration

One runtime-confirmed documentation defect was found. Anonymous access to products and cart was correctly rejected without returning catalog or cart data.

## Session and evidence

Target: https://awesome.byst.re, 12 September 2026. Charter: compare the public live contract with anonymous protected-route behavior and stop after reproducing a useful discrepancy. Public read-only scope; six direct GET requests, zero browser actions, no credentials/cookies, no redirects followed, no submissions or mutations. HTTP evidence has UTC timestamps and timings. Work completed within the five-minute limit (approximately four minutes; exact full-session timing was not instrumented). Eleven tool calls including final artifact verification; no token or cost metrics available.

The live contract reports OpenAPI 3.1.0, API version 1.0. That version is not a deployed commit identifier. Source snapshots were supplied but their Git metadata is absent; exact source revisions and deployed build match are unknown. [Source excerpts and SHA256 identities](evidence/source-evidence.txt) preserve the inspected evidence. No numbered business requirements were supplied, so the finding is UNMAPPED and uses the live operation schema as its oracle.

## Finding: products 401 response has the wrong documented JSON type

**Confirmed contract/documentation defect; provisional Low severity.**

The live `GET /api/v1/products` contract declares its 401 body as an array of ProductDto. Both anonymous runtime requests returned `401`, `Content-Type: application/json;charset=UTF-8`, and `{"message":"Unauthorized"}`. The two independent specification fetches both retained the array declaration. Reproduction: 2/2 product requests, each paired with a fetched live contract. An object cannot satisfy an array schema. [Exact reproduction](evidence/reproduction.txt), [comparison](evidence/contract-comparison.json), [first response](evidence/http-3.json), [repeat response](evidence/http-6.json), [live repeated specification](evidence/body-5.txt).

The demonstrated consequence is a contract-validation failure. Generated-client parsing failures are a possible downstream effect, not an observed result. Authentication enforcement succeeded; no data exposure was observed. The corrective expectation is accurate error documentation, not changing the response to a product array.

In the source snapshot, ProductController.java:25 declares 401 without an explicit error schema and its method at line 34 returns List<ProductDto>. ErrorResponseDefinition.java:12-19 writes the message object. Inference: response-schema inference likely reused the success return type. Source/deployment equivalence is unknown; the finding rests on live evidence independently of that inference.

OpenApiContractTest.java:135-139 and 151 assert response-code presence, not this 401 body schema. GetAllProductsControllerTest and GetCartControllerTest include anonymous 401 status assertions. These tests were inspected, not executed. Suggested regression: a generated-OpenAPI integration assertion for the explicit ErrorDto schema on 401 plus a representative anonymous HTTP body/schema check. Retest on an identified fixed build.

## Risk map and coverage

| Area | Evidence / impact | Priority | Result / next step |
| --- | --- | --- | --- |
| Anonymous private-route access | Source requires bearer authentication; live products/cart both return 401 message objects with no-store cache headers | High exploration priority | No defect observed in these cases; authenticated isolation remains untested |
| Products error contract | Array declaration versus object, reproduced twice | Medium exploration priority | Confirmed documentation finding above |
| Cart error contract | Live 401 references CartDto but returns a message object | Medium | Documentation ambiguity: CartDto has no required fields and allows extra properties, so this is not a demonstrated schema-validation failure; clarify intended ErrorDto |
| Cart ownership and roles | Snapshot uses principal username; no authenticated contrasts allowed | High residual priority | Authorized disposable users with separate fixtures required |
| Token lifecycle and login | Valid/expired/revoked tokens and form workflows excluded | Medium residual priority | Authorized disposable session required |

`GET /login` returned 200 HTML; no rendering, accessibility, focus, or responsiveness claim is made. `GET /v3/api-docs` returned 200 JSON twice and identifies bearerAuth on both scoped protected operations. Products returned 401 twice; cart returned 401 once. [All observations](evidence/observations.json). No malformed-token probes were needed to establish the documentation discrepancy.

## Limits and cleanup

Only the four allowed paths were requested. No accounts, email, forms, private record enumeration, mutations, injected faults, or stored credentials were used. No browser was opened. Authenticated 200 bodies, cross-user isolation, admin restrictions, token lifecycle, and state transitions require a separately authorized disposable session. The exploration is bounded and is not exhaustive API coverage.

No product/source/test/skill changes or external issues were made. Only this report, submission.json, and evidence remain; no fixtures or sessions require cleanup. Source revision and deployed build identification remain outstanding before attributing a code cause or retesting a change.
