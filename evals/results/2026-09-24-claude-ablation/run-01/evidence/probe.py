import json, urllib.request
B="http://127.0.0.1:50689"; log=[]
def call(m,p,u="alice",body=None,raw=None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    h={"Content-Type":"application/json"}
    if u: h["X-Test-User"]=u
    r=urllib.request.Request(B+p,data=data,method=m,headers=h)
    try:
        with urllib.request.urlopen(r) as x: s,v=x.status,json.loads(x.read())
    except urllib.error.HTTPError as e: s,v=e.code,json.loads(e.read() or b"{}")
    log.append({"m":m,"p":p,"u":u,"req":body if raw is None else raw.decode(),"status":s,"resp":v}); print(s,m,p,u,body if raw is None else raw,"->",json.dumps(v)); return s,v
print("## baseline"); call("GET","/api/orders"); call("GET","/api/orders/B100","bob")
print("## authz"); call("GET","/api/orders"," ".strip() or None); call("GET","/api/orders/B100"); call("POST","/api/orders/B100/refund",body={"amount":1}); call("POST","/api/orders/B100/address",body={"address":"hack","version":1}); call("POST","/api/orders/B100/note",body={"note":"hack"})
print("## refund cumulative (A200 paid 6000)"); call("POST","/api/orders/A200/refund",body={"amount":4000}); call("POST","/api/orders/A200/refund",body={"amount":4000}); call("GET","/api/orders/A200")
print("## refund validation"); 
for a in [0,-5,1.5,"100",True,None]: call("POST","/api/orders/B100/refund","bob",{"amount":a})
call("POST","/api/orders/B100/refund","bob",{"amount":4001}); call("POST","/api/orders/B100/refund","bob",raw=b"{bad")
print("## address stale"); s,o=call("GET","/api/orders/A200"); v=o["version"]
call("POST","/api/orders/A200/address",body={"address":"Newer Address","version":v})
call("POST","/api/orders/A200/address",body={"address":"Stale Overwrite","version":v})
call("GET","/api/orders/A200")
call("POST","/api/orders/A200/address",body={"address":"x","version":v+99})
call("POST","/api/orders/A200/address",body={"address":"   ","version":v})
call("POST","/api/orders/A200/address",body={"address":"a"*121,"version":v+2})
s,o=call("GET","/api/orders/A200"); call("POST","/api/orders/A200/address",body={"address":"20 Pine Street","version":o["version"]})
print("## services atomicity"); call("POST","/api/services",body={"ids":["A100","B100"],"service":"express"}); call("GET","/api/orders/A100"); call("GET","/api/orders/B100","bob")
call("POST","/api/services",body={"ids":["A200","NOPE"],"service":"express"}); call("GET","/api/orders/A200")
call("POST","/api/services",body={"ids":["A100"],"service":"overnight"})
call("POST","/api/services",body={"ids":["A100","A200"],"service":"standard"})
print("## note"); call("POST","/api/orders/A100/note",body={"note":"LOCKER: 12"}); call("POST","/api/orders/A100/note",body={"note":"locker: 12"}); call("POST","/api/orders/A100/note",body={"note":"   "}); call("POST","/api/orders/A100/note",body={"note":"n"*161}); call("GET","/api/orders/A100")
call("POST","/api/orders/A100/note",body={"note":" "*50+"n"*160}); call("POST","/api/orders/A100/note",body={"note":"Leave with reception"})
print("## final"); call("GET","/api/orders"); call("GET","/api/orders","bob")
json.dump(log,open("evidence/probe_log.json","w"),indent=1); print("requests:",len(log))
