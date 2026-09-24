async page => {
  const E = '/private/tmp/awesome-skills-ui-evidence-smoke-20260924/candidate/evidence/';
  const log = []; let seq = 0;
  page.on('response', async r => { const u = r.url(); if (!u.includes('/api/')) return;
    let b=''; try { b = (await r.text()).slice(0,300);} catch(e){}
    log.push({seq: ++seq, t: Date.now(), method: r.request().method(), url: u.replace('http://127.0.0.1:51117',''), req: r.request().postData(), status: r.status(), body: b}); });
  const out = {};
  await page.setViewportSize({width: 1280, height: 800});
  await page.goto('http://127.0.0.1:51117/');
  await page.waitForFunction(() => !document.getElementById('save').disabled);
  out.initial = {h: await page.textContent('#heading'), note: await page.inputValue('#note'), svc: await page.textContent('#service')};
  await page.screenshot({path: E+'C01-initial-A100-desktop.png'});
  // C02 valid save + reload
  out.origNoteA100 = out.initial.note;
  await page.fill('#note', 'Ring twice QA'); await page.click('#save');
  await page.waitForFunction(() => document.getElementById('feedback').textContent);
  out.saveFb = await page.textContent('#feedback');
  await page.reload(); await page.waitForFunction(() => !document.getElementById('save').disabled);
  out.afterReload = await page.inputValue('#note');
  // C03 LOCKER rejected
  await page.fill('#note', 'LOCKER: 12'); await page.click('#save');
  await page.waitForFunction(() => document.getElementById('feedback').textContent);
  out.lockerFb = await page.textContent('#feedback'); out.lockerDraft = await page.inputValue('#note');
  await page.screenshot({path: E+'C03-locker-rejected.png'});
  await page.reload(); await page.waitForFunction(() => !document.getElementById('save').disabled);
  out.afterLockerReload = await page.inputValue('#note');
  // C04 race: from A200 switch to A100 (slow) then quickly back to A200
  await page.selectOption('#order','A200'); await page.waitForFunction(() => !document.getElementById('save').disabled);
  out.origNoteA200 = await page.inputValue('#note'); out.origSvcA200 = await page.textContent('#service');
  await page.selectOption('#order','A100'); await page.waitForTimeout(100); await page.selectOption('#order','A200');
  await page.waitForTimeout(1200);
  out.race = {sel: await page.inputValue('#order'), h: await page.textContent('#heading'), note: await page.inputValue('#note'), svc: await page.textContent('#service'), addr: await page.textContent('#address')};
  await page.screenshot({path: E+'C04-race-after-A100-then-A200.png'});
  // C05 service express on A200 via keyboard
  await page.focus('#order');
  const tabs = [];
  for (let i=0;i<6;i++){ await page.keyboard.press('Tab'); tabs.push(await page.evaluate(()=>{const a=document.activeElement; return a.id+':'+getComputedStyle(a).outlineStyle+' '+getComputedStyle(a).outlineColor;})); }
  out.tabs = tabs;
  await page.focus('#express'); await page.screenshot({path: E+'C06-keyboard-focus-express.png'});
  await page.keyboard.press('Enter'); await page.waitForTimeout(400);
  out.svcFb = await page.textContent('#feedback'); out.svcShown = await page.textContent('#service');
  await page.reload(); await page.selectOption('#order','A200'); await page.waitForFunction(() => !document.getElementById('save').disabled);
  out.svcAfterReload = await page.textContent('#service');
  // keyboard save instruction on A200
  await page.focus('#note'); await page.keyboard.press('Control+A'); await page.keyboard.type('Leave at door QA');
  await page.keyboard.press('Tab'); out.focusAfterNote = await page.evaluate(()=>document.activeElement.id);
  await page.keyboard.press('Space'); await page.waitForTimeout(400); out.kbSaveFb = await page.textContent('#feedback');
  // narrow
  await page.setViewportSize({width: 360, height: 780}); await page.screenshot({path: E+'C07-narrow-360.png', fullPage: true});
  out.hOverflow = await page.evaluate(()=>document.documentElement.scrollWidth > innerWidth);
  // restore
  await page.setViewportSize({width: 1280, height: 800});
  out.log = log;
  return JSON.stringify(out, null, 1);
}
