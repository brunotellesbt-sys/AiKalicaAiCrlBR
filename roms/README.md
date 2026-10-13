# ROMs atuais

Esta pasta contém sempre as quatro edições GBA da entrega atual. Comece um **save novo**; saves anteriores à ampliação da Bag não são compatíveis.

| Edição | Download | IVs dos oponentes importantes |
|---|---|---|
| Gerações 1–4 Normal | [ROM GBA](Pokemon-Journey-Gen1-4-Normal.gba) | Originais/aleatórios |
| Gerações 1–4 Difícil | [ROM GBA](Pokemon-Journey-Gen1-4-Hard.gba) | 31 |
| Gerações 1–9 Normal | [ROM GBA](Pokemon-Journey-Gen1-9-Normal.gba) | Originais/aleatórios |
| Gerações 1–9 Difícil | [ROM GBA](Pokemon-Journey-Gen1-9-Hard.gba) | 31 |

As quatro edições incluem Kanto, Hoenn e Sevii. Megas e formas regionais de espécies até #493 permanecem nas edições 1–4. Ambas as dificuldades usam os EVs, builds e IA configurados para oponentes importantes. No PWT, todas as edições usam a otimização temporária de nature, EVs e IVs para ambas as equipes; seus golpes escolhidos permanecem e os dados originais voltam ao sair. Há torneios por geração e Copa global, com 162 personagens e arena própria.

[ZIP com as quatro ROMs e documentação](../mods/hoenn/versions/Pokemon-Journey-Four-Editions.zip) · [Documentação](../docs/README.md) · [Limites da validação](../mods/hoenn/INTEGRATION-STATUS.md) · [SHA-256](SHA256SUMS)

O manifesto desta atualização declara `validation_scope: pwt-update`: validação do PWT e integridade das quatro ROMs, sem afirmar que as campanhas completas foram testadas.

## Atualizar a entrega

Execute `tools/hoenn/seal_versions.py` com `--output mods/hoenn/versions` depois de compilar e produzir as evidências do novo build. Para uma atualização limitada ao PWT, use `--validation-scope pwt-update`, que exige as quatro inspeções de equipes, dois torneios completos, os sprites da arena, a desistência e a reprodução do código. O empacotamento atualiza automaticamente as quatro ROMs e os hashes nesta pasta. `tools/hoenn/verify_versions.py` e a CI recusam arquivos divergentes ou edições extras. O GitHub Pages utiliza as ROMs desta pasta após conferir seus hashes contra o manifesto validado.
