import json, urllib.request, urllib.error
from pathlib import Path
ROOT=Path(__file__).parent
records=[]
def call(label,method,path,body=None,actor='alice',raw=None):
    data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    headers={'Content-Type':'application/json'}
    if actor is not None: headers['X-Test-User']=actor
    req=urllib.request.Request('http://127.0.0.1:59820'+path,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(req,timeout=5) as r: status,value=r.status,json.load(r)
    except urllib.error.HTTPError as e: status,value=e.code,json.load(e)
    except Exception as e: status,value=0,repr(e)
    records.append({'seq':88+len(records)+1,'label':label,'method':method,'path':path,'actor':actor,'body':body,'raw':repr(raw) if raw is not None else None,'status':status,'response':value})
    (ROOT/'boundary-evidence.json').write_text(json.dumps(records,indent=2))
    return status,value
for oid,actor in [('A100','alice'),('A200','alice'),('B100','bob')]: call('owner detail read','GET','/api/orders/'+oid,actor=actor)
call('anonymous detail read','GET','/api/orders/A200',actor=None)
call('anonymous bulk update','POST','/api/services',{'ids':['A100'],'service':'express'},actor=None)
call('Bob bulk forbidden second order','POST','/api/services',{'ids':['B100','A100'],'service':'express'},actor='bob')
call('Bob bulk rejected state','GET','/api/orders/B100',actor='bob')
for op in ['refund','address','note']: call('missing operation fields','POST','/api/orders/A200/'+op,{})
# Whitespace boundary: returned and persisted string exceeds the stated note limit.
call('161-character padded note','POST','/api/orders/A200/note',{'note':'n'*160+' '})
call('padded note persisted','GET','/api/orders/A200')
call('long padded note','POST','/api/orders/A200/note',{'note':'n'+' '*1000})
call('long padded note persisted','GET','/api/orders/A200')
call('one character note','POST','/api/orders/A200/note',{'note':'n'})
call('restore note','POST','/api/orders/A200/note',{'note':'Ring twice'})
call('oversized request body','POST','/api/orders/A200/note',raw=json.dumps({'note':'n'*8200}).encode())
call('Bob valid service','POST','/api/services',{'ids':['B100'],'service':'express'},actor='bob')
call('Bob service persisted','GET','/api/orders/B100',actor='bob')
call('restore Bob service','POST','/api/services',{'ids':['B100'],'service':'standard'},actor='bob')
call('final Alice','GET','/api/orders')
call('final Bob','GET','/api/orders',actor='bob')
print(json.dumps([{'seq':r['seq'],'label':r['label'],'status':r['status'],'note_length':len(r['response']['note']) if isinstance(r['response'],dict) and 'note' in r['response'] else None} for r in records],indent=2))
