# HTTP request index

Request 1 was the preliminary Alice order-list curl (200). Requests 2–90 are recorded in http.jsonl. Concurrent requests may appear in completion order.

| Request | Check | Method and path | Status |
| --- | --- | --- | --- |
| 2 | baseline alice | GET /api/orders | 200 |
| 3 | baseline bob | GET /api/orders | 200 |
| 4 | unauthenticated None | GET /api/orders | 401 |
| 5 | unauthenticated None | GET /api/orders/A200 | 401 |
| 6 | unauthenticated None | POST /api/orders/A200/refund | 401 |
| 7 | unauthenticated None | POST /api/orders/A200/address | 401 |
| 8 | unauthenticated None | POST /api/orders/A200/note | 401 |
| 9 | unauthenticated None | POST /api/services | 401 |
| 10 | unauthenticated unknown | GET /api/orders | 401 |
| 11 | unauthenticated unknown | GET /api/orders/A200 | 401 |
| 12 | unauthenticated unknown | POST /api/orders/A200/refund | 401 |
| 13 | unauthenticated unknown | POST /api/orders/A200/address | 401 |
| 14 | unauthenticated unknown | POST /api/orders/A200/note | 401 |
| 15 | unauthenticated unknown | POST /api/services | 401 |
| 16 | foreign read | GET /api/orders/B100 | 403 |
| 17 | foreign refund alice | POST /api/orders/B100/refund | 403 |
| 18 | foreign address alice | POST /api/orders/B100/address | 403 |
| 19 | foreign note alice | POST /api/orders/B100/note | 403 |
| 20 | foreign service alice | POST /api/services | 403 |
| 21 | foreign read | GET /api/orders/A200 | 403 |
| 22 | foreign refund bob | POST /api/orders/A200/refund | 403 |
| 23 | foreign address bob | POST /api/orders/A200/address | 403 |
| 24 | foreign note bob | POST /api/orders/A200/note | 403 |
| 25 | foreign service bob | POST /api/services | 403 |
| 26 | after authorization alice | GET /api/orders | 200 |
| 27 | after authorization bob | GET /api/orders | 200 |
| 28 | atomic batch ['A100', 'B100'] | POST /api/services | 403 |
| 29 | batch state | GET /api/orders | 200 |
| 30 | atomic batch ['A100', 'MISSING'] | POST /api/services | 404 |
| 31 | batch state | GET /api/orders | 200 |
| 32 | atomic batch ['B100', 'A100'] | POST /api/services | 403 |
| 33 | batch state | GET /api/orders | 200 |
| 34 | atomic batch ['MISSING', 'A100'] | POST /api/services | 404 |
| 35 | batch state | GET /api/orders | 200 |
| 36 | valid two-order batch | POST /api/services | 200 |
| 37 | batch persisted read | GET /api/orders | 200 |
| 38 | restore service | POST /api/services | 200 |
| 39 | invalid batch {'ids': [], 'service': 'express'} | POST /api/services | 400 |
| 40 | invalid batch {'ids': ['A200', 42], 'service': 'express'} | POST /api/services | 400 |
| 41 | invalid batch {'ids': 'A200', 'service': 'express'} | POST /api/services | 400 |
| 42 | invalid batch {'ids': ['A200'], 'service': 'overnight'} | POST /api/services | 400 |
| 43 | invalid refund 0 | POST /api/orders/A100/refund | 400 |
| 44 | invalid refund -1 | POST /api/orders/A100/refund | 400 |
| 45 | invalid refund True | POST /api/orders/A100/refund | 400 |
| 46 | invalid refund 1.5 | POST /api/orders/A100/refund | 400 |
| 47 | invalid refund 100 | POST /api/orders/A100/refund | 400 |
| 48 | invalid refund None | POST /api/orders/A100/refund | 400 |
| 49 | partial refund one | POST /api/orders/A100/refund | 200 |
| 50 | partial refund two | POST /api/orders/A100/refund | 200 |
| 51 | cumulative excess | POST /api/orders/A100/refund | 409 |
| 52 | refund after excess | GET /api/orders/A100 | 200 |
| 53 | concurrent refund 0 | POST /api/orders/A100/refund | 200 |
| 54 | concurrent refund 1 | POST /api/orders/A100/refund | 409 |
| 55 | exact remaining refund | POST /api/orders/A100/refund | 200 |
| 56 | refund exhausted balance | POST /api/orders/A100/refund | 409 |
| 57 | refund final read | GET /api/orders/A100 | 200 |
| 58 | invalid address {'address': ' ', 'version': 1} | POST /api/orders/A200/address | 400 |
| 59 | invalid address {'address': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', 'version': 1} | POST /api/orders/A200/address | 400 |
| 60 | invalid address {'address': 7, 'version': 1} | POST /api/orders/A200/address | 400 |
| 61 | invalid address {'address': 'Valid', 'version': True} | POST /api/orders/A200/address | 400 |
| 62 | invalid address {'address': 'Valid', 'version': 1.0} | POST /api/orders/A200/address | 400 |
| 63 | invalid address {'address': 'Valid'} | POST /api/orders/A200/address | 400 |
| 64 | address 120 character boundary | POST /api/orders/A200/address | 200 |
| 65 | stale address | POST /api/orders/A200/address | 409 |
| 66 | address after stale | GET /api/orders/A200 | 200 |
| 67 | concurrent address 0 | POST /api/orders/A200/address | 409 |
| 68 | concurrent address 1 | POST /api/orders/A200/address | 200 |
| 69 | address concurrency read | GET /api/orders/A200 | 200 |
| 70 | restore address | POST /api/orders/A200/address | 200 |
| 71 | note maximum boundary | POST /api/orders/A200/note | 200 |
| 72 | invalid note {'note': ''} | POST /api/orders/A200/note | 400 |
| 73 | invalid note {'note': '   '} | POST /api/orders/A200/note | 400 |
| 74 | invalid note {'note': 'nnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn'} | POST /api/orders/A200/note | 400 |
| 75 | invalid note {'note': True} | POST /api/orders/A200/note | 400 |
| 76 | invalid note {'note': 'LOCKER: 1'} | POST /api/orders/A200/note | 422 |
| 77 | invalid note {'note': '  locker: 2'} | POST /api/orders/A200/note | 422 |
| 78 | note after rejection | GET /api/orders/A200 | 200 |
| 79 | restore note | POST /api/orders/A200/note | 200 |
| 80 | malformed JSON envelope | POST /api/orders/A200/note | 400 |
| 81 | malformed JSON envelope | POST /api/orders/A200/note | 400 |
| 82 | malformed JSON envelope | POST /api/orders/A200/note | 400 |
| 83 | malformed JSON envelope | POST /api/orders/A200/note | 400 |
| 84 | malformed JSON envelope | POST /api/orders/A200/note | 400 |
| 85 | malformed JSON envelope | POST /api/orders/A200/note | 400 |
| 86 | missing order refund | POST /api/orders/MISSING/refund | 404 |
| 87 | missing order address | POST /api/orders/MISSING/address | 404 |
| 88 | missing order note | POST /api/orders/MISSING/note | 404 |
| 89 | final alice | GET /api/orders | 200 |
| 90 | final bob | GET /api/orders | 200 |
