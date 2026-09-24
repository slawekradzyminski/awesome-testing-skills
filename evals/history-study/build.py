"""Build pinned original revisions outside their source repositories."""
import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile

BUILDS={
    'api-before':('backend','8bfa560dbdd309036cf850b1302d8e1fc1806573','java21'),
    'api-fixed':('backend','75ca60d8879b8c9b1e7c78031f01429852d1f72c','java21'),
    'runtime-backend':('backend','b4973a53b1697f84a479b6aceeb870cd48423091','java25'),
    'ui-before':('frontend','f71a4f63ca7514c0b8109a2d3d3a335406fa10f1','node'),
    'ui-fixed':('frontend','bc2d904fa7906e028248b5122d8024719900de3d','node'),
    'mobile-before':('frontend','aa90523b8eaa9b1d1e575f125c3f2c83b7dc372e','node'),
    'mobile-fixed':('frontend','d866c7f4dc18573a46f78a976feb0f2c7e6c9d78','node'),
    'cart-before':('frontend','b49cf3cb7b1e8ccdbe11b5ec6cb468bb3f723ab7','node'),
    'cart-fixed':('frontend','7d78de050c83897ccd77ed8d51ed9fed0c52b9e6','node'),
}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--backend-repo',type=Path,required=True)
    parser.add_argument('--frontend-repo',type=Path,required=True)
    parser.add_argument('--java21',type=Path,required=True,help='JDK21 home directory')
    parser.add_argument('--java25',type=Path,required=True,help='JDK25 home directory')
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    java={k:str(getattr(args,k).resolve()/'bin/java') for k in ['java21','java25']}
    (out/'runtime-tools.json').write_text(json.dumps(java,indent=2)+'\n')
    manifest={}
    for name,(repo_key,ref,tool) in BUILDS.items():
        repo=getattr(args,repo_key+'_repo').resolve()
        revision=subprocess.check_output(['git','rev-parse',ref],cwd=repo,text=True).strip()
        raw=subprocess.check_output(['git','archive',revision],cwd=repo)
        folder=out/name;folder.mkdir()
        with tarfile.open(fileobj=io.BytesIO(raw)) as tar:tar.extractall(folder,filter='data')
        env=os.environ.copy()
        if tool=='node':
            commands=[['npm','ci','--ignore-scripts','--no-audit','--no-fund'],['npm','run','build']]
        else:
            home=str(getattr(args,tool).resolve());env['JAVA_HOME']=home;env['PATH']=home+'/bin'+os.pathsep+env['PATH']
            commands=[['./mvnw','-q','-Dmaven.test.skip=true','package']]
        with open(out/(name+'-build.log'),'w') as log:
            for command in commands:subprocess.run(command,cwd=folder,env=env,stdout=log,stderr=log,check=True)
        manifest[name]={'repository':str(repo),'revision':revision,'commands':commands,'tool':tool}
        (out/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print(name+' built',flush=True)


if __name__=='__main__':main()
