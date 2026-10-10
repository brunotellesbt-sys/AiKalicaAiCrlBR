"""Generate route and special encounter reference from installed map overlays."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def label(name):
 return name.removeprefix('SPECIES_').removeprefix('MAPSEC_').replace('_',' ').title()

def special_category(mon):
 return 'mítico' if mon['mythical'] else 'Ultra Beast' if mon['ultra_beast'] else 'lendário' if mon['legendary'] else 'especial'

def map_region(data):
 section=data['region_map_section']
 islands=('EMERALD_CAY','SUNLIT_ISLE','TIDEWOOD_ISLE','ONE_ISLAND','TWO_ISLAND','THREE_ISLAND','FOUR_ISLAND','FIVE_ISLAND','SIX_ISLAND','SEVEN_ISLAND','THREE_ISLE','BIRTH_ISLAND','NAVEL_ROCK','TANOBY','TREASURE_BEACH','KINDLE_ROAD','MT_EMBER','BOND_BRIDGE','BERRY_FOREST','ICEFALL_CAVE','WATER_LABYRINTH','RESORT_GORGEOUS','LOST_CAVE','MEMORIAL_PILLAR','OUTCAST_ISLAND','GREEN_PATH','WATER_PATH','RUIN_VALLEY','DOTTED_HOLE','TRAINER_TOWER','CANYON_ENTRANCE','SEVAULT_CANYON')
 if data.get('region','REGION_HOENN')=='REGION_KANTO':
  return 'Sevii' if any(token in section or token in data['id'] for token in islands) else 'Kanto'
 return 'Hoenn'

def generate(source,output):
 source=Path(source);output=Path(output);output.mkdir(parents=True,exist_ok=True)
 ecology=json.loads((source/'.journey-ecology').read_text());special=json.loads((source/'.journey-sanctuaries').read_text());catalog=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text())
 if (source/'.journey-lostelle-habitats').exists():
  overlay=json.loads((source/'.journey-lostelle-habitats').read_text())
  ecology.update({k:overlay[k] for k in ['locations_data','map_species','pools','field_slots']})
 if (source/'.journey-tower-habitats').exists():
  overlay=json.loads((source/'.journey-tower-habitats').read_text())
  ecology.update({k:overlay[k] for k in ['locations_data','map_species','pools','field_slots']})
 if (source/'.journey-remote-islands').exists():
  overlay=json.loads((source/'.journey-remote-islands').read_text())
  ecology.update({k:overlay[k] for k in ['locations_data','map_species','pools','field_slots']})
 maps={}
 for path in sorted((source/'data/maps').glob('*/map.json')):
  data=json.loads(path.read_text());maps[data['id']]=data;maps[path.parent.name]=data
 referenced={m for h in ecology['locations_data'] for m in h['maps']}|{c[k] for c in special['captures'] for k in ('map','surface')}
 missing=referenced-maps.keys()
 if missing:raise ValueError(f'Mapas ausentes: {sorted(missing)}')
 special_ids=[c['id'] for c in special['captures']]
 if len(special_ids)!=len(set(special_ids)) or set(special_ids)!=set(catalog['special_species']):raise ValueError('Altares duplicados ou catálogo especial incompleto')
 ordinary=[];lines=['# Pokémon por habitat e encontros especiais','',
 'Referência da candidata nativa com Kanto, Hoenn e Sevii. Não é uma declaração de que todas as histórias e mecânicas da integração estão concluídas.','',
 'Os encontros aleatórios das 920 espécies-base comuns e variantes regionais ficam em 444 famílias, sem repetir famílias entre habitats. Andares da mesma caverna, zonas de Safari e a superfície/subsolo da mesma rota marinha contam como um habitat.','',
 f'A distribuição atual tem {sum(bool(h["land"]) for h in ecology["locations_data"])} habitats terrestres e {sum(not h["land"] for h in ecology["locations_data"])} habitats exclusivamente aquáticos. Sunlit Isle e Tidewood Isle têm oito famílias cada. As famílias com Pokémon do tipo Água ficam em locais com Surf ou pesca e também podem aparecer na grama do mesmo habitat.','',
 f'Existem mais lagos e pontos de pesca que famílias aquáticas. Para preservar a regra de não repetir famílias, {len(ecology["quiet_water_maps"])} mapas ficam sem encontros aquáticos; os encontros terrestres desses habitats permanecem. Esses pontos estão listados ao final. Nenhuma rota foi fechada por isso.','',
 'Nível: média inteira da equipe menos cinco até mais dois, limitada a 1–100. Ovos não contam; Pokémon desmaiados contam. Etapa evolutiva: média inteira das insígnias das duas regiões; 0–2 básicos, 3–5 básicos ou estágio 2, 6–8 estágios 2 ou 3. Famílias sem a etapa seguinte preservam a última disponível.','',
 'Na água, o filtro seleciona as evoluções aquáticas disponíveis da família: por exemplo, Vaporeon pode aparecer na água, enquanto as outras evoluções de Eevee continuam na grama do mesmo habitat. Famílias com etapas de tipos diferentes ficam em habitats terrestres com água, para que nenhuma espécie-base perca seu local.', '',
 ('A Pokédex Nacional vem junto à primeira Pokédex e marca o habitat da família inteira. Os slots e as chances da troca em Berry Forest constam em `lostelle-habitat-validation/preparation/preparation.json`; os locais não alterados seguem `integration-validation/ecology-preparation.json`. As chances de pesca dependem da vara.' if (source/'.journey-lostelle-habitats').exists() else 'A Pokédex Nacional vem junto à primeira Pokédex e marca o habitat da família inteira. Os slots e as chances de cada modalidade constam no arquivo `integration-validation/ecology-preparation.json`; as chances de pesca dependem da vara.'),'',
 '## Encontro fixo de história verificado','', ('O Hypno do resgate de Lostelle permanece em Berry Forest. A família Drowzee/Hypno também está nos encontros aleatórios da mesma floresta; Skorupi/Drapion ocupa o lugar anterior em Mt. Pyre. O evento não adiciona outro habitat à família. Seu nível segue a média da equipe −5/+2. Percurso e resgate em [LOSTELLE-STORY.md](LOSTELLE-STORY.md); revisão de outros encontros fixos pendente, conforme [LOSTELLE-HABITATS.md](LOSTELLE-HABITATS.md).' if (source/'.journey-lostelle-habitats').exists() else 'O Hypno do resgate de Lostelle permanece em Berry Forest. Na distribuição anterior à camada lostelle-habitats, os encontros aleatórios da família ficam em Mt. Pyre.'),'',
 ('Cubone/Marowak fica na Pokémon Tower, incluindo o fantasma original; Nidoran♀/Nidorina/Nidoqueen ocupa Diglett’s Cave. Os slots atuais estão em `tower-habitat-validation/preparation/preparation.json`. O fantasma continua não capturável. [TOWER-HABITATS.md](TOWER-HABITATS.md).' if (source/'.journey-tower-habitats').exists() else ''),'',
 ('Encontros fixos ligados à história são exceções à localização única dos encontros aleatórios: Snorlax permanece nas Rotas 12/16; Kecleon nas Rotas 119/120; Sudowoodo na Battle Frontier; e Voltorb/Electrode nos locais originais de itens disfarçados. Seus eventos não foram removidos nem realocados. Silph Scope, Devon Scope e Wailmer Pail vêm da mãe desde o começo; a Poké Flute continua sendo prêmio do primeiro ginásio em qualquer região. A entrega antecipada não conclui as missões. Detalhes, locais fixos e limites da auditoria em [EARLY-STORY-TOOLS.md](EARLY-STORY-TOOLS.md).' if (source/'.journey-early-story-tools').exists() else ''),'',
 ('O resgate de Fuji exige acalmar Marowak, vencer os três Rockets do 7º andar e falar com Fuji. Esse episódio e os demais descritos em [MANDATORY-NATIVE-MISSIONS.md](MANDATORY-NATIVE-MISSIONS.md) são obrigatórios para avançar nos ginásios regionais; possuir os itens antecipados não substitui suas conclusões.' if (source/'.journey-mandatory-native-missions').exists() else ''),'',
 '## Encontros comuns por habitat','', 'Use a busca pelo nome do Pokémon nesta página ou filtre a planilha `pokemon-locations.csv`. A coluna Região identifica Kanto, Hoenn e Sevii; os nomes internos dos mapas permitem localizar os arquivos exatos do jogo.', '', '| Região | Habitat | Famílias e espécies | Mapas |', '|---|---|---|---|']
 canonical={int(i) for i in catalog['canonical_species'].values()}
 for h in ecology['locations_data']:
  region=' / '.join(sorted({map_region(maps[m]) for m in h['maps']}))
  text=[]
  for f in h['families']:
   text.append(' / '.join(label(m['name']) for m in f['species']))
   for m in f['species']:
    ordinary.append(dict(national_dex=m['national_dex'],species=label(m['name']),internal_id=m['id'],category='comum' if m['id'] in canonical else 'forma regional',region=region,habitat=label(h['section']),maps='; '.join(h['maps']),access='grama/caverna e água local' if h['land'] and h['water'] else 'grama/caverna' if h['land'] else 'Surf/pesca',unlock='progressão evolutiva pela média regional',family=label(f['name'])))
  lines.append('| '+region+' | '+label(h['section'])+' | '+'; '.join(text)+' | '+', '.join(h['maps'])+' |')
 lines+=['','## Lendários, míticos e Ultra Beasts','',
 'Nenhum destes 105 Pokémon entra nos encontros aleatórios. Os altares só iniciam a batalha com oito insígnias de Kanto **e** oito de Hoenn, sem exigir vitória nas Ligas. Fugir ou derrotar o Pokémon permite tentar novamente. Capturá-lo desativa seu altar; capturas em locais antigos também são reconhecidas pela Pokédex.','',
 'As cavernas de Surf ficam nas novas ilhas desenhadas dentro do mar existente: desembarque e entre na montanha a pé. Nas cavernas de Dive, mergulhe no quadrado de água profunda, procure a entrada submersa e entre. As escadas internas levam de volta ao local de entrada.','',
 'As coordenadas abaixo são da entrada externa da caverna (Surf) ou do centro do trecho de água profunda (Dive), sem o deslocamento interno de sete tiles do motor.','',
 '| Local | Rota marítima | Acesso e coordenadas | Pokémon |','|---|---|---|---|']
 for site in special['sites']:
  mons=[c for c in special['captures'] if c['site']==site['theme']];x,y=site['entry'];entrance=(x,y-4) if site['access']=='surf' else (x,y)
  lines.append('| Caverna '+site['theme']+' | '+site['surface']+' ('+label(site['section'])+') | '+('Surf' if site['access']=='surf' else 'Surf + Dive')+f' ({entrance[0]}, {entrance[1]}) | '+', '.join(label(c['species']) for c in mons)+' |')
 for c in special['captures']:
  ordinary.append(dict(national_dex=c['national_dex'],species=label(c['species']),internal_id=c['id'],category=special_category(catalog['species'][str(c['id'])]),region=map_region(maps[c['surface']]),habitat='Caverna '+c['site'],maps=c['map']+'; '+c['surface'],access='Surf' if c['access']=='surf' else 'Surf + Dive',unlock='8 insígnias de Kanto + 8 de Hoenn; antes das Ligas',family=''))
 lines+=['','## Capturas especiais originais','',
 'Os eventos originais de captura também verificam as 16 insígnias. A movimentação dos personagens e os eventos de história foram preservados. Se o Pokémon já estiver marcado como capturado, a nova tentativa não inicia batalha.','']
 for entry in special['legacy_capture_gates']:lines.append('- '+entry['path'].split('/')[2]+': '+', '.join(label(s) for s in sorted(set(entry['species'])))+'.')
 lines+=['','## Pontos aquáticos sem encontros','',', '.join(ecology['quiet_water_maps'])+'.','',
 '## Limites da validação','',
 'Kanto, Hoenn e Sevii estão conectados na candidata; 96 travessias físicas por Surf e as entradas e saídas dos 14 santuários têm verificações nativas registradas. Ainda faltam revisão completa das rotas, interiores, NPCs, puzzles e as duas campanhas jogadas integralmente. Os relatórios de mGBA cobrem situações específicas; não equivalem a finalizar o jogo.', '',
 'A arte de 3.323 imagens e 3.154 paletas foi comparada no motor ARM aos dados compilados. As 97 Megas têm referências auditadas; cinco transformações reais, Battle Bond, trocas, desmaios e batalhas duplas possuem verificações específicas. Isso não significa que todas as animações e batalhas foram jogadas. Os locais deste guia são da candidata, ainda não publicada no player.','']
 sea_note = ['O [traçado marítimo atual](EASTERN-SEA-UNION.md) passa atrás de Ever Grande.',
 'As coordenadas de entradas e Dive deste catálogo permanecem iguais; o mar',
 '`JourneyHoennSouthSea` fica junto à Rota 129 e a saída antiga da Rota 131',
 'não existe mais.', '', '']
 if (source/'.journey-eastern-sea-union').exists():lines[2:2] = sea_note
 (output/'POKEMON-LOCATIONS.md').write_text('\n'.join(lines))
 stream=io.StringIO();writer=csv.DictWriter(stream,lineterminator='\n',fieldnames=['national_dex','species','internal_id','category','region','habitat','maps','access','unlock','family']);writer.writeheader();writer.writerows(sorted(ordinary,key=lambda r:(r['national_dex'],r['internal_id'])))
 (output/'pokemon-locations.csv').write_text(stream.getvalue())
 base_rows=[r for r in ordinary if r['internal_id'] in canonical]
 base={r['national_dex'] for r in base_rows};assert base==set(range(1,1026)) and len(base_rows)==1025,base
 guide=['# Localização de lendários, míticos e Ultra Beasts','', 'Todos exigem **8 insígnias de Kanto e 8 de Hoenn**, antes das Ligas. Não aparecem nos encontros aleatórios. Os locais antigos permanecem como alternativas; este índice aponta os novos altares. Fugir ou derrotar permite outra tentativa; capturar encerra o encontro.', '', 'Coordenadas externas em tiles: X cresce para a direita e Y para baixo, contando de zero. Surf indica a porta na ilha; Surf + Dive indica o centro do trecho de água profunda. A posição do altar é interna à caverna. Não some os sete tiles da borda interna do motor.', '']
 if (source/'.journey-family-postgame').exists():
  guide[2] += ' Encontros errantes nas rotas estão desativados, inclusive após as Ligas. Latias, Latios, Raikou, Entei e Suicune usam os santuários deste índice; a notícia de Latias/Latios permanece um evento da família.'
 categories={}
 for category in ('lendário','mítico','Ultra Beast','especial'):
  captures=[c for c in special['captures'] if special_category(catalog['species'][str(c['id'])])==category]
  categories[category]=len(captures)
  if not captures:continue
  guide += [f'## {category.title()} — {len(captures)}', '', '| Nº Dex | Pokémon | Região | Santuário | Mapa externo | Acesso / entrada (X, Y) | Altar (X, Y) |', '|---|---|---|---|---|---|---|']
  for c in sorted(captures,key=lambda c:c['national_dex']):
   site=next(s for s in special['sites'] if s['theme']==c['site']);x,y=site['entry'];y-=4 if site['access']=='surf' else 0
   guide.append(f"| {c['national_dex']} | {label(c['species'])} | {map_region(maps[c['surface']])} | {c['site']} | {c['surface']} | {'Surf' if c['access']=='surf' else 'Surf + Dive'} ({x}, {y}) | {tuple(c['position'])} |")
  guide.append('')
 if (source/'.journey-eastern-sea-union').exists():guide[2:2] = sea_note
 (output/'SPECIAL-LOCATIONS.md').write_text('\n'.join(guide))
 evidence=dict(base_species=1025,canonical_rows=len(base_rows),ordinary_base_species=920,special_categories=categories,habitats=len(ecology['locations_data']),special_sites=len(special['sites']),referenced_maps=len(referenced),all_referenced_maps_exist=True,source_commit=catalog['source_commit'],input_sha256={n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in ('.journey-ecology','.journey-sanctuaries')})
 if (source/'.journey-lostelle-habitats').exists():evidence['input_sha256']['.journey-lostelle-habitats']=hashlib.sha256((source/'.journey-lostelle-habitats').read_bytes()).hexdigest()
 if (source/'.journey-tower-habitats').exists():evidence['input_sha256']['.journey-tower-habitats']=hashlib.sha256((source/'.journey-tower-habitats').read_bytes()).hexdigest()
 if (source/'.journey-early-story-tools').exists():evidence['input_sha256']['.journey-early-story-tools']=hashlib.sha256((source/'.journey-early-story-tools').read_bytes()).hexdigest()
 if (source/'.journey-mandatory-native-missions').exists():evidence['input_sha256']['.journey-mandatory-native-missions']=hashlib.sha256((source/'.journey-mandatory-native-missions').read_bytes()).hexdigest()
 if (source/'.journey-sixteen-badge-leagues').exists():evidence['input_sha256']['.journey-sixteen-badge-leagues']=hashlib.sha256((source/'.journey-sixteen-badge-leagues').read_bytes()).hexdigest()
 if (source/'.journey-eastern-sea-union').exists():evidence['input_sha256']['.journey-eastern-sea-union']=hashlib.sha256((source/'.journey-eastern-sea-union').read_bytes()).hexdigest()
 if (source/'.journey-remote-islands').exists():evidence['input_sha256']['.journey-remote-islands']=hashlib.sha256((source/'.journey-remote-islands').read_bytes()).hexdigest()
 rom=source/'pokeemerald.gba'
 if rom.exists():evidence['rom_sha256']=hashlib.sha256(rom.read_bytes()).hexdigest()
 evidence['documents_sha256']={n:hashlib.sha256((output/n).read_bytes()).hexdigest() for n in ('POKEMON-LOCATIONS.md','SPECIAL-LOCATIONS.md','pokemon-locations.csv')}
 (output/'location-documentation.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+'\n')
 return dict(base_species=1025,rows=len(ordinary),habitats=len(ecology['locations_data']),special_sites=len(special['sites']))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,default=ROOT/'mods/hoenn');a=p.parse_args();print(generate(a.source,a.output))
