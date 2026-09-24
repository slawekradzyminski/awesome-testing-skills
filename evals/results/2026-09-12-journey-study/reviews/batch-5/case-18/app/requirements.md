# Dispatch Desk product brief

The desk serves customers editing delivery arrangements after purchase. Its API also supports refund and address administration. All data and identities are disposable; `X-Test-User: alice` and `X-Test-User: bob` select fixture users, not production authentication. The browser is deliberately Alice-only. Login, real payments, emails, order creation/deletion and production security hardening are outside this demo's scope.

Alice owns A100 (10000 cents paid) and A200 (6000); Bob owns B100 (4000). `GET /api/orders` lists the caller's orders; `GET /api/orders/{id}` returns one. Anonymous calls are rejected and another customer's order must be inaccessible and unchangeable. Money uses integer cents. Changes last until the fixture owner restarts the server; no reset route is provided.

## API operations

- `POST /api/orders/{id}/refund`, JSON `{"amount": 1000}`: positive integer amount only. Several partial refunds are allowed; their cumulative amount must not exceed the original payment. Reject an excessive refund with 409 and no further refund recorded.
- `POST /api/orders/{id}/address`, JSON `{"address": "New address", "version": 1}`: nonblank address up to 120 characters and an integer version from the customer's last read. Save only if the version still matches; increment it after saving. Reject stale edits with 409 and preserve the newer address.
- `POST /api/services`, JSON `{"ids": ["A100", "A200"], "service": "express"}`: standard and express are supported. This is an all-or-nothing change: if any order is missing or forbidden, return 404 or 403 and leave every order unchanged.
- `POST /api/orders/{id}/note`, JSON `{"note": "Ring twice"}`: 1–160 nonblank characters. Instructions beginning `LOCKER:` are rejected with 422 because locker delivery is not supported. Retain the previous saved note on rejection.
- Malformed inputs are rejected with 400. Source tests cover some routine behaviour; there is no claim of complete coverage.

## Browser experience

Customers can switch between their two orders, edit delivery instructions, and choose a service. The selected order, displayed details and target of a save must remain consistent even when delivery lookups complete in a different order. A100 lookups normally take about 700 ms; this latency is intentional and is not itself a defect.

Successful edits survive reloading. Rejected instructions display actionable failure feedback, preserve the draft so it can be corrected, and never claim success. Both service choices and instruction editing must be usable with ordinary keyboard navigation and visible focus. Support desktop and narrow layouts; the visual style has no pixel-perfect reference. Design preferences alone are not confirmed defects.

API assessments cover the administrative operations; UI assessments cover the browser journey and its backing calls. Documentation-only auditing, general hardening, real-device certification and performance SLAs are excluded. You may mutate this isolated instance's fixture data; restore reversible changes and disclose irreversible refunds or changed version counters for owner reset.
