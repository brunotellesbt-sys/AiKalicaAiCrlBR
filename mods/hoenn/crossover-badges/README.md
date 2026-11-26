# Batalhas de Eren e Luffy por insígnias

São oito batalhas de estrada, quatro para cada personagem. O jogo conta insígnias de Hoenn, Kanto e dos ginásios extras. Eren aparece com 1, 5, 13 e 20 insígnias. Luffy aparece com 2, 7, 11 e 15. Vitórias antigas, inclusive em locais aposentados, valem para o mesmo personagem. [Tabela e direções](../../../docs/historia-e-missoes.md#eren-e-luffy)

A escada da Rota 108 leva ao encontro no convés. Os dois últimos locais são o Caminho Aquático da Ilha 6 e o oeste da Rota 123. As equipes finais de seis Pokémon usam a escala de cinco níveis abaixo a dois acima da média do jogador, limitada ao intervalo 1–100.

## Patches

Aplique o BPS sobre a mesma edição da camada [Titan Story](../titan-story/README.md).

| Edição | Patch |
| --- | --- |
| Gen 1–4 Normal | [BPS](Pokemon-Journey-Gen1-4-Normal-crossover.bps) |
| Gen 1–4 Hard | [BPS](Pokemon-Journey-Gen1-4-Hard-crossover.bps) |
| Gen 1–9 Normal | [BPS](Pokemon-Journey-Gen1-9-Normal-crossover.bps) |
| Gen 1–9 Hard | [BPS](Pokemon-Journey-Gen1-9-Hard-crossover.bps) |
| TESTE | [BPS](Pokemon-Journey-TESTE-crossover.bps) |

## Reprodução

Execute `prepare_crossover_badges.py` sobre a fonte privada da Titan Story. A validação executa as oito batalhas em cada edição da ROM e verifica cada rota com uma insígnia a menos. As insígnias, a viagem até as rotas e a equipe reforçada são preparadas para o teste. Cada vitória e seu registro resultam da batalha jogada. O teste em C cobre todas as combinações dos registros de vitória, e o mGBA confere as espécies e os níveis das duas equipes novas. [Manifesto e hashes](validation.json)
