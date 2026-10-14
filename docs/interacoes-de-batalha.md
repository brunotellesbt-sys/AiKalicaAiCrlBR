# Interações de batalha — validação nativa

Os resultados desta página pertencem à ROM do PR #79, preservada com seus hashes em `mods/hoenn/validation-baselines/pr79/`. A atualização costeira posterior valida os mapas e encontros alterados, sem repetir torneios ou afirmar nova validação completa destas mecânicas.

A suíte executou **684 cenários em cada uma das quatro edições**, totalizando 2.736 verificações. Os relatórios identificam a SHA-256 exata de cada ROM, os resultados observados e as expectativas. Dos 684 casos, 324 verificam a tabela dos 18 tipos e 360 exercitam as demais interações.

## Correção encontrada

A IA estimava dano de Spikes mesmo com Heavy-Duty Boots ativas. Em um cenário com HP máximo 100 e uma camada de Spikes, a rotina nativa retornava 12 HP de dano esperado; o correto era zero. O teste anterior foi preservado em [boots-spikes.json](../mods/hoenn/battle-interactions-validation/regression-before-fix/boots-spikes.json).

A condição de avaliação foi corrigida. Boots ativas agora excluem o custo de hazards, incluindo Spikes e Toxic Spikes, da decisão de troca. Quando Magic Room ou Klutz anulam o item, o custo volta a ser considerado. Magic Guard e Levitate mantêm suas proteções pertinentes. A aplicação de hazards ao jogador já respeitava Boots; o problema encontrado estava na previsão da IA.

## Cobertura

| Área | Interações verificadas |
| --- | --- |
| Tipos e status | Tabela completa incluindo Fada; veneno, queimadura, paralisia, gelo, sono e confusão; Corrosion e imunidades por habilidade |
| Terrenos e duplas | Misty/Electric/Psychic Terrain, alvos voadores, Sweet/Pastel/Flower Veil, Friend Guard e Telepathy |
| Habilidades e imunidades | Mold Breaker, Ability Shield, Neutralizing Gas, Gastro Acid, absorção de golpes, Wonder Guard, Spore, Safety Goggles e Overcoat |
| Aterramento e itens | Levitate, Air Balloon, Iron Ball, Gravity, Smack Down, Ingrain, Embargo, Magic Room e Klutz |
| Dano e sobrevivência | Choice Band/Specs, Life Orb, Guts, Facade, Huge Power, Technician, Sheer Force, Tough Claws, Punk Rock, Multiscale, Fluffy, Fur Coat, Ice Scales, Eviolite, Assault Vest, telas, clima, críticos, Sturdy, Focus Sash e False Swipe |
| Ordem dos ataques | Trick Room, prioridade, Stall, Choice Scarf, Tailwind, paralisia, Unburden e habilidades de clima |
| Berries e efeitos de itens | Cura de status com Unnerve, Oran/Sitrus com Ripen, Gluttony, Heal Block, PP de Leppa com limite máximo, Mental Herb, Leftovers, Black Sludge, Toxic Orb e Flame Orb |
| Avaliação de hazards pela IA | Spikes, Toxic Spikes, Stealth Rock, Boots ativas/anuladas, Magic Guard e Levitate |

As quatro edições produziram os mesmos resultados mecânicos nesses cenários. O [índice de evidências](../mods/hoenn/battle-interactions-validation/validation.json) contém as contagens de cada grupo.

## Relatórios

- [Gen 1–4 Normal](../mods/hoenn/battle-interactions-validation/Gen1-4-Normal/battle-interactions.json)
- [Gen 1–4 Hard](../mods/hoenn/battle-interactions-validation/Gen1-4-Hard/battle-interactions.json)
- [Gen 1–9 Normal](../mods/hoenn/battle-interactions-validation/Gen1-9-Normal/battle-interactions.json)
- [Gen 1–9 Hard](../mods/hoenn/battle-interactions-validation/Gen1-9-Hard/battle-interactions.json)

O manifesto de entrega inclui cinco relatórios: um da compilação-base e um por edição. Eles são verificados pelo empacotador e pelos testes do repositório.

## Método e limites

mGBA executa as funções ARM compiladas da ROM. Os cenários preparam os Pokémon, atributos, habilidades, itens, status, terrenos e estruturas de batalha em memória. O layout é obtido pelo compilador da própria árvore, incluindo campos compactados; não é reutilizado de outra compilação.

Os cálculos de dano são determinísticos, sem o sorteio de 85–100%. Aplicam tanto a etapa anterior ao sorteio quanto os modificadores posteriores. As comparações de multiplicadores toleram até três pontos de dano devido ao arredondamento das etapas inteiras.

Parte dos testes consulta permissões/imunidades; outros calculam dano, ordem de ação, previsão de hazards ou executam o dispatcher de itens. A cura de status e a recuperação de PP são verificadas nas estruturas nativas. As animações de ativação, o consumo visual de berries e a persistência após salvar não são reproduzidos por esta suíte. As quantidades de cura de HP são verificadas no valor agendado pelo motor.

Esta suíte amplia a cobertura e encontrou uma regressão concreta. Ela não testa todas as combinações das habilidades e itens, não mede o balanceamento de uma campanha e não substitui testes de turnos completos com todos os efeitos simultâneos. Efeitos secundários probabilísticos, todas as trocas de itens, todas as formas temporárias e sequências longas continuam exigindo casos adicionais.

## Reproduzir

Depois de preparar a árvore da integração e a biblioteca mGBA:

```sh
python3 tools/hoenn/validate_battle_interactions.py --source .local/hoenn-route12-src --library .local/mgba-bridge.so --output .local/battle-interactions-release/common/battle-interactions
python3 tools/hoenn/verify_battle_interactions.py --manifest mods/hoenn/versions/versions.json --reports mods/hoenn/battle-interactions-validation
python3 -m unittest discover -s tools/hoenn -p test_battle_interactions.py -v
```

Para cada edição, o `--source` deve usar a ROM variante e o ELF da mesma compilação. Os estados preparados são declarados nos relatórios.
