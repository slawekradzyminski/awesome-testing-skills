from pathlib import Path
import json,datetime
root=Path(__file__).resolve().parent.parent
records=json.loads((root/'evidence/http.json').read_text())
checks=[]
def check(label,ok):
    checks.append({'check':label,'passed':bool(ok)})
    assert ok,label
byid={r['number']:r for r in records}
check('Negative quantity is accepted and persists (confirmed defect)',byid[9]['status']==200 and byid[10]['response']['totalItems']==-1 and byid[10]['response']['totalPrice']==-12)
for n in range(13,27,2):
    check('Invalid quantity rejected without mutation, request '+str(n),byid[n]['status']==400 and byid[n+1]['response']['totalItems']==1)
for n in [29,31]:
    check('Overstock rejects without mutation, request '+str(n),byid[n]['status']==409 and byid[n+1]['response']['totalItems']==5)
check('No stock reservation across identities',byid[48]['status']==200 and byid[49]['status']==200 and byid[50]['response'][0]['stockQuantity']==5)
check('Cleanup Alice exact baseline',byid[55]['response']==byid[1]['response'])
check('Cleanup Bob exact baseline',byid[56]['response']==byid[2]['response'])
(root/'evidence/checks.json').write_text(json.dumps(checks,indent=2)+'\n')
(root/'evidence/reproduction.txt').write_text('CART-2: negative quantity persists\nAssigned runtime: http://127.0.0.1:64181\n\n'+ '\n\n'.join(json.dumps(byid[n],indent=2) for n in [1,9,10,11,12,55,56])+'\n\nCode: app/domain.py:24 checks exact int type, but no quantity < 0 guard precedes assignment at line 36.\n')
findings=[{'requirement_id':'CART-2','title':'Negative integer quantity is accepted and persisted with negative totals','status':'confirmed','expected':'CART-2 requires negative quantities to return 400 and leave the cart unchanged. Alice should remain quantity 1, totalItems 1, totalPrice 12.','actual':'PUT /api/v1/cart/items/1 with Alice token and {"quantity":-1} returns 200; a subsequent GET persists quantity -1, totalItems -1, totalPrice -12.','impact':'An authenticated fixture caller can corrupt their own cart quantity and produce a negative total. Bob remained unchanged. No checkout or financial impact was tested.','evidence':['evidence/reproduction.txt','evidence/http.json']}]
risks=[{'area':'Zero removal through the HTTP boundary','reason':'In-process Store removal passes, but removing the runtime item prevents API restoration because adding items is out of scope. No live zero mutation was issued.','priority':'medium','next_probe':'With a fresh resettable fixture, PUT quantity 0 and GET the empty cart, confirming zero totals and isolation; let the owner reset afterward.'},{'area':'UI provisional editing, feedback, and keyboard layout','reason':'Only UI source was inspected. No browser session or visual evidence was collected. Async refresh and identity changes remain unexercised.','priority':'medium','next_probe':'Test Edit/Cancel/reopen and Save via keyboard at narrow and desktop widths, including account changes while a response is delayed.'},{'area':'Current unit price used by totals','reason':'app/domain.py:21 multiplies by literal 12, matching current catalog data. No price mutation endpoint exists in scope, so no current runtime discrepancy is claimed.','priority':'low','next_probe':'If product prices become configurable, add a controlled price-change domain probe and confirm cart totals follow the catalog price.'}]
limitations=['No browser/UI execution or screenshots; UI-1 and UI-2 remain runtime-unverified.','Zero removal checked only in a disposable in-process Store, not the assigned HTTP runtime, to preserve restorable fixture carts.','Single-item fixed-price fixture only; concurrency and transport fault injection were not tested.','Token/account usage metrics are unavailable; only observed request counts and wall-clock time are reported.']
cleanup='Alice restored to quantity 1 / total 12 and Bob to quantity 2 / total 24; final GET responses exactly match initial snapshots (requests 55 and 56). Catalog stock remained 5 and price 12. Application and existing tests were not edited. No browser session was opened.'
submission={'source_access':True,'runtime_exercised':True,'findings':findings,'risks':risks,'observations':[{'method':r['method'],'path':r['path'],'status':r['status'],'action':f"Request {r['number']}: {r['action']}",'evidence':'evidence/http.json'} for r in records],'limitations':limitations,'cleanup':cleanup}
(root/'submission.json').write_text(json.dumps(submission,indent=2)+'\n')
now=datetime.datetime.now(datetime.timezone.utc)
start=datetime.datetime(2026,9,12,8,35,8,tzinfo=datetime.timezone.utc)
elapsed=(now-start).total_seconds()
report=f'''# Cart API exploratory report

One confirmed defect: **negative quantities persist**, violating CART-2. Priority: high within this feature, because a routine validation boundary permits invalid cart state. This is not a claim of checkout or cross-account exploitation.

## Scope and approach

Read TASK.md, requirements.md, REPORTING.md, app/app.py, app/domain.py, app/test_domain.py, and the UI HTML/CSS/JavaScript. Ran the two existing unit tests (both passed). Investigated source-identified lower-bound validation risk, rejected input atomicity, authentication, isolation, availability, totals, and product data using the assigned runtime only.

Started 2026-09-12 08:35:08 UTC; report generated {now.isoformat()}. Elapsed through report generation: {elapsed:.1f} seconds, below the five-minute limit. **56 API requests; 0 browser actions.** Evidence generation and the isolated Store probe made no HTTP requests. No delegated work. Usage metrics beyond these counts are unavailable.

## Confirmed finding — CART-2

1. GET Alice cart with `Authorization: Bearer demo-alice`: quantity 1, totalItems 1, totalPrice 12.
2. PUT `/api/v1/cart/items/1` with `{{"quantity":-1}}` and Alice's token.
3. Expected 400 and unchanged state. Actual 200 with quantity -1, totalItems -1 and totalPrice -12.
4. GET Alice cart confirms persistence. GET Bob cart still shows quantity 2 and totalPrice 24.
5. Restore Alice to 1; final cleanup restores both identities to their original state.

[Exact reproduction](evidence/reproduction.txt) and [all HTTP evidence](evidence/http.json). Source explains the result: app/domain.py:24 validates integer type, then line 36 assigns negative integers without a lower-bound check. The negative total is a consequence of this quantity defect, not a separate arithmetic defect.

## Other results

- Anonymous cart/products reads and mutation returned 401; an unknown token returned 401. Cart state stayed unchanged.
- Fractional 1.5, missing, null, string, both booleans, and float-form 2.0 returned 400; each following GET confirmed unchanged state.
- Valid quantities 1, 3, 4, and 5 produced the expected quantities and totals at price 12. Quantity 6 and 1,000,000 returned 409 and preserved the saved value.
- Alice and Bob mutations remained isolated in both directions. Both could independently hold quantity 5, and catalog stock stayed 5, as required by CART-3's non-reservation behavior.
- Unknown item returned 404; malformed JSON and a non-object body returned 400, preserving the cart.
- Zero removed the item and produced zero totals in a fresh in-process Store; Bob stayed unchanged. This is local domain evidence, not HTTP confirmation. See [zero probe](evidence/local-zero.json).
- [Existing test output](evidence/existing-tests.txt) confirms two passing tests. These tests cover a valid update and stock rejection; they do not cover negative input. [Evidence assertions](evidence/checks.json) verify key observed outcomes.

## Remaining risks and limitations

Medium: runtime zero removal remains untested because the API cannot re-add a removed item. Next probe: use an owner-resettable fixture, remove at zero, verify empty totals and isolation, then reset.

Medium: UI-1/UI-2 are not browser-tested, including provisional changes, Cancel, acknowledgments, keyboard operation, narrow layout, and delayed-response account switching. Source inspection alone is insufficient to claim these pass or fail. No screenshots or visual observations are claimed.

Low: totals use literal 12 rather than a product lookup. It matches the current immutable fixture, so no current defect is reported. If price configuration is added, test that totals follow changes.

Concurrency, transport faults, multiple products, and changing prices were not exercised. Production authentication, adding items, and checkout are outside scope.

## Cleanup

{cleanup}
'''
(root/'report.md').write_text(report)
(root/'evidence/session.json').write_text(json.dumps({'started_utc':start.isoformat(),'report_generated_utc':now.isoformat(),'elapsed_seconds_through_report_generation':elapsed,'api_requests':len(records),'browser_actions':0,'existing_unit_tests':2,'source_modified':False},indent=2)+'\n')
print(json.dumps({'api_requests':len(records),'checks':len(checks),'elapsed_seconds':elapsed,'report':'report.md','submission':'submission.json'}))
