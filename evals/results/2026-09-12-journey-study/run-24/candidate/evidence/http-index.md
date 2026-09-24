# HTTP evidence index

Full request and response bodies are in `http-evidence.json` (1–88) and `boundary-evidence.json` (89–110).

| Request | Check | Actor | HTTP |
| --- | --- | --- | --- |
| 1 | initial Alice | alice | 200 |
| 2 | initial Bob | bob | 200 |
| 3 | Bob isolation | bob | 200 |
| 4 | unauthorized list | None | 401 |
| 5 | unauthorized mutation | None | 401 |
| 6 | unauthorized list | mallory | 401 |
| 7 | unauthorized mutation | mallory | 401 |
| 8 | cross-user read | alice | 403 |
| 9 | cross-user refund | alice | 403 |
| 10 | cross-user address | alice | 403 |
| 11 | cross-user note | alice | 403 |
| 12 | cross-user read | bob | 403 |
| 13 | cross-user refund | bob | 403 |
| 14 | cross-user address | bob | 403 |
| 15 | cross-user note | bob | 403 |
| 16 | Alice after forbidden | alice | 200 |
| 17 | Bob after forbidden | bob | 200 |
| 18 | missing read | alice | 404 |
| 19 | missing refund | alice | 404 |
| 20 | missing address | alice | 404 |
| 21 | missing note | alice | 404 |
| 22 | refund invalid None | alice | 400 |
| 23 | refund invalid True | alice | 400 |
| 24 | refund invalid 0 | alice | 400 |
| 25 | refund invalid -1 | alice | 400 |
| 26 | refund invalid 1.5 | alice | 400 |
| 27 | refund invalid '1' | alice | 400 |
| 28 | refund invalid [] | alice | 400 |
| 29 | refund invalid {} | alice | 400 |
| 30 | refund above original | alice | 409 |
| 31 | first partial refund | alice | 200 |
| 32 | cumulative excessive refund | alice | 409 |
| 33 | after excessive refund | alice | 200 |
| 34 | exact remaining refund | alice | 200 |
| 35 | fully refunded rejects more | alice | 409 |
| 36 | concurrent refund 2 | alice | 200 |
| 37 | concurrent refund 1 | alice | 409 |
| 38 | after concurrent refunds | alice | 200 |
| 39 | invalid address {'address': '', 'version': 1} | alice | 400 |
| 40 | invalid address {'address': '   ', 'version': 1} | alice | 400 |
| 41 | invalid address {'address': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', 'version': 1} | alice | 400 |
| 42 | invalid address {'address': 5, 'version': 1} | alice | 400 |
| 43 | invalid address {'address': 'valid', 'version': True} | alice | 400 |
| 44 | invalid address {'address': 'valid', 'version': '1'} | alice | 400 |
| 45 | invalid address {'address': 'valid'} | alice | 400 |
| 46 | invalid address {'version': 1} | alice | 400 |
| 47 | valid maximum address | alice | 200 |
| 48 | stale address conflict | alice | 409 |
| 49 | after stale address | alice | 200 |
| 50 | concurrent address 2 | alice | 200 |
| 51 | concurrent address 1 | alice | 409 |
| 52 | after concurrent address | alice | 200 |
| 53 | atomic services ['A100', 'MISSING'] | alice | 404 |
| 54 | services after rejection | alice | 200 |
| 55 | atomic services ['A100', 'B100'] | alice | 403 |
| 56 | services after rejection | alice | 200 |
| 57 | atomic services ['B100', 'A100'] | alice | 403 |
| 58 | services after rejection | alice | 200 |
| 59 | atomic services ['A100', 'A200', 'MISSING'] | alice | 404 |
| 60 | services after rejection | alice | 200 |
| 61 | invalid service | alice | 400 |
| 62 | invalid service | alice | 400 |
| 63 | invalid service | alice | 400 |
| 64 | invalid service | alice | 400 |
| 65 | invalid service | alice | 400 |
| 66 | invalid service | alice | 400 |
| 67 | bulk express | alice | 200 |
| 68 | bulk persisted | alice | 200 |
| 69 | invalid note '' | alice | 400 |
| 70 | invalid note '   ' | alice | 400 |
| 71 | invalid note 5 | alice | 400 |
| 72 | invalid note 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' | alice | 400 |
| 73 | invalid note 'LOCKER: 1' | alice | 422 |
| 74 | invalid note ' locker: 2' | alice | 422 |
| 75 | after note rejections | alice | 200 |
| 76 | maximum valid note | alice | 200 |
| 77 | note persisted | alice | 200 |
| 78 | malformed JSON | alice | 400 |
| 79 | malformed JSON | alice | 400 |
| 80 | malformed JSON | alice | 400 |
| 81 | malformed JSON | alice | 400 |
| 82 | malformed JSON | alice | 400 |
| 83 | before cleanup | alice | 200 |
| 84 | restore address | alice | 200 |
| 85 | restore note | alice | 200 |
| 86 | restore service | alice | 200 |
| 87 | final Alice | alice | 200 |
| 88 | final Bob | bob | 200 |
| 89 | owner detail read | alice | 200 |
| 90 | owner detail read | alice | 200 |
| 91 | owner detail read | bob | 200 |
| 92 | anonymous detail read | None | 401 |
| 93 | anonymous bulk update | None | 401 |
| 94 | Bob bulk forbidden second order | bob | 403 |
| 95 | Bob bulk rejected state | bob | 200 |
| 96 | missing operation fields | alice | 400 |
| 97 | missing operation fields | alice | 400 |
| 98 | missing operation fields | alice | 400 |
| 99 | 161-character padded note | alice | 200 |
| 100 | padded note persisted | alice | 200 |
| 101 | long padded note | alice | 200 |
| 102 | long padded note persisted | alice | 200 |
| 103 | one character note | alice | 200 |
| 104 | restore note | alice | 200 |
| 105 | oversized request body | alice | 400 |
| 106 | Bob valid service | bob | 200 |
| 107 | Bob service persisted | bob | 200 |
| 108 | restore Bob service | bob | 200 |
| 109 | final Alice | alice | 200 |
| 110 | final Bob | bob | 200 |
