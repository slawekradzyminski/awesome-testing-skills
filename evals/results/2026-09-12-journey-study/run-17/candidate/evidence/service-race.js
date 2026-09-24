async page => {
  await page.unroute('http://127.0.0.1:58576/api/services');
  await page.reload(); await page.waitForFunction(()=>!document.querySelector('#save').disabled);
  await page.setViewportSize({width:1280,height:900});
  const events=[];
  await page.route('http://127.0.0.1:58576/api/services',async route=>{
    const service=route.request().postDataJSON().service;
    events.push({event:'request',service,at:Date.now()});
    const response=await route.fetch();
    events.push({event:'server_response',service,status:response.status(),body:await response.json(),at:Date.now()});
    if(service==='express')await page.waitForTimeout(900);
    await route.fulfill({response});
    events.push({event:'browser_response',service,at:Date.now()});
  });
  await page.locator('#express').click();
  await page.waitForTimeout(100);
  await page.locator('#standard').click();
  await page.waitForTimeout(1100);
  const beforeReload={selected:await page.locator('#order').inputValue(),heading:await page.locator('#heading').textContent(),service:await page.locator('#service').textContent(),feedback:await page.locator('#feedback').textContent()};
  await page.screenshot({path:'evidence/service-race-before-reload.png'});
  await page.unroute('http://127.0.0.1:58576/api/services');
  await page.reload(); await page.waitForFunction(()=>!document.querySelector('#save').disabled);
  const afterReload={service:await page.locator('#service').textContent(),selected:await page.locator('#order').inputValue()};
  return {method:'Forwarded real local server responses; delayed only express response delivery by 900ms; no fabricated response bodies.',events,beforeReload,afterReload};
}
