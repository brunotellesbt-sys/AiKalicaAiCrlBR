'use strict';
const status = document.querySelector('#status');
const play = document.querySelector('#play');
const fileInput = document.querySelector('#local-rom');
const dataPath = 'emulator/';
let launched = false;
let launching = false;
let objectUrl;
const edition = document.querySelector('#edition');
let editions;
let editionError;
const editionsReady = fetch('games/versions.json', {cache: 'no-store'}).then(async response => {
  if (response.status === 404) return;
  if (!response.ok) throw new Error('The edition list could not load. Please retry.');
  const info = await response.json();
  if (info.validated !== true || !Array.isArray(info.variants) || info.variants.length !== 4) {
    throw new Error('The four editions are unavailable.');
  }
  for (const row of info.variants) validateRelease(row);
  const names = new Set(info.variants.map(row => row.file));
  if (names.size !== 4 || [...edition.options].filter(option => !option.disabled).some(option => !names.has(option.value))) {
    throw new Error('The edition list is invalid.');
  }
  editions = [...info.variants];
  if (['extra-gyms','dewford-coast-safety','badge-story','coastal-closures','sevii-integrated-piers'].includes(info.validation_scope)) {
    const response = await fetch('games/review.json', {cache: 'no-store'});
    if (!response.ok) throw new Error('The test edition could not load. Please retry.');
    const review = validateRelease(await response.json());
    const normal = editions.find(row => row.file === review.base_normal_file);
    if (review.file !== 'Pokemon-Journey-TESTE.gba' || !normal ||
        review.base_normal_sha256 !== normal.sha256 || review.automatic_trainer_approaches !== false ||
        review.random_wild_encounters !== false || review.separate_save_identity !== true) {
      throw new Error('The test edition does not match the current game.');
    }
    editions.push(review);
    const option = edition.querySelector('[value="Pokemon-Journey-TESTE.gba"]');
    option.disabled = false;
    option.hidden = false;
  }
  document.querySelector('#edition-label').hidden = false;
  document.querySelector('#edition-description').hidden = false;
  updateDownload();
}).catch(error => { editionError = error; status.textContent = error.message; });

function validateRelease(info) {
  if (!/^Pokemon-Journey-[A-Za-z0-9-]+\.gba$/.test(info.file) ||
      !/^[a-f0-9]{64}$/.test(info.sha256) || !Number.isInteger(info.bytes) ||
      info.bytes < 192 || info.bytes > 32 * 1024 * 1024) {
    throw new Error('The release information is invalid.');
  }
  return info;
}
function updateDownload() {
  const anchor = document.querySelector('#download-rom');
  if (editions) anchor.href = 'games/' + edition.value;
}
edition.addEventListener('change', updateDownload);

async function sha256(bytes) {
  return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)),
    byte => byte.toString(16).padStart(2, '0')).join('');
}

async function release() {
  await editionsReady;
  if (editionError) throw editionError;
  if (editions) return editions.find(row => row.file === edition.value);
  const response = await fetch('games/release.json', { cache: 'no-store' });
  if (!response.ok) throw new Error('The release is unavailable. You can open a downloaded .gba file instead.');
  const info = await response.json();
  return validateRelease(info);
}

async function launch(localFile) {
  if (launched || launching) return;
  launching = true;
  play.disabled = true;
  fileInput.disabled = true;
  edition.disabled = true;
  status.textContent = 'Loading and checking the game…';
  try {
    let bytes;
    let name;
    let expected;
    if (localFile) {
      if (!/\.gba$/i.test(localFile.name) || localFile.size < 192 || localFile.size > 32 * 1024 * 1024) {
        throw new Error('Choose a .gba ROM, up to 32 MiB.');
      }
      bytes = await localFile.arrayBuffer();
      const hash = await sha256(bytes);
      // A matching downloaded release uses the same save slot as Play.
      try { expected = await release(); } catch (_) { expected = null; }
      const matching = editions?.find(row => row.sha256 === hash) || (expected && hash === expected.sha256 ? expected : null);
      name = matching ? matching.file : 'Local-' + hash + '.gba';
      if (matching && editions) { edition.value = matching.file; updateDownload(); }
    } else {
      expected = await release();
      const response = await fetch('games/' + expected.file + '?sha256=' + expected.sha256);
      if (!response.ok) throw new Error('The game download failed. Please try again.');
      bytes = await response.arrayBuffer();
      if (bytes.byteLength !== expected.bytes || await sha256(bytes) !== expected.sha256) {
        throw new Error('The game download is incomplete or belongs to a different release. Please retry.');
      }
      name = expected.file;
    }
    objectUrl = URL.createObjectURL(new Blob([bytes], { type: 'application/octet-stream' }));
    window.EJS_player = '#game';
    window.EJS_core = 'gba';
    window.EJS_gameUrl = objectUrl;
    window.EJS_gameName = name;
    window.EJS_pathtodata = dataPath;
    window.EJS_DEBUG_XX = true;
    window.EJS_startOnLoaded = true;
    window.EJS_defaultControls = { 0: {
      0: { value: 'z', value2: 'BUTTON_2' },
      8: { value: 'x', value2: 'BUTTON_1' },
      2: { value: 'shift', value2: 'SELECT' },
      3: { value: 'enter', value2: 'START' },
      4: { value: 'up arrow', value2: 'DPAD_UP' },
      5: { value: 'down arrow', value2: 'DPAD_DOWN' },
      6: { value: 'left arrow', value2: 'DPAD_LEFT' },
      7: { value: 'right arrow', value2: 'DPAD_RIGHT' },
      10: { value: 'a', value2: 'LEFT_TOP_SHOULDER' },
      11: { value: 's', value2: 'RIGHT_TOP_SHOULDER' }
    }, 1: {}, 2: {}, 3: {} };
    window.EJS_language = 'en-US';
    window.EJS_onGameStart = () => { status.textContent = 'Game started. Save in the game and export your save from the emulator menu.'; };
    await new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = dataPath + 'loader.js';
      script.onload = resolve;
      script.onerror = () => { script.remove(); reject(new Error('The emulator could not load. Please retry.')); };
      document.body.appendChild(script);
    });
    launched = true;
  } catch (error) {
    status.textContent = error.message;
    if (objectUrl) { URL.revokeObjectURL(objectUrl); objectUrl = undefined; }
    play.disabled = false;
    fileInput.disabled = false;
    edition.disabled = false;
    fileInput.value = '';
  } finally {
    launching = false;
  }
}

play.addEventListener('click', () => launch());
fileInput.addEventListener('change', () => {
  const file = fileInput.files[0];
  if (file) launch(file);
});
window.addEventListener('pagehide', () => { if (objectUrl) URL.revokeObjectURL(objectUrl); });
