async page => {
  const out = [];
  const state = () => page.evaluate(() => ({selected: document.querySelector('#order').value, heading: document.querySelector('#heading').textContent, note: document.querySelector('#note').value, service: document.querySelector('#service').textContent, feedback: document.querySelector('#feedback').textContent}));
  await page.locator('#save').waitFor({state:'visible'});
  await page.locator('#order').selectOption('A200');
  await page.waitForFunction(() => document.querySelector('#heading').textContent === 'Order A200');
  await page.locator('#order').selectOption('A100');
  await page.locator('#order').selectOption('A200');
  await page.waitForTimeout(900);
  out.push({test:'out-of-order reads', state:await state()});
  await page.screenshot({path:'evidence/race.png'});
  const saved = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith('/note'));
  await page.locator('#save').click();
  const response = await saved;
  out.push({test:'save mismatched details',url:response.url(),status:response.status(),body:await response.json(),state:await state()});
  await page.locator('#note').fill('LOCKER: 1');
  const rejected = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith('/note'));
  await page.locator('#save').click();
  const failure = await rejected;
  await page.waitForTimeout(100);
  out.push({test:'rejected note',status:failure.status(),body:await failure.json(),state:await state()});
  await page.screenshot({path:'evidence/rejected-note.png'});
  await page.locator('#order').focus();
  const focus=[];
  for(let i=0;i<5;i++){await page.keyboard.press('Tab');focus.push(await page.evaluate(() => ({id:document.activeElement.id,tag:document.activeElement.tagName,outline:getComputedStyle(document.activeElement).outline})));}
  out.push({test:'keyboard tab order',focus});
  return out;
}
