# Cart API exploratory assessment

One **code-evidenced defect** was found: the quantity-update API accepts and persists negative integers. No runtime behavior was confirmed. The assigned runtime was unavailable and was not started.

## Scope and method

Read the task, reporting contract, requirements, API handler, domain implementation, existing tests, and adjacent UI source. Traced the authenticated request through validation, mutation, and totals. Inspected the product fixture and both disposable cart identities. Application files and existing tests were not changed or executed.

- Product: notebook id 1, unit price 12, stock 5 (`app/domain.py:14`).
- Initial carts: Alice quantity 1, Bob quantity 2 (`app/domain.py:15`).
- Existing tests cover Alice quantity 3 with Bob isolation, and quantity 6 rejection preserving Alice's quantity. This is source inspection, not a passing test result.
- Evidence: [numbered source snapshots and hashes](evidence/source-review.txt).

## Finding: negative quantity is saved successfully

**Requirement:** CART-2. **Status:** code-evidenced. **Priority:** high.

Expected: `PUT /api/v1/cart/items/1` with Alice's disposable token and `{"quantity":-1}` returns 400 and leaves the cart unchanged.

Actual, derived from source: the handler passes -1 to `Store.update`. The domain rejects non-integers and quantities above stock, but has no lower-bound rejection. It saves -1 and returns a cart that the handler sends with status 200. The predicted persisted result has `totalItems: -1` and `totalPrice: -12`. This violates the permitted quantity range and corrupts the caller's cart state. No checkout or financial consequence is claimed.

Evidence: `app/domain.py:23–37`, totals at `app/domain.py:17–21`, and HTTP mapping at `app/app.py:69–87`, captured in [source evidence](evidence/source-review.txt). The [proposed reproduction](evidence/reproduction.txt) includes baseline reads, expected versus predicted behavior, a persistence check, Bob/stock checks, and restoration. None of those requests has been sent. The browser's minimum-value constraint cannot protect a direct API call.

## Source-supported coverage and remaining risks

| Area | Assessment and next probe | Priority |
| --- | --- | --- |
| Quantity matrix | Exact `int` checking appears to reject booleans, fractions, strings, null and missing quantity before mutation. Validate each through HTTP with before/after cart reads, plus 0, 1, 5, 6 and -1. Zero removes the item and should be tested last on a resettable fixture because re-adding is out of scope. | High |
| Identity isolation | Both API handlers call the fixed token mapping; cart selection uses the authenticated actor. No cross-user access defect found in this trace. Exercise Alice/Bob independently, invalid token and anonymous GET/PUT, verifying both baselines after rejection. | Medium |
| Stock and totals | Rejection occurs before mutation; the update does not decrement stock. Check 5 accepted, 6 rejected unchanged, and current fixture totals 12 × quantity. Negative totals belong to the CART-2 finding, not a separate arithmetic defect. | Medium |
| Product-price consistency | `cart()` multiplies by literal 12 instead of reading catalog price. This matches the only current product and is not a demonstrated fixture discrepancy. If configurable prices enter scope, test with a supported price change and compare catalog/cart totals. | Low |
| Transport and state transitions | No HTTP parser, authentication response, concurrency, or error-delivery behavior was exercised. After runtime restoration, prioritize the negative reproduction and malformed/missing payload preservation over speculative edge cases. | Medium |
| Adjacent UI | Source shows explicit submit, Cancel hiding the form without fetch, and reopening from saved `current`. Fetch failure handling and refresh races remain unverified risks. No browser observations or UI defect claims are made; test keyboard flow, narrow layout and delayed/failed requests when available. | Medium |

Missing test coverage is recorded as risk, not as a product defect. No claim is made that the hardcoded price is wrong for this fixture. Adding products/items, checkout and production authentication were excluded.

## Limits, cleanup and handoff

API requests: **0/60**. Browser actions: **0/45**. No screenshots were taken. No runtime, application, or existing tests were executed. No cart state was changed, so no fixture restoration was needed. Only the requested assessment artifacts were created.

Unfinished verification: execute the proposed negative-quantity reproduction on the assigned runtime when available; verify its HTTP response and persisted state, restore Alice, then exercise the listed quantity and identity matrix. No observed HTTP records are submitted.

Elapsed time and action accounting are recorded in `evidence/session.txt`. Token/usage metrics are unavailable and are not estimated.
