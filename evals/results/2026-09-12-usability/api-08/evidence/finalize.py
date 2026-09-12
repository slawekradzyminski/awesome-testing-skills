import json, urllib.request, urllib.error, time
from pathlib import Path
rows=json.loads(Path('evidence/http.json').read_text()); meta=json.loads(Path('evidence/session.json').read_text())
name=meta['created'][0]+'reuse'
body={'username':name,'email':meta['created'][0]+'@example.test','password':'Abcd1234'}
for method,path,label,data in [('POST','/api/v1/users/signup','8-character password; reuse email after cleanup',body),('GET','/api/v1/users/'+name,'verify minimum-password registration',None),('DELETE','/api/v1/users/'+name,'cleanup final registration',None),('GET','/api/v1/users/'+name,'verify final cleanup',None)]:
    assert len(rows)<60
    encoded=json.dumps(data).encode() if data else None
    t=time.time()
    try: response=urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:49530'+path,data=encoded,method=method,headers={'Content-Type':'application/json'}),timeout=4)
    except urllib.error.HTTPError as e: response=e
    raw=response.read().decode()
    rows.append({'id':len(rows)+1,'method':method,'path':path,'action':label,'request':data,'request_bytes':len(encoded or b''),'status':response.status,'headers':dict(response.headers),'body':json.loads(raw) if raw else None,'elapsed_ms':round((time.time()-t)*1000)})
    Path('evidence/http.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
assert [r['status'] for r in rows[-4:]]==[201,200,204,404]
assert rows[-3]['body']=={'username':name,'email':body['email']}
meta['api_requests']=len(rows); meta['created'].append(name)
meta['checks'].append({'name':'8-character password and email reuse following deletion','basis':'runtime','status':'passed','expected':'AUTH-2/AUTH-3: 201, persist only username/email, then 204 and 404','actual':'201, GET matching record; DELETE 204; GET 404. Previously deleted email available again.','evidence':['evidence/http.json'],'request_ids':[57,58,59,60]})
meta['last_request_unix']=time.time()
Path('evidence/session.json').write_text(json.dumps(meta,indent=2))
for p in [Path('app/app.py'),Path('app/domain.py')]:
    Path('evidence/'+p.name+'.txt').write_text('\n'.join(f'{i}: {s}' for i,s in enumerate(p.read_text().splitlines(),1))+'\n')
finding={'requirement_id':'AUTH-2','title':'Signup rejects contract-valid passwords exceeding 72 UTF-8 bytes','status':'confirmed','expected':'Unique registrations with passwords of 8–255 Unicode characters return 201 and persist username/email.','actual':'73 ASCII characters (two fresh registrations), 255 ASCII characters and 19 emoji (76 UTF-8 bytes) return 400 with error "password cannot be more than 72 bytes"; subsequent GET returns 404. Controls of 72 ASCII characters and 18 emoji succeed.','impact':'Users cannot register with valid passwords above an undocumented byte limit; the effective character ceiling varies with encoding.','severity':'Medium (provisional)','evidence':['evidence/http.json','evidence/domain.py.txt'],'request_ids':[9,10,11,12,13,14,15,16,17,18,19,20]}
risks=[{'area':'Password character/byte boundary regression','reason':'Confirmed AUTH-2 failure; no existing tests supplied.','priority':'high','next_probe':'After a fix, run domain boundary cases for 8/72/73/255/256 ASCII and multibyte characters, plus representative signup/persistence API checks.'},{'area':'Other input shapes and oversized objects','reason':'Tested null password, array email, malformed JSON, array root and 8192-byte object; other missing/type variations and 8193 bytes not exercised.','priority':'low','next_probe':'A follow-up bounded pass over missing fields, scalar roots and 8193-byte rejection with state inspection.'}]
limitations=['No existing tests or revision metadata were supplied in the candidate directory; relevant application source was inspected, but no existing suite was executed. Source file hashes are recorded; health build validation-fixture-1 has no verifiable commit mapping.','Scoped to registration, lookup and cleanup. Signin, production authentication, concurrency, normalization, full email syntax, password strength and restart persistence were not exercised.','Not exhaustive: missing-field permutations, all non-string inputs, other Unicode classes and the 8193-byte rejection boundary remain untested. Malformed and non-object rejection did not include a record lookup because neither supplied a usable username.','API-only exploration: no browser session or screenshots.']
out={'source_access':True,'runtime_exercised':True,'runtime_status':'tested','checks':meta['checks'],'findings':[finding],'risks':risks,'observations':[{'method':r['method'],'path':r['path'],'status':r['status'],'action':r['action'],'evidence':'evidence/http.json','request_id':r['id']} for r in rows],'limitations':limitations,'cleanup':'Seven successful registrations deleted; every DELETE returned 204 and subsequent GET returned 404. All rejected identifiable registrations were absent. No browser opened; server lifecycle left to fixture owner.','accounting':{'api_requests':60,'availability_requests':1,'browser_actions':0,'request_budget':60}}
Path('submission.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps({'requests':len(rows),'checks':len(meta['checks']),'failed':sum(c['status']=='failed' for c in meta['checks']),'cleanup_statuses':[r['status'] for r in rows[-4:]]}))
