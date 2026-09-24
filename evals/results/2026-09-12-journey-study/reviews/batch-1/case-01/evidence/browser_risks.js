async page => {
 const log=[]; const ready=()=>page.waitForFunction(()=>!document.querySelector('#save').disabled);
 const state=()=>page.evaluate(()=>({order:document.querySelector('#order').value,heading:document.querySelector('#heading').textContent,note:document.querySelector('#note').value,service:document.querySelector('#service').textContent,feedback:document.querySelector('#feedback').textContent,loading:document.querySelector('#loading').textContent,saveDisabled:document.querySelector('#save').disabled}));
 await page.setViewportSize({width:1280,height:900});
 // Hold a real express response after the server commits it; let standard complete first.
 let release; const gate=new Promise(r=>release=r); let firstCommitted; const committed=new Promise(r=>firstCommitted=r);
 await page.route('**/api/services',async route=>{
   const response=await route.fetch();
   if(route.request().postDataJSON().service==='express'){firstCommitted(); await gate;}
   await route.fulfill({response});
 });
 await page.locator('#express').click(); await committed;
 await page.locator('#standard').click();
 await page.waitForFunction(()=>document.querySelector('#service').textContent==='standard');
 await page.waitForTimeout(100); release();
 await page.waitForFunction(()=>document.querySelector('#service').textContent==='express');
 log.push({serviceRaceBeforeReload:await state()});
 await page.screenshot({path:'evidence/service-race.png'});
 await page.unroute('**/api/services');
 await page.reload(); await ready(); await page.locator('#order').selectOption('A200'); await ready();
 log.push({serviceRaceAfterReload:await state()});
 // Input remains editable during intentional A100 lookup.
 await page.locator('#order').selectOption('A100');
 await page.locator('#note').fill('New draft entered while loading');
 log.push({draftDuringLookup:await state()});
 await ready(); log.push({draftAfterLookup:await state()});
 // Abort one save to reproduce transient connection loss, not a fabricated API response.
 const errors=[]; page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/api/orders/A100/note',route=>route.abort('failed'),{times:1});
 await page.locator('#note').fill('Draft survives interrupted request');
 await page.locator('#save').click();
 await page.waitForTimeout(150);
 log.push({failedSave:await state(),errors});
 await page.screenshot({path:'evidence/network-failure.png'});
 await page.unroute('**/api/orders/A100/note');
 await page.reload(); await ready(); log.push({recoveredByReload:await state()});
 return log;
}
