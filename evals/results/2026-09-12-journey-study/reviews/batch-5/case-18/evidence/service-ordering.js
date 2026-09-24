async page => {
 const events=[];
 let releaseFirst, firstArrived;
 const gate=new Promise(r=>releaseFirst=r);
 const arrived=new Promise(r=>firstArrived=r);
 await page.route('http://127.0.0.1:58432/api/services',async route=>{
  const request=route.request().postDataJSON();
  const response=await route.fetch();
  events.push({phase:'server-response',request,status:response.status(),body:await response.json()});
  if(request.service==='express'){firstArrived();await gate;}
  await route.fulfill({response});
  events.push({phase:'delivered-to-browser',service:request.service});
 });
 await page.locator('#express').click();
 await arrived;
 await page.locator('#standard').click();
 await page.waitForFunction(()=>document.querySelector('#feedback').textContent==='Delivery service saved');
 const beforeRelease=await page.locator('#service').textContent();
 releaseFirst();
 await page.waitForFunction(()=>document.querySelector('#service').textContent==='express');
 const displayed=await page.locator('#service').textContent();
 await page.screenshot({path:'evidence/service-race-desktop.png',fullPage:true});
 await page.unroute('http://127.0.0.1:58432/api/services');
 return {order:await page.locator('#order').inputValue(),beforeRelease,displayed,events};
}
