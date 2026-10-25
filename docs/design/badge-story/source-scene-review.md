# Revisão visual das cenas do classificador

Foram inspecionados os dois mapas inteiros com os tiles, paletas e sprites
nativos. As quatro imagens abaixo são **renderizações do source**, identificadas
como tal. Não são propostas nem capturas do emulador.

| Mapa inteiro | Antes | Depois |
|---|---|---|
| Battle Frontier, lado oeste, 56 × 74 tiles | [Source anterior](BattleFrontier_OutsideWest-before-source.png) | [Source com os participantes](BattleFrontier_OutsideWest-after-source.png) |
| Estádio, 20 × 10 tiles | [Source anterior](JourneyPWTArena-before-source.png) | [Source com os competidores](JourneyPWTArena-after-source.png) |

Os pixels do terreno antes e depois são idênticos nos dois mapas. A comparação
inclui os prédios, seus acessos, árvores, encostas, cercas, água, arquibancada e
passarelas. Os hashes das imagens, dos pixels de terreno e dos blockdata estão
em [source-scene-review.json](source-scene-review.json). Essa comparação não
substitui os testes de passagem e batalha na ROM final.

A cena externa ocupa o piso existente diante da recepção, ao sul da ilha.
O exemplo ilustrado usa Red começando em Hoenn: May, Leaf e Brendan são os
três rivais, acompanhados de Luffy e Eren. As identidades dos três primeiros
mudam conforme o início da campanha. Os 25 objetos originais foram mantidos;
os cinco participantes foram acrescentados sem sobrepor os dois tiles do
desembarque, em (19,67) e (20,67). O jogador fica em (26,67). Os seis corpos
estão separados da fachada, do mar, dos vasos e dos demais personagens.

Na arena, o jogador termina a entrada em (9,6) e o adversário em (13,6),
com espaço livre entre eles. O adversário entra pela lateral direita e usa
um objeto temporário separado dos treze espectadores originais. O terreno
e a decoração do estádio permanecem completos.

A [captura externa do emulador](../../../mods/hoenn/badge-story-validation/Gen1-9-Normal/qualifier-outdoor-six-participants.png)
também foi inspecionada: os seis participantes aparecem inteiros diante da
recepção; Luffy e Eren têm proporções próximas às dos três rivais. Os sprites
normalizados possuem 20 pixels de altura visível em cada um dos nove quadros,
preservando os pés e a transparência. O relatório nativo correspondente
identifica a ROM que produziu a captura. Os testes e o publicador devem exigir
novamente essa evidência quando houver outra compilação.

Não foi identificado novo corte em árvore, encosta, prédio ou outro objeto
causado por essas cenas. O SS Tidal original encosta no limite sul do mapa e
seu recorte no render inteiro já existe na imagem anterior; ele não foi
movido ou redesenhado nesta alteração.
