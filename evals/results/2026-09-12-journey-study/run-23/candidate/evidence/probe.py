import concurrent.futures, datetime, json, pathlib, threading, time, urllib.request, urllib.error
BASE='http://127.0.0.1:59662'
OUT=pathlib.Path(__file__).parent
counter=1
lock=threading.Lock()
checks=[]
def call(label,method,path,body=None,actor='alice',raw=None):
 global counter
 with lock:
  counter+=1
  n=counter
  assert n<=115, 'Request budget reserve reached'
 data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
 headers={'Content-Type':'application/json'}
 if actor is not None: headers['X-Test-User']=actor
 req=urllib.request.Request(BASE+path,data=data,headers=headers,method=method)
 start=time.monotonic()
 try:
  try: r=urllib.request.urlopen(req,timeout=5)
  except urllib.error.HTTPError as e: r=e
  with r:
   text=r.read().decode(errors='replace')
   try: value=json.loads(text)
   except ValueError: value=text
   row={'n':n,'label':label,'method':method,'path':path,'actor':actor,'request':body if raw is None else raw.decode(errors='replace'),'status':r.status,'headers':dict(r.headers),'body':value,'elapsed_ms':round((time.monotonic()-start)*1000,1)}
 except Exception as e:
  row={'n':n,'label':label,'method':method,'path':path,'actor':actor,'request':body,'transport_error':repr(e)}
 with lock:
  with (OUT/'http.jsonl').open('a') as f: f.write(json.dumps(row)+'\n')
 if row.get('status') in (502,503,504) or 'transport_error' in row: raise RuntimeError(row)
 return row['status'], row['body']
def check(label,condition):
 checks.append({'check':label,'passed':bool(condition)})
 print(('PASS ' if condition else 'FAIL ')+label,flush=True)
def snapshot(label):
 a=call(label+' Alice','GET','/api/orders')[1]['orders']
 b=call(label+' Bob','GET','/api/orders',actor='bob')[1]['orders']
 return {o['id']:o for o in a+b}
def post(label,path,body,expected=400,actor='alice'):
 result=call(label,'POST',path,body,actor)
 check(label+' status '+str(expected),result[0]==expected)
 return result
initial=snapshot('initial')
(OUT/'initial-state.json').write_text(json.dumps(initial,indent=2))
check('fixture ownership lists',set(initial)=={'A100','A200','B100'} and initial['B100']['owner']=='bob')
for method,path,body,actor,status in [
 ('GET','/api/orders',None,None,401),('POST','/api/orders/A100/refund',{'amount':1},None,401),
 ('GET','/api/orders/B100',None,'alice',403),('GET','/api/orders/A200',None,'bob',403),
 ('POST','/api/orders/B100/refund',{'amount':1},'alice',403),
 ('POST','/api/orders/B100/address',{'address':'Forbidden','version':1},'alice',403),
 ('POST','/api/orders/B100/note',{'note':'Forbidden'},'alice',403),
 ('GET','/api/orders/MISSING',None,'alice',404),
 ('POST','/api/orders/MISSING/refund',{'amount':1},'alice',404)]:
 check('access '+str(actor)+' '+method+' '+path,call('access',method,path,body,actor)[0]==status)
check('access denials preserve state',snapshot('after access')==initial)
for raw in (b'{',b'[]',b'null',b''):
 check('malformed JSON '+repr(raw),call('malformed JSON','POST','/api/orders/A200/note',raw=raw)[0]==400)
for amount in (0,-1,True,1.5,'100',None): post('invalid refund '+repr(amount),'/api/orders/A100/refund',{'amount':amount})
check('invalid refunds preserve state',call('after invalid refunds','GET','/api/orders')[1]['orders'][0]==initial['A100'])
post('first partial refund','/api/orders/A100/refund',{'amount':6000},200)
post('cumulative excess refund','/api/orders/A100/refund',{'amount':4001},409)
check('excess leaves cumulative refund unchanged',call('read rejected refund','GET','/api/orders')[1]['orders'][0]['refunded']==6000)
post('exact remaining refund','/api/orders/A100/refund',{'amount':4000},200)
post('exhausted refund','/api/orders/A100/refund',{'amount':1},409)
# Two competing refunds exceed the remaining payment together, but each fits alone.
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 futures=[pool.submit(call,'concurrent refund '+str(i),'POST','/api/orders/B100/refund',{'amount':2500},'bob') for i in range(2)]
 results=[f.result() for f in futures]
