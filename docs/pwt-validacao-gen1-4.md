# PWT Gen 1–4 — validação e correções de batalha

Os resultados desta página pertencem à ROM do PR #79, preservada com seus hashes em `mods/hoenn/validation-baselines/pr79/`. A atualização costeira posterior valida os mapas e encontros alterados, sem repetir torneios ou afirmar nova validação completa destas mecânicas.

Os quatro torneios por geração foram concluídos nas edições Normal e Hard: oito torneios e 56 batalhas nativas, incluindo grupos e mata-mata. Cada torneio retornou à recepção, entregou 10 BP uma vez e restaurou a equipe original byte a byte.

| Edição | Geração | Batalhas | Relatório |
| --- | --- | ---: | --- |
| Normal | 1 | 7 | [JSON](../mods/hoenn/pwt-gen1-4-validation/Normal-gen1/pwt-generation-cup.json) |
| Normal | 2 | 7 | [JSON](../mods/hoenn/pwt-gen1-4-validation/Normal-gen2/pwt-generation-cup.json) |
| Normal | 3 | 7 | [JSON](../mods/hoenn/pwt-gen1-4-validation/Normal-gen3/pwt-generation-cup.json) |
| Normal | 4 | 7 | [JSON](../mods/hoenn/pwt-gen1-4-validation/Normal-gen4/pwt-generation-cup.json) |
| Hard | 1 | 7 | [JSON](../mods/hoenn/pwt-gen1-4-validation/Hard-gen1/pwt-generation-cup.json) |
| Hard | 2 | 7 | [JSON](../mods/hoenn/pwt-gen1-4-validation/Hard-gen2/pwt-generation-cup.json) |
| Hard | 3 | 8 | [JSON](../mods/hoenn/pwt-gen1-4-validation/Hard-gen3/pwt-generation-cup.json) |
| Hard | 4 | 7 | [JSON](../mods/hoenn/pwt-gen1-4-validation/Hard-gen4/pwt-generation-cup.json) |

Cada relatório identifica a SHA-256 da ROM testada, os adversários, a fase e o resultado. A validação usa mGBA com viagem, inscrição e equipe preparadas. HP, Ataque, Ataque Especial e Velocidade do jogador são aumentados somente na memória do emulador para testar o fluxo. As equipes inimigas, os resultados e a progressão executam no motor real. Isso não mede o equilíbrio de uma partida sem esses aumentos nem substitui uma campanha contínua.

## Correções

- Encore falha normalmente quando o alvo ainda não usou um golpe, sem consultar o sentinel 65535 como golpe válido. O mesmo cuidado protege a consulta de Shell Trap.
- Disable não pode selecionar um slot vazio; Sketch não pode copiar um golpe vazio e apagar seu slot.
- Mimic, Spite, Instruct, Copycat e Me First rejeitam históricos fora do catálogo antes de consultar seus dados. Slots inválidos ficam indisponíveis na seleção.
- A IA registra STAB ofensivo usando a potência do golpe real; golpes de status não são tratados como ataques por esse registro.

Os [65 cenários de regressão](../mods/hoenn/pwt-gen1-4-validation/move-restrictions.json) exercitam os comandos nativos: histórico vazio/inválido, aplicação e expiração de Disable/Encore/Torment, combinações com itens Choice, cópia de golpes, troca, Spite e consumo de PP com um ou dois adversários com Pressure. O teste adicional de [Encore](../mods/hoenn/pwt-gen1-4-validation/pwt-encore.json) cobre cinco cenários. O consumo de PP e as regras válidas de Torment já estavam corretos e foram preservados.

No torneio Gen 1 Normal, os PP foram esgotados deliberadamente em uma fixture. O motor selecionou Struggle e concluiu o torneio; a restauração devolveu os PP originais ao sair. O controlador de testes agora escolhe golpes considerando Disable, Encore, Torment, Taunt, Choice e PP, em vez de insistir no primeiro slot bloqueado.

## Mega Dimension

A auditoria atual verifica 1.571 espécies/formas, incluindo as 91 chaves de Mega da referência Pokémon Showdown congelada na revisão `942cda71d14bf0618bd57991708a2e2734b6daba`. Todas as formas Z-A/Mega Dimension dessa referência estão presentes e seus base stats coincidem; não houve faltantes. Exemplos: Raichu X/Y, Absol Z, Garchomp Z, Lucario Z, Heatran, Darkrai, Zeraora e Baxcalibur. Veja o [relatório dos atributos](../mods/hoenn/pwt-gen1-4-validation/species-stats.json) e o [índice de Mega Stones](itens-e-evolucoes.md).

As edições Gen 1–4 mantêm somente as Megas de espécies permitidas até #493. A auditoria de formas Pokémon é distinta da cobertura de treinadores de Legends Z-A no PWT, que continua pendente.

## Reproduzir

Com a árvore de 116 camadas preparada e a biblioteca mGBA do projeto:

```sh
python3 tools/hoenn/validate_move_restrictions.py --source .local/hoenn-route12-src --library .local/mgba-bridge.so --output .local/move-rules
python3 tools/hoenn/validate_pwt_encore.py --source .local/hoenn-route12-src --library .local/mgba-bridge.so --output .local/encore
python3 tools/hoenn/validate_pwt_generation_cup.py --source .local/pwt-validation-views/Gen1-4-Normal --library .local/mgba-bridge.so --output .local/gen1-normal --play-cup --cup-generation 1 --exhaust-pp-once
```

Para os demais sete torneios, selecione a árvore da edição, a geração 1–4 e omita `--exhaust-pp-once`. A árvore da edição deve usar a ROM variante e o ELF da mesma compilação. Os relatórios arquivados em `regression-before-fix` são falhas históricas de ROM/controlador e não são evidências de aprovação.
