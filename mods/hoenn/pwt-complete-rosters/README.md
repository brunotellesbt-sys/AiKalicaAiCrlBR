# Catálogo completo do PWT

O PWT tem **162 treinadores**. Esta revisão fecha as últimas 73 equipes, incluindo 21 de Paldea. As partidas são Singles de seis Pokémon no nível 50. A Gen 1–4 tem 61 adversários elegíveis e quatro copas regionais. A Gen 1–9 tem 162 adversários e nove copas regionais. Ambas incluem a Copa Mundial.

Os lotes anteriores cobriram 54 times do PWT oficial, 14 de Liga e 13 de Galar. Cinco equipes já tinham referências registradas de Platinum e três são de convidados do projeto. Para as 73 restantes, cada ficha registra a batalha de referência, os Pokémon usados pelo treinador e as escolhas que completam as seis vagas. Wally, por exemplo, usa como base a revanche da Battle Maison. Sua equipe Gen 1–4 usa Altaria, que ele já usa em outra batalha, na vaga de Talonflame. [Referências por treinador](../../../tools/hoenn/data/pwt-complete-roster-review.json)

Gladion usa Silvally do tipo Água com a Water Memory. O elenco segue com as mesmas identidades, e os treinadores compatíveis podem usar as Mega Evoluções de Legends Z-A. A Gen 1–4 permite 17 formas e a Gen 1–9 permite 49. As 45 pedras de Z-A continuam à venda em Ever Grande. [Uso das Megas](../pwt-galar-za-megas/README.md)

## Como jogar

Fale com o guia no saguão do Battle Dome e inscreva seis Pokémon no balcão da recepção do PWT. O torneio começa com uma fase de grupos e segue para o mata-mata. O título vale 10 BP nas copas regionais e 25 BP na Copa Mundial. Ao sair do torneio, você recebe sua equipe nas condições em que ela estava na inscrição.

Os patches abaixo são cumulativos para o PWT. Aplique o BPS à ROM da **mesma edição** gerada pelos patches do Atlas que contêm os cortes H, J e K. O player usa esses mesmos patches para reconstruir as cinco edições disponíveis em Play e Download. [Base do Atlas](../atlas-route-pruning/README.md) · [Player](https://brunotellesbt-sys.github.io/AiKalicaAiCrlBR/)

| Edição | Patch |
| --- | --- |
| Gen 1–4 Normal | [BPS](Pokemon-Journey-Gen1-4-Normal-pwt-complete.bps) |
| Gen 1–4 Hard | [BPS](Pokemon-Journey-Gen1-4-Hard-pwt-complete.bps) |
| Gen 1–9 Normal | [BPS](Pokemon-Journey-Gen1-9-Normal-pwt-complete.bps) |
| Gen 1–9 Hard | [BPS](Pokemon-Journey-Gen1-9-Hard-pwt-complete.bps) |
| TESTE | [BPS](Pokemon-Journey-TESTE-pwt-complete.bps) |

## Reprodução e verificação

O emulador conferiu 608 equipes ao somar as cinco edições e 2.736 interações de batalha nas quatro edições de jogo. Os testes chegaram ao título nas nove copas regionais e nas duas Copas Mundiais com atributos reforçados para percorrer todas as fases. Na rodada adicional sem reforço em Paldea Hard, a equipe avançou até o mata-mata, venceu quatro partidas e foi eliminada por Kieran. O jogo devolveu a equipe ao estado da inscrição.

A edição TESTE aceitou o save de inspeção existente e voltou ao ponto salvo em Mossdeep. As cinco ROMs abriram no mGBA do navegador com o mesmo hash dos downloads. [Raichu Mega X e Mega Y na mesma partida](Pokemon-Journey-Gen1-9-Hard-mega.png)

Em uma cópia privada da fonte que já contém a camada `pwt-galar-za-megas`, rode `python3 tools/hoenn/prepare_pwt_complete_rosters.py CAMINHO_DA_FONTE`. Compile e gere as edições com `package_versions.py` e `package_review_rom.py`. Use `python3 tools/hoenn/verify_pwt_complete_rosters.py` para reconstruir as cinco ROMs, conferir as equipes e verificar os relatórios nativos associados aos binários. Para validar a publicação local, use `run_versions_browser.py` e `stage_pages.py` com o Chromium do Playwright. [Manifesto com hashes](validation.json) · [Prova do navegador](../versions-validation/browser-pwt-complete/browser-versions.json)
