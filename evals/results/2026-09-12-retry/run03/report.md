# Source-only cart API exploration

One code-evidenced defect was found: negative integer quantities pass validation and are persisted, producing negative cart totals. There are no runtime-confirmed findings. The runtime was unavailable and was not started.

## Session and scope

September 12, 2026. Charter: trace viewing products and each fixture user's existing cart, then investigate quantity-update validation, ownership, availability, and totals against CART-1 through CART-4. Stop after important source paths and existing tests are assessed, within five minutes and 60 API requests. Actual API requests: **0**; browser actions: **0**. UI interaction and out-of-scope checkout, re-adding removed items, and production authentication were excluded.

Requirements: local `requirements.md`; the inspected `app/requirements.md` states the same rules. Roles: public disposable Alice/Bob fixture identities. Source: local `app/`; no revision metadata is available inside the candidate. No parent directory or external application copy was inspected. [Source fingerprints](evidence/source-snapshot.json) identify the inspected inputs. Deployed build/base URL: unavailable; source/deployment equivalence unknown. The source's health response string `sample-1` is not a verified deployed build.

## Finding F1 — Negative quantities are saved

**Requirement:** CART-2. **Status:** code-evidenced, runtime unverified. **Severity:** provisional Medium: material invalid-cart behavior within a disposable sample; no checkout or monetary loss was observed or inferred.

On fresh fixtures Alice has product 1 quantity 1, Bob has quantity 2, and the catalog reports price 12 with stock 5. The minimal proposed request is authenticated `PUT /api/v1/cart/items/1` with JSON `{"quantity":-1}` as Alice. CART-2 requires HTTP 400 and an unchanged cart.

The handler authenticates before parsing and calls `store.update(actor, productId, body.get("quantity"))` at `app/app.py:82`, returning 200 at line 83. In `app/domain.py:24`, -1 passes the exact integer check. It is below the stock bound at line 31 and nonzero at line 33, so line 36 assigns -1 to Alice's existing item. The resulting cart calculation at lines 20–21 yields `totalItems: -1` and `totalPrice: -12`. These are source-derived predictions, not captured HTTP results. Observed reproduction count: **0**. No status, header, response, or state snapshot is claimed as live evidence.

The missing lower-bound check is the directly evidenced cause. No additional validator is present on the inspected HTTP route. HTML min=0 constrains normal form input but does not protect direct API requests. An unexpected runtime rejection would require checking source/build correspondence or an upstream validator. Bob's separate dictionary and the unchanged product data should remain unaffected; verify those relationships when reproducing.

[Exact source lines](evidence/source-lines.txt) and [proposed request sequence, expected/predicted results, follow-up reads, cleanup, and disconfirming evidence](evidence/reproduction.txt) make the finding reproducible without implying it was executed. The sequence restores the captured Alice baseline without removing the item.

**Focused regression suggestion:** at domain level, submit -1 and assert ApiError status 400 and full cart equality before/after. Add one representative HTTP test to verify the parse-to-domain boundary, response status, persisted state, and unchanged Bob/catalog. No tests or product code were modified.

## Risk map and inspected protections

Ordering favors invalid writes and identity boundaries because they affect stored user state. Boundary coverage comes next. Future price changes and concurrency remain lower-priority uncertainties within this fixed sample.

| Area | Evidence / plausible failure | User impact / priority | Protection or uncertainty | Next probe |
| --- | --- | --- | --- | --- |
| Negative quantity | Missing `< 0` check at domain lines 24–36 | Invalid cart and negative aggregates; high exploration priority | Code-evidenced F1; runtime blocked | Execute F1 reproduction and compare full state |
| Identity isolation | Exact token map at handler lines 40–45; actor used at lines 64 and 82 | Cross-user state would be serious; high | Per-user indexing and normal-update Bob assertion support isolation; no source discrepancy found | Alice/Bob contrast, anonymous and invalid token GET/PUT, unchanged state on rejection |
| Types, boundaries, stock and zero | Exact int check; stock guard before write; zero deletes | Invalid writes/removal errors; medium | Bool/fraction/string/null/missing reject in source; 6 rejects at stock 5; zero removes; live behavior unverified | Boundary/type sequence, verify full state and stock; zero last on resettable fixture |
| Current product totals | `cart` hardcodes 12; catalog's only product price is 12 | Future changed-price mismatch; low | Current fixture arithmetic agrees with CART-4; no separate actual defect | Compare product price and totals at quantity 1 and 5; changed-price test only if future scope allows |
| Concurrent updates/removal | Shared Store under ThreadingHTTPServer, lock used for audit only | Potential inconsistent responses; low | Unexecuted concern, not a finding; concurrency semantics unspecified | Overlap writes/removal on resettable fixture and inspect full outcomes |

## Existing tests and coverage limits

`app/test_domain.py` was read in full and **not run**. The first test checks Alice quantity 3 produces totalPrice 36 and Bob totalItems stays 2. The second checks quantity 6 raises 409 and Alice totalItems remains 1. These assertions do not cover the negative branch, full-cart equality, invalid JSON types, missing quantity, zero, stock preservation, exact available stock, or HTTP authentication/parsing. Coverage gaps are risks, not additional product defects.

Source review also found protections: GET products and GET cart require authentication; catalog returns a deep copy; quantity updates never decrement product stock; errors for wrong types and over-stock quantities occur before writes. CART-4 matches the supplied sole product price. These are inspected branches, not claims of passing runtime tests. Browser source was read only to establish the API caller; no UI finding or screenshot is reported.

## Closeout

Source-only review is complete for the principal scoped paths. Runtime exploration remains blocked by the explicit task constraint; live status codes, headers, persistence, ownership contrast, concurrent requests, malformed transport handling, and UI behavior remain unverified. No app code or tests were executed. The next useful action is to run the supplied F1 sequence on an owner-provided matching runtime, followed by the identity and boundary contrasts.

No fixture state was changed and no restoration was necessary. No browser session or process was created. Deliverables: this report, `submission.json`, and the evidence files linked above. Timing and action accounting are in `evidence/session-accounting.json`.
