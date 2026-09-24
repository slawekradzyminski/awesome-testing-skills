# F-02-address

Extracted verbatim from http-transcript.jsonl; request numbers match its line numbers.

## Request 67 — address-fresh-save

```http
POST http://127.0.0.1:55995/api/orders/A200/address
X-Test-User: alice
Content-Type: application/json

{"address": "Assessment newer address", "version": 1}
```

Response status: 200

```json
{
  "id": "A200",
  "owner": "alice",
  "paid": 6000,
  "refunded": 6001,
  "address": "Assessment newer address",
  "version": 2,
  "note": "Ring twice",
  "service": "standard"
}
```

## Request 68 — address-stale-save

```http
POST http://127.0.0.1:55995/api/orders/A200/address
X-Test-User: alice
Content-Type: application/json

{"address": "Assessment stale overwrite", "version": 1}
```

Response status: 200

```json
{
  "id": "A200",
  "owner": "alice",
  "paid": 6000,
  "refunded": 6001,
  "address": "Assessment stale overwrite",
  "version": 3,
  "note": "Ring twice",
  "service": "standard"
}
```

## Request 69 — address-persisted-state

```http
GET http://127.0.0.1:55995/api/orders/A200
X-Test-User: alice
Content-Type: application/json

(no body)
```

Response status: 200

```json
{
  "id": "A200",
  "owner": "alice",
  "paid": 6000,
  "refunded": 6001,
  "address": "Assessment stale overwrite",
  "version": 3,
  "note": "Ring twice",
  "service": "standard"
}
```

## Request 70 — address-future-version

```http
POST http://127.0.0.1:55995/api/orders/A200/address
X-Test-User: alice
Content-Type: application/json

{"address": "Future version", "version": 4}
```

Response status: 409

```json
{
  "error": "Order changed; reload before saving"
}
```
