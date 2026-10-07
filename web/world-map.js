'use strict';
const NS = 'http://www.w3.org/2000/svg';
const atlas = document.querySelector('#atlas');
const places = document.querySelector('#place');
const showRoutes = document.querySelector('#show-routes');
const showPlanned = document.querySelector('#show-planned');
let data, selected, points, routeLayer, plannedLayer, cursorLayer;

function element(name, attrs = {}, text) {
  const node = document.createElementNS(NS, name);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  if (text !== undefined) node.textContent = text;
  return node;
}

function select(id) {
  selected = points.get(id);
  places.value = id;
  document.querySelector('#place-name').textContent = selected.name;
  document.querySelector('#place-status').textContent = selected.status === 'planned'
    ? 'Planejado: cartografia de Emerald disponível; região ainda não jogável nesta ROM.'
    : 'Presente na ROM. ' + (selected.port_index !== null ? 'Porto conectado às novas rotas de Surf, sem ticket ou insígnias.' : 'Cidade de Kanto; acesso marítimo às ilhas por Vermilion.');
  const list = document.querySelector('#connections'); list.replaceChildren();
  for (const link of data.links.filter(l => l.source === id || l.target === id)) {
    const other = points.get(link.source === id ? link.target : link.source);
    const li = document.createElement('li');
    li.textContent = `${link.mode} ↔ ${other.name} — ${link.status === 'playable' ? 'jogável' : 'ainda não implementado'}`;
    list.append(li);
  }
  if (!list.children.length) {
    const li = document.createElement('li');
    li.textContent = selected.status === 'planned' ? 'Eventos e viagens desta cidade ainda aguardam o porte.' : 'As rotas locais permanecem no mapa de Kanto.';
    list.append(li);
  }
  for (const marker of atlas.querySelectorAll('.point')) {
    const active = marker.dataset.id === id;
    marker.classList.toggle('selected', active);
    marker.setAttribute('aria-pressed', String(active));
  }
  for (const path of atlas.querySelectorAll('.route')) path.classList.toggle('active', path.dataset.source === id || path.dataset.target === id);
  cursorLayer.replaceChildren(element('rect', { x: selected.x - 12, y: selected.y - 12, width: 24, height: 24, class: 'selection' }),
    element('text', { x: selected.x, y: selected.y - 21, 'text-anchor': 'middle', class: 'selection-label' }, selected.name));
}

function visibility() {
  if (!data) return;
  routeLayer.style.display = showRoutes.checked ? '' : 'none';
  plannedLayer.style.display = showPlanned.checked ? '' : 'none';
  for (const path of routeLayer.querySelectorAll('.planned')) path.style.display = showPlanned.checked ? '' : 'none';
  for (const option of places.options) option.hidden = !showPlanned.checked && points.get(option.value).status === 'planned';
  if (!showPlanned.checked && selected.status === 'planned') select('MAPSEC_VERMILION_CITY');
}

