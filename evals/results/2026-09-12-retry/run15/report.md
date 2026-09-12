# Public API and authentication boundary exploration

Tested https://awesome.byst.re on 2026-09-12, beginning 08:47:38 UTC. Six direct HTTP GET requests, zero browser actions, no credentials, no redirects followed, no mutations. Only the four permitted paths were requested. Source snapshots were read as supporting context; their deployed revision is unknown.

## Confirmed finding: published products 401 schema disagrees with runtime

**Requirement: UNMAPPED. Priority: medium.** The live OpenAPI document is the contract basis: `paths["/api/v1/products"].get.responses["401"].content["*/*"].schema` declares an array of ProductDto. Requests without Authorization or Cookie headers returned HTTP 401 with `application/json;charset=UTF-8` and `{"message":"Unauthorized"}`, an object. This repeated twice. The authentication status is correct; the error-body contract is incorrect.

Reproduce with GET `/v3/api-docs` accepting JSON, inspect that schema, then GET `/api/v1/products` accepting JSON without credentials. Compare the response's top-level object type with the documented array. A schema validator expecting an array rejects this observed response. Generated-client deserialization failures are plausible but were not tested.

Evidence: [live contract](evidence/02-v3-api-docs.body), [first response](evidence/03-api-v1-products.body), [response headers](evidence/03-api-v1-products.headers), [repeat response](evidence/05-repeat-api-v1-products.body), [offline comparison](evidence/contract-analysis.txt).

Related observation: the live cart 401 response references CartDto, yet both cart requests returned the same error object. This is misleading documentation, but CartDto has no required properties and allows additional properties, so this exploration does not claim a formal schema-validation failure for cart. Both controllers in the supplied source declare class-level 401 annotations without explicit content schemas. That is consistent with success-model inference, but causation and deployed source identity are unverified. The source error writer emits a message object. See [source excerpts](evidence/source-excerpts.txt).

## Coverage and passing observations

| Request | Outcome | Evidence |
|---|---|---|
| GET /login | 200 HTML application shell | evidence/01-login.body and .headers |
| GET /v3/api-docs | 200 JSON OpenAPI 3.1.0 | evidence/02-v3-api-docs.body and .headers |
| GET /api/v1/products, twice | 401; error only, no catalog data | evidence/03-api-v1-products.body; evidence/05-repeat-api-v1-products.body |
| GET /api/v1/cart, twice | 401; error only, no cart data | evidence/04-api-v1-cart.body; evidence/06-repeat-api-v1-cart.body |

The stack README documents 200 for login and OpenAPI. The backend README documents authenticated product access; source security configuration protects remaining endpoints. The live spec marks products and cart as bearer-protected. Its generated server URL correctly names `https://awesome.byst.re`. Offline traversal of the downloaded spec found no unresolved local references or duplicate operation IDs across 53 operations. This is a focused structural check, not full OpenAPI validation or execution of those operations. All HTTP observations and evidence names are in [the request log](evidence/http-observations.json).

## Important gaps requiring an authorized disposable session

- **High:** ownership and role enforcement remain untested. In an authorized disposable environment, use two ordinary users and an administrator to check cart isolation and role-controlled product actions with cleanup.
- **High:** token expiry, refresh, logout/revocation, 2FA and password-reset behavior remain untested. Exercise those flows only with disposable accounts and explicit authorization for mutations/email.
- **Medium:** authenticated 200 product/cart payload conformance and session transitions remain untested. Obtain authorized disposable sessions, compare success payloads with the downloaded contract, and verify browser session transitions.
- **Low:** no rendered UI, keyboard, responsive or browser-network inspection was performed. The login 200 establishes shell availability only; a fresh public browser session could check labels and focus without submitting forms.

No malformed-token probes, rate-limit stress, other HTTP methods, private-record enumeration or requests outside the permitted paths were made. Public documentation alone cannot establish deployed implementation identity. Findings on unexercised endpoints are not inferred from this narrow boundary check.

## Cleanup and timing

No browser session or application process was created. No product, source, test, account or remote data was changed. Only the required local deliverables and evidence were created. No external issues were filed. Timing and request/action counts are recorded in evidence/run-metrics.json; token and monetary usage were unavailable.
