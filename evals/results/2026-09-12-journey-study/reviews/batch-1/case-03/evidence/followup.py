"""Focused remaining HTTP boundaries; reuses helper definitions without rerunning exploration."""
import json,pathlib
source=pathlib.Path('evidence/explore.py').read_text().split("initial=read('baseline Alice')")[0]
exec(compile(source,'evidence/explore.py','exec'))
records=json.loads((OUT/'http.json').read_text()); checks=json.loads((OUT/'checks.json').read_text()); count=95
before=read('Bob before valid own-order write','bob')['B100']
r=post('Bob valid note with server-owned extras','/api/orders/B100/note',{'note':'Assessment Bob own note','owner':'alice','paid':999999,'refunded':-100,'version':0,'service':'express'},actor='bob')
expected=dict(before,note='Assessment Bob own note')
check('server-owned extras ignored in response',r==expected)
check('Bob own note persists without unrelated changes',read('Bob after own note','bob')['B100']==expected)
post('restore Bob note','/api/orders/B100/note',{'note':before['note']},actor='bob')
for body in [{},{'note':True},{'note':123}]:
    post('note missing or wrong type','/api/orders/B100/note',body,400,'bob')
s,_=call('oversized JSON body','POST','/api/orders/B100/note',raw=json.dumps({'note':'x'*8200}).encode(),actor='bob'); check('oversized body rejected',s==400)
s,_=call('unknown fixture identity','GET','/api/orders',actor='mallory'); check('unknown identity rejected',s==401)
final=read('Bob final restoration','bob')['B100']; check('Bob restored and failed writes unchanged',final==before)
summary=json.loads((OUT/'summary.json').read_text()); summary.update(api_requests_including_baseline_curl=count,checks=len(checks),failed_checks=[c for c in checks if not c['passed']],finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2))
