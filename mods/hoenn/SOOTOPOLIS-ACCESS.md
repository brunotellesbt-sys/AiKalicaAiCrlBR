# Acesso aquático a Sootopolis

Esta etapa exercita na candidata `water-continue` a viagem da Rota 126 a
Sootopolis e a volta. Não cria uma nova ROM nem atualiza o player.

O teste começa com um personagem de Kanto, zero insígnias nas duas regiões
e Surf/Dive conhecidos. A posição inicial no mar, equipe, origem e estado
inicial da história são fixtures. Depois dessa colocação, a entrada por Dive,
as travessias, as portas e a subida à superfície usam comandos do controle
no motor mGBA. Encontros selvagens são desativados; este teste não avalia
balanceamento nem substitui uma campanha completa.

O roteiro visita uma residência na margem oeste e o Centro Pokémon na
margem leste, atravessando o lago por Surf. Passaram **190 mudanças de
posição, seis transições de mapa e três ativações de Surf na margem**.
As transições por Dive/subida são verificadas separadamente. Salva e
continua em seis pontos:

| Local | Modo esperado |
|---|---|
| Entrada submersa de Sootopolis | Dive |
| Lago de Sootopolis | Surf |
| Casa 1, margem oeste | A pé |
| Centro Pokémon, margem leste | A pé |
| Rota 126 submersa, na volta | Dive |
| Rota 126 na superfície | Surf |

Cada Continue deve manter mapa, posição e modo, com zero insígnias e o
episódio de Kyogre pendente. A ida e a volta não exigem batalhas de treinador.
Isso verifica duas portas e as duas margens, não todos os interiores da cidade.

## Planejamento e regressão

O planejador de caminhada usado na Seafloor Cavern foi extraído para
`tools/hoenn/native_water_walk.py` e reutilizado aqui. As portas animadas são
consideradas no planejamento, mas precisam abrir no motor pelos comandos
normais. Um evento de warp sobre um tile comum não vira uma transição
automática: o planejador consulta os classificadores nativos de comportamento.
Correntezas e saídas direcionais continuam passando pelo motor.

A Seafloor Cavern é percorrida novamente para verificar essa extração,
incluindo a entrada por Dive, batalhas, recusa de Archie com missões pendentes,
volta e os três Continues na água. A regressão passou; as batalhas usam
atributos aumentados, cura entre confrontos e recuperação de status em RAM,
conforme [WATER-CONTINUE.md](WATER-CONTINUE.md). Nenhum arquivo da candidata
é alterado.

## Evidências e reprodução

- [Roteiro de Sootopolis](sootopolis-validation/native/sootopolis-access.json).
- [Continue na casa oeste](sootopolis-validation/native/sootopolis-west-house-after-continue.png).
- [Continue no Centro Pokémon](sootopolis-validation/native/sootopolis-east-pokemon-center-after-continue.png).
- [Continue na Rota 126 após voltar](sootopolis-validation/native/route126-surface-return-after-continue.png).
- [Regressão da Seafloor Cavern](sootopolis-validation/seafloor/seafloor-route.json).

Candidata: `12379c4eee922d73f1f90f167d4e53845510fc1b00fa55bc927a7e84728d9e6e`,
com fonte fixada em `e05c82865d38a6638173fd30b2c830d1250aa50d`.
Preparar a árvore compilada e a ponte mGBA conforme
[WATER-CONTINUE.md](WATER-CONTINUE.md). Então:

```sh
python3 tools/hoenn/validate_sootopolis_access.py --source .local/hoenn-water-continue-src --library .local/mgba-bridge.so --output mods/hoenn/sootopolis-validation/native
python3 tools/hoenn/validate_seafloor_route.py --source .local/hoenn-water-continue-src --library .local/mgba-bridge.so --output mods/hoenn/sootopolis-validation/seafloor
python3 -m unittest discover -s tools/hoenn -v
python3 -m unittest discover -s tools/sea_routes -v
```

## Estimativa de trabalho restante

No tamanho recente dos PRs, a estimativa provisória é **10 a 20 PRs para uma
candidata de lançamento**. A quantidade depende dos problemas encontrados
ao jogar as campanhas e revisar os percursos. PRs são unidades de revisão,
não uma medida de conclusão; não há porcentagem validada de jogo pronto.

Os maiores blocos ainda são as duas campanhas completas com atributos
normais, os demais percursos e santuários, instalações do pós-jogo,
balanceamento e sessões prolongadas no navegador. Os critérios de conclusão
estão em [REMAINING-WORK.md](REMAINING-WORK.md).
