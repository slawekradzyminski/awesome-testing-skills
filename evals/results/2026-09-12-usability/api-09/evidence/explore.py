import urllib.request, urllib.error, json, time, hashlib
from pathlib import Path
BASE='http://127.0.0.1:49532'
START=time.time()
records=[]; checks=[]; owned=set(); prefix='qh926'

def call(method,path,body=None,action='',raw=None):
    assert len(records)<60
    data=raw if raw is not None else (json.dumps(body,ensure_ascii=False).encode('utf-8') if body is not None else None)
    req=urllib.request.Request(BASE+path,data=data,method=method,headers={'Content-Type':'application/json'})
    t=time.time()
    try:
        with urllib.request.urlopen(req,timeout=3) as r: status=r.status; headers=dict(r.headers); response=r.read().decode()
    except urllib.error.HTTPError as r: status=r.code; headers=dict(r.headers); response=r.read().decode()
    except Exception as e: status=None; headers={}; response=str(e)
    safe=dict(body) if isinstance(body,dict) else body
    if isinstance(safe,dict) and 'password' in safe:
        p=safe['password']; safe['password']={'synthetic':True,'type':type(p).__name__,'characters':len(p) if isinstance(p,str) else None,'utf8_bytes':len(p.encode()) if isinstance(p,str) else None,'value_description':('U+1F680 repeated' if isinstance(p,str) and p and set(p)=={'🚀'} else 'invented ASCII password' if isinstance(p,str) else repr(p))}
    entry={'id':len(records)+1,'method':method,'path':path,'action':action,'request':safe,'encoded_request_bytes':len(data) if data is not None else 0,'raw_request_description':('JSON object padded with ignored field' if raw and raw.startswith(b'{"username"') else raw.decode() if raw else None),'status':status,'headers':headers,'response':response,'elapsed_ms':round((time.time()-t)*1000,2)}
    records.append(entry)
    Path('evidence/http.json').write_text(json.dumps(records,indent=2,ensure_ascii=False))
    return status,json.loads(response) if response and status is not None else None,entry['id']

def check(name,expected,actual,ids,ok):
    checks.append({'name':name,'basis':'runtime','status':'passed' if ok else 'failed','expected':expected,'actual':actual,'evidence':['evidence/http.json'],'request_ids':ids})

def path(name): return '/api/v1/users/'+name

def trial(label,changes,expected):
    name=prefix+label
    b={'username':name,'email':name+'@example.test','password':'Invented88'}; b.update(changes)
    name=b['username'] if isinstance(b['username'],str) else name
    s,r,i=call('POST','/api/v1/users/signup',b,label)
    gs,gr,j=call('GET',path(name),action=label+' persisted state')
    ids=[i,j]
    if s==201:
        owned.add(name)
        ds,dr,k=call('DELETE',path(name),action=label+' cleanup'); ids.append(k)
        if ds==204: owned.discard(name)
    good=s==expected and (gs==200 and gr=={'username':b['username'],'email':b['email']} if expected==201 else gs==404)
    check(label,'AUTH-2: '+str(expected)+'; valid records persist username/email only, invalid records absent',f'POST {s}; GET {gs}; response {r}',ids,good)

s,r,i=call('GET','/health',action='single initial availability request')
if s!=200:
    Path('evidence/blocked.json').write_text(json.dumps({'checks':checks,'records':records}))
    raise SystemExit('Runtime blocked; no further availability requests')
