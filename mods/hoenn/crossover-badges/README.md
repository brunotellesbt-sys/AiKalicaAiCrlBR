# Batalhas de Eren e Luffy por insígnias

Os encontros de cada região seguem seis marcos, da primeira à sexta insígnia local. Kanto e Hoenn têm progressões independentes. Ao voltar para completar encontros pendentes, o jogador encontra primeiro o adversário da etapa mais antiga. As vitórias já registradas no save seguem válidas. [Tabela de batalhas](../../../docs/historia-e-missoes.md#eren-e-luffy)

Na Rota 108, Luffy aborda o jogador após a subida pelas escadas para o convés do Navio Abandonado. O encontro usa o registro de vitória que a Rota 108 já tinha nos saves anteriores. [Entrada testada no mGBA](route108-entry.json)

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

Execute `prepare_crossover_badges.py` sobre a fonte privada da Titan Story. A validação executa as doze batalhas em cada edição da ROM e verifica cada rota com uma insígnia a menos. As insígnias, a viagem até as rotas e a equipe reforçada são preparadas para o teste. Cada vitória e seu registro resultam da batalha jogada. O teste em C também cobre todas as combinações de vitórias em saves anteriores. [Manifesto e hashes](validation.json)
