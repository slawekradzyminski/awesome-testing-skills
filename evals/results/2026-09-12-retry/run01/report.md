# Cart API exploration

One runtime-confirmed CART-2 defect: negative integer quantities are saved and produce negative cart totals. Both existing unit tests pass but neither covers the missing lower bound.

## Session and scope

Explored the existing cart read/update API and product catalog at `http://127.0.0.1:64091` on 2026-09-12. Source inspection began at 08:28:14 UTC. Budget: five minutes, 60 API requests, 45 browser actions. Used 42 HTTP requests total (41 API requests and one health request), zero browser actions. This was a short source-informed session, not exhaustive coverage. Request timing, status, relevant response headers, bodies, identity labels and purpose are recorded in [HTTP evidence](evidence/http.json); readable equivalents are in [http.txt](evidence/http.txt).

Oracle: candidate `requirements.md`, specifically CART-1 through CART-4. Fixtures: Alice starts at quantity 1; Bob at quantity 2; notebook product ID 1, price 12, stock 5. Only these disposable carts were modified. No application, requirement, skill, or existing test source was changed.

Runtime `/health` reports `sample-1`, with Python 3.14.7 in the HTTP server header. No source commit identifier is provided within the inspected files. [SHA-256 fingerprints](evidence/source-sha256.json) identify the inspected source; exact correspondence to the deployed build is unknown. Matching responses and logic support, but do not prove, correspondence.

Charter: determine whether an existing-item update enforces quantity/stock rules, persists correct totals, and confines writes to the authenticated fixture identity. Stop after major scoped hypotheses have discriminating evidence and the discovered anomaly is reproduced and cleaned up.

## Prioritized risk map

| Area | Evidence and plausible failure | Impact / priority | Protection and observed outcome | Next useful action |
| --- | --- | --- | --- | --- |
| Integer lower bound | `app/domain.py:24` validates exact int type but lacks a negative check before assignment at line 36 | Invalid saved quantities and totals; high exploration priority | Confirmed twice through PUT and follow-up GET | Add domain regression for -1 preserving state, fix validation, retest HTTP |
| Ownership | HTTP handler derives actor from bearer token; Store indexes carts by actor | Cross-user cart modification would be serious; high initial priority | Anonymous cart GET/PUT returned 401; Alice/Bob writes remained isolated; supplied username did not retarget Alice's update | Test malformed/invalid bearer credentials if expanding authentication coverage |
| Stock and atomic rejection | Stock guard precedes assignment; existing unit test covers 6 against stock 5 | Overselling/changed cart after error; medium | 5 accepted, 6 returned 409, GET retained 5; product stock stayed 5 | Small concurrent same-cart update probe only if a concurrency contract is established |
| Quantity types | Explicit exact-int guard; no existing type tests | Invalid inputs may corrupt persisted state; medium | Fractional, missing, null, string, true and false all returned 400; every follow-up GET remained quantity 1 | Parameterized domain tests plus representative route-level validation check |
| Totals and catalog | Cart total uses hardcoded 12 at `app/domain.py:21`; fixture catalog price is 12 | Future differing product prices could produce wrong totals; medium residual risk | All tested valid quantities matched quantity × catalog price; no present fixture discrepancy | With separately authorized price-changing fixture, verify totals follow current product price |
| Zero removal | Code deletes item for zero; API cannot re-add removed items | Removal semantics and empty totals; medium residual risk | Source inspected, live zero transition deliberately untested to keep fixture fully restorable | Use a resettable fixture lifecycle to PUT zero and GET empty cart and zero totals |

Ordering prioritized known validation weakness and identity exposure before stock/type boundaries. The hardcoded price and zero transition remain risks, not invented runtime defects.

## Finding F1 — PUT /api/v1/cart/items/1 saves negative quantity

- **Requirement:** CART-2 requires negative quantities to return 400 and leave the cart unchanged.
- **Classification:** functional defect, runtime-confirmed. **Severity:** Medium (provisional): persisted invalid cart state materially impairs the existing cart flow; no checkout or financial transaction impact was tested.
- **Precondition:** authenticated Alice, existing notebook item 1. Initial failure began at quantity 3; independent repeat began at restored baseline quantity 1.
- **Minimal reproduction:** read Alice's cart, send `PUT /api/v1/cart/items/1` with `Content-Type: application/json`, Alice's documented fixture bearer identity and body `{"quantity":-1}`, then GET `/api/v1/cart`.
- **Expected:** HTTP 400, previous quantity and totals preserved.
- **Actual:** HTTP 200 and JSON `{"username":"alice","items":[{"productId":1,"quantity":-1}],"totalItems":-1,"totalPrice":-12}`. A separate GET returns the same invalid state.
- **Reproduction:** 2 failures / 2 attempts. Evidence records 12–13 preserve the first occurrence; 14 restores quantity 1; 15–16 show the second occurrence; 17 restores the baseline. [Focused reproduction](evidence/reproduction.txt).
- **Demonstrated impact:** an authenticated caller can save an invalid negative quantity into their own cart, which then exposes negative item count and price. No cross-user effect or checkout consequence was observed. A valid positive update restores usable state.
- **Likely cause:** `Store.update` checks `type(quantity) is int` but never rejects values below zero. Negative integers bypass the stock upper bound and the zero-removal branch and reach persistence. This source explanation matches the HTTP result; deployed/source identity remains unverified.
- **Retest recommendation:** a domain test should assert -1 raises ApiError 400 and preserves the entire prior cart. Retest via the real route and independent GET; retain neighbors 0, 1, 5, 6 and boolean rejection. Zero requires disposable fixture reset because re-adding is outside this API's scope. No regression code or fix was implemented in this exploration.

## Existing tests and closeout

Read `app/app.py`, `app/domain.py`, and `app/test_domain.py`. Routing authenticates before domain calls, parses JSON objects, extracts quantity, selects the actor's cart and maps ApiError to JSON/status. Existing tests assert a positive update total with Bob unchanged and overstock rejection with quantity preserved; they do not assert negative/type validation or HTTP integration. Executed `python3 -m unittest discover -s app -v`: both tests passed; [output](evidence/unit-tests.txt).

Observed no defect for valid quantity persistence, tested totals, stock preservation, overstock atomicity, six invalid-type/missing cases, anonymous cart read/write rejection, and two-way fixture identity isolation. Extra `username: bob` in Alice's body was ignored and Alice remained the update target.

Limitations: no browser work or UI-1/UI-2 conclusions; no live zero-removal transition; no changing product prices, concurrency, transport fault injection, malformed JSON/body-size boundary, or invalid-token variants. Checkout, adding items, and production authentication are out of scope. Source revision/build linkage is unknown. Existing green tests do not establish comprehensive correctness.

Cleanup: Alice restored to quantity 1 / totalPrice 12, Bob restored to quantity 2 / totalPrice 24, independently verified by final GETs 41–42. Product stock remained 5 in the last catalog read. No browser was opened; server lifecycle remains with the fixture owner. Nothing remains to restore. Follow-up work: fix F1 and run the focused retest described above; no required exploration deliverable remains unfinished.