check('concurrent refund one success one conflict',sorted(r[0] for r in results)==[200,409])
check('concurrent refunds cannot exceed paid',call('after concurrent refunds','GET','/api/orders/B100',actor='bob')[1]['refunded']==2500)
for address,version in [('',1),(' '*3,1),('x'*121,1),('Valid',True),('Valid','1'),(None,1)]:
 post('invalid address '+repr(address)[:30]+' version '+repr(version),'/api/orders/A200/address',{'address':address,'version':version})
post('address at length 120','/api/orders/A200/address',{'address':'x'*120,'version':1},200)
post('stale address','/api/orders/A200/address',{'address':'Stale overwrite','version':1},409)
r=call('read after stale address','GET','/api/orders/A200')[1]
check('stale address preserves newer state',r['address']=='x'*120 and r['version']==2)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 futures=[pool.submit(call,'concurrent address '+str(i),'POST','/api/orders/A200/address',{'address':'Concurrent '+str(i),'version':2}) for i in range(2)]
 results=[f.result() for f in futures]
check('same-version concurrent address one winner',sorted(r[0] for r in results)==[200,409])
check('concurrent address persists winner',call('after concurrent address','GET','/api/orders/A200')[1]==next(r[1] for r in results if r[0]==200))
for ids,service,status in [(['A100','MISSING'],'express',404),(['A100','B100'],'express',403),(['B100','A100'],'express',403),([], 'express',400),(['A100',1],'express',400),(['A100'],'overnight',400)]:
 post('batch '+repr(ids)+' '+service,'/api/services',{'ids':ids,'service':service},status)
state=snapshot('after rejected batches')
check('failed batches leave all services unchanged',all(state[k]['service']==initial[k]['service'] for k in state))
post('valid batch','/api/services',{'ids':['A100','A200'],'service':'express'},200)
check('valid batch persists',all(o['service']=='express' for o in call('read valid batch','GET','/api/orders')[1]['orders']))
for note in ('', '   ', 'n'*161, None): post('invalid note '+repr(note)[:35],'/api/orders/A200/note',{'note':note})
post('valid note at length 160','/api/orders/A200/note',{'note':'n'*160},200)
for note in ('LOCKER: 1','  locker: 2'):
 post('unsupported locker note','/api/orders/A200/note',{'note':note},422)
check('rejected notes preserve previous note',call('read rejected locker','GET','/api/orders/A200')[1]['note']=='n'*160)
# Source validates trimmed note length but stores the untrimmed string.
for i,note in enumerate(('n'*160+' ', ' '+ 'n'*160+' ')):
 status,row=call('padded note over 160 '+str(i),'POST','/api/orders/A200/note',{'note':note})
 read=call('read padded note '+str(i),'GET','/api/orders/A200')[1]
 check('raw note length bound '+str(i),status==400)
 check('padded note persists as returned '+str(i),status==200 and row==read and len(read['note'])==len(note))
# Restore reversible fields using public APIs. Refunds and version increments cannot be undone.
current=snapshot('before cleanup')
for order_id,old in initial.items():
 actor=old['owner']; now=current[order_id]
 if now['address']!=old['address']:
  post('restore address '+order_id,'/api/orders/'+order_id+'/address',{'address':old['address'],'version':now['version']},200,actor)
 if now['note']!=old['note']:
  post('restore note '+order_id,'/api/orders/'+order_id+'/note',{'note':old['note']},200,actor)
 if now['service']!=old['service']:
  post('restore service '+order_id,'/api/services',{'ids':[order_id],'service':old['service']},200,actor)
final=snapshot('final')
(OUT/'final-state.json').write_text(json.dumps(final,indent=2))
check('all reversible fields restored',all(all(final[k][f]==initial[k][f] for f in ('address','note','service')) for k in initial))
(OUT/'checks.json').write_text(json.dumps({'api_requests_including_baseline':counter,'checks':checks},indent=2))
print('TOTAL REQUESTS',counter,flush=True)
