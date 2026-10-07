const { chromium } = require('/opt/codex/runtimes/cua/lib/node_modules/playwright-core');
const fs = require('fs');
const crypto = require('crypto');
(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/chromium', headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  try {
    const page = await browser.newPage({ viewport: { width: 1024, height: 900 }, ignoreHTTPSErrors: true });
    const errors = [];
    page.on('pageerror', e => { errors.push(String(e)); console.log('Page error:', String(e)); });
    page.on('console', m => { if (m.type() === 'error') console.log('Browser console:', m.text()); });
    page.on('requestfailed', r => console.log('Request failed:', r.url(), r.failure()?.errorText));
    await page.goto('http://127.0.0.1:8765/');
    await page.locator('#play').click();
    await page.waitForFunction(() => document.querySelector('#status').textContent.startsWith('Jogo iniciado'), null, { timeout: 120000 });
    await page.waitForTimeout(4000);
    for (let i = 0; i < 12; i++) {
      await page.keyboard.press('Enter', { delay: 100 });
      await page.waitForTimeout(700);
    }
    await page.keyboard.press('x', { delay: 100 });
    await page.waitForTimeout(2000);
    const state = await page.evaluate(() => ({ file: EJS_emulator.fileName,
      frames: EJS_emulator.gameManager.functions.getFrameNum() }));
    console.log('Core state:', state);
    if (state.frames < 300) throw new Error('Core did not advance enough frames');
    if (errors.length) throw new Error(errors.join('\n'));
    if (!await page.locator('#game canvas').count()) throw new Error('No emulator canvas');
    fs.mkdirSync('mods/sea-routes/validation', { recursive: true });
    await page.screenshot({ path: 'mods/sea-routes/validation/browser-game.png' });
    fs.writeFileSync('mods/sea-routes/validation/browser.json', JSON.stringify({ passed: true,
      emulator: '@emulatorjs/emulatorjs@4.2.3', core: '@emulatorjs/core-mgba@4.2.3',
      rom_sha256: crypto.createHash('sha256').update(fs.readFileSync('mods/sea-routes/LeafGreen-Journey-SeaRoutes.gba')).digest('hex'),
      frames: state.frames, check: 'Real ROM boots in browser with game canvas and keyboard input', page_errors: errors }, null, 2) + '\n');
    console.log('Browser ROM boot passed');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
