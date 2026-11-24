# Revisão de equipes do PWT

Este lote revisa 68 adversários. A edição Gen 1–9 usa 54 equipes do PWT de Black 2 e White 2 e 14 equipes de revanche de Liga. As 48 equipes elegíveis na Gen 1–4 têm uma composição própria que preserva os Pokémon disponíveis e completa as vagas com escolhas do personagem ou da sua especialidade.

As referências seguem a Champions Tournament, a World Leaders Tournament e as copas regionais. Para os 14 treinadores sem registro no PWT, o lote usa as revanches de Liga de Let's Go, HeartGold e SoulSilver, Omega Ruby e Alpha Sapphire e do Challenge Mode de Black 2 e White 2. As decisões, URLs e hashes das páginas consultadas constam no [inventário das equipes](../../../tools/hoenn/data/pwt-official-party-review.json).

- **Glacia, Gen 1–4.** Mamoswine e Sealeo ocupam as vagas de Beartic e Vanilluxe. Sua equipe fica com um Glalie.
- **Shauntal, Gen 1–9.** A revanche no Challenge Mode tem Gengar e um único Drifblim.
- **Agatha.** Os dois Gengar pertencem à revanche de Let's Go. A Gen 1–9 usa Marowak de Alola e a Gen 1–4 usa Haunter, que Agatha já usa em jogos de Kanto.

O levantamento cobre a composição das equipes. Golpes, itens, habilidades e atributos seguem a preparação competitiva do Journey no nível 50.

## Como jogar esta revisão

Aplique o patch BPS sobre a ROM de mesmo nome que já contém os cortes **H, J e K**. Essa ROM-base pode ser obtida no [player atual](https://brunotellesbt-sys.github.io/AiKalicaAiCrlBR/) ou reconstruída com o [patch do Atlas](../atlas-route-pruning/README.md). Os hashes de entrada e da ROM resultante constam em `validation.json`.

| Edição | Patch |
| --- | --- |
| Gen 1–4 Normal | [BPS](Pokemon-Journey-Gen1-4-Normal-pwt-review.bps) |
| Gen 1–4 Hard | [BPS](Pokemon-Journey-Gen1-4-Hard-pwt-review.bps) |
| Gen 1–9 Normal | [BPS](Pokemon-Journey-Gen1-9-Normal-pwt-review.bps) |
| Gen 1–9 Hard | [BPS](Pokemon-Journey-Gen1-9-Hard-pwt-review.bps) |

## Reprodução

Parta de uma cópia privada da fonte compilável com a camada `atlas-route-pruning`. Aplique `tools/hoenn/prepare_pwt_official_parties.py` nessa fonte, recompile e use `tools/hoenn/package_versions.py` para obter as quatro edições. Passe `--roster-review tools/hoenn/data/pwt-official-party-review.json` a `validate_pwt_world.py` para comparar os times gerados no emulador com as referências.

## Testes no emulador

- **PWT.** Os 446 times foram gerados e conferidos nas quatro edições. Cada partida usa seis Pokémon no nível 50. As copas de Kanto e Unova terminaram com título, 10 BP e restauração da equipe. O teste de percurso usou atributos reforçados. As partidas isoladas do Hard usaram equipes sem reforço.
- **Batalhas.** As quatro edições passaram por 2.736 verificações de regressão e 70 verificações novas, incluindo Sharpness, Punching Glove, Covert Cloak, Magic Room e Booster Energy com Protosynthesis e Quark Drive.
- **Menus.** Dipplin e Girafarig foram testados antes e depois de aprender o golpe exigido. Na Gen 1–9 Normal e Hard, a evolução, o consumo do Rare Candy e o recarregamento do save passaram. Na Gen 1–4 Normal, a pedra de evolução e o uso do mesmo TM em dois Pokémon também passaram.

`python3 tools/hoenn/verify_pwt_official_review.py` recompõe os quatro binários a partir dos patches e confere os hashes e os relatórios por edição. [Manifesto](validation.json)

## Trabalho restante

Das 94 entradas fora deste lote, cinco têm dados de Platinum já conferidos no repositório. Ash, Eren e Luffy são convidados com equipes próprias. A revisão seguinte cobre 13 revanches de Galar e o uso das Mega Evoluções de Legends Z-A pelo elenco existente. [Galar e Megas no PWT](../pwt-galar-za-megas/README.md)
