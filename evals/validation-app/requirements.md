# Orders and profile requirements

## Order access

- ORDER-1: Users may read only their own orders. `GET /api/orders/1` belongs to Alice (Book); `/api/orders/2` belongs to Bob (Pen). Owner reads return 200 and the order; another user's read returns 403 without order details. Unauthenticated or unknown identities receive 401. An authenticated read of an absent order returns 404.
- In this disposable fixture only, `X-Test-User: alice` and `X-Test-User: bob` select identities. This is a testing mechanism, not production authentication. Orders are read-only.

## Profile editing

- PROFILE-1: Save persists the entered display name exactly once. Cancel must leave the persisted name and save count unchanged and must send no save request. Reload must display the persisted name. Cancel may leave the unsaved input visible until reload.
- `GET /api/profile` returns `displayName` and `saveCount`. The initial values are `Original` and 0. `POST /api/profile` with a JSON object containing a string `displayName` of 1–80 characters stores it and increments `saveCount`. Invalid input returns 400 and changes neither value.
- The profile is one shared scratch record in this isolated process; it intentionally requires no identity. It is not an account-specific profile or an authentication feature. You may change it and restore its display name; the save counter records these writes and cannot be reset through the API.

Restarting the fixture resets all data. No emails, external services, database or real accounts are involved.
