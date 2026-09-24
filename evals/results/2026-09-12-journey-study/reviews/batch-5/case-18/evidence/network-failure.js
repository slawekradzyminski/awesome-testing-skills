async page => {
 const failures=[];
 page.on('requestfailed',r=>failures.push({method:r.method(),url:r.url(),failure:r.failure()}));
 await page.route('http://127.0.0.1:58432/api/orders/A100/note',route=>route.abort('connectionreset'));
 await page.locator('#note').fill('Journey 16 network retry draft');
 await page.locator('#save').click();
 await page.waitForEvent('requestfailed').catch(()=>{});
 await page.unroute('http://127.0.0.1:58432/api/orders/A100/note');
 const read=await page.request.get('http://127.0.0.1:58432/api/orders/A100',{headers:{'X-Test-User':'alice'}});
 const state=await page.evaluate(()=>({draft:document.querySelector('#note').value,disabled:document.querySelector('#save').disabled,feedback:document.querySelector('#feedback').textContent}));
 await page.screenshot({path:'evidence/failed-save.png',fullPage:true});
 return {state,persisted:await read.json(),failures};
}
