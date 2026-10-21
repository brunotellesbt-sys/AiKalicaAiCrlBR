/* Boot each actual release in bundled mGBA and verify edition/save identity. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const ROOT = path.resolve(__dirname, '../..');
const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, 'mods/hoenn/versions/versions.json')));
const releases = [...manifest.variants];
const includesTestEdition = ['extra-gyms','dewford-coast-safety','sevii-integrated-piers'].includes(manifest.validation_scope);
if (includesTestEdition) releases.push(JSON.parse(fs.readFileSync(path.join(ROOT,'roms/rom-de-teste/review.json'))));
const OUT = process.env.BROWSER_VALIDATION_OUTPUT || path.join(ROOT, 'mods/hoenn/versions-validation/browser');
const url = process.env.PLAYABLE_SITE_URL || 'http://127.0.0.1:8770/';
(async () => {
  const browser = await chromium.launch({executablePath:process.env.CHROMIUM_PATH || (fs.existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined),headless:true,
    args:['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  fs.mkdirSync(OUT,{recursive:true});
  try {
    const assets = await browser.newContext();
    const playerSources = {};
    try {
      for (const name of ['index.html','player.js','style.css']) {
        const response = await assets.request.get(new URL(name,url).href);
        if (!response.ok()) throw new Error('Published player asset unavailable: '+name);
        const hash = crypto.createHash('sha256').update(await response.body()).digest('hex');
        const expected = crypto.createHash('sha256').update(fs.readFileSync(path.join(ROOT,'web',name))).digest('hex');
        if (hash !== expected) throw new Error('Published player asset is stale: '+name);
        playerSources[name] = hash;
      }
    } finally { await assets.close(); }
    const invalid = await browser.newPage();
    await invalid.route('**/games/versions.json',route=>route.fulfill({contentType:'application/json',body:JSON.stringify({...manifest,validated:false})}));
    await invalid.goto(url);await invalid.locator('#play').click();
    await invalid.waitForFunction(()=>document.querySelector('#status').textContent.includes('unavailable'));
    if(await invalid.evaluate(()=>!!window.EJS_emulator))throw new Error('Unvalidated manifest booted');
    if(await invalid.locator('#play').isDisabled())throw new Error('Manifest rejection prevented retry');
    await invalid.close();
    if (includesTestEdition) {
      const stale = await browser.newPage();
      await stale.route('**/games/review.json', route=>route.fulfill({contentType:'application/json',body:JSON.stringify({...releases.at(-1),base_normal_sha256:'0'.repeat(64)})}));
      await stale.goto(url);await stale.locator('#play').click();
      await stale.waitForFunction(()=>document.querySelector('#status').textContent.includes('does not match'));
      if(await stale.evaluate(()=>!!window.EJS_emulator))throw new Error('Stale test edition booted');
      await stale.close();
    }
    const incomplete = await browser.newPage();
    await incomplete.route('**/games/*.gba?*',route=>route.fulfill({body:Buffer.alloc(192)}));
    await incomplete.goto(url);await incomplete.locator('#play').click();
    await incomplete.waitForFunction(()=>document.querySelector('#status').textContent.includes('incomplete'));
    if(await incomplete.evaluate(()=>!!window.EJS_emulator))throw new Error('Corrupt ROM booted');
    await incomplete.close();
    const checks=[];
    for(const row of releases){
      const page=await browser.newPage({viewport:{width:row.max_national===493?1280:390,height:844}});
      await page.goto(url);
      await page.locator('#edition-label').waitFor({state:'visible'});
      await page.locator('#edition').selectOption(row.file);
      if(!((await page.locator('#download-rom').getAttribute('href')).endsWith(row.file)))throw new Error('Wrong edition download');
      // Hash the real server response and pass those same bytes to the player.
      // A 32 MiB ROM exceeds Chromium's response-inspection cache.
      let bytes;
      await page.route('**/games/' + row.file + '?*', async route => {
        const response = await route.fetch();
        bytes = await response.body();
        await route.fulfill({response, body:bytes});
      });
      const downloaded = page.waitForResponse(response => new URL(response.url()).pathname.endsWith('/games/' + row.file) && response.ok());
      await page.locator('#play').click();
      await downloaded;
      const observedHash = crypto.createHash('sha256').update(bytes).digest('hex');
      if (bytes.length !== row.bytes || observedHash !== row.sha256) throw new Error('Served ROM does not match the current edition');
      await page.waitForFunction(()=>window.EJS_emulator?.gameManager?.functions?.getFrameNum()>360,null,{timeout:120000});
      const actual=await page.evaluate(()=>({name:EJS_gameName,frames:EJS_emulator.gameManager.functions.getFrameNum(),
        state:EJS_emulator.gameManager.getState().length,controls:EJS_defaultControls[0]}));
      if(actual.name!==row.file||actual.state<1000)throw new Error('Wrong edition/save identity or native state unavailable');
      if(!await page.locator('#game canvas').count())throw new Error('Missing native renderer');
      if(!await page.locator('#edition').isDisabled())throw new Error('Edition changed during running game');
      await page.screenshot({path:path.join(OUT,row.file+'.png'),fullPage:true});
      checks.push({file:row.file,rom_sha256:observedHash,downloaded_bytes:bytes.length,actual_game_name:actual.name,native_frames:actual.frames,
        exported_native_state_bytes:actual.state,distinct_save_identity:true});
      console.log('Bundled mGBA boot passed:',row.file);
      await page.close();
    }
    if(new Set(checks.map(c=>c.actual_game_name)).size!==releases.length)throw new Error('Save identities collide');
    fs.writeFileSync(path.join(OUT,'browser-versions.json'),JSON.stringify({passed:true,checks,
      invalid_manifest_rejected:true,incomplete_rom_rejected:true,bundled_mgba:true,
      stale_test_edition_rejected:includesTestEdition,
      player_sources_sha256:playerSources,
      desktop_and_mobile_viewports:true,full_campaign_playthrough:false},null,2)+'\n');
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exit(1);});
