import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
OUT=Path(__file__).parent
records=[]
def req(label, method='GET', body=None):
    request=Request('http://127.0.0.1:59591/api/orders/A200'+('/note' if method=='POST' else ''),method=method,headers={'X-Test-User':'alice','Content-Type':'application/json'},data=json.dumps(body).encode() if body is not None else None)
    try:
        with urlopen(request,timeout=5) as response: status,value=response.status,json.load(response)
    except HTTPError as error: status,value=error.code,json.load(error)
    records.append(dict(label=label,method=method,path=request.full_url,request=body,status=status,response=value))
    return status,value
_,before=req('baseline')
try:
    oversized='n'*160+' '
    status,value=req('161 character note with trailing space','POST',{'note':oversized})
    _,stored=req('read persisted oversized note')
    result=dict(input_length=len(oversized),trimmed_length=len(oversized.strip()),status=status,persisted_length=len(stored['note']),persisted_exact_input=stored['note']==oversized)
    status,value=req('161 nonspace character control','POST',{'note':'n'*161})
    result['nonspace_161_status']=status
    _,retained=req('read after rejected length control')
    result['rejected_control_retains_previous']=retained['note']==stored['note']
    status,value=req('locker with whitespace and mixed case','POST',{'note':'  LoCkEr: 12  '})
    result['normalized_locker_status']=status
finally:
    req('restore original note','POST',{'note':before['note']})
    _,after=req('verify restored order')
    result['full_order_restored']=before==after
    result['api_requests']=len(records)
    (OUT/'note-boundary-http.json').write_text(json.dumps(records,indent=2)+'\n')
    (OUT/'note-boundary-summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
