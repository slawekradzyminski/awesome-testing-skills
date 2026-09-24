import json
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
out=Path(__file__).parent
logs=[json.loads(line) for line in (out/'http.jsonl').read_text().splitlines()]
checks=[]
def check(label,actual,expected):checks.append(dict(label=label,passed=actual==expected,actual=actual,expected=expected))
for actor,ids in [('alice',['A100','A200']),('bob',['B100'])]:
    row=next(r for r in logs if r['label']=='baseline '+actor)
    check('exact list isolation '+actor,sorted(o['id'] for o in row['response']['orders']),ids)
records=[]
def req(label,path,body=None):
    request=Request('http://127.0.0.1:59591'+path,data=None if body is None else json.dumps(body).encode(),headers={'X-Test-User':'alice','Content-Type':'application/json'})
    try:
        with urlopen(request,timeout=5) as r:status,value=r.status,json.load(r)
    except HTTPError as e:status,value=e.code,json.load(e)
    records.append(dict(label=label,path=path,request=body,status=status,response=value))
    return status,value
initial=json.loads((out/'initial-state.json').read_text())
final=json.loads((out/'final-state.json').read_text())
status,value=req('reject above original payment','/api/orders/A100/refund',{'amount':10001})
check('above original payment',status,409)
status,value=req('read after excessive refund','/api/orders/A100')
check('owned single order read',status,200)
check('excessive initial refund preserves whole order',value,initial['A100'])
status,value=req('stale address after restore','/api/orders/A200/address',{'address':'Stale attempt','version':1})
check('stale address rejection',status,409)
status,value=req('read after stale address','/api/orders/A200')
check('stale address preserves whole order',value,final['A200'])
(out/'additional-http.json').write_text(json.dumps(records,indent=2)+'\n')
(out/'additional-checks.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(dict(api_requests=len(records),checks=len(checks),passed=sum(c['passed'] for c in checks),failed=[c for c in checks if not c['passed']]),indent=2))
