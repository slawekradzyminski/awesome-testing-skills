# F-03-services

Extracted verbatim from http-transcript.jsonl; request numbers match its line numbers.

## Request 74 — batch-missing-later-item

```http
POST http://127.0.0.1:55995/api/services
X-Test-User: alice
Content-Type: application/json

{"ids": ["A100", "MISSING"], "service": "express"}
```

Response status: 404

```json
{
  "error": "Order not found"
}
```

## Request 75 — batch-missing-persisted-state

```http
GET http://127.0.0.1:55995/api/orders
X-Test-User: alice
Content-Type: application/json

(no body)
```

Response status: 200

```json
{
  "orders": [
    {
      "id": "A100",
      "owner": "alice",
      "paid": 10000,
      "refunded": 0,
      "address": "10 Oak Street",
      "version": 1,
      "note": "Leave with reception",
      "service": "express"
    },
    {
      "id": "A200",
      "owner": "alice",
      "paid": 6000,
      "refunded": 6001,
      "address": "20 Pine Street",
      "version": 5,
      "note": "Ring twice",
      "service": "standard"
    }
  ]
}
```

## Request 76 — restore-service-after-missing

```http
POST http://127.0.0.1:55995/api/services
X-Test-User: alice
Content-Type: application/json

{"ids": ["A100"], "service": "standard"}
```

Response status: 200

```json
{
  "orders": [
    {
      "id": "A100",
      "owner": "alice",
      "paid": 10000,
      "refunded": 0,
      "address": "10 Oak Street",
      "version": 1,
      "note": "Leave with reception",
      "service": "standard"
    }
  ]
}
```

## Request 77 — batch-forbidden-later-item

```http
POST http://127.0.0.1:55995/api/services
X-Test-User: alice
Content-Type: application/json

{"ids": ["A100", "B100"], "service": "express"}
```

Response status: 403

```json
{
  "error": "Access denied"
}
```

## Request 78 — batch-forbidden-persisted-state

```http
GET http://127.0.0.1:55995/api/orders
X-Test-User: alice
Content-Type: application/json

(no body)
```

Response status: 200

```json
{
  "orders": [
    {
      "id": "A100",
      "owner": "alice",
      "paid": 10000,
      "refunded": 0,
      "address": "10 Oak Street",
      "version": 1,
      "note": "Leave with reception",
      "service": "express"
    },
    {
      "id": "A200",
      "owner": "alice",
      "paid": 6000,
      "refunded": 6001,
      "address": "20 Pine Street",
      "version": 5,
      "note": "Ring twice",
      "service": "standard"
    }
  ]
}
```

## Request 79 — restore-service-after-forbidden

```http
POST http://127.0.0.1:55995/api/services
X-Test-User: alice
Content-Type: application/json

{"ids": ["A100"], "service": "standard"}
```

Response status: 200

```json
{
  "orders": [
    {
      "id": "A100",
      "owner": "alice",
      "paid": 10000,
      "refunded": 0,
      "address": "10 Oak Street",
      "version": 1,
      "note": "Leave with reception",
      "service": "standard"
    }
  ]
}
```
