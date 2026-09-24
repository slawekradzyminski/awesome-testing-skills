"""Known-answer native registration regression and gateway preflight."""
import argparse
import json
from pathlib import Path
from runtime import Runtime,request


def run(build,out):
    out.mkdir(parents=True,exist_ok=False)
    results=[]
    for backend in ['api-before','api-fixed']:
        for repeat in [1,2]:
            folder=out/f'{backend}-{repeat}';folder.mkdir()
            with Runtime(build,folder/'controller',backend=backend) as runtime:
                account={'username':'history_alpha','email':'conflict@example.test','password':'HistoryPass123!',
                         'firstName':'John','lastName':'Boyd','roles':['ROLE_CLIENT']}
                observations=[]
                def observe(method,path,body=None,token=None):
                    response=request(runtime.url+path,method,body,token)
                    observations.append({'method':method,'path':path,'request':body,'response':response})
                    (folder/'http.json').write_text(json.dumps(observations,indent=2)+'\n')
                    return response
                assert observe('POST','/users/signup',account)['status']==201
                login=observe('POST','/users/signin',{'username':account['username'],'password':account['password']})
                assert login['status']==200
                assert observe('GET','/users/me',token=login['json']['token'])['status']==200
                duplicate=observe('POST','/users/signup',{**account,'username':'history_beta'})
                assert duplicate['status']==(500 if backend=='api-before' else 400),duplicate
                if backend=='api-fixed':assert 'Email is already in use' in duplicate['body']
                assert observe('POST','/users/signup',{**account,'email':'fresh@example.test'})['status']==400
                results.append({'backend':backend,'repeat':repeat,'passed':True,'duplicate_status':duplicate['status']})
                (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
                print(json.dumps(results[-1]),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--build',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();run(args.build.resolve(),args.out.resolve())
