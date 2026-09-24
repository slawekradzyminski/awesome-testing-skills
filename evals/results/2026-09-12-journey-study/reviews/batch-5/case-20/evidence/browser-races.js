async page => {
  const results=[];
  const state=()=>page.evaluate(()=>({order:document.querySelector('#order').value,heading:document.querySelector('#heading').textContent,note:document.querySelector('#note').value,service:document.querySelector('#service').textContent,feedback:document.querySelector('#feedback').textContent,loading:document.querySelector('#loading').textContent,noteDisabled:document.querySelector('#note').disabled}));
  await page.setViewportSize({width:1280,height:900});
  await page.selectOption('#order','A200');
  await page.waitForFunction(()=>document.querySelector('#heading').textContent==='Order A200');
  await page.selectOption('#order','A100');
  await page.fill('#note','Draft typed during loading');
  results.push({stage:'draft during loading',state:await state()});
  await page.waitForFunction(()=>document.querySelector('#loading').textContent==='');
  results.push({stage:'after lookup',state:await state()});
  await page.screenshot({path:'evidence/draft-after-lookup.png'});
  let release,committed;
  const held=new Promise(r=>release=r),serverDone=new Promise(r=>committed=r);
  const responses=[];
  await page.route('http://127.0.0.1:56415/api/services',async route=>{
    const body=route.request().postDataJSON();
    const response=await route.fetch();
    responses.push({request:body,status:response.status(),body:await response.json()});
    if(body.service==='express'){committed();await held;}
    await route.fulfill({response});
  });
  await page.click('#express');
  await serverDone;
  await page.click('#standard');
  await page.waitForFunction(()=>document.querySelector('#feedback').textContent==='Delivery service saved');
  release();
  await page.waitForFunction(()=>document.querySelector('#service').textContent==='express');
  const rows=await page.evaluate(async()=> (await (await fetch('/api/orders',{headers:{'X-Test-User':'alice'}})).json()).orders);
  results.push({stage:'reordered genuine service responses',state:await state(),server:rows,responses});
  await page.screenshot({path:'evidence/service-mismatch.png'});
  await page.unroute('http://127.0.0.1:56415/api/services');
  await page.reload();
  await page.waitForFunction(()=>!document.querySelector('#save').disabled);
  results.push({stage:'service after reload',state:await state()});
  return results;
}
