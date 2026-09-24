import json, urllib.request
B="http://127.0.0.1:50691"
log=[]
def req(m,p,user="alice",body=None):
    h={"Content-Type":"application/json"}
    if user: h["X-Test-User"]=user
    d=json.dumps(body).encode() if body is not None else None
    r=urllib.request.Request(B+p,data=d,headers=h,method=m)
    try:
        with urllib.request.urlopen(r,timeout=5) as x: s,t=x.status,x.read().decode()
    except urllib.error.HTTPError as e: s,t=e.code,e.read().decode()
    log.append({"req":f"{m} {p}","user":user,"body":body,"status":s,"resp":t}); print(m,p,user,body,"->",s,t); return s,t
print("## baseline"); req("GET","/api/orders"); req("GET","/api/orders/B100","bob"); req("GET","/api/orders",None)
print("## F1 cumulative refund on A200 (paid 6000)")
req("POST","/api/orders/A200/refund",body={"amount":5000})
req("POST","/api/orders/A200/refund",body={"amount":5000})
req("GET","/api/orders/A200")
print("## F2 stale address version on A200")
req("POST","/api/orders/A200/address",body={"address":"Newer Addr","version":1})
req("POST","/api/orders/A200/address",body={"address":"Stale Addr","version":1})
req("GET","/api/orders/A200")
print("## F3 services partial write")
req("POST","/api/services",body={"ids":["A100","B100"],"service":"express"})
req("POST","/api/services",body={"ids":["A100","ZZZ"],"service":"express"})
req("GET","/api/orders/A100"); req("GET","/api/orders/B100","bob")
print("## authz contrasts")
req("POST","/api/orders/B100/refund",body={"amount":1}); req("POST","/api/orders/B100/note",body={"note":"x"}); req("POST","/api/orders/B100/address",body={"address":"x","version":1})
req("GET","/api/orders/B100","bob")
print("## note")
req("POST","/api/orders/A200/note",body={"note":"  locker: box 5"}); req("POST","/api/orders/A200/note",body={"note":"   "})
req("POST","/api/orders/A200/note",body={"note":" "*50+"x"*150}); req("GET","/api/orders/A200")
print("## validation")
req("POST","/api/orders/A100/refund",body={"amount":True}); req("POST","/api/orders/A100/refund",body={"amount":10.0}); req("POST","/api/orders/A100/refund",body={"amount":"100"})
req("POST","/api/orders/A100/address",body={"address":"x"*121,"version":1})
req("POST","/api/services",body={"ids":["A100"],"service":"overnight"})
print("## restore")
req("POST","/api/services",body={"ids":["A100","A200"],"service":"standard"})
s,t=req("GET","/api/orders/A200"); v=json.loads(t)["version"]
req("POST","/api/orders/A200/address",body={"address":"20 Pine Street","version":v})
req("POST","/api/orders/A200/note",body={"note":"Ring twice"})
req("GET","/api/orders")
json.dump(log,open("probe_log.json","w"),indent=1); print("requests:",len(log))
