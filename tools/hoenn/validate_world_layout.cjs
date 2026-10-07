const { chromium } = require(process.env.PLAYWRIGHT_MODULE_PATH || '/opt/codex/runtimes/cua/lib/node_modules/playwright-core');
const fs = require('fs');
const crypto = require('crypto');
const assert = require('assert/strict');
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1600 }, deviceScaleFactor: 1 });
    const errors = [];
    page.on('pageerror', e => errors.push(String(e)));
    await page.goto('http://127.0.0.1:8765/world-layout.html');
    await page.waitForFunction(() => document.querySelector('#world-layout').contentDocument?.querySelectorAll('image').length === 5);
    await page.waitForFunction(() => [...document.querySelector('#world-layout').contentDocument.querySelectorAll('image')].every(image => {
      const img = new Image(); img.src = image.getAttribute('href'); return img.complete;
    }));
    const data = JSON.parse(fs.readFileSync('web/world-layout.json'));
    assert.equal(data.width, data.height);
    assert.equal(data.cinnabar_south_endpoint, 'MAPSEC_ROUTE_114');
    assert.equal(data.full_story_validated, false);
    const placements = data.placements;
    assert(placements.hoenn[1] > placements.kanto[1] + placements.kanto[3]);
    assert(placements.sevii_123[0] > placements.kanto[0] + placements.kanto[2]);
    assert(placements.sevii_45[1] > placements.sevii_123[1]);
    assert(placements.sevii_67[1] > placements.sevii_45[1]);
    assert(data.surf_links.some(l => l.source === 'MAPSEC_ROUTE_131' && l.target === 'MAPSEC_SIX_ISLAND'));
    assert(data.surf_links.some(l => l.source === 'MAPSEC_ROUTE_125' && l.target === 'JOURNEY_VERMILION_SEA'));
    assert(data.surf_links.some(l => l.source === 'MAPSEC_ROUTE_127' && l.target === 'MAPSEC_FOUR_ISLAND'));
    assert(data.surf_links.some(l => l.source === 'MAPSEC_ROUTE_129' && l.target === 'MAPSEC_SIX_ISLAND'));
    assert(data.surf_links.some(l => l.source === 'MAPSEC_ROUTE_19' && l.target === 'JOURNEY_VERMILION_SEA'));
    assert.equal(await page.locator('#world-layout').evaluate(el => el.contentDocument.querySelectorAll('circle').length), data.points.length);
    assert.deepEqual(errors, []);
    fs.mkdirSync('mods/hoenn/validation', { recursive: true });
    await page.locator('#world-board').screenshot({ path: 'mods/hoenn/validation/connected-world.png' });
    await page.setViewportSize({ width: 390, height: 844 });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    const report = { passed: true, browser: await browser.version(), points: data.points.length,
      data_sha256: crypto.createHash('sha256').update(fs.readFileSync('web/world-layout.json')).digest('hex'),
      checks: ['five native land charts load', 'square projection', 'Kanto north of Hoenn',
        'Sevii in three eastern rows', 'Route131 to Six Island', 'Route114 southern crossing', 'mobile no overflow',
        'Route125/127/129 and Fuchsia ocean entrances'],
      page_errors: errors };
    fs.writeFileSync('mods/hoenn/validation/connected-world-browser.json', JSON.stringify(report, null, 2) + '\n');
    console.log('Connected-world browser checks passed');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
