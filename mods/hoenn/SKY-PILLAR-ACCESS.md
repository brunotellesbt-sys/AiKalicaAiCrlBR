# Sky Pillar explorável sem antecipar a crise

A porta externa de Sky Pillar ainda exigia o evento em que Wallace vai à
torre. A camada `sky-pillar-access` abre essa porta ao carregar o mapa,
permitindo explorar a torre durante a jornada livre. Os andares, suas
escadas, layouts limpos e rachados e a queda original do quarto para o
terceiro andar permanecem iguais.

Uma abertura simples permitiria pisar no evento original do topo e
despertar Rayquaza antes de Archie. Por isso, o evento verifica agora:

- Pelo menos sete insígnias de Hoenn e os requisitos da aliança com Giovanni:
  Silph, Instituto Meteorológico, esconderijo Aqua, Centro Espacial e
  missões adicionais de Hoenn.
- O episódio de Archie concluído, a crise climática ativa e a cena inicial
  do confronto dos lendários em Sootopolis concluída.
- Rayquaza ainda não despertado.

Sem esses requisitos, uma fala informa que Rayquaza dorme e devolve o
controle. Nenhuma flag de conclusão é concedida. Quando os requisitos
existem, o corpo original do despertar executa normalmente. A volta a
Sootopolis e a cena de paz continuam necessárias para liberar o último
ginásio de Hoenn. A captura de Rayquaza continua separada do despertar,
exigindo as 16 insígnias como os demais especiais.

## Validação no motor

Na base, os controles reproduziram a porta fechada sem o evento de Wallace.
Na candidata, passaram os cinco andares, topo, retorno e nova entrada:
**211 mudanças de posição, 16 transições de mapa e três Saves/Continues**.
A queda do quarto para o terceiro andar foi feita pelo evento nativo,
sem escrever a posição ou iniciar o script de queda diretamente.

O evento do topo foi acionado pelo controle com zero insígnias. Ele recusou
o despertar e manteve Rayquaza, Sootopolis e a crise nos estados iniciais.
Os três Continues conservaram mapa, posição e pendências.

A nova permissão passou **4.352 casos**: todos os 256 conjuntos de insígnias
em 17 cenários, incluindo requisitos ausentes e estados da cidade. A matriz
regional anterior também passou suas **5.120 decisões e 44 permissões**.

A batalha nativa de Giovanni contra Archie/Shelly e o restante do desfecho
foram repetidos nesta candidata. Passaram a saída para a Rota 128, o
confronto original em Sootopolis, o despertar de Rayquaza, a cena de paz
e a porta física do último ginásio. Despertar sozinho continuou insuficiente
para abrir esse ginásio. Altering Cave e Desert Underpass também passaram
novamente com seus quatro Continues.

- [Porta da base](sky-pillar-validation/baseline/sky-pillar-access.json).
- [Percurso da torre](sky-pillar-validation/native/sky-pillar-access.json).
- [Visita antecipada ao topo](sky-pillar-validation/native/rayquaza-early-awakening-refused.png).
- [Continue no topo](sky-pillar-validation/native/sky-pillar-summit-after-continue.png).
- [Matriz do despertar](sky-pillar-validation/permissions/rayquaza-permission.json).
- [Batalha e desfecho](sky-pillar-validation/aftermath/archie-aftermath.json).
- [Regressão regional](sky-pillar-validation/missions/campaign-matrix.json).
- [Regressão das cavernas](sky-pillar-validation/caves/cave-access.json).

## Reprodução

Somente três arquivos da candidata mudam: `SkyPillar_Outside/scripts.inc`,
`SkyPillar_Top/scripts.inc` e `src/journey_campaign_gates.c`. O overlay confere
hashes dos arquivos alterados e preservados; reprodução e idempotência passaram.

Base: `6fb57b0539403b49d4cb1eb67dcba99f7102d83b8e6bc5a45b74bfa496009261`.
Candidata: `3b3e16d60b50a9be8105eaa8a62bb91ea7923f7748d0bfbd68be64a264fe544d`.
Fonte: `e05c82865d38a6638173fd30b2c830d1250aa50d`.

Partir de uma cópia compilada de `cave-access`, conforme
[CAVE-ACCESS.md](CAVE-ACCESS.md). Então:

```sh
python3 tools/hoenn/prepare_sky_pillar_access.py --source .local/hoenn-sky-access-src
PATH="$PWD/.local/arm-gcc/usr/bin:$PWD/.local/arm-binutils/usr/bin:$PATH" make -C .local/hoenn-sky-access-src -j4
python3 tools/hoenn/verify_abilities.py --layer sky-pillar-access --source .local/hoenn-cave-access-src --candidate .local/hoenn-sky-access-src --output mods/hoenn/sky-pillar-validation
python3 tools/hoenn/validate_sky_pillar_access.py --source .local/hoenn-cave-access-src --library .local/mgba-bridge.so --output mods/hoenn/sky-pillar-validation/baseline
python3 tools/hoenn/validate_sky_pillar_access.py --source .local/hoenn-sky-access-src --library .local/mgba-bridge.so --output mods/hoenn/sky-pillar-validation/native
python3 tools/hoenn/validate_rayquaza_permission.py --source .local/hoenn-sky-access-src --library .local/mgba-bridge.so --output mods/hoenn/sky-pillar-validation/permissions
python3 tools/hoenn/validate_archie_aftermath.py --source .local/hoenn-sky-access-src --library .local/mgba-bridge.so --output mods/hoenn/sky-pillar-validation/aftermath
python3 tools/hoenn/validate_campaign_matrix.py --source .local/hoenn-sky-access-src --library .local/mgba-bridge.so --output mods/hoenn/sky-pillar-validation/missions
python3 tools/hoenn/validate_cave_access.py --source .local/hoenn-sky-access-src --library .local/mgba-bridge.so --output mods/hoenn/sky-pillar-validation/caves
python3 -m unittest discover -s tools/hoenn -v
python3 -m unittest discover -s tools/sea_routes -v
```

## Limites

Estado inicial da história, insígnias, equipe e viagem inicial são fixtures.
O roteiro da torre desativa encontros selvagens e usa os layouts limpos
selecionados originalmente quando a história da torre está no início. Não
testa a corrida de Mach Bike dos layouts rachados posteriores. O planejador
modela a queda, mas o motor realiza o deslocamento e a mudança de andar.

No desfecho, viagens e entrada de scripts são fixtures; a batalha usa equipe
de nível 100. Os resultados não substituem campanhas completas ou avaliação
de dificuldade. O player permanece na versão anterior; esta candidata não
foi publicada.
