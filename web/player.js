'use strict';
const status = document.querySelector('#status');
const play = document.querySelector('#play');
const fileInput = document.querySelector('#local-rom');
const dataPath = 'emulator/';
let launched = false;
let objectUrl;

async function launch(url, name) {
  if (launched) return;
  play.disabled = true;
  fileInput.disabled = true;
  status.textContent = 'Carregando o jogo e o emulador…';
  try {
    if (!url.startsWith('blob:')) {
      const response = await fetch(url);
      if (!response.ok) throw new Error('A ROM não está disponível neste site. Abra uma cópia local pelo seletor de arquivos.');
      objectUrl = URL.createObjectURL(await response.blob());
      url = objectUrl;
    }
    window.EJS_player = '#game';
    window.EJS_core = 'gba';
    window.EJS_gameUrl = url;
    // Stable name keeps IndexedDB saves separate from locally loaded ROMs.
    window.EJS_gameName = name.endsWith('.gba') ? name : name + '.gba';
    window.EJS_pathtodata = dataPath;
    window.EJS_DEBUG_XX = true; // The package ships readable source, not minified bundles.
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
    window.EJS_language = 'pt-BR';
    window.EJS_onGameStart = () => { status.textContent = 'Jogo iniciado. Exporte seu save pelo menu do emulador.'; };
    const script = document.createElement('script');
    script.src = dataPath + 'loader.js';
    script.onerror = () => { status.textContent = 'Não foi possível carregar o emulador. Recarregue a página e confira sua conexão.'; };
    document.body.appendChild(script);
    launched = true;
  } catch (error) {
    status.textContent = error.message;
    play.disabled = false;
    fileInput.disabled = false;
  }
}

play.addEventListener('click', () => launch('games/LeafGreen-Journey-SeaRoutes.gba', 'LeafGreen-Journey-SeaRoutes'));
fileInput.addEventListener('change', () => {
  const file = fileInput.files[0];
  if (!file) return;
  if (!/\.gba$/i.test(file.name) || file.size < 192 || file.size > 32 * 1024 * 1024) {
    status.textContent = 'Selecione uma ROM .gba válida, com até 32 MB.';
    fileInput.value = '';
    return;
  }
  objectUrl = URL.createObjectURL(file);
  launch(objectUrl, file.name.replace(/\.gba$/i, ''));
});
window.addEventListener('pagehide', () => { if (objectUrl) URL.revokeObjectURL(objectUrl); });
