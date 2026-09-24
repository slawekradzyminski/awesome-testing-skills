"""Verify unchanged production bundles through the actual study gateway."""
import argparse
import json
from pathlib import Path
import subprocess
from runtime import Runtime, CUSTOMER, request


def run(build,out):
    out.mkdir(parents=True,exist_ok=False)
    results=[]
    for frontend in ['cart-before','cart-fixed']:
        for repeat in [1,2]:
            folder=out/f'{frontend}-{repeat}';folder.mkdir()
            session=f'history-legacy-{frontend}-{repeat}'
            try:
                with Runtime(build,folder/'controller',backend='api-fixed',frontend=frontend) as r:
                    token=request('http://localhost:4001/users/signin','POST',CUSTOMER)['json']['token']
                    args={'token':token,'folder':str(folder),'id':r.products[0]['id'],'fixed':frontend=='cart-fixed'}
                    code='''async page => {
                      const a=ARGS;
                      await page.context().addInitScript(t=>localStorage.setItem('token',t),a.token);
                      await page.goto('http://127.0.0.1:8081/cart');
                      await page.getByRole('heading',{name:'Cart Items',exact:true}).waitFor();
                      const quantity=p=>p.locator('span.border-t.border-b');
                      const initial=await quantity(page).innerText();
                      const second=await page.context().newPage();
                      await second.goto('http://127.0.0.1:8081/cart');
                      await second.getByRole('heading',{name:'Cart Items',exact:true}).waitFor();
                      await second.getByRole('button',{name:'+',exact:true}).click();
                      await second.getByRole('button',{name:'+',exact:true}).click();
                      const saved=second.waitForResponse(r=>r.url().includes('/api/cart/items/') && r.request().method()==='PUT');
                      await second.getByRole('button',{name:'Update',exact:true}).click();
                      await saved;
                      const refreshed=page.waitForResponse(r=>r.url().endsWith('/api/cart') && r.status()===200);
                      await page.bringToFront();
                      await page.context().setOffline(true);
                      await page.context().setOffline(false);
                      const cart=await (await refreshed).json();
                      await page.getByText('$199.80',{exact:true}).nth(1).waitFor();
                      if(a.fixed) await page.waitForFunction(()=>document.querySelector('span.border-t.border-b')?.textContent.trim()==='4');
                      await page.screenshot({path:a.folder+'/state.png',fullPage:true});
                      return {initial,quantity:await quantity(page).innerText(),cart,body:await page.locator('body').innerText()};
                    }'''.replace('ARGS',json.dumps(args))
                    (folder/'experiment.js').write_text(code)
                    subprocess.run(['playwright-cli','-s='+session,'open'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True,timeout=30)
                    done=subprocess.run(['playwright-cli','-s='+session,'run-code','--filename='+str(folder/'experiment.js')],capture_output=True,text=True,timeout=55)
                    (folder/'browser.txt').write_text(done.stdout+done.stderr)
                    assert done.returncode==0 and '### Error' not in done.stdout,done.stdout
                    observed=json.loads(done.stdout.split('### Result\n',1)[1].split('\n###',1)[0])
                    assert observed['initial']=='2' and observed['cart']['items'][0]['quantity']==4,observed
                    assert observed['quantity']==('2' if frontend=='cart-before' else '4'),observed
                    results.append({'frontend':frontend,'repeat':repeat,'passed':True,'observed':observed})
                    (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
                    print(json.dumps({'frontend':frontend,'repeat':repeat,'passed':True}),flush=True)
            finally:
                subprocess.run(['playwright-cli','-s='+session,'close'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--build',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();run(args.build.resolve(),args.out.resolve())
