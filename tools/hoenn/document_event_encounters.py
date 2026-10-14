"""Document the installed event-only family locations and usable form tools."""
import argparse,json
from pathlib import Path
from special_encounters import FOSSILS,FORM_TOOLS
ROOT=Path(__file__).resolve().parents[2]
def label(name):return name.removeprefix('SPECIES_').removeprefix('ITEM_').replace('_',' ').title()
def generate(source,output):
    source=Path(source);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    info=json.loads((source/'.journey-special-encounter-workshop').read_text())
    catalog=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text())['species']
    locations={0:'Torre Pokémon, Lavender: escada lateral à direita no primeiro andar, (21, 9). A TV fica em (2, 4) na oficina.',
      1:'Memorial Pillar, Sevii 5: poço em (16, 47).',2:'Monean Chamber, Tanoby Ruins, Sevii 7: glifo em (11, 8).',
      3:'Lost Cave, Sevii 5: Room 10, baú em (7, 5).',4:'Instituto Meteorológico, Rota 119, segundo andar: cientista original, depois de Shelly.',
      5:'Celadon Game Corner: balcão de prêmios Pokémon, usando moedas e Coin Case.'}
    lines=['# Encontros especiais e mudanças de forma','',
      'Estas 21 famílias têm aquisição por evento ou restauração. Nenhuma delas continua nos encontros aleatórios de grama, cavernas, Surf ou pesca. As evoluções são obtidas a partir do Pokémon inicial da família. Lendários, míticos e Paradoxos continuam no índice separado e exigem as 16 insígnias.','',
      'Os novos encontros comuns seguem a média de nível da equipe −5/+2. Rotom, Spiritomb, Unown e Gimmighoul não exigem uma Liga. Fugir ou perder permite nova tentativa. Rotom, Spiritomb e Gimmighoul param de aparecer após a captura; o glifo de Unown continua disponível para suas letras.','',
      '| Família | Local e método |','|---|---|']
    for index,dest in enumerate(info['destinations'][:6]):
        lines.append('| '+label(catalog[str(dest['root'])]['name'])+' | '+locations[index]+' |')
    lines+=['','## Rotom e Deoxys','',
      'Capture somente Rotom base na TV com estática. Interaja com um eletrodoméstico da oficina, escolha Rotom na equipe e selecione o aparelho no catálogo: forno, lavadora, geladeira, ventilador ou cortador. LIGHT BULB devolve a forma base. A mudança usa a animação nativa, recalcula os atributos e oferece o golpe do aparelho; se necessário, o jogo pergunta qual golpe substituir. Os golpes exclusivos do aparelho anterior são retirados.','',
      'O meteoro dentro da mesma oficina alterna Deoxys entre Normal, Attack, Defense e Speed. Ele não entrega nem consome o Meteorite da história de Hoenn.','',
      '![Oficina de Lavender](images/lavender-workshop.png)','',
      '## Odd Keystone e fósseis','',
      'O explorador na Altering Cave de Hoenn, (4, 5), entrega um conjunto inicial de fósseis e o Odd Keystone. O conjunto de fósseis é entregue uma vez. A pedra é instalada no poço de Memorial Pillar e consumida uma vez; novas tentativas após fuga não exigem outra pedra. A instalação fica no save.','',
      'O cientista no primeiro andar do Museu de Pewter, (24, 7), oferece uma lista de restauração com rolagem. A lista mostra apenas as espécies permitidas na edição. O Pokémon vai à equipe ou ao PC; fósseis não são consumidos se não houver espaço. Os laboratórios originais de Cinnabar e Devon continuam com suas restaurações antigas. A nova marcação de área aponta o centro universal de Pewter.','',
      '| Pokémon inicial | Material necessário |','|---|---|']
    for name,item,other in FOSSILS:lines.append('| '+label(name)+' | '+label(item)+(' + '+label(other) if other else '')+' |')
    lines+=['','Os fósseis até Shieldon funcionam nas edições 1–4; os posteriores ficam nas edições 1–9. As formas regionais e Megas de espécies até #493 continuam permitidas.','',
      '![Poço de Spiritomb](images/spiritomb-well.png)','',
      '## Outros itens de mudança de forma','',
      'O cientista da oficina entrega os seguintes recursos sem duplicar os que já estão na Bag. Eles usam os sistemas nativos dos respectivos Pokémon. Fusão exige os parceiros corretos na equipe; Gracidea depende das condições de Shaymin e do horário. Megas continuam exigindo suas pedras próprias e os Origin Orbs de Dialga, Palkia e Giratina continuam sendo recompensas da história Galactic.','',
      ', '.join(label(item) for item in FORM_TOOLS)+'.','',
      'Formas automáticas em batalha, como Castform sob clima, continuam sendo automáticas. Evoluções por pedras, doces e itens continuam no [guia de itens e evoluções](itens-e-evolucoes.md).','',
      '## Validação','',
      'Nas quatro edições foram exercitados a entrada/saída da oficina, captura real de Rotom com Master Ball preparada no teste, seis escolhas do catálogo, quatro formas de Deoxys, instalação/consumo único do Keystone, save/reload, receitas dos fósseis e consultas nativas das novas áreas na Pokédex. Viagem, equipe e itens iniciais são fixtures declaradas; isso não equivale a jogar a campanha inteira. Os demais recursos de forma utilizam os callbacks existentes e não foram todos exercitados por menus nesta atualização.','']
    (output/'encontros-especiais-e-formas.md').write_text('\n'.join(lines))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,default=ROOT/'docs')
    a=p.parse_args();generate(a.source,a.output)
