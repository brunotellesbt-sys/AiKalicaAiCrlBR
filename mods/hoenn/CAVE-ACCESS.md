# Passagens de cavernas antes da Liga

Altering Cave, na Rota 103, e Desert Underpass, pelo túnel do Fossil Maniac
na Rota 114, ainda estavam fechadas até vencer a Liga de Hoenn. As duas
já fazem parte da distribuição de encontros. Isso impedia alcançar seus
habitats durante a jornada livre.

A camada `cave-access` altera somente dois arquivos de scripts:

- A Rota 103 abre a entrada de Altering Cave ao carregar o mapa.
- O túnel deixa de fechar Desert Underpass e posiciona o Fossil Maniac
  na posição original de pós-jogo. A fala sobre o desabamento passa a
  informar que a passagem está segura.

Os mapas, warps, encontros, famílias evolutivas, níveis e chances não mudam.
O fóssil da caverna mantém a recompensa original, condicionada à escolha
do primeiro fóssil. As missões nas portas dos ginásios continuam valendo;
lendários, míticos e demais especiais continuam exigindo 16 insígnias.
O player não recebeu esta candidata.

## Verificação no motor

Na base, os controles reproduziram as duas portas fechadas. Na candidata,
as duas passagens foram percorridas com zero insígnias nas duas regiões e
sem nenhum título de campeão. Passaram entrada, saída e nova entrada após
Continue: **36 mudanças de posição, oito transições de mapa e quatro saves**.
O marco de descoberta de Desert Underpass foi ativado pelo script original
e preservado após Continue; a conversa do desabamento também foi exercitada.
A permissão para capturar especiais continuou fechada.

O teste observa os tiles de entrada depois dos scripts nativos de OnLoad.
Isso permite planejar uma porta que abre durante o carregamento, em vez
de presumir que o tile fechado do arquivo de mapa continua igual em RAM.
Todos os deslocamentos após a colocação inicial de cada caso usam controles,
sem iniciar diretamente os scripts de abertura ou escrever as posições.

Também passaram na nova candidata o percurso aquático de Sootopolis e seus
seis Continues, mais **5.120 decisões de missão e 44 permissões** regionais.

- [Reprodução das portas fechadas](cave-access-validation/baseline/cave-access.json).
- [Percursos corrigidos](cave-access-validation/native/cave-access.json).
- [Continue dentro de Altering Cave](cave-access-validation/native/AlteringCave-inside-after-continue.png).
- [Continue dentro de Desert Underpass](cave-access-validation/native/DesertUnderpass-inside-after-continue.png).
- [Regressão aquática](cave-access-validation/sootopolis/sootopolis-access.json).
- [Regressão de missões](cave-access-validation/missions/campaign-matrix.json).

## Candidatas e reprodução

Base: `12379c4eee922d73f1f90f167d4e53845510fc1b00fa55bc927a7e84728d9e6e`.
Candidata: `6fb57b0539403b49d4cb1eb67dcba99f7102d83b8e6bc5a45b74bfa496009261`.
Fonte fixada em `e05c82865d38a6638173fd30b2c830d1250aa50d`.

Partir de uma cópia compilada da árvore `water-continue`, conforme
[WATER-CONTINUE.md](WATER-CONTINUE.md). O overlay confere hashes de entrada
e saída e arquivos preservados; reprodução determinística e idempotência
passaram.

```sh
python3 tools/hoenn/prepare_cave_access.py --source .local/hoenn-cave-access-src
PATH="$PWD/.local/arm-gcc/usr/bin:$PWD/.local/arm-binutils/usr/bin:$PATH" make -C .local/hoenn-cave-access-src -j4
python3 tools/hoenn/verify_abilities.py --layer cave-access --source .local/hoenn-water-continue-src --candidate .local/hoenn-cave-access-src --output mods/hoenn/cave-access-validation
python3 tools/hoenn/validate_cave_access.py --source .local/hoenn-water-continue-src --library .local/mgba-bridge.so --output mods/hoenn/cave-access-validation/baseline
python3 tools/hoenn/validate_cave_access.py --source .local/hoenn-cave-access-src --library .local/mgba-bridge.so --output mods/hoenn/cave-access-validation/native
python3 tools/hoenn/validate_sootopolis_access.py --source .local/hoenn-cave-access-src --library .local/mgba-bridge.so --output mods/hoenn/cave-access-validation/sootopolis
python3 tools/hoenn/validate_campaign_matrix.py --source .local/hoenn-cave-access-src --library .local/mgba-bridge.so --output mods/hoenn/cave-access-validation/missions
python3 -m unittest discover -s tools/hoenn -v
python3 -m unittest discover -s tools/sea_routes -v
```

## Limites

Insígnias, estado inicial da história, equipe e colocação diante de cada
entrada são fixtures. Encontros selvagens são desativados; não houve captura
nem avaliação de dificuldade nesta etapa. O teste percorre as entradas e
retornos, não toda a extensão de Desert Underpass. As campanhas completas,
outros percursos e o balanceamento continuam pendentes.
