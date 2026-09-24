"""Known-answer historical UI preflight; never give this to candidates."""
import argparse
import json
from pathlib import Path
import subprocess
from runtime import Runtime, CUSTOMER, request


def run(build, out):
    out.mkdir(parents=True, exist_ok=False)
    results = []
    for frontend in ['ui-before', 'ui-fixed', 'mobile-before', 'mobile-fixed']:
        for repeat in [1, 2]:
            folder = out/f'{frontend}-{repeat}'
            folder.mkdir()
            session = f'history-preflight-{frontend}-{repeat}'
            try:
                with Runtime(build, folder/'controller', frontend=frontend) as runtime:
                    login = request(runtime.url+'/api/v1/users/signin','POST',CUSTOMER)['json']
                    args = {'url':runtime.url,'tokens':{k:login[k] for k in ['token','refreshToken']},
                            'folder':str(folder), 'mobile':frontend.startswith('mobile')}
                    script = '''async page => {
                      const a = ARGS;
                      await page.context().addInitScript(tokens => {
                        localStorage.setItem('token', tokens.token);
                        localStorage.setItem('refreshToken', tokens.refreshToken);
                      }, a.tokens);
                      await page.setViewportSize(a.mobile ? {width:375,height:812} : {width:1280,height:900});
                      if(a.mobile) {
                        await page.goto(a.url+'/products/3');
                        await page.getByTestId('product-title').waitFor();
                        await page.screenshot({path:a.folder+'/mobile.png',fullPage:true});
                        return await page.evaluate(() => ({width:document.documentElement.clientWidth,
                          scroll:document.documentElement.scrollWidth, text:document.body.innerText}));
                      }
                      const cart = page.waitForResponse(r=>r.url().endsWith('/api/v1/cart') && r.status()===200);
                      const detail = page.waitForResponse(r=>r.url().endsWith('/api/v1/products/1') && r.status()===200);
                      await page.goto(a.url+'/cart');
                      await cart;
                      await page.waitForTimeout(150);
                      const during = await page.locator('body').innerText();
                      await page.screenshot({path:a.folder+'/during.png',fullPage:true});
                      await detail;
                      await page.getByTestId('cart-items-list').waitFor();
                      const after = await page.locator('body').innerText();
                      await page.screenshot({path:a.folder+'/after.png',fullPage:true});
                      return {during, after};
                    }'''.replace('ARGS',json.dumps(args))
                    (folder/'experiment.js').write_text(script)
                    with open(folder/'browser-open.txt','w') as log:
                        subprocess.run(['playwright-cli','-s='+session,'open'],stdout=log,stderr=log,check=True,timeout=30)
                    result = subprocess.run(['playwright-cli','-s='+session,'run-code','--filename='+str(folder/'experiment.js')],
                                            capture_output=True,text=True,timeout=50)
                    (folder/'browser.txt').write_text(result.stdout+result.stderr)
                    assert result.returncode == 0 and '### Error' not in result.stdout, result.stdout
                    raw = result.stdout.split('### Result\n',1)[1].split('\n###',1)[0]
                    observed = json.loads(raw)
                    if frontend.startswith('mobile'):
                        failure = observed['scroll'] > observed['width']+1
                    else:
                        failure = 'Your cart is empty' in observed['during']
                        assert 'Desk lamp' in observed['after'], observed
                    assert failure == frontend.endswith('before'), (frontend, observed)
                    results.append({'frontend':frontend,'repeat':repeat,'expected_failure_observed':failure,
                                    'check_passed':True,'observed':observed})
                    (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
                    print(json.dumps({'frontend':frontend,'repeat':repeat,'check_passed':True}),flush=True)
            finally:
                subprocess.run(['playwright-cli','-s='+session,'close'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    run(args.build.resolve(),args.out.resolve())
