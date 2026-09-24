# Selected HTTP evidence

Extracted from `http.jsonl`. Sequence numbers identify original requests; all calls used http://127.0.0.1:58282.

## Request 52: refund first partial

```json
{
  "seq": 52,
  "label": "refund first partial",
  "method": "POST",
  "path": "/api/orders/A100/refund",
  "actor": "alice",
  "request": {
    "amount": 6000
  },
  "status": 200,
  "response": {
    "id": "A100",
    "owner": "alice",
    "paid": 10000,
    "refunded": 6000,
    "address": "10 Oak Street",
    "version": 1,
    "note": "Leave with reception",
    "service": "standard"
  }
}
```

## Request 53: refund remaining payment

```json
{
  "seq": 53,
  "label": "refund remaining payment",
  "method": "POST",
  "path": "/api/orders/A100/refund",
  "actor": "alice",
  "request": {
    "amount": 4000
  },
  "status": 200,
  "response": {
    "id": "A100",
    "owner": "alice",
    "paid": 10000,
    "refunded": 10000,
    "address": "10 Oak Street",
    "version": 1,
    "note": "Leave with reception",
    "service": "standard"
  }
}
```

## Request 54: F01 cumulative refund overrun

```json
{
  "seq": 54,
  "label": "F01 cumulative refund overrun",
  "method": "POST",
  "path": "/api/orders/A100/refund",
  "actor": "alice",
  "request": {
    "amount": 1
  },
  "status": 200,
  "response": {
    "id": "A100",
    "owner": "alice",
    "paid": 10000,
    "refunded": 10001,
    "address": "10 Oak Street",
    "version": 1,
    "note": "Leave with reception",
    "service": "standard"
  }
}
```

## Request 55: F01 persisted refund

```json
{
  "seq": 55,
  "label": "F01 persisted refund",
  "method": "GET",
  "path": "/api/orders/A100",
  "actor": "alice",
  "request": null,
  "status": 200,
  "response": {
    "id": "A100",
    "owner": "alice",
    "paid": 10000,
    "refunded": 10001,
    "address": "10 Oak Street",
    "version": 1,
    "note": "Leave with reception",
    "service": "standard"
  }
}
```

## Request 56: address editor one saves

```json
{
  "seq": 56,
  "label": "address editor one saves",
  "method": "POST",
  "path": "/api/orders/A200/address",
  "actor": "alice",
  "request": {
    "address": "Current dispatch address",
    "version": 1
  },
  "status": 200,
  "response": {
    "id": "A200",
    "owner": "alice",
    "paid": 6000,
    "refunded": 0,
    "address": "Current dispatch address",
    "version": 2,
    "note": "Ring twice",
    "service": "standard"
  }
}
```

## Request 57: F02 stale editor saves

```json
{
  "seq": 57,
  "label": "F02 stale editor saves",
  "method": "POST",
  "path": "/api/orders/A200/address",
  "actor": "alice",
  "request": {
    "address": "Stale dispatch address",
    "version": 1
  },
  "status": 200,
  "response": {
    "id": "A200",
    "owner": "alice",
    "paid": 6000,
    "refunded": 0,
    "address": "Stale dispatch address",
    "version": 3,
    "note": "Ring twice",
    "service": "standard"
  }
}
```

## Request 58: F02 persisted stale edit

```json
{
  "seq": 58,
  "label": "F02 persisted stale edit",
  "method": "GET",
  "path": "/api/orders/A200",
  "actor": "alice",
  "request": null,
  "status": 200,
  "response": {
    "id": "A200",
    "owner": "alice",
    "paid": 6000,
    "refunded": 0,
    "address": "Stale dispatch address",
    "version": 3,
    "note": "Ring twice",
    "service": "standard"
  }
}
```

## Request 60: F03 mixed batch missing

```json
{
  "seq": 60,
  "label": "F03 mixed batch missing",
  "method": "POST",
  "path": "/api/services",
  "actor": "alice",
  "request": {
    "ids": [
      "A200",
      "MISSING"
    ],
    "service": "express"
  },
  "status": 404,
  "response": {
    "error": "Order not found"
  }
}
```

## Request 61: F03 persisted service missing

```json
{
  "seq": 61,
  "label": "F03 persisted service missing",
  "method": "GET",
  "path": "/api/orders/A200",
  "actor": "alice",
  "request": null,
  "status": 200,
  "response": {
    "id": "A200",
    "owner": "alice",
    "paid": 6000,
    "refunded": 0,
    "address": "Stale dispatch address",
    "version": 3,
    "note": "Ring twice",
    "service": "express"
  }
}
```

## Request 65: F03 mixed batch forbidden

```json
{
  "seq": 65,
  "label": "F03 mixed batch forbidden",
  "method": "POST",
  "path": "/api/services",
  "actor": "alice",
  "request": {
    "ids": [
      "A200",
      "B100"
    ],
    "service": "express"
  },
  "status": 403,
  "response": {
    "error": "Access denied"
  }
}
```

## Request 66: F03 persisted service forbidden

```json
{
  "seq": 66,
  "label": "F03 persisted service forbidden",
  "method": "GET",
  "path": "/api/orders/A200",
  "actor": "alice",
  "request": null,
  "status": 200,
  "response": {
    "id": "A200",
    "owner": "alice",
    "paid": 6000,
    "refunded": 0,
    "address": "Stale dispatch address",
    "version": 3,
    "note": "Ring twice",
    "service": "express"
  }
}
```

## Request 82: final fixture alice

```json
{
  "seq": 82,
  "label": "final fixture alice",
  "method": "GET",
  "path": "/api/orders",
  "actor": "alice",
  "request": null,
  "status": 200,
  "response": {
    "orders": [
      {
        "id": "A100",
        "owner": "alice",
        "paid": 10000,
        "refunded": 10001,
        "address": "10 Oak Street",
        "version": 1,
        "note": "Leave with reception",
        "service": "standard"
      },
      {
        "id": "A200",
        "owner": "alice",
        "paid": 6000,
        "refunded": 0,
        "address": "20 Pine Street",
        "version": 5,
        "note": "Ring twice",
        "service": "standard"
      }
    ]
  }
}
```

## Request 83: final fixture bob

```json
{
  "seq": 83,
  "label": "final fixture bob",
  "method": "GET",
  "path": "/api/orders",
  "actor": "bob",
  "request": null,
  "status": 200,
  "response": {
    "orders": [
      {
        "id": "B100",
        "owner": "bob",
        "paid": 4000,
        "refunded": 0,
        "address": "30 Elm Street",
        "version": 1,
        "note": "Side entrance",
        "service": "standard"
      }
    ]
  }
}
```
