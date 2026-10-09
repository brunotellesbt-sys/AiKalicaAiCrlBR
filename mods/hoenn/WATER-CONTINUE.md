# Continue debaixo d'água e volta da Seafloor Cavern

Na base, os dois personagens de Kanto voltavam de um save submerso em modo
Surf, apesar de conservarem o mapa e a posição debaixo d'água. Red e Leaf
reutilizam o mesmo sprite para Surf e Dive; a restauração procurava o primeiro
modo associado ao sprite e encontrava Surf. Os personagens de Hoenn mantinham
o modo correto porque seus identificadores de sprites são diferentes.

A camada `water-continue` faz a restauração respeitar o tipo do mapa: em um
mapa submerso, o personagem retorna em Dive. A escolha por sprite continua
para os demais mapas. Somente `src/field_player_avatar.c` muda. As tabelas e
imagens existentes, o layout do save, os golpes e as permissões da história
permanecem iguais.

## Validação no motor

A base reproduziu o problema nos dois casos submersos de Kanto. Na candidata,
**16 saves e Continues** passaram: masculino/feminino de Kanto/Hoenn, cada um
em terra, Surf, Dive e Surf após emergir. Mapas, posições, origem, sexo e
insígnias permaneceram iguais antes e depois de continuar. Os mergulhos e
as subidas usaram os comandos normais de A/B, com confirmação.

O percurso da Seafloor Cavern também passou na candidata. A ida preservou
o caminho anterior até a recusa de Archie, incluindo a batalha dupla de
Shelly e seu grunt. A volta registrou **122 mudanças de posição e cinco
transições de mapa**, pelas salas 9/8/3/6, entrada e mar submerso da Rota 128.
Surf foi ativado normalmente na sala 6 e na margem da entrada. A correnteza,
a saída direcional da sala final e as passagens originais foram usadas sem
escrever posições, trocar mapas internamente ou iniciar scripts artificialmente.

Houve Save/Continue em três pontos da volta:

| Local | Posição | Modo antes e depois |
|---|---|---|
| Underwater Seafloor Cavern | 6, 5 | Dive |
| Underwater Route 128 | 38, 27 | Dive |
| Route 128 | 38, 27 | Surf |

As insígnias continuaram em zero e o episódio de Kyogre permaneceu pendente.
Archie continuou exigindo as missões. A matriz ARM também passou novamente
na candidata: **5.120 decisões de missão e 44 permissões**.

- [Matriz da base](water-continue-validation/baseline/water-continue.json).
- [16 casos corrigidos](water-continue-validation/native/water-continue.json).
- [Percurso e estados dos saves](water-continue-validation/route/seafloor-route.json).
- [Continue submerso na saída](water-continue-validation/route/native-underwater-return-after-continue.png).
- [Retorno à superfície](water-continue-validation/route/native-route128-return-after-continue.png).
- [Regressão das missões](water-continue-validation/missions/campaign-matrix.json).

## Candidatas e reprodução

- Base `seafloor-access`: `7a054af7067d071e0bca051d5004898312f8bdb9e4722a7050ab05dac5a141ea`.
- Candidata: `12379c4eee922d73f1f90f167d4e53845510fc1b00fa55bc927a7e84728d9e6e`.
- Fonte fixada em `e05c82865d38a6638173fd30b2c830d1250aa50d`.

Partir de uma cópia compilada da árvore anterior, preparada conforme
[SEAFLOOR-ACCESS.md](SEAFLOOR-ACCESS.md). O overlay confere hashes de entrada,
arquivos preservados e sua própria saída; passou por reprodução determinística
e idempotência.

```sh
python3 tools/hoenn/prepare_water_continue.py --source .local/hoenn-water-continue-src
PATH="$PWD/.local/arm-gcc/usr/bin:$PWD/.local/arm-binutils/usr/bin:$PATH" make -C .local/hoenn-water-continue-src -j4
python3 tools/hoenn/verify_abilities.py --layer water-continue --source .local/hoenn-seafloor-src --candidate .local/hoenn-water-continue-src --output mods/hoenn/water-continue-validation
python3 tools/hoenn/validate_water_continue.py --source .local/hoenn-seafloor-src --library .local/mgba-bridge.so --output mods/hoenn/water-continue-validation/baseline
python3 tools/hoenn/validate_water_continue.py --source .local/hoenn-water-continue-src --library .local/mgba-bridge.so --output mods/hoenn/water-continue-validation/native
python3 tools/hoenn/validate_seafloor_route.py --source .local/hoenn-water-continue-src --library .local/mgba-bridge.so --output mods/hoenn/water-continue-validation/route
python3 tools/hoenn/validate_campaign_matrix.py --source .local/hoenn-water-continue-src --library .local/mgba-bridge.so --output mods/hoenn/water-continue-validation/missions
python3 -m unittest discover -s tools/hoenn -v
```

## Limites

Origem/sexo, estado inicial da história e insígnias, viagem até o mar e equipe
com golpes conhecidos são fixtures. No percurso, os atributos são aumentados,
há cura entre batalhas e remoção de condições de status em RAM durante os
confrontos para acelerar o teste. Vitórias e marcadores de treinadores
continuam nativos; o resultado não comprova dificuldade ou balanceamento.
Encontros selvagens são desativados.

Foram testados esses percursos e pontos de save, não todos os mapas submersos
ou todas as salas da caverna. Ainda faltam campanhas completas e sessões
longas no navegador. A ROM do player continua na versão anterior e a candidata
exige novo jogo; não existe migração dos saves antigos.
