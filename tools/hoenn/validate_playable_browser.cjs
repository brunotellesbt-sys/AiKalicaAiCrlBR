/* Actual bundled mGBA core: release integrity, controls, state and mobile UI. */
const { chromium } = require('/opt/codex/runtimes/cua/lib/node_modules/playwright-core');
const fs = require('fs');
const crypto = require('crypto');
const path = require('path');
const ROOT = path.resolve(__dirname, '../..');
const OUT = path.join(ROOT, 'mods/hoenn/playable-validation');
const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, 'mods/hoenn/playable/release.json')));
const url = process.env.PLAYABLE_SITE_URL || 'http://127.0.0.1:8765/';
(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/chromium', headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  try {
    fs.mkdirSync(OUT, { recursive: true });
    // A corrupt/partial deployment must fail visibly and allow retry.
    const rejected = await browser.newPage();
    await rejected.route('**/games/*.gba?*', r => r.fulfill({ status: 200, body: Buffer.alloc(192) }));
    await rejected.goto(url);
    await rejected.locator('#play').click();
    await rejected.waitForFunction(() => document.querySelector('#status').textContent.includes('incomplete'),null,{timeout:30000});
    if (await rejected.locator('#game canvas').count() || await rejected.locator('#play').isDisabled()) throw new Error('Broken download started or retry was disabled');
    await rejected.close();
    const errors=[];
    const page = await browser.newPage({ viewport: { width: 1024, height: 1000 } });
    page.on('pageerror', e => errors.push(String(e)));
    await page.goto(url);
    await page.locator('#play').click();
    await page.waitForFunction(() => document.querySelector('#status').textContent.startsWith('Game started'), null, { timeout: 120000 });
    await page.waitForTimeout(4000);
    for (let i=0;i<12;i++) { await page.keyboard.press('Enter',{delay:100}); await page.waitForTimeout(500); }
    await page.keyboard.press('x',{delay:100});
    await page.waitForTimeout(1500);
    await page.waitForFunction(() => EJS_emulator.gameManager.functions.getFrameNum()>300,null,{timeout:120000});
    const before = await page.evaluate(() => ({ file: EJS_emulator.fileName, name:EJS_gameName, frames:EJS_emulator.gameManager.functions.getFrameNum(), controls:EJS_defaultControls[0] }));
    if (before.name!==manifest.file || before.frames<300) throw new Error('Wrong ROM/save slot or core did not run');
    if (!await page.locator('#game canvas').count()) throw new Error('No game canvas');
    function coreFrame(data) {
      const bytes=Buffer.from(data);
      // mGBA's documented raw state: game code at +0x1c, video frame at +0x1fc.
      let at=bytes.indexOf(Buffer.from(manifest.game_code));
      while(at>=0) {
        const base=at-0x1c;
        if(base>=0 && base+0x200<=bytes.length && (bytes.readUInt32LE(base)>>>8)===0x010000) return bytes.readUInt32LE(base+0x1fc);
        at=bytes.indexOf(Buffer.from(manifest.game_code),at+1);
      }
      fs.writeFileSync('/tmp/playable-browser-state.bin',bytes);
      throw new Error('Could not locate the native mGBA state header');
    }
    const state = await page.evaluate(() => Array.from(EJS_emulator.gameManager.getState()));
    const savedCoreFrame=coreFrame(state);
    if (state.length<1000) throw new Error('Could not export state');
    await page.waitForTimeout(1500);
    const advanced=coreFrame(await page.evaluate(() => Array.from(EJS_emulator.gameManager.getState())));
    await page.evaluate(data => EJS_emulator.gameManager.loadState(new Uint8Array(data)),state);
    const restored=coreFrame(await page.evaluate(() => Array.from(EJS_emulator.gameManager.getState())));
    if (advanced<=savedCoreFrame || restored>=advanced || Math.abs(restored-savedCoreFrame)>30) throw new Error('Native game state did not restore: '+JSON.stringify({savedCoreFrame,advanced,restored}));
    await page.screenshot({path:path.join(OUT,'browser-desktop.png')});
    await page.setViewportSize({width:390,height:844});
    await page.waitForTimeout(700);
    const mobile=await page.evaluate(() => document.documentElement.scrollWidth<=innerWidth);
    if (!mobile) throw new Error('Mobile page overflows horizontally');
    await page.screenshot({path:path.join(OUT,'browser-mobile.png')});
    if(errors.length)throw new Error(errors.join('\n'));
    await page.close();
    // A local copy of this release should use the exact same save namespace.
    const local=await browser.newPage();
    await local.goto(url);
    await local.locator('#local-rom').setInputFiles(path.join(ROOT,'mods/hoenn/playable',manifest.file));
    await local.waitForFunction(() => document.querySelector('#status').textContent.startsWith('Game started'),null,{timeout:120000});
    const localName=await local.evaluate(() => EJS_gameName);
    if(localName!==manifest.file)throw new Error('Local release would lose access to browser save slot');
    await local.close();
    fs.writeFileSync(path.join(OUT,'browser.json'),JSON.stringify({passed:true,rom_sha256:manifest.sha256,
      emulator:'EmulatorJS 4.2.3 / mGBA',game_name:before.name,frames:before.frames,
      corrupt_download_rejected:true,retry_available:true,actual_core_boot:true,keyboard_inputs_sent:true,
      state_export_bytes:state.length,state_saved_frame:savedCoreFrame,state_restore_frame:restored,later_frame:advanced,
      same_local_release_save_namespace:true,mobile_no_horizontal_overflow:mobile,
      page_errors:errors,full_campaign_playthrough:false},null,2)+'\n');
    console.log('Playable browser ROM/core, state export/restore, download checks and mobile UI passed');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode=1; });