async function init() {
  const response = await fetch('world-map.json');
  if (!response.ok) throw new Error(`Atlas indisponível (${response.status})`);
  data = await response.json(); points = new Map(data.points.map(p => [p.id, p]));
  atlas.append(element('rect', { width: data.width, height: data.height, fill: '#80c5dc' }));
  const defs = element('defs'); const pattern = element('pattern', { id: 'grid', width: 16, height: 16, patternUnits: 'userSpaceOnUse' });
  pattern.append(element('path', { d: 'M 16 0 L 0 0 0 16', fill: 'none', stroke: '#4d95b3', 'stroke-width': .5, opacity: .35 }));
  defs.append(pattern); atlas.append(defs, element('rect', { width: data.width, height: data.height, fill: 'url(#grid)' }),
    element('text', { x: 32, y: 36, class: 'info-title' }, 'NAV DA JORNADA  /  MAPA REGIONAL'),
    element('text', { x: 1256, y: 36, class: 'panel-note', 'text-anchor': 'end' }, 'KANTO + SEVII JOGÁVEIS · HOENN EM CONSTRUÇÃO'));
  plannedLayer = element('g', { id: 'planned-region' });
  for (const panel of data.panels) {
    const group = element('g');
    group.append(element('text', { x: panel.x, y: panel.y - 14, class: 'panel-name' }, panel.name),
      element('rect', { x: panel.x - 3, y: panel.y - 3, width: panel.width + 6, height: panel.height + 6, fill: '#347b9b', rx: 3 }),
      element('image', { x: panel.x, y: panel.y, width: panel.width, height: panel.height, href: panel.image, class: 'map-image' }));
    (panel.status === 'planned' ? plannedLayer : atlas).append(group);
  }
  atlas.append(plannedLayer);
  routeLayer = element('g', { 'aria-hidden': 'true' }); atlas.append(routeLayer);
  data.links.forEach((link, index) => {
    const a = points.get(link.source), b = points.get(link.target);
    const bend = link.status === 'planned' ? (link.mode === 'Surf' ? 90 : 150) : 42 + index * 2;
    routeLayer.append(element('path', { d: `M ${a.x} ${a.y} Q ${(a.x + b.x) / 2} ${(a.y + b.y) / 2 + bend} ${b.x} ${b.y}`,
      class: `route ${link.status === 'planned' ? 'planned' : ''}`, 'data-source': link.source, 'data-target': link.target }));
  });
  const markers = element('g'); atlas.append(markers);
  data.points.forEach((point, index) => {
    const marker = element('g', { class: `point ${point.status === 'planned' ? 'planned' : ''}`, 'data-id': point.id,
      role: 'button', tabindex: 0, 'aria-label': `${point.name}, ${point.status === 'planned' ? 'planejado' : 'presente na ROM'}` });
    marker.append(element('title', {}, point.name), element('circle', { cx: point.x, cy: point.y, r: point.port_index !== null ? 7 : 5 }));
    marker.addEventListener('click', () => select(point.id));
    marker.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); select(point.id); }
      else if (['ArrowLeft', 'ArrowUp', 'ArrowRight', 'ArrowDown'].includes(event.key)) {
        event.preventDefault();
        const visible = data.points.filter(p => showPlanned.checked || p.status !== 'planned');
        const current = visible.findIndex(p => p.id === point.id);
        const direction = ['ArrowLeft', 'ArrowUp'].includes(event.key) ? -1 : 1;
        const next = visible[(current + direction + visible.length) % visible.length];
        atlas.querySelector(`[data-id="${next.id}"]`).focus(); select(next.id);
      }
    });
    (point.status === 'planned' ? plannedLayer : markers).append(marker);
    const option = document.createElement('option'); option.value = point.id;
    option.textContent = `${point.name}${point.status === 'planned' ? ' (planejado)' : ''}`; places.append(option);
  });
  const info = element('g');
  info.append(element('rect', { x: 638, y: 440, width: 224, height: 286, rx: 8, fill: '#d9f0ed', opacity: .95 }),
    element('text', { x: 658, y: 474, class: 'info-title' }, 'ACESSOS POR SURF'));
  ['Vermilion ↔ ilhas 1–7', '↔ Birth ↔ Navel Rock', '', 'Azul: conexões atuais', 'Âmbar: Hoenn planejada', '', 'Barcos atuais preservados.', 'Hoenn ainda não jogável.', '', 'Clique nos marcadores.'].forEach((line, i) => info.append(element('text', { x: 658, y: 505 + i * 21, class: 'info-text' }, line)));
  atlas.append(info); cursorLayer = element('g', { 'aria-hidden': 'true' }); atlas.append(cursorLayer);
  select('MAPSEC_VERMILION_CITY'); visibility();
}
places.addEventListener('change', () => select(places.value));
showRoutes.addEventListener('change', visibility); showPlanned.addEventListener('change', visibility);
document.querySelector('#reset').addEventListener('click', () => { if (data) select('MAPSEC_VERMILION_CITY'); });
init().catch(error => { document.querySelector('#place-name').textContent = 'Não foi possível carregar o atlas.'; document.querySelector('#place-status').textContent = error.message; });
