# F-01-refund

Extracted verbatim from http-transcript.jsonl; request numbers match its line numbers.

## Request 62 — refund-first-part

```http
POST http://127.0.0.1:55995/api/orders/A200/refund
X-Test-User: alice
Content-Type: application/json

{"amount": 5000}
```

Response status: 200

```json
{
  "id": "A200",
  "owner": "alice",
  "paid": 6000,
  "refunded": 5000,
  "address": "20 Pine Street",
  "version": 1,
  "note": "Ring twice",
  "service": "standard"
}
```

## Request 63 — refund-exact-remaining

```http
POST http://127.0.0.1:55995/api/orders/A200/refund
X-Test-User: alice
Content-Type: application/json

{"amount": 1000}
```

Response status: 200

```json
{
  "id": "A200",
  "owner": "alice",
  "paid": 6000,
  "refunded": 6000,
  "address": "20 Pine Street",
  "version": 1,
  "note": "Ring twice",
  "service": "standard"
}
```

## Request 64 — refund-exceeds-cumulative-by-one

```http
POST http://127.0.0.1:55995/api/orders/A200/refund
X-Test-User: alice
Content-Type: application/json

{"amount": 1}
```

Response status: 200

```json
{
  "id": "A200",
  "owner": "alice",
  "paid": 6000,
  "refunded": 6001,
  "address": "20 Pine Street",
  "version": 1,
  "note": "Ring twice",
  "service": "standard"
}
```

## Request 65 — refund-exceeds-original-payment

```http
POST http://127.0.0.1:55995/api/orders/A200/refund
X-Test-User: alice
Content-Type: application/json

{"amount": 6001}
```

Response status: 409

```json
{
  "error": "Refund exceeds remaining paid amount"
}
```

## Request 66 — refund-persisted-state

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
  "address": "20 Pine Street",
  "version": 1,
  "note": "Ring twice",
  "service": "standard"
}
```
