# Cart API exploratory report

One confirmed defect: **negative quantities persist**, violating CART-2. Priority: high within this feature, because a routine validation boundary permits invalid cart state. This is not a claim of checkout or cross-account exploitation.

## Scope and approach

Read TASK.md, requirements.md, REPORTING.md, app/app.py, app/domain.py, app/test_domain.py, and the UI HTML/CSS/JavaScript. Ran the two existing unit tests (both passed). Investigated source-identified lower-bound validation risk, rejected input atomicity, authentication, isolation, availability, totals, and product data using the assigned runtime only.

Started 2026-09-12 08:35:08 UTC; report generated 2026-09-12T08:38:02.160097+00:00. Elapsed through report generation: 174.2 seconds, below the five-minute limit. **56 API requests; 0 browser actions.** Evidence generation and the isolated Store probe made no HTTP requests. No delegated work. Usage metrics beyond these counts are unavailable.

## Confirmed finding — CART-2

1. GET Alice cart with `Authorization: Bearer demo-alice`: quantity 1, totalItems 1, totalPrice 12.
2. PUT `/api/v1/cart/items/1` with `{"quantity":-1}` and Alice's token.
3. Expected 400 and unchanged state. Actual 200 with quantity -1, totalItems -1 and totalPrice -12.
4. GET Alice cart confirms persistence. GET Bob cart still shows quantity 2 and totalPrice 24.
5. Restore Alice to 1; final cleanup restores both identities to their original state.

[Exact reproduction](evidence/reproduction.txt) and [all HTTP evidence](evidence/http.json). Source explains the result: app/domain.py:24 validates integer type, then line 36 assigns negative integers without a lower-bound check. The negative total is a consequence of this quantity defect, not a separate arithmetic defect.

## Other results

- Anonymous cart/products reads and mutation returned 401; an unknown token returned 401. Cart state stayed unchanged.
- Fractional 1.5, missing, null, string, both booleans, and float-form 2.0 returned 400; each following GET confirmed unchanged state.
- Valid quantities 1, 3, 4, and 5 produced the expected quantities and totals at price 12. Quantity 6 and 1,000,000 returned 409 and preserved the saved value.
- Alice and Bob mutations remained isolated in both directions. Both could independently hold quantity 5, and catalog stock stayed 5, as required by CART-3's non-reservation behavior.
- Unknown item returned 404; malformed JSON and a non-object body returned 400, preserving the cart.
- Zero removed the item and produced zero totals in a fresh in-process Store; Bob stayed unchanged. This is local domain evidence, not HTTP confirmation. See [zero probe](evidence/local-zero.json).
- [Existing test output](evidence/existing-tests.txt) confirms two passing tests. These tests cover a valid update and stock rejection; they do not cover negative input. [Evidence assertions](evidence/checks.json) verify key observed outcomes.

## Remaining risks and limitations

Medium: runtime zero removal remains untested because the API cannot re-add a removed item. Next probe: use an owner-resettable fixture, remove at zero, verify empty totals and isolation, then reset.

Medium: UI-1/UI-2 are not browser-tested, including provisional changes, Cancel, acknowledgments, keyboard operation, narrow layout, and delayed-response account switching. Source inspection alone is insufficient to claim these pass or fail. No screenshots or visual observations are claimed.

Low: totals use literal 12 rather than a product lookup. It matches the current immutable fixture, so no current defect is reported. If price configuration is added, test that totals follow changes.

Concurrency, transport faults, multiple products, and changing prices were not exercised. Production authentication, adding items, and checkout are outside scope.

## Cleanup

Alice restored to quantity 1 / total 12 and Bob to quantity 2 / total 24; final GET responses exactly match initial snapshots (requests 55 and 56). Catalog stock remained 5 and price 12. Application and existing tests were not edited. No browser session was opened.
