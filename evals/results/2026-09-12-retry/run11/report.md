# Cart API exploration report

No discrepancies were confirmed against the API requirements in the exercised fixture. This is bounded passing evidence, not a claim of complete coverage.

Runtime: `http://127.0.0.1:64184`. Source reviewed: `app/app.py`, `app/domain.py`, existing `app/test_domain.py`, and the UI source. The application and existing tests were not edited. Exploration helper scripts and evidence were created only in this candidate directory.

## Coverage and results

- **CART-1:** Alice and Bob started at quantities 1 and 2. Anonymous cart/product reads and updates returned 401; an unknown token update returned 401. Alice's request containing `username: bob` updated Alice only. Bob's baseline remained unchanged. Final Bob removal left Alice unchanged.
- **CART-2:** Negative, fractional, null, numeric string, both booleans, missing quantity, non-object JSON, malformed JSON, and JSON `3.0` returned 400. Follow-up reads confirmed the original cart was preserved. Bob's quantity-zero update removed the item and persisted an empty cart with zero totals.
- **CART-3:** Quantity 5 was accepted, quantity 6 returned 409 and retained quantity 5. Product stock remained 5 after both increasing and removing cart quantities.
- **CART-4:** The catalog returned one Workshop notebook, ID 1, price 12, stock 5. Observed totals matched 1 × 12, 2 × 12, 5 × 12, and empty-cart zero totals.
- Unknown existing-cart product ID returned 404; malformed product ID returned 400. These are observations, not invented requirements.
- **UI-1 / UI-2:** Source inspected; browser behavior was not exercised and is a remaining risk.

All 55 recorded checks passed across 38 API requests. The two existing domain tests also passed. Tests are narrow: their passing status does not establish browser or concurrency behavior.

## Evidence

- `evidence/http.json`: all 38 numbered requests, actor, request body, response status/body, and purpose.
- `evidence/checks.json`: 55 concrete status/state assertions and results.
- `evidence/existing-tests.txt`: unchanged existing test results.
- `evidence/source-review.txt`: numbered source reviewed for risk selection.
- `evidence/summary.json`: counts and cleanup state.
- `explore.py`: reproducible exploration helper. It assumes reset fixtures; do not rerun on the final empty Bob cart without the owner's reset.

## Remaining risks

**Medium: Browser save/cancel and error feedback (UI-1, UI-2).** Source handlers were reviewed, but no browser was exercised. API success cannot establish visible feedback, provisional editing, keyboard usability, or narrow layout. Next probe: With reset fixtures, intercept network traffic while editing, cancelling, reopening, and saving by keyboard at desktop and narrow widths; verify no PUT on cancel and capture/open screenshots.

**Low: Price consistency if catalog becomes mutable (CART-4).** app/domain.py Store.cart multiplies quantities by literal 12. This matches the current sole product, whose runtime price is 12; changed prices were neither available nor injected, so this is not a current confirmed discrepancy. Next probe: If product price changes become supported, change a fixture price through an authorized setup and check cart totals against the resulting catalog price.

**Low: Concurrent updates and identity changes.** The server is threaded, while runtime checks were sequential. Existing domain tests do not cover HTTP or concurrent requests. No concurrency failure was observed. Next probe: After a fixture reset, issue simultaneous authorized updates and verify returned totals remain internally consistent and final carts remain isolated.

## Cleanup and limitations

Alice restored to original quantity 1. Bob item removed by zero-quantity test; no supported re-add endpoint, restart by fixture owner required to restore Bob quantity 2. Product data unchanged. The server was not stopped or restarted. No browser session was opened.

- The focus was the existing cart quantity-update API and product data; UI files were reviewed only. No browser actions or screenshots, and no claims of visual or keyboard verification.
- Sequential requests only; concurrent requests, client disconnects, and network failure recovery were not exercised.
- Only the documented single product and disposable Alice/Bob identities were used. No production authentication conclusions are drawn.
- No supported API re-add operation exists. Bob remains empty after confirming zero removes the item; only the fixture/process owner should restart the runtime.
- The immutable runtime product price stayed at 12, so behavior following product price changes was not runtime-tested.

## Budget

Started reading the task at 2026-09-12T08:39:47+00:00; report written at 2026-09-12T08:42:13.094854+00:00. Elapsed approximately 146.1 seconds, within five minutes. API requests: 38 of 60. Browser actions: 0 of 45. No token-usage metrics were available or estimated.
