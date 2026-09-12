# Cart API exploration — runtime blocked

No product defects are confirmed. The assigned service returned HTTP **503** with `{"error":"Application temporarily unavailable"}` for every request. Functional application behavior was not exercised; these responses do not establish cart, authentication, or validation defects.

## Scope and environment

Explored the source for existing-cart quantity updates and product data against CART-1 through CART-4 in `requirements.md`. The charter was to verify identity isolation, strict quantity validation and rejection atomicity, stock limits, totals, and zero removal. UI work, checkout, adding items, and production authentication were excluded. Only the supplied candidate directory and `http://127.0.0.1:49525` were used. Roles were the supplied disposable Alice/Bob identities and anonymous access.

The session took less than five minutes. Source revision metadata was not supplied and no parent repository was inspected. [The source snapshot](evidence/source.txt) records file SHA-256 hashes and numbered source. The local health implementation advertises `sample-1`, but the deployed health request returned 503 without a version; deployed build and source correspondence are unknown.

## Accounting and constraint deviation

**35 HTTP requests were actually issued: one health request and 34 API requests. All returned 503.** Zero browser actions were performed and no browser session was created. The batch script did not stop when availability failed and exceeded the explicit six-request fallback limit. This was an exploration error. It continued through planned probes until attempting to derive a restoration quantity from a 503 body raised `KeyError: 'items'`. No further network requests were made. See [actual request/response evidence](evidence/http.json), [console output and traceback](evidence/run.txt), [the executed probe script](evidence/explore.py), and [accounting](evidence/accounting.json). Statements describing request intent in those artifacts are not claims that the behavior succeeded.

## Source and test observations

The relevant routing, JSON parsing, token mapping, cart selection, domain validation, persistence in memory, and response/error mapping were inspected in `app/app.py` and `app/domain.py`. No outbound dependencies are involved. Existing tests were read and executed, without modifying the application or tests.

| Check | Observed result | Evidence |
| --- | --- | --- |
| Existing domain total/isolation test | Passed: Alice quantity 3 yields total 36; Bob remains quantity 2 | [Test output](evidence/existing-tests.txt) |
| Existing domain stock rejection test | Passed: quantity 6 raises 409; Alice remains quantity 1 | [Test output](evidence/existing-tests.txt) |
| Authentication and ownership source review | Known token selects actor; API requests use actor to access/update the cart. Anonymous tokens raise 401 in source. Runtime unverified. | [Source](evidence/source.txt), app.py lines 47–52, 70–74, 82–93 |
| Quantity and removal source review | Exact `int` type check rejects booleans, strings, fractions, null and missing values; negative values rejected before mutation. Zero deletes an existing item. Runtime unverified. | [Source](evidence/source.txt), domain.py lines 26–42 |
| Product stock and totals source review | Fixture product price is 12 and stock is 5. Stock is checked before mutation and never decremented. Totals use quantity sums and fixed price 12. This agrees with the supplied fixture; dynamic price changes are not exposed or tested. | [Source](evidence/source.txt) |
| Runtime availability | Blocked: all requests returned the same 503 error; no functional assertions can be assessed from those responses | [HTTP evidence](evidence/http.json) |

The two tests execute the domain directly. They do not establish that deployed HTTP authentication, parsing, persistence, or status mapping works. Additional validation branches were inspected, not tested through a functioning API.

## Prioritized remaining risks

| Area | Evidence, impact and priority | Next useful probe |
| --- | --- | --- |
| Identity isolation | **High:** source uses authenticated actor, but runtime ownership remains unverified; cross-user mutation would affect another cart | Once owner restores service, capture both baselines, attempt anonymous access and Alice update, then verify Bob unchanged; contrast extra client-supplied username |
| Quantity validation / rejection atomicity | **High:** validation precedes writes in source, but parser integration and actual unchanged state could not be observed | Test negative, fractional, missing, null, string, boolean, and stock+1 inputs, with follow-up reads after each rejection |
| Boundaries, zero removal and totals | **Medium:** source arithmetic and zero branch appear consistent; only quantity 3/stock 6 have executed domain-test evidence | Exercise quantities 1, 3, 5 and zero with persisted reads; zero requires owner reset to restore the removed item because re-add is out of scope |
| Product stock consistency | **Medium:** code does not reserve stock, but live catalog was inaccessible | Compare product data before and after successful updates/removal |

These are coverage gaps, not findings. No request outcomes justify claiming that the feature is defect-free. The availability blocker needs fixture-owner attention before further live probes; no repair or restart was attempted.

## Cleanup and handoff

No successful mutation was observed: every mutation attempt returned 503. Baselines and final cart state were inaccessible, so unchanged state cannot be verified. The restore and zero-removal requests shown later in the probe script were never reached. No service was started, stopped, restarted, or repaired. No browser was opened. Python test execution may have created ordinary `app/__pycache__` files; no application source, requirements, skill, or existing tests were edited.

Deliverables: this report, [structured submission](submission.json), and evidence files linked above. Outstanding checks are the live experiments listed in the risk table, after the fixture owner makes the assigned runtime available. UI requirements were not assessed. No external issue or publication was created.
