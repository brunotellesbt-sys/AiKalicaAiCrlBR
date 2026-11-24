# Revisão das cenas de Sootopolis e da Titan Cave

Os mapas da área do resgate, da Wishstar Chamber e da Titan Cave conservam o terreno, as conexões e as entradas originais. Os sprites novos usam posições conferidas na água ou no piso caminhável. As três aves aparecem uma por vez na cena de retorno da jangada. O exterior da Titan Cave foi comparado antes e depois.

| Mapa inteiro | Revisão na fonte |
| --- | --- |
| Área de resgate | [Antes](resgate-antes.png) · [Posições das aves](resgate-atores.png) |
| Wishstar Chamber | [Antes](wishstar-antes.png) · [Posições da cena](wishstar-atores.png) |
| Titan Cave | [Antes](titan-cave-antes.png) · [Posições dos guardiões](titan-cave-atores.png) |

As imagens de fonte mostram as posições previstas de todos os atores no mesmo mapa. As capturas do mGBA mostram a presença de cada ator durante sua cena. [Articuno](../../../mods/hoenn/titan-story/Pokemon-Journey-Gen1-9-Normal/articuno-with-lugia.png) · [Zapdos](../../../mods/hoenn/titan-story/Pokemon-Journey-Gen1-9-Normal/zapdos-with-lugia.png) · [Moltres](../../../mods/hoenn/titan-story/Pokemon-Journey-Gen1-9-Normal/moltres-with-lugia.png) · [Groudon e Regigigas](../../../mods/hoenn/titan-story/Pokemon-Journey-Gen1-9-Normal/regigigas-and-groudon.png)

O estado do resgate continua em `0x40E5`. A variável `0x409B` registra a investigação de Eren, as escolhas dos selos, o encontro com Groudon e a conclusão. O teste percorre o porto, faz o resgate por Surf, atravessa as duas entradas, recusa e aceita o selo de Maria, grava uma bateria na Titan Cave, testa o Continue e verifica a entrada física do navio. [Provas por edição](../../../mods/hoenn/titan-story/validation.json)
