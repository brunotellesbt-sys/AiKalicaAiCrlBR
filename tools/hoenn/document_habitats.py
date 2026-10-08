"""Generate route and special encounter reference from installed map overlays."""
import argparse
import csv
import io
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def label(name):
 return name.removeprefix('SPECIES_').removeprefix('MAPSEC_').replace('_',' ').title()

def generate(source,output):
 source=Path(source);output=Path(output);output.mkdir(parents=True,exist_ok=True)
 ecology=json.loads((source/'.journey-ecology').read_text());special=json.loads((source/'.journey-sanctuaries').read_text());catalog=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text())
 ordinary=[];lines=['# Pokémon por habitat e encontros especiais','',
 'Referência da candidata nativa com Kanto, Hoenn e Sevii. Não é uma declaração de que todas as histórias e mecânicas da integração estão concluídas.','',
 'As 920 espécies-base comuns e as variantes regionais ficam em 444 famílias, sem repetir famílias entre habitats. Andares da mesma caverna, zonas de Safari e a superfície/subsolo da mesma rota marinha contam como um habitat.','',
 'A distribuição corrigida tem 97 habitats terrestres: 18 com cinco famílias e 79 com quatro; outros 38 habitats exclusivamente aquáticos têm uma família cada. As 77 famílias com Pokémon do tipo Água estão reservadas para locais com Surf ou pesca, e também podem aparecer na grama do mesmo habitat quando ela existe.','',
 f'Existem mais lagos e pontos de pesca que famílias aquáticas. Para preservar a regra de não repetir famílias, {len(ecology["quiet_water_maps"])} mapas ficam sem encontros aquáticos; os encontros terrestres desses habitats permanecem. Esses pontos estão listados ao final. Nenhuma rota foi fechada por isso.','',
 'Nível: média inteira da equipe menos cinco até mais dois, limitada a 1–100. Ovos não contam; Pokémon desmaiados contam. Etapa evolutiva: média inteira das insígnias das duas regiões; 0–2 básicos, 3–5 básicos ou estágio 2, 6–8 estágios 2 ou 3. Famílias sem a etapa seguinte preservam a última disponível.','',
 'Na água, o filtro seleciona as evoluções aquáticas disponíveis da família: por exemplo, Vaporeon pode aparecer na água, enquanto as outras evoluções de Eevee continuam na grama do mesmo habitat. Famílias com etapas de tipos diferentes ficam em habitats terrestres com água, para que nenhuma espécie-base perca seu local.', '',
 'A Pokédex Nacional vem junto à primeira Pokédex e marca o habitat da família inteira. Os slots e as chances de cada modalidade constam no arquivo `integration-validation/ecology-preparation.json`; as chances de pesca dependem da vara.','',
 '## Encontros comuns por habitat','', '| Habitat | Famílias e espécies | Mapas |', '|---|---|---|']
 canonical={int(i) for i in catalog['canonical_species'].values()}
 for h in ecology['locations_data']:
  text=[]
  for f in h['families']:
   text.append(' / '.join(label(m['name']) for m in f['species']))
   for m in f['species']:
    ordinary.append(dict(national_dex=m['national_dex'],species=label(m['name']),internal_id=m['id'],category='comum' if m['id'] in canonical else 'forma regional',habitat=label(h['section']),maps='; '.join(h['maps']),access='grama/caverna e água local' if h['land'] and h['water'] else 'grama/caverna' if h['land'] else 'Surf/pesca',unlock='progressão evolutiva pela média regional',family=label(f['name'])))
  lines.append('| '+label(h['section'])+' | '+'; '.join(text)+' | '+', '.join(h['maps'])+' |')
 lines+=['','## Lendários, míticos e Ultra Beasts','',
 'Nenhum destes 105 Pokémon entra nos encontros aleatórios. Os altares só iniciam a batalha com oito insígnias de Kanto **e** oito de Hoenn, sem exigir vitória nas Ligas. Fugir ou derrotar o Pokémon permite tentar novamente. Capturá-lo desativa seu altar; capturas em locais antigos também são reconhecidas pela Pokédex.','',
 'As cavernas de Surf ficam nas novas ilhas desenhadas dentro do mar existente: desembarque e entre na montanha a pé. Nas cavernas de Dive, mergulhe no quadrado de água profunda, procure a entrada submersa e entre. As escadas internas levam de volta ao local de entrada.','',
 'As coordenadas abaixo são da entrada externa da caverna (Surf) ou do centro do trecho de água profunda (Dive), sem o deslocamento interno de sete tiles do motor.','',
 '| Local | Rota marítima | Acesso e coordenadas | Pokémon |','|---|---|---|---|']
 for site in special['sites']:
  mons=[c for c in special['captures'] if c['site']==site['theme']];x,y=site['entry'];entrance=(x,y-4) if site['access']=='surf' else (x,y)
  lines.append('| Caverna '+site['theme']+' | '+site['surface']+' ('+label(site['section'])+') | '+('Surf' if site['access']=='surf' else 'Surf + Dive')+f' ({entrance[0]}, {entrance[1]}) | '+', '.join(label(c['species']) for c in mons)+' |')
 for c in special['captures']:
  ordinary.append(dict(national_dex=c['national_dex'],species=label(c['species']),internal_id=c['id'],category='encontro especial',habitat='Caverna '+c['site'],maps=c['map']+'; '+c['surface'],access='Surf' if c['access']=='surf' else 'Surf + Dive',unlock='8 insígnias de Kanto + 8 de Hoenn; antes das Ligas',family=''))
 lines+=['','## Capturas especiais originais','',
 'Os eventos originais de captura também verificam as 16 insígnias. A movimentação dos personagens e os eventos de história foram preservados. Se o Pokémon já estiver marcado como capturado, a nova tentativa não inicia batalha.','']
 for entry in special['legacy_capture_gates']:lines.append('- '+entry['path'].split('/')[2]+': '+', '.join(label(s) for s in sorted(set(entry['species'])))+'.')
 lines+=['','## Pontos aquáticos sem encontros','',', '.join(ecology['quiet_water_maps'])+'.','',
 '## Limites da validação','',
 'Os relatórios de mGBA documentam as passagens e encontros exercitados. Eles não equivalem a jogar as duas campanhas completas. A auditoria do catálogo verifica dados e referências de sprites; nem todos os sprites SMOL foram renderizados individualmente. Megas/Battle Bond e demais sistemas anteriores têm sua própria validação pendente.','']
 (output/'POKEMON-LOCATIONS.md').write_text('\n'.join(lines))
 stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=['national_dex','species','internal_id','category','habitat','maps','access','unlock','family']);writer.writeheader();writer.writerows(sorted(ordinary,key=lambda r:(r['national_dex'],r['internal_id'])))
 (output/'pokemon-locations.csv').write_text(stream.getvalue())
 base={r['national_dex'] for r in ordinary if r['internal_id'] in canonical};assert base==set(range(1,1026)),base
 return dict(base_species=1025,rows=len(ordinary),habitats=len(ecology['locations_data']),special_sites=len(special['sites']))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,default=ROOT/'mods/hoenn');a=p.parse_args();print(generate(a.source,a.output))
