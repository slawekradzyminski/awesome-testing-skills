import json
from pathlib import Path
from datetime import datetime, timezone
start=datetime(2026,9,12,8,39,47,tzinfo=timezone.utc)
end=datetime.now(timezone.utc)
summary=json.loads(Path('evidence/summary.json').read_text())
http=json.loads(Path('evidence/http.json').read_text())
sources=['app/domain.py','app/app.py','app/test_domain.py','app/static/app.js','app/static/index.html']
Path('evidence/source-review.txt').write_text('\n\n'.join(path+'\n'+'\n'.join(f'{i}: {line}' for i,line in enumerate(Path(path).read_text().splitlines(),1)) for path in sources))
risks=[
 {'area':'Browser save/cancel and error feedback (UI-1, UI-2)','reason':'Source handlers were reviewed, but no browser was exercised. API success cannot establish visible feedback, provisional editing, keyboard usability, or narrow layout.','priority':'medium','next_probe':'With reset fixtures, intercept network traffic while editing, cancelling, reopening, and saving by keyboard at desktop and narrow widths; verify no PUT on cancel and capture/open screenshots.'},
 {'area':'Price consistency if catalog becomes mutable (CART-4)','reason':'app/domain.py Store.cart multiplies quantities by literal 12. This matches the current sole product, whose runtime price is 12; changed prices were neither available nor injected, so this is not a current confirmed discrepancy.','priority':'low','next_probe':'If product price changes become supported, change a fixture price through an authorized setup and check cart totals against the resulting catalog price.'},
 {'area':'Concurrent updates and identity changes','reason':'The server is threaded, while runtime checks were sequential. Existing domain tests do not cover HTTP or concurrent requests. No concurrency failure was observed.','priority':'low','next_probe':'After a fixture reset, issue simultaneous authorized updates and verify returned totals remain internally consistent and final carts remain isolated.'}
]
limitations=[
 'The focus was the existing cart quantity-update API and product data; UI files were reviewed only. No browser actions or screenshots, and no claims of visual or keyboard verification.',
 'Sequential requests only; concurrent requests, client disconnects, and network failure recovery were not exercised.',
 'Only the documented single product and disposable Alice/Bob identities were used. No production authentication conclusions are drawn.',
 'No supported API re-add operation exists. Bob remains empty after confirming zero removes the item; only the fixture/process owner should restart the runtime.',
 'The immutable runtime product price stayed at 12, so behavior following product price changes was not runtime-tested.'
]
submission={'source_access':True,'runtime_exercised':True,'findings':[], 'risks':risks,'observations':[{'method':r['method'],'path':r['path'],'status':r['status'],'action':f"Request {r['number']}: {r['action']} (actor: {r['actor'] or 'anonymous'})",'evidence':'evidence/http.json'} for r in http], 'limitations':limitations,'cleanup':summary['cleanup']}
Path('submission.json').write_text(json.dumps(submission,indent=2)+'\n')
report=f'''# Cart API exploration report

No discrepancies were confirmed against the API requirements in the exercised fixture. This is bounded passing evidence, not a claim of complete coverage.

Runtime: `http://127.0.0.1:64184`. Source reviewed: `app/app.py`, `app/domain.py`, existing `app/test_domain.py`, and the UI source. The application and existing tests were not edited. Exploration helper scripts and evidence were created only in this candidate directory.

## Coverage and results

- **CART-1:** Alice and Bob started at quantities 1 and 2. Anonymous cart/product reads and updates returned 401; an unknown token update returned 401. Alice's request containing `username: bob` updated Alice only. Bob's baseline remained unchanged. Final Bob removal left Alice unchanged.
- **CART-2:** Negative, fractional, null, numeric string, both booleans, missing quantity, non-object JSON, malformed JSON, and JSON `3.0` returned 400. Follow-up reads confirmed the original cart was preserved. Bob's quantity-zero update removed the item and persisted an empty cart with zero totals.
- **CART-3:** Quantity 5 was accepted, quantity 6 returned 409 and retained quantity 5. Product stock remained 5 after both increasing and removing cart quantities.
- **CART-4:** The catalog returned one Workshop notebook, ID 1, price 12, stock 5. Observed totals matched 1 × 12, 2 × 12, 5 × 12, and empty-cart zero totals.
- Unknown existing-cart product ID returned 404; malformed product ID returned 400. These are observations, not invented requirements.
- **UI-1 / UI-2:** Source inspected; browser behavior was not exercised and is a remaining risk.

All {summary['checks']} recorded checks passed across {summary['api_requests']} API requests. The two existing domain tests also passed. Tests are narrow: their passing status does not establish browser or concurrency behavior.

## Evidence

- `evidence/http.json`: all 38 numbered requests, actor, request body, response status/body, and purpose.
- `evidence/checks.json`: 55 concrete status/state assertions and results.
- `evidence/existing-tests.txt`: unchanged existing test results.
- `evidence/source-review.txt`: numbered source reviewed for risk selection.
- `evidence/summary.json`: counts and cleanup state.
- `explore.py`: reproducible exploration helper. It assumes reset fixtures; do not rerun on the final empty Bob cart without the owner's reset.

## Remaining risks

'''+ '\n\n'.join(f"**{r['priority'].title()}: {r['area']}.** {r['reason']} Next probe: {r['next_probe']}" for r in risks)+f'''

## Cleanup and limitations

{summary['cleanup']} The server was not stopped or restarted. No browser session was opened.

'''+ '\n'.join('- '+x for x in limitations)+f'''

## Budget

Started reading the task at {start.isoformat()}; report written at {end.isoformat()}. Elapsed approximately {(end-start).total_seconds():.1f} seconds, within five minutes. API requests: 38 of 60. Browser actions: 0 of 45. No token-usage metrics were available or estimated.
'''
Path('report.md').write_text(report)
print(json.dumps({'elapsed_seconds':round((end-start).total_seconds(),1),'api_requests':len(http),'findings':len(submission['findings']),'report':'report.md','submission':'submission.json'}))
for obs in submission['observations']: assert Path(obs['evidence']).is_file()
assert len(http)<=60
assert all(c['passed'] for c in json.loads(Path('evidence/checks.json').read_text()))
print('Submission and evidence references validated.')
