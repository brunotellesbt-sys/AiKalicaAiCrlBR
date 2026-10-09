# Acesso às cidades e serviços de Sevii

O roteiro parte do mar conectado ao sul de Vermilion, visita Sevii 1–7 e
retorna ao mesmo ponto. Cada visita inclui o porto original, a cidade,
o Centro Pokémon, cura pela enfermeira, Continue no interior, retorno à
cidade e ao mar e outro Continue em Surf. Na Ilha 3, passa também pelo
mapa original do porto entre o cais e a cidade.

![Enfermeira da Ilha 1](sevii-town-validation/one-native-healing.png)

![Centro Pokémon da Ilha 7](sevii-town-validation/seven-center-land-after-continue.png)

Passaram **34 mapas, 62 transições nativas, 1.701 mudanças de posição,
16 ativações de Surf e 14 Continues**. As sete enfermeiras restauraram o HP
de 1 para o máximo (260 na equipe preparada), por interação normal.
As duas regiões mantiveram zero insígnias e as capturas especiais bloqueadas.

- [Relatório das ilhas](sevii-town-validation/sevii-town-access.json).
- [Regressão no mar oeste](sevii-town-validation/west/ocean-journey.json).

## Validador e preservação

Os tilesets de interiores FRLG podem compartilhar tabelas de atributos com
nomes diferentes. O validador tentava inferir o símbolo da tabela pelo nome
do tileset e não encontrava `gMetatileAttributes_BuildingFrlg`. Agora lê o
ponteiro real da estrutura `Tileset`, no offset 0x10 da revisão fixada.
Quando o símbolo inferido existe, verifica que seu endereço coincide com
esse ponteiro. Classificação de colisões, formatos e movimento são preservados.
A candidata continua sendo `2f53d410`; não foi necessário alterar a ROM
para acessar esses interiores ou usar as enfermeiras.

A viagem Cinnabar–Rustboro–Dewford–Cinnabar foi repetida após o ajuste para
verificar os formatos Emerald/FRLG, conexões, elevações e persistência no mar:
13 mapas, 24 travessias, cinco batalhas e seis Continues passaram.

## Correção da Rota 131 levada à main

O PR #53 foi mesclado na branch `mods/native-ocean-journey` depois que o #52
já havia sido mesclado na `main`. Sua correção não estava na `main` no início
desta etapa. O novo PR inclui essa correção e suas evidências junto com a
validação das cidades de Sevii, tendo `main` como base. A camada
`route131-sea-access` e a candidata permanecem as mesmas de
[EASTERN-OCEAN-JOURNEY.md](EASTERN-OCEAN-JOURNEY.md).

## Reprodução e limites

Usar a candidata de [EASTERN-OCEAN-JOURNEY.md](EASTERN-OCEAN-JOURNEY.md), SHA-256
`2f53d410522b8c1a186112875659791328ae6681f210e6b94a69f15f81049e09`.

```sh
python3 tools/hoenn/validate_sevii_town_access.py --source .local/hoenn-route131-sea-src --library .local/mgba-bridge.so --output mods/hoenn/sevii-town-validation
python3 tools/hoenn/validate_ocean_journey.py --source .local/hoenn-route131-sea-src --library .local/mgba-bridge.so --output mods/hoenn/sevii-town-validation/west
python3 -m unittest discover -s tools/hoenn -p test_sevii_town_access.py -v
```

Uma colocação inicial, equipe preparada e estados anteriores de história
são fixtures. O HP é reduzido a 1 antes de cada conversa para comprovar a
cura nativa; a recuperação vem da enfermeira, sem chamar `HealPlayerParty`
nessas interações. Encontros selvagens ficam desligados. Não há warps
intermediários ou entrada direta nos scripts dos NPCs. Não comprova
balanceamento, todos os serviços, exploração completa das ilhas ou conclusão
das missões de Celio/Lostelle. O player permanece na versão anterior.
