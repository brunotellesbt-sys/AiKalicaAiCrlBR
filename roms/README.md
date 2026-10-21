# ROMs atuais

Atualização atual: [terminais ligados às pontes, retorno do Surf, Six Island e Dewford](../docs/sevii-integrated-piers.md), incluindo a abertura da TESTE com e sem o save de inspeção. Mantém o [circuito de 24 insígnias](../docs/ginasios-extras-e-travessias.md), Dewford com dois atendentes e o novo sprite do Luffy.

Inclui [casas e feira de Mega Stones em Ever Grande](../docs/ever-grande-market.md), dois presentes únicos e Sootopolis com marcador vermelho. Inclui as formas Origin do PR #93, o mercado competitivo no exterior da Battle Frontier e o Hyper Training em Dewford.

Inclui a [correção do rio de Fallarbor](../docs/fallarbor-river.md): praia caminhável, margens completas e desembarque para a cidade.
[Mercado da Battle Frontier e Hyper Training de Dewford](../docs/vendinha-dewford.md): um vendedor de itens na praça externa da Frontier e treinamento em Dewford.

Esta pasta contém sempre as quatro edições GBA da entrega atual. Comece um **save novo**; saves anteriores à ampliação da Bag não são compatíveis.

| Edição | Download | IVs dos oponentes importantes |
|---|---|---|
| Gerações 1–4 Normal | [ROM GBA](Pokemon-Journey-Gen1-4-Normal.gba) | Originais/aleatórios |
| Gerações 1–4 Difícil | [ROM GBA](Pokemon-Journey-Gen1-4-Hard.gba) | 31 |
| Gerações 1–9 Normal | [ROM GBA](Pokemon-Journey-Gen1-9-Normal.gba) | Originais/aleatórios |
| Gerações 1–9 Difícil | [ROM GBA](Pokemon-Journey-Gen1-9-Hard.gba) | 31 |

As quatro edições incluem Kanto, Hoenn e Sevii. Megas e formas regionais de espécies até #493 permanecem nas edições 1–4. Ambas as dificuldades usam os EVs, builds e IA configurados para oponentes importantes. No PWT, todas as edições usam a otimização temporária de nature, EVs e IVs para ambas as equipes; seus golpes escolhidos permanecem e os dados originais voltam ao sair. Há torneios por geração e Copa global, com 162 personagens e arena própria.

[ZIP com as quatro ROMs e documentação](../mods/hoenn/versions/Pokemon-Journey-Four-Editions.zip) · [Documentação](../docs/README.md) · [Limites da validação](../mods/hoenn/INTEGRATION-STATUS.md) · [SHA-256](SHA256SUMS)

A entrega atual inclui a revisão de Surf, [105 espécies especiais em 48 câmaras nomeadas](../docs/cavernas-lendarias.md) e acesso à Artisan Cave. [Mapa e imagens](../docs/revisao-surf-cavernas.md). A [ROM de teste e o save de inspeção](rom-de-teste/LEIA-ME.md) ficam em pasta separada, sem encontros aleatórios ou abordagem automática. O manifesto atual usa `validation_scope: sevii-integrated-piers`; as evidências de campanha e recursos anteriores continuam associadas às suas ROMs históricas.

## Atualizar a entrega

Para esta entrega, siga os validadores e a publicação descritos na [revisão dos terminais integrados](../docs/sevii-integrated-piers.md). O manifesto exige as cinco ROMs atuais e conserva a validação anterior com seus hashes originais.

Para outras entregas, execute `tools/hoenn/seal_versions.py` com `--output mods/hoenn/versions` depois de compilar e produzir as evidências do novo build. Para uma atualização limitada ao PWT, use `--validation-scope pwt-update`, que exige as quatro inspeções de equipes, dois torneios completos, os sprites da arena, a desistência e a reprodução do código. O empacotamento atualiza automaticamente as quatro ROMs e os hashes nesta pasta. `tools/hoenn/verify_versions.py` e a CI recusam arquivos divergentes ou edições extras. O GitHub Pages utiliza as ROMs desta pasta após conferir seus hashes contra o manifesto validado.

Esta atualização inclui o laboratório de formas na Torre de Lavender, encontros dedicados e fósseis. [Locais e métodos](../docs/encontros-especiais-e-formas.md) · [Balanceamento do PWT](../docs/pwt-balanceamento.md).

Os oito ginásios extras possuem quatro treinadores e passagens obrigatórias pelos seus campos de visão nas edições normais. O player oferece as quatro edições e **TESTE**, com download e save próprios. A TESTE mantém os mesmos mapas, portos e ginásios, sem encontros selvagens ou abordagens automáticas.
