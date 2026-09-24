async page => {
 const log=[]; const state=()=>page.evaluate(()=>Object.fromEntries(['order','heading','address','note','service','feedback','loading'].map(id=>[id,document.getElementById(id).value??document.getElementById(id).textContent])));
 const ready=()=>page.waitForFunction(()=>!document.getElementById('save').disabled);
 const calls=[]; page.on('request',r=>{if(r.url().includes('/api/'))calls.push({method:r.method(),url:r.url(),body:r.postData()})});
 await ready(); log.push({initial:await state()});
 await page.locator('#note').fill('LOCKER: 1');
 await page.locator('#save').click();
 await page.waitForFunction(()=>document.getElementById('feedback').textContent.includes('unavailable'));
 log.push({rejected:await state()});
 await page.locator('#note').fill('Assessment: ring three times');
 await page.locator('#save').click();
 await page.waitForFunction(()=>document.getElementById('feedback').textContent.includes('instruction saved'));
 await page.reload(); await ready(); log.push({persisted:await state()});
 await page.locator('#note').fill('Leave with reception'); await page.locator('#save').click(); await ready();
 await page.locator('#order').selectOption('A200'); await ready();
 await page.locator('#order').selectOption('A100');
 log.push({duringLoad:await page.evaluate(()=>({selected:document.querySelector('#order').value,heading:document.querySelector('#heading').textContent,saveDisabled:document.querySelector('#save').disabled,expressDisabled:document.querySelector('#express').disabled}))});
 await page.locator('#order').selectOption('A200'); await ready();
 await page.waitForTimeout(850); log.push({outOfOrder:await state()});
 await page.locator('#note').fill('Assessment target A200'); await page.locator('#save').click(); await ready();
 await page.reload(); await ready(); await page.locator('#order').selectOption('A200'); await ready(); log.push({targetPersisted:await state()});
 await page.locator('#note').fill('Ring twice'); await page.locator('#save').click(); await ready();
 await page.locator('#order').focus(); const focus=[];
 for(let i=0;i<4;i++){await page.keyboard.press('Tab'); focus.push(await page.evaluate(()=>({id:document.activeElement.id,outline:getComputedStyle(document.activeElement).outline}))); if(i===2){await page.keyboard.press('Enter');await page.waitForFunction(()=>document.getElementById('service').textContent==='express')} if(i===3){await page.keyboard.press('Enter');await page.waitForFunction(()=>document.getElementById('service').textContent==='standard')}}
 log.push({keyboard:focus,final:await state(),calls});
 await page.setViewportSize({width:320,height:720});
 log.push({narrow:await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,controls:[...document.querySelectorAll('select,textarea,button')].map(e=>({id:e.id,left:e.getBoundingClientRect().left,right:e.getBoundingClientRect().right}))}))});
 await page.screenshot({path:'evidence/narrow.png',fullPage:true});
 return log;
}
