# Porto de Pallet

O mar se estende para a direita e se une ao canal onde fica o barco pequeno.
A antiga ponte horizontal mantém seus oito tiles, com uma extensão que une
as duas passarelas. O barco pequeno mantém o sprite e foi deslocado um tile
para a direita. A passarela sobre a água leva ao novo terminal, colocado dois
tiles abaixo da antiga casa. A faixa de água acima do prédio foi reduzida em um tile durante a revisão.

![Exterior atual](images/pallet-harbor/PalletTown_Frlg.png)

O exterior usa os tiles originais do terminal de Slateport, com telhado laranja.
O interior tem um S.S. Tidal de 96×40 pixels, permanentemente visível, com colisão
em todo o casco sobre a água. O capitão interno atende o destino estável `18`
da rede geral; as viagens para Pallet desembarcam dentro do terminal.
O barqueiro externo foi removido.

![Interior com navio](images/pallet-harbor/JourneyPalletHarbor.png)

O mapa ganhou nove fileiras ao sul e duas colunas a leste para acomodar o
terminal e árvores completas. A borda de pedra continua acima do telhado e
o contorno novo é fechado com árvores inteiras, sem copas recortadas.
O laboratório e os acessos nativos da cidade foram preservados. O canal continua navegável até
a Rota 21, com as posições do atlas contínuas na transição. O antigo interior
da casa permanece registrado para que seu warp de saída continue válido.

## Reprodução e evidência

A camada `pallet-harbor` é aplicada depois de `sootopolis-harbor`. Com o ambiente
GCC ARM e mGBA preparado, use o checkout existente:

```sh
python3 tools/hoenn/build_integration_candidate.py --source .local/sootopolis-src --jobs 4
python3 tools/hoenn/render_pallet_harbor.py --source .local/sootopolis-src --output docs/images/pallet-harbor
python3 tools/hoenn/validate_pallet_harbor.py --source .local/sootopolis-src --library .local/mgba-bridge.so --output mods/hoenn/pallet-harbor-validation/validation
```

Os testes físicos verificam a ponte original, a caminhada até a porta, entrada
e saída, colisão do navio, conversa com o capitão interno, viagem
Pallet ↔ Lavender, Surf entre as duas partes da baía e até a Rota 21 e de volta.
Também são conferidas a ausência do barqueiro externo, a união andável das
passarelas, a nova posição do barco e as árvores completas com colisão.
A posição inicial e o estado inicial da história são fixtures; os percursos usam comandos do controle.
Não se afirma uma campanha completa.

As quatro edições recebem relatórios próprios, junto com novos testes do porto
de Sootopolis e dos encontros especiais. As provas costeiras mais antigas
permanecem vinculadas às ROMs de origem. A validação do navegador precisa ser
refeita com os novos hashes antes de preparar o Pages:

```sh
python3 tools/hoenn/publish_sootopolis_update.py --source .local/sootopolis-src --validation mods/hoenn/sootopolis-harbor-validation --pallet-validation mods/hoenn/pallet-harbor-validation --output mods/hoenn/versions
python3 tools/sea_routes/serve.py --port 8770
# Em outro terminal:
node tools/hoenn/validate_versions_browser.cjs
python3 tools/hoenn/stage_pages.py --output /tmp/player-site
```
