async page => {
 await page.reload();
 await page.waitForFunction(()=>!document.querySelector('#save').disabled);
 const focus=[];
 for(let i=0;i<4;i++) {await page.keyboard.press('Tab');focus.push(await page.evaluate(()=>({id:document.activeElement.id,outline:getComputedStyle(document.activeElement).outline})));}
 await page.keyboard.press('Enter');
 await page.waitForFunction(()=>document.querySelector('#service').textContent==='express');
 await page.screenshot({path:'evidence/keyboard-express.png',fullPage:true});
 await page.keyboard.press('Tab');
 focus.push(await page.evaluate(()=>({id:document.activeElement.id,outline:getComputedStyle(document.activeElement).outline})));
 await page.keyboard.press('Space');
 await page.waitForFunction(()=>document.querySelector('#service').textContent==='standard');
 await page.setViewportSize({width:375,height:812});
 await page.screenshot({path:'evidence/narrow.png',fullPage:true});
 return {focus,service:await page.locator('#service').textContent(),layout:await page.evaluate(()=>({viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth}))};
}
