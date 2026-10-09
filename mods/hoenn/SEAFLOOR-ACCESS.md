# Passagem da Seafloor Cavern

Na candidata anterior, Dive permitia alcançar a caverna desde o início, mas
um grunt ocupava `(10, 2)`, o único tile diante da entrada da primeira sala.
O diálogo não o movia. Ele desaparecia somente na entrega original de Dive
por Steven, após o Centro Espacial. Isso mantinha uma trava antiga de estrada
apesar de a família já entregar Dive.

A camada `seafloor-access` move esse mesmo NPC para **`(11, 3)`**, ao lado da
passagem. Mantém seu identificador, sprite, diálogo, direção e flag de
visibilidade. A entrega de Steven ainda pode fazê-lo desaparecer no momento
original. Não concede insígnias nem conclui missões.

As permissões de Archie continuam exigindo sete insígnias de Hoenn, os
episódios anteriores de Hoenn, o Centro Espacial e Giovanni derrotado na
Silph de Kanto. As missões dos ginásios e sua escala de níveis não mudam.
Surf, Dive e Waterfall permanecem como os únicos HMs; as correntezas e
todos os layouts da caverna permanecem iguais.

## Candidata e reprodução

Somente `data/maps/SeafloorCavern_Entrance/map.json` muda, nas duas coordenadas
do grunt. Os scripts preservados, a escala de ginásios e o layout binário da
entrada são conferidos por hash. A preparação recusa entradas modificadas,
pode ser reproduzida e confere os arquivos ao ser executada novamente.

- Base `aqua-episodes`: `0e4626b06423c27889a08588fdfd2f9d294df20fdb4064273c75af1da8b7c285`.
- Candidata: `7a054af7067d071e0bca051d5004898312f8bdb9e4722a7050ab05dac5a141ea`.
- Fonte fixada em `e05c82865d38a6638173fd30b2c830d1250aa50d`.

Partir de uma cópia compilada da árvore `aqua-episodes`, preparada conforme
[PUZZLES-AND-AQUA.md](PUZZLES-AND-AQUA.md):

```sh
python3 tools/hoenn/prepare_seafloor_access.py --source .local/hoenn-seafloor-src
PATH="$PWD/.local/arm-gcc/usr/bin:$PWD/.local/arm-binutils/usr/bin:$PATH" make -C .local/hoenn-seafloor-src -j4
python3 tools/hoenn/verify_abilities.py --layer seafloor-access --source .local/hoenn-aqua-episodes-src --candidate .local/hoenn-seafloor-src --output mods/hoenn/seafloor-access-validation
python3 tools/hoenn/validate_seafloor_route.py --source .local/hoenn-aqua-episodes-src --library .local/mgba-bridge.so --output mods/hoenn/seafloor-access-validation/baseline
python3 tools/hoenn/validate_seafloor_route.py --source .local/hoenn-seafloor-src --library .local/mgba-bridge.so --output mods/hoenn/seafloor-access-validation/native
python3 tools/hoenn/validate_campaign_matrix.py --source .local/hoenn-seafloor-src --library .local/mgba-bridge.so --output mods/hoenn/seafloor-access-validation/matrix
python3 -m unittest discover -s tools/hoenn -v
```

## Evidências e limites

A base passou por Dive e pela subida nativos com zero insígnias, mas ficou
fisicamente bloqueada pelo NPC mesmo após conversar e tentar andar novamente:
[relatório da base](seafloor-access-validation/baseline/seafloor-baseline.json).
A candidata passou pela reprodução determinística e idempotência, mais a
matriz ARM de **5.120 decisões de missão e 44 permissões**:
[reprodução](seafloor-access-validation/reproduction.json) e
[matriz regional](seafloor-access-validation/matrix/campaign-matrix.json).

Na candidata, o percurso passou por Dive na Rota 128 `(38, 27)`, subida
na caverna, conversa com o grunt reposicionado e as salas 1, 2, 6, 3, 8 e 9.
Foram **163 mudanças de posição monitoradas e sete transições de mapa**,
além da subida por Dive. As correntezas da sala 6 foram percorridas pelos
controles normais; o planejador considera seu movimento forçado. Houve vitória
nativa na batalha dupla de Shelly e seu grunt, com os dois marcadores de
derrota conferidos. O jogador não usou Strength, Rock Smash, Flash ou Acro Bike.

Chegar à sala final não libera o boss: o gatilho original de Archie recusou
o confronto com zero insígnias. Save/Continue conservou a ausência de
insígnias e a crise ainda não concluída. O percurso não injetou posições,
viagens internas ou entradas de scripts. Evidências:

- [Relatório do percurso](seafloor-access-validation/native/seafloor-route.json).
- [Grunt ao lado da passagem](seafloor-access-validation/native/native-relocated-grunt-dialogue.png).
- [Chegada à sala final](seafloor-access-validation/native/native-seafloor-route-before-archie.png).
- [Recusa do gatilho de Archie](seafloor-access-validation/native/native-archie-trigger-refuses-zero-badges.png).

Esse teste cobre um caminho até a sala final, não todas as salas ou a volta.
Estados iniciais de
história e insígnias, posição inicial no oceano, equipe, atributos e cura são
fixtures. Encontros selvagens são desativados para testar o percurso. Isso não
comprova balanceamento ou duas campanhas completas. Esta etapa não atualiza
a ROM do player; a candidata continua exigindo novo jogo, sem migração de saves.
