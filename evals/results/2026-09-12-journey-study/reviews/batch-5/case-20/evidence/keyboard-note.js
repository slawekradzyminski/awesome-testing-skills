async page => {
  await page.keyboard.press('Tab');
  await page.keyboard.press('Tab');
  const focused=await page.evaluate(()=>document.activeElement.id);
  if(focused!=='note')throw Error('Unexpected focus '+focused);
  await page.keyboard.press('ControlOrMeta+A');
  await page.keyboard.type('Keyboard-only instruction');
  await page.keyboard.press('Tab');
  const response=page.waitForResponse(r=>r.url().endsWith('/A100/note'));
  await page.keyboard.press('Enter');
  const saved=await response;
  await page.waitForFunction(()=>document.querySelector('#feedback').textContent==='Delivery instruction saved');
  const result={focused,status:saved.status(),saved:await saved.json(),feedback:await page.locator('#feedback').textContent()};
  const restored=await page.evaluate(async()=>{
    const r=await fetch('/api/orders/A100/note',{method:'POST',headers:{'Content-Type':'application/json','X-Test-User':'alice'},body:JSON.stringify({note:'Leave with reception'})});
    return {status:r.status,body:await r.json()};
  });
  return {result,restored};
}
