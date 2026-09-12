import json, urllib.request, urllib.error, time, hashlib
from pathlib import Path
BASE='http://127.0.0.1:49530'
rows=[]; checks=[]; created=[]
started=time.time()
prefix='uf'+str(int(started))[-7:]
def req(method,path,action,body=None,raw=None):
    assert len(rows)<60
    data=raw if raw is not None else (json.dumps(body,ensure_ascii=False).encode() if body is not None else None)
    r=urllib.request.Request(BASE+path,data=data,method=method,headers={'Content-Type':'application/json'})
    t=time.time()
    try:
        response=urllib.request.urlopen(r,timeout=4)
    except urllib.error.HTTPError as e: response=e
    except Exception as e:
        row={'id':len(rows)+1,'method':method,'path':path,'action':action,'error':str(e),'elapsed_ms':round((time.time()-t)*1000)}
        rows.append(row); persist(); raise
    payload=response.read().decode()
    row={'id':len(rows)+1,'method':method,'path':path,'action':action,'request':body if raw is None else raw.decode(),'request_bytes':len(data or b''),'status':response.status,'headers':dict(response.headers),'body':json.loads(payload) if payload else None,'elapsed_ms':round((time.time()-t)*1000)}
    rows.append(row); persist(); return row

def persist():
    Path('evidence/http.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))

def check(name,expected,ok,ids,actual):
    checks.append({'name':name,'basis':'runtime','status':'passed' if ok else 'failed','expected':expected,'actual':actual,'evidence':['evidence/http.json'],'request_ids':ids})

def signup(label,password='Invented8',expected=201,username=None,email=None,extra=None):
    name=username or prefix+label
    body={'username':name,'email':email if email is not None else name+'@example.test','password':password}
    if extra: body.update(extra)
    p=req('POST','/api/v1/users/signup',label,body)
    if p['status']==201: created.append(name)
    g=req('GET','/api/v1/users/'+name,label+' persistence inspection')
    good=p['status']==expected and (g['body']=={'username':name,'email':body['email']} if expected==201 else g['status']==404)
    check(label,'AUTH-2: '+str(expected)+'; '+('persist only username/email' if expected==201 else 'no record'),good,[p['id'],g['id']],f"POST {p['status']}: {p['body']}; GET {g['status']}")
    return name

health=req('GET','/health','identify assigned deployed build')
req('GET','/api/v1/users/'+prefix+'base','baseline absence')
base=signup('base',extra={'admin':True,'displayName':'ignored'})
p=req('POST','/api/v1/users/signup','duplicate username with altered email',{'username':base,'email':prefix+'different@example.test','password':'Invented9'})
g=req('GET','/api/v1/users/'+base,'original record after duplicate username')
check('duplicate username','AUTH-2: 409 and original record unchanged',p['status']==409 and g['body']=={'username':base,'email':base+'@example.test'},[p['id'],g['id']],f"POST {p['status']}; GET {g['body']}")
p=req('POST','/api/v1/users/signup','duplicate email under fresh username',{'username':prefix+'dupemail','email':base+'@example.test','password':'Invented9'})
g=req('GET','/api/v1/users/'+prefix+'dupemail','duplicate email creates no new record')
check('duplicate email','AUTH-2: 409 and no new record',p['status']==409 and g['status']==404,[p['id'],g['id']],f"POST {p['status']}; GET {g['status']}")
for label,password in [('ascii72','A'*72),('ascii73','A'*73),('ascii255','A'*255),('unicode18','😀'*18),('unicode19','😀'*19),('ascii73repeat','B'*73)]: signup(label,password)
for label,password in [('shortpassword','A'*7),('longpassword','A'*256),('nullpassword',None)]: signup(label,password,400)
signup('shortusername',expected=400,username='u'+prefix[-2:])
signup('longusername',expected=400,username=prefix+'x'*(256-len(prefix)))
signup('username255',username=prefix+'x'*(255-len(prefix)))
signup('username4',username='u'+prefix[-3:])
signup('emailnodomain',expected=400,email=prefix+'@')
signup('emailnolocal',expected=400,email='@example.test')
signup('emailnonscalar',expected=400,email=[])
for label,raw in [('malformed',b'{"username":'),('nonobject',b'[]')]:
    p=req('POST','/api/v1/users/signup',label,raw=raw)
    check(label,'AUTH-4: 400',p['status']==400,[p['id']],str(p['body']))
# Requests at the actual encoded-byte ceiling, padding an ignored field.
name=prefix+'body8192'; body={'username':name,'email':name+'@example.test','password':'Invented8','padding':''}
raw=json.dumps(body,ensure_ascii=False).encode(); body['padding']='x'*(8192-len(raw)); raw=json.dumps(body,ensure_ascii=False).encode()
p=req('POST','/api/v1/users/signup','8192 encoded bytes accepted',raw=raw)
if p['status']==201: created.append(name)
g=req('GET','/api/v1/users/'+name,'8192-byte payload persistence')
check('8192-byte JSON object','AUTH-4: accepted; AUTH-2: only username/email stored',p['status']==201 and g['body']=={'username':name,'email':name+'@example.test'},[p['id'],g['id']],f"POST {p['status']}, GET {g['body']}")
for name in created:
    d=req('DELETE','/api/v1/users/'+name,'cleanup own successful registration')
    g=req('GET','/api/v1/users/'+name,'confirm cleanup')
    check('cleanup '+name,'AUTH-3: DELETE 204 then GET 404',d['status']==204 and g['status']==404,[d['id'],g['id']],f"DELETE {d['status']}; GET {g['status']}")
meta={'started_unix':started,'duration_seconds':round(time.time()-started,3),'api_requests':len(rows),'browser_actions':0,'availability_requests':1,'created':created,'checks':checks,'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path('app/app.py'),Path('app/domain.py')]}}
Path('evidence/session.json').write_text(json.dumps(meta,indent=2))
print(json.dumps({'requests':len(rows),'passed':sum(c['status']=='passed' for c in checks),'failed':[c['name'] for c in checks if c['status']=='failed'],'created_cleaned':created},indent=2))
