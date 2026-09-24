async page => {
  const results=[];
  const state=()=>page.evaluate(()=>({order:document.querySelector('#order').value,heading:document.querySelector('#heading').textContent,note:document.querySelector('#note').value,service:document.querySelector('#service').textContent,feedback:document.querySelector('#feedback').textContent,loading:document.querySelector('#loading').textContent,noteDisabled:document.querySelector('#note').disabled}));
  await page.setViewportSize({width:1280,height:900});
  await page.selectOption('#order','A200');
  await page.waitForFunction(()=>document.querySelector('#heading').textContent==='Order A200');
  await page.selectOption('#order','A100');
  await page.fill('#note','Draft typed during loading');
  results.push({stage:'draft during loading',state:await state()});
  await page.waitForFunction(()=>document.querySelector('#loading').textContent==='');
  results.push({stage:'after lookup',state:await state()});
  await page.screenshot({path:'evidence/draft-after-lookup.png'});
  return results;
}