import json,time,urllib.request,urllib.error
from pathlib import Path
BASE='http://127.0.0.1:49525'
records=[]
def req(method,path,actor=None,body=None,action='',raw=None):
 headers={}
 if actor: headers['Authorization']='Bearer demo-'+actor
 if body is not None or raw is not None: headers['Content-Type']='application/json'
 data=raw.encode() if raw is not None else json.dumps(body).encode() if body is not None else None
 start=time.monotonic()
 request=urllib.request.Request(BASE+path,data=data,headers=headers,method=method)
 try:
  response=urllib.request.urlopen(request,timeout=4)
 except urllib.error.HTTPError as e: response=e
 except Exception as e:
  record={'id':len(records)+1,'method':method,'path':path,'role':actor or 'anonymous','request':raw if raw is not None else body,'action':action,'transport_error':str(e),'elapsed_ms':round((time.monotonic()-start)*1000,2)}
  records.append(record); Path('evidence/http.json').write_text(json.dumps(records,indent=2)); raise
 text=response.read().decode()
 try: payload=json.loads(text)
 except ValueError: payload=text
 record={'id':len(records)+1,'method':method,'path':path,'role':actor or 'anonymous','request':raw if raw is not None else body,'action':action,'status':response.status,'headers':dict(response.headers),'response':payload,'elapsed_ms':round((time.monotonic()-start)*1000,2)}
 records.append(record); Path('evidence/http.json').write_text(json.dumps(records,indent=2))
 print(record['id'],method,path,actor,response.status,payload)
 return response.status,payload
cart='/api/v1/cart'; item=cart+'/items/1'; catalog='/api/v1/products'
req('GET','/health',action='Availability and deployed build identity')
req('GET',catalog,'alice',action='Product price and stock baseline')
a=req('GET',cart,'alice',action='Alice initial cart')[1]
b=req('GET',cart,'bob',action='Bob initial cart')[1]
req('GET',cart,action='Anonymous read rejected')
req('PUT',item,body={'quantity':3},action='Anonymous update rejected')
req('GET',cart,'alice',action='Verify anonymous mutation did not change Alice')
req('PUT',item,'alice',{'quantity':3},action='Representative valid update')
req('GET',cart,'alice',action='Verify quantity three and total 36 persisted')
req('GET',cart,'bob',action='Verify Alice update left Bob unchanged')
req('PUT',item,'alice',{'quantity':4,'username':'bob'},action='Client supplied username cannot choose another cart')
req('GET',cart,'alice',action='Extra username field still updates authenticated Alice')
req('GET',cart,'bob',action='Verify extra username field left Bob unchanged')
req('PUT',item,'alice',{'quantity':5},action='Exact stock boundary accepted')
req('GET',catalog,'alice',action='Stock remains five after cart changes')
for label,body in [('negative',{'quantity':-1}),('fractional',{'quantity':1.5}),('missing',{}),('null',{'quantity':None}),('string',{'quantity':'2'}),('boolean true',{'quantity':True}),('boolean false',{'quantity':False}),('above stock',{'quantity':6})]:
 req('PUT',item,'alice',body,action='Reject '+label+' quantity')
 req('GET',cart,'alice',action='Verify unchanged quantity five after '+label)
req('PUT',item,'alice',raw='{',action='Malformed JSON rejected')
req('GET',cart,'alice',action='Verify malformed JSON did not mutate cart')
req('PUT',item,'alice',raw='[]',action='Non-object JSON rejected')
req('GET',cart,'alice',action='Verify non-object JSON did not mutate cart')
req('PUT',item,'alice',{'quantity':a['items'][0]['quantity']},action='Restore Alice initial quantity')
req('GET',cart,'alice',action='Verify Alice baseline restored')
req('PUT',item,'bob',{'quantity':0},action='Zero removes existing Bob item; no supported re-add operation')
req('GET',cart,'bob',action='Verify removal persisted with zero totals')
req('GET',cart,'alice',action='Verify Bob removal leaves Alice unchanged')
req('GET',catalog,'bob',action='Verify removal leaves product stock unchanged')
Path('evidence/accounting.json').write_text(json.dumps({'http_requests':len(records),'api_requests':sum(r['path'].startswith('/api/') for r in records),'availability_requests':1,'browser_actions':0,'browser_sessions_created':0,'cleanup':'Alice restored to quantity 1 and verified. Bob removed by zero test; re-add is out of scope and unavailable, so owner restart is required to restore Bob to quantity 2.'},indent=2))
