# Revisão dos mapas inteiros

O [registro de cobertura](visual-review-coverage.json) associa cada um dos
414 mapas cujo terreno foi criado ou alterado a uma imagem inteira examinada.
Ele distingue a revisão da base da revisão dos arquivos corrigidos nesta
camada. A ROM final tem SHA-256
`b04918724939a54bbe3321d274953a9311ab8c7b4eebc3cbeb844ffcd3604386`.

Foram examinados os lotes de 337 mapas marinhos e de acesso, 33 mapas e
franjas das Sevii, 115 cavernas/interiores, 24 mapas de ginásios e eventos e
oito mapas complementares. Os conjuntos se sobrepõem; sua soma não representa
uma contagem de locais diferentes. O registro deduplica os 414 terrenos.

Os 32 arquivos de terreno corrigidos nesta camada têm imagens atuais com
proveniência completa. A rodada final examinou 44 mapas inteiros, incluindo
os vizinhos necessários para contextualizar portos e emendas:

- [Mar, Three Island e portos de contexto](marine/final/source-provenance.json):
  28 mapas, cinco pranchas.
- [Base Rocket, santuário Dimensões e fundos subaquáticos](caves/final/source-provenance.json):
  oito mapas, duas pranchas.
- [Mapas complementares](misc/final/source-provenance.json): oito mapas,
  duas pranchas.

Cada catálogo atual registra os hashes do mapa, do layout, do terreno, das
bases de tiles, das paletas, das definições e imagens de atores e do próprio
renderizador. O hash da imagem salva também é conferido. Isso evita aceitar
um PNG antigo apenas porque seu nome coincide com o mapa em revisão.

As rochas restauradas formam objetos inteiros de 2 × 2 tiles, conservando a
colisão e a altura de cada célula. A meia rocha da Rota 126 usa pedras pequenas
completas, mantendo a água livre abaixo. As três copas sob o ginásio de
Three Island terminam a floresta sem bloquear a entrada.

As mesas da base Rocket agora têm as quatro peças nativas. O santuário
Dimensões tem duas escadas completas e a encosta sul restaurada. Nos cinco
fundos subaquáticos, a face vertical antes repetida como chão foi substituída
por piso; as entradas têm arco, relevo, lados e cantos completos.

A imagem antiga que mostrava o porto de Navel Rock como oceano vazio foi
descartada como evidência. O render atual demonstra o porto completo, com o
mesmo layout de Birth Island; o teste nativo confirmou chegada, circulação e
retorno. Nenhuma alteração foi feita nesse porto por causa do PNG antigo.

Estas imagens são renderizações dos dados de origem, **não capturas do
emulador**. Elas não aprovam colisões, animação, estado de Surf ou eventos.
Essas verificações pertencem aos relatórios nativos vinculados à ROM final.
Sprites variáveis que o renderizador não resolve continuam identificados nos
catálogos, sem serem confundidos com defeitos de terreno.

Os outros mapas com somente eventos alterados e os 234 consumidores indiretos
de bancos/scripts estão no inventário geral. Este documento não declara que
901 mapas tiveram suas imagens examinadas individualmente.

Para produzir uma imagem nova com todos os insumos identificados:

```sh
python3 tools/hoenn/audit_generated_visual_provenance.py \
  --source .local/generated-world-audit-src \
  --maps ThreeIsland_Frlg,SixIsland_Frlg \
  --output .local/revisao-atual
```

A geração deixa `visually_inspected: false`. Esse campo só pode ser marcado
após abrir e examinar as imagens inteiras. A conformidade da fonte e os
testes de movimento permanecem verificações separadas.
