async page => {
 const result=[];
 await page.keyboard.press('Tab');
 result.push({step:'first tab',focus:await page.evaluate(()=>document.activeElement.id)});
 await page.keyboard.press('Tab');
 result.push({step:'second tab',focus:await page.evaluate(()=>document.activeElement.id)});
 await page.keyboard.press('ControlOrMeta+A');
 await page.keyboard.type('Keyboard delivery instruction');
 await page.keyboard.press('Tab');
 result.push({step:'save focus',focus:await page.evaluate(()=>({id:document.activeElement.id,outline:getComputedStyle(document.activeElement).outline}))});
 await page.keyboard.press('Enter');
 await page.waitForFunction(()=>document.querySelector('#feedback').textContent==='Delivery instruction saved');
 result.push({step:'keyboard saved',state:await page.evaluate(async()=>await(await fetch('/api/orders/A200',{headers:{'X-Test-User':'alice'}})).json())});
 await page.click('#express');
 await page.waitForFunction(()=>document.querySelector('#service').textContent==='express');
 await page.reload();
 await page.selectOption('#order','A200');
 await page.waitForFunction(()=>!document.querySelector('#save').disabled);
 result.push({step:'reload persistence',note:await page.locator('#note').inputValue(),service:await page.locator('#service').textContent()});
 await page.fill('#note','Ring twice'); await page.click('#save');
 await page.waitForFunction(()=>!document.querySelector('#save').disabled);
 await page.click('#standard');
 await page.waitForFunction(()=>document.querySelector('#service').textContent==='standard');
 return result;
}
