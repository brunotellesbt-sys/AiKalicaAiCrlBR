# Resgate de Sootopolis, Titan Cave e final Galactic

Depois de Rayquaza, fale com o capitão em Sootopolis. Ao recolher a jangada, Lugia protege o grupo, Articuno detém a água que atinge a embarcação, Zapdos ilumina a passagem entre os recifes e Moltres aquece os moradores resgatados por Luffy.

Com todos de volta ao porto, siga pela Rota 112 até a Wishstar Chamber na Fiery Path. Eren e Jirachi revelam os selos. A Titan Cave fica no mar perto de Three Island. Interaja com os guardiões das três muralhas e ajude Regigigas e Groudon a interromper os tremores. Na Gen 1–9 e na TESTE, Regieleki e Regidrago mostram as memórias de Reiner e Zeke como passos adicionais. As capturas seguem as regras das câmaras individuais.

O último ginásio de Hoenn é liberado no desembarque em Sootopolis. O final Galactic exige também o capítulo de Eren, a vitória na competição da Frontier, 22 insígnias e os doze encontros dos viajantes. Eren e Luffy retornam aos próprios mundos no navio. Quem já iniciou os combates da sala final pode continuar pelo save antigo. [Guia da campanha](../../../docs/historia-e-missoes.md)

## Patches

Aplique o BPS à ROM da mesma edição com a camada [Resgate de Sootopolis](../sootopolis-rescue/README.md).

| Edição | Patch |
| --- | --- |
| Gen 1–4 Normal | [BPS](Pokemon-Journey-Gen1-4-Normal-titans.bps) |
| Gen 1–4 Hard | [BPS](Pokemon-Journey-Gen1-4-Hard-titans.bps) |
| Gen 1–9 Normal | [BPS](Pokemon-Journey-Gen1-9-Normal-titans.bps) |
| Gen 1–9 Hard | [BPS](Pokemon-Journey-Gen1-9-Hard-titans.bps) |
| TESTE | [BPS](Pokemon-Journey-TESTE-titans.bps) |

## Reprodução e provas

Use `prepare_titan_story.py` sobre uma cópia privada da fonte após `sootopolis-rescue`. Compile e gere as edições com `package_versions.py` e `package_review_rom.py`. `verify_titan_story.py` reconstrói as cinco edições, verifica seus hashes e confere as provas correspondentes. [Manifesto](validation.json)

O percurso de teste usa controles no resgate, nas entradas e saídas das câmaras e nas interações com os Pokémon. Os pontos de partida, o progresso anterior e a vitória prévia do guarda do navio são preparados para testar a nova sequência. [Revisão dos mapas e do percurso](../../../docs/design/titan-story/README.md)
