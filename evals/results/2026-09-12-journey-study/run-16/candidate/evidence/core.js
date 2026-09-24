async page => {
 page.removeAllListeners('response');
 const logs=[];
 page.on('response', async r=> {if(r.url().includes('/api/')) logs.push({method:r.request().method(),path:r.url().replace('http://127.0.0.1:58432',''),status:r.status(),request:r.request().postData(),body:await r.text()});});
 await page.getByRole('textbox',{name:'Delivery instruction'}).fill('Journey 16: reception after 5');
 await page.getByRole('button',{name:'Save instruction'}).click();
 await page.waitForFunction(()=>document.querySelector('#feedback').textContent==='Delivery instruction saved');
 await page.reload();
 await page.waitForFunction(()=>!document.querySelector('#save').disabled);
 const persisted=await page.locator('#note').inputValue();
 await page.locator('#note').fill('LOCKER: 16');
 await page.locator('#save').click();
 await page.waitForFunction(()=>document.querySelector('#feedback').textContent.includes('Locker'));
 const rejected={draft:await page.locator('#note').inputValue(),feedback:await page.locator('#feedback').textContent()};
 await page.screenshot({path:'evidence/rejected-desktop.png'});
 await page.locator('#note').fill('Leave with reception');
 await page.locator('#save').click();
 await page.waitForFunction(()=>!document.querySelector('#save').disabled);
 await page.locator('#order').selectOption('A200');
 await page.waitForFunction(()=>document.querySelector('#heading').textContent==='Order A200');
 await page.locator('#order').selectOption('A100');
 await page.locator('#order').selectOption('A200');
 await page.waitForLoadState('networkidle');
 const race=await page.evaluate(()=>({selected:document.querySelector('#order').value,heading:document.querySelector('#heading').textContent,note:document.querySelector('#note').value}));
 return {persisted,rejected,race,logs,environment:await page.evaluate(()=>({ua:navigator.userAgent,width:innerWidth,height:innerHeight,devicePixelRatio}))};
}
