const { chromium } = require(process.env.PLAYWRIGHT_MODULE_PATH || '/opt/codex/runtimes/cua/lib/node_modules/playwright-core');
const fs = require('fs');
const crypto = require('crypto');
const assert = require('assert/strict');
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1200 }, deviceScaleFactor: 1 });
    const errors = [];
    page.on('pageerror', e => errors.push(String(e)));
    await page.goto('http://127.0.0.1:8765/world-map.html');
    await page.waitForFunction(() => document.querySelectorAll('.point').length === 36);
    await page.waitForFunction(() => [...document.querySelectorAll('#atlas image')].every(image => {
      const img = new Image(); img.src = image.getAttribute('href'); return img.complete;
    }));
    assert.equal(await page.locator('#place').inputValue(), 'MAPSEC_VERMILION_CITY');
    await page.selectOption('#place', 'MAPSEC_SLATEPORT_CITY');
    assert.match(await page.locator('#place-status').textContent(), /ainda não jogável/);
    assert.match(await page.locator('#connections').textContent(), /Surf.*ainda não implementado/);
    assert.match(await page.locator('#connections').textContent(), /Barco com ticket.*ainda não implementado/);
    await page.locator('#show-planned').uncheck();
    assert.equal(await page.locator('#place').inputValue(), 'MAPSEC_VERMILION_CITY');
    assert.equal(await page.locator('#planned-region').isVisible(), false);
    await page.locator('#show-planned').check();
    await page.locator('#show-routes').uncheck();
    assert.equal(await page.locator('.route').first().isVisible(), false);
    await page.locator('#show-routes').check();
    await page.locator('[data-id="MAPSEC_ONE_ISLAND"]').click();
    assert.match(await page.locator('#connections').textContent(), /Vermilion City — jogável/);
    await page.locator('[data-id="MAPSEC_ONE_ISLAND"]').focus();
    await page.keyboard.press('ArrowRight');
    assert.equal(await page.locator('#place').inputValue(), 'MAPSEC_TWO_ISLAND');
    await page.locator('#reset').click();
    assert.deepEqual(errors, []);
    fs.mkdirSync('mods/hoenn/validation', { recursive: true });
    await page.locator('#atlas-board').screenshot({ path: 'mods/hoenn/validation/world-atlas.png' });
    // Mobile: controls remain usable and the page never overflows horizontally.
    await page.setViewportSize({ width: 390, height: 844 });
    await page.selectOption('#place', 'MAPSEC_BIRTH_ISLAND_FRLG');
    assert.match(await page.locator('#place-status').textContent(), /Porto conectado/);
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.screenshot({ path: 'mods/hoenn/validation/world-atlas-mobile.png', fullPage: true });
    const report = { passed: true, browser: await browser.version(), places: 36, panels: 5,
      data_sha256: crypto.createHash('sha256').update(fs.readFileSync('web/world-map.json')).digest('hex'),
      checks: ['native map panels render', 'pending Hoenn and ferry labeled', 'planned layer toggle',
        'Surf link toggle', 'port selection', 'keyboard navigation', 'mobile selection and layout'], page_errors: errors };
    fs.writeFileSync('mods/hoenn/validation/atlas-browser.json', JSON.stringify(report, null, 2) + '\n');
    console.log('Atlas browser checks passed');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