# Baseline remains until final isolation/cleanup check.
b={'username':prefix+'base','email':prefix+'base@example.test','password':'Invented88','role':'admin','extra':{'ignored':True}}
s,r,i=call('POST','/api/v1/users/signup',b,'valid registration with ignored extra fields'); owned.add(b['username']) if s==201 else None
s2,r2,j=call('GET',path(b['username']),action='baseline read')
check('valid baseline and ignored fields','AUTH-2/4: 201 and only username/email persisted',f'POST {s}, GET {s2}: {r2}',[i,j],s==201 and s2==200 and r2=={'username':b['username'],'email':b['email']})
dup=dict(b,email=prefix+'other@example.test')
s,r,i=call('POST','/api/v1/users/signup',dup,'duplicate username with alternate email')
s2,r2,j=call('GET',path(b['username']),action='duplicate username does not replace email')
check('duplicate username preserves record','AUTH-2: 409, existing record unchanged',f'POST {s}; GET {r2}',[i,j],s==409 and r2=={'username':b['username'],'email':b['email']})
dup=dict(b,username=prefix+'dupemail')
s,r,i=call('POST','/api/v1/users/signup',dup,'duplicate email with new username')
s2,r2,j=call('GET',path(dup['username']),action='duplicate email creates no secondary record')
check('duplicate email creates no record','AUTH-2: 409 and candidate GET 404',f'POST {s}; GET {s2}',[i,j],s==409 and s2==404)
for label,pw,expected in [('ascii7','A'*7,400),('ascii255','A'*255,201),('ascii256','A'*256,400),('unicode7','🚀'*7,400),('unicode8','🚀'*8,201),('unicode255','🚀'*255,201),('unicode256','🚀'*256,400)]: trial(label,{'password':pw},expected)
for label,name,expected in [('name3','q9x',400),('name4','q9xz',201),('name255',prefix+'x'*250,201),('name256',prefix+'x'*251,400)]: trial(label,{'username':name},expected)
for label,email in [('emaillocal','@example.test'),('emaildomain',prefix+'@'),('emailat',prefix+'.example.test'),('emailempty','')]: trial(label,{'email':email},400)
for label,change in [('pwnull',{'password':None}),('namelist',{'username':[]}),('emailnumber',{'email':123})]: trial(label,change,400)
for label,raw in [('malformed',b'{'),('nonobject',b'[]')]:
    s,r,i=call('POST','/api/v1/users/signup',raw=raw,action=label)
    check(label,'AUTH-4: 400',f'{s}: {r}',[i],s==400)
# Exact encoded byte boundary using ignored ASCII padding.
for size in [8192,8193]:
    name=prefix+'bytes'+str(size)
    ob={'username':name,'email':name+'@example.test','password':'Invented88','padding':''}
    raw=json.dumps(ob,separators=(',',':')).encode(); ob['padding']='x'*(size-len(raw)); raw=json.dumps(ob,separators=(',',':')).encode()
    assert len(raw)==size
    s,r,i=call('POST','/api/v1/users/signup',raw=raw,action=f'exact {size} encoded bytes')
    gs,gr,j=call('GET',path(name),action=f'{size} bytes state')
    ids=[i,j]
    if s==201:
        owned.add(name); ds,dr,k=call('DELETE',path(name),action='byte boundary cleanup'); ids.append(k)
        if ds==204: owned.discard(name)
    check(f'{size} byte envelope','AUTH-4: 8192 accepted; oversized rejected (specific status unspecified)',f'POST {s}; GET {gs}',ids,(s==201 and gs==200) if size==8192 else (s>=400 and gs==404))
# Baseline survives removal of other own resources, then is deleted.
s,r,i=call('GET',path(b['username']),action='deleting other records preserves baseline')
check('cleanup isolation','AUTH-3: baseline survives other deletes',f'GET {s}: {r}',[i],s==200 and r=={'username':b['username'],'email':b['email']})
s,r,i=call('DELETE',path(b['username']),action='final baseline cleanup')
if s==204: owned.discard(b['username'])
s2,r2,j=call('GET',path(b['username']),action='verify baseline absent after delete')
check('delete then absent','AUTH-3: DELETE 204 then GET 404',f'DELETE {s}; GET {s2}',[i,j],s==204 and s2==404)
meta={'started_unix':START,'duration_seconds':round(time.time()-START,2),'api_requests':len(records),'availability_requests':1,'browser_actions':0,'remaining_owned_records':sorted(owned),'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path('app/app.py'),Path('app/domain.py'),Path('requirements.md')]},'deployed_build':'validation-fixture-1','source_revision':'No revision metadata supplied inside allowed directory; content hashes recorded','source_runtime_relationship':'Unknown; runtime health version is not a source revision'}
Path('evidence/checks.json').write_text(json.dumps(checks,indent=2,ensure_ascii=False))
Path('evidence/session.json').write_text(json.dumps(meta,indent=2))
print(json.dumps({'metadata':meta,'check_count':len(checks),'failed_checks':[c for c in checks if c['status']!='passed']},indent=2))
