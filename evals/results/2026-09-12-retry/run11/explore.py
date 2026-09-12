import json, urllib.request, urllib.error, time
from pathlib import Path
BASE='http://127.0.0.1:64184'
records=[]
checks=[]
def req(method,path,actor='alice',body=None,raw=None,action='',expected=200):
    headers={}
    if actor: headers['Authorization']='Bearer demo-'+actor
    if body is not None or raw is not None: headers['Content-Type']='application/json'
    data=raw.encode() if raw is not None else json.dumps(body).encode() if body is not None else None
    r=urllib.request.Request(BASE+path,headers=headers,data=data,method=method)
    try:
        response=urllib.request.urlopen(r,timeout=5)
    except urllib.error.HTTPError as e: response=e
    text=response.read().decode()
    try: payload=json.loads(text)
    except ValueError: payload=text
    rec={'number':len(records)+1,'method':method,'path':path,'actor':actor,'request':raw if raw is not None else body,'status':response.status,'response':payload,'action':action}
    records.append(rec)
    Path('evidence/http.json').write_text(json.dumps(records,indent=2))
    checks.append({'check':action+' status','passed':response.status==expected,'expected':expected,'actual':response.status})
    return payload

def check(name,condition): checks.append({'check':name,'passed':condition})
cart='/api/v1/cart'; item=cart+'/items/1'; products='/api/v1/products'
a=req('GET',cart,action='Alice baseline')
b=req('GET',cart,'bob',action='Bob baseline')
p=req('GET',products,action='Product baseline')
check('Fixture baseline',a['totalItems']==1 and b['totalItems']==2 and p[0]['stockQuantity']==5 and p[0]['price']==12)
for path in (cart,products): req('GET',path,None,action='Anonymous read rejected',expected=401)
req('PUT',item,None,{'quantity':3},action='Anonymous update rejected',expected=401)
req('PUT',item,'invalid',{'quantity':3},action='Unknown fixture token rejected',expected=401)
req('GET',cart+'?username=bob',action='Query cannot select Bob cart')
for value in [-1,1.5,None,'3',True,False]:
    req('PUT',item,body={'quantity':value},action='Reject quantity '+repr(value),expected=400)
    actual=req('GET',cart,action='Read after rejection '+repr(value))
    check('Rejected '+repr(value)+' preserved Alice baseline',actual==a)
for raw in ['{}','[]','null','{"quantity":','{"quantity":3.0}']:
    req('PUT',item,raw=raw,action='Reject malformed/type request '+raw,expected=400)
check('All extra invalid bodies preserve Alice',req('GET',cart,action='Read after malformed/type requests')==a)
u=req('PUT',item,body={'quantity':5,'username':'bob'},action='Accept exact stock with spoofed username body')
check('Stock boundary totals and authenticated actor',u['username']=='alice' and u['totalItems']==5 and u['totalPrice']==60)
check('Spoofed username did not update Bob',req('GET',cart,'bob',action='Bob after Alice body spoof')==b)
check('Stock is not decremented',req('GET',products,action='Catalog after cart update')==p)
req('PUT',item,body={'quantity':6},action='Reject stock plus one',expected=409)
check('Stock rejection preserves five',req('GET',cart,action='Read after stock rejection')==u)
req('PUT',cart+'/items/999',body={'quantity':1},action='Unknown cart item rejected',expected=404)
req('PUT',cart+'/items/not-a-number',body={'quantity':1},action='Invalid product ID rejected',expected=400)
check('Restore Alice baseline',req('PUT',item,body={'quantity':1},action='Restore Alice quantity')==a)
zero=req('PUT',item,'bob',{'quantity':0},action='Remove Bob item using quantity zero')
check('Zero removes item and clears totals',zero['items']==[] and zero['totalItems']==0 and zero['totalPrice']==0)
check('Removal persisted',req('GET',cart,'bob',action='Read after Bob removal')==zero)
check('Bob removal leaves Alice unchanged',req('GET',cart,action='Final Alice verification')==a)
check('Removal leaves stock unchanged',req('GET',products,action='Final catalog verification')==p)
Path('evidence/checks.json').write_text(json.dumps(checks,indent=2))
Path('evidence/summary.json').write_text(json.dumps({'api_requests':len(records),'checks':len(checks),'passed':sum(c['passed'] for c in checks),'failures':[c for c in checks if not c['passed']],'cleanup':'Alice restored to original quantity 1. Bob item removed by zero-quantity test; no supported re-add endpoint, restart by fixture owner required to restore Bob quantity 2. Product data unchanged.'},indent=2))
print(Path('evidence/summary.json').read_text())
