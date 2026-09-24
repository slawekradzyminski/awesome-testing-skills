import json, urllib.request
from pathlib import Path
base='http://127.0.0.1:56450'
def req(path,body=None,user='alice'):
    r=urllib.request.Request(base+path,headers={'Content-Type':'application/json','X-Test-User':user},data=None if body is None else json.dumps(body).encode())
    with urllib.request.urlopen(r) as response:return json.load(response)
before=req('/api/orders')
assert next(o for o in before['orders'] if o['id']=='A100')['note']=='Leave with reception'
assert next(o for o in before['orders'] if o['id']=='A200')['note']=='Assessment A200 only'
req('/api/orders/A200/note',{'note':'Ring twice'})
after=req('/api/orders'); bob=req('/api/orders',user='bob')
Path('evidence/final-fixtures.json').write_text(json.dumps({'beforeCleanup':before,'alice':after,'bob':bob,'leftovers':'A200 refunded 6000 cents and version 3; all addresses, notes and services restored. Owner reset required.'},indent=2))
print('4 cleanup/read requests. Reversible changes restored; A200 refund=6000 and version=3 require owner reset.')
