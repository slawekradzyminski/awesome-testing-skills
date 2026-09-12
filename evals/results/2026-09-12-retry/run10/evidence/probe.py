import urllib.request,urllib.error,json,datetime
BASE='http://127.0.0.1:64183'
def req(method,path,actor,action,body=None):
 headers={'Content-Type':'application/json'}
 if actor:headers['Authorization']='Bearer demo-'+actor
 data=None if body is None else json.dumps(body).encode()
 try:r=urllib.request.urlopen(urllib.request.Request(BASE+path,data=data,headers=headers,method=method))
 except urllib.error.HTTPError as e:r=e
 out={'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':method,'path':path,'actor':actor,'action':action,'request':body,'status':r.status,'response':json.load(r)}
 with open('evidence/http.jsonl','a') as f:f.write(json.dumps(out)+'\n')
 print(json.dumps(out))
 return out
if __name__=='__main__':
 req('GET','/api/v1/cart','alice','Persisted state after clicking Cancel')
 req('GET','/api/v1/cart','bob','Other identity after Alice Cancel')
 req('GET','/api/v1/cart',None,'Anonymous rejection')
 req('PUT','/api/v1/cart/items/1',None,'Anonymous update rejection',{'quantity':4})
 for body in [{'quantity':-1},{'quantity':1.5},{},{'quantity':None},{'quantity':'3'},{'quantity':True},{'quantity':6}]:
  req('PUT','/api/v1/cart/items/1','alice','Quantity/stock rejection',body)
  req('GET','/api/v1/cart','alice','Check rejection leaves state unchanged')
 req('PUT','/api/v1/cart/items/1','alice','Accept maximum stock quantity',{'quantity':5})
 req('GET','/api/v1/products','alice','Stock remains five after cart update')
 req('PUT','/api/v1/cart/items/1','alice','Restore Alice baseline',{'quantity':1})
