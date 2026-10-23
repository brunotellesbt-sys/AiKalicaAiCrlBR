# Tiles nativos reutilizáveis

Catálogo local com recortes dos tiles reais da camada 162. As imagens são renderizações do source, sem NPCs; não são capturas da ROM.

[Catálogo visual](catalogo-visual.png) · [Dados completos](catalogo.json) · [Guia de ajustes](../../docs/AJUSTES-GBA.txt)

Os nomes separam **Emerald** de **FRLG**. IDs, paletas, altura e comportamento pertencem ao tileset indicado, não são universais. `catalogo.json` contém mapa doador, coordenadas, oito referências gráficas por metatile e hashes.

`native/` conserva os gráficos 8×8 indexados `.4bpp`, as paletas `.pal` e os frames nativos usados. Cada referência aponta para seu arquivo correto. `source.png` é um preview RGB; para implementar, use os dados indexados e preserve atributos, flips e callbacks. Os arquivos de animação declaram slot inicial e quantidade de gráficos no catálogo.

Uma **peça de contorno** precisa ser combinada com topo, corpo, pé e vizinhos correspondentes. `objeto-inteiro` identifica árvores e montanhas exportadas com toda a sua composição. A entrada de Rusturf é um encaixe numa montanha contínua, não uma caverna isolada completa.

Nas pastas `animacao/`, os PNGs mostram o ciclo dos gráficos nativos. Emerald é amostrado a cada 16 ticks; FRLG a cada 8, conservando a relação 16/8 entre água e espuma. Copiar `source.png` para outro slot não copia o callback de animação. O novo banco privado animado de Dewford, na camada 163, é tratado pelos helpers e provas específicos dessa camada; este catálogo conserva o doador 162.

## Exemplos

| Nome | Formato | Tipo | Doador (x,y,w,h) | Imagem |
|---|---|---|---|---|
| Grama baixa | emerald | peca | Route116 [14, 2, 1, 1] | [PNG](emerald/grama/grama-baixa/source.png) |
| Árvore isolada inteira 2×3 | emerald | objeto-inteiro | Route116 [0, 13, 2, 3] | [PNG](emerald/arvores/arvore-isolada-inteira-2x3/source.png) |
| Areia seca | emerald | peca | Route106 [51, 12, 1, 1] | [PNG](emerald/areia/areia-seca/source.png) |
| Mar aberto | emerald | peca | Route106 [3, 3, 1, 1] | [PNG](emerald/praias/mar-aberto/source.png) |
| Grama baixa | frlg | peca | SixIsland_Frlg [8, 3, 1, 1] | [PNG](frlg/grama/grama-baixa/source.png) |
| Árvore isolada inteira 2×3 | frlg | objeto-inteiro | SixIsland_Frlg [13, 14, 2, 3] | [PNG](frlg/arvores/arvore-isolada-inteira-2x3/source.png) |
| Areia de praia | frlg | peca | Route20_Frlg [23, 5, 1, 1] | [PNG](frlg/areia/areia-de-praia/source.png) |
| Ilha de areia com contorno fechado | frlg | conjunto-inteiro | Route20_Frlg [20, 3, 9, 7] | [PNG](frlg/praias/ilha-de-areia-contorno-fechado/source.png) |
| Caverna marinha: montanha inteira 11×9 | frlg | objeto-inteiro | Route20_Frlg [67, 6, 11, 9] | [PNG](frlg/cavernas/caverna-marinha-montanha-inteira-11x9/source.png) |
| Entrada na encosta: encaixe de Rusturf | emerald | encaixe-em-montanha-continua | Route116 [46, 7, 3, 2] | [PNG](emerald/cavernas/entrada-na-encosta-rusturf/source.png) |
| Face oeste com água | frlg | peca-composta | SevenIsland_Frlg [1, 10, 2, 1] | [PNG](frlg/encostas/face-oeste-com-agua/source.png) |
| Pé sudoeste com água | frlg | canto-completo | SevenIsland_Frlg [1, 12, 2, 2] | [PNG](frlg/encostas/pe-sudoeste-com-agua/source.png) |
| Face sul com água | frlg | peca-composta | SevenIsland_Frlg [3, 12, 1, 2] | [PNG](frlg/encostas/face-sul-com-agua/source.png) |
| Canto interno: sul para oeste | frlg | canto-completo | SevenIsland_Frlg [5, 12, 2, 2] | [PNG](frlg/encostas/canto-interno-sul-oeste/source.png) |
| Montanha com topo, faces e cantos | frlg | objeto-inteiro | Route20_Frlg [67, 6, 11, 9] | [PNG](frlg/encostas/montanha-com-topo-faces-e-cantos/source.png) |
| Canto externo noroeste | emerald | peca-de-contorno | DewfordTown [14, 10, 1, 1] | [PNG](emerald/praias/canto-externo-noroeste/source.png) |
| Praia reta norte | emerald | peca-de-contorno | DewfordTown [15, 10, 1, 1] | [PNG](emerald/praias/reta-norte/source.png) |
| Canto externo nordeste | emerald | peca-de-contorno | JourneySootopolisSouthChannel [13, 14, 1, 1] | [PNG](emerald/praias/canto-externo-nordeste/source.png) |
| Praia reta oeste | emerald | peca-de-contorno | JourneySootopolisSouthChannel [8, 18, 1, 1] | [PNG](emerald/praias/reta-oeste/source.png) |
| Praia reta leste | emerald | peca-de-contorno | DewfordTown [11, 0, 1, 1] | [PNG](emerald/praias/reta-leste/source.png) |
| Canto externo sudoeste | emerald | peca-de-contorno | JourneySootopolisSouthChannel [7, 17, 1, 1] | [PNG](emerald/praias/canto-externo-sudoeste/source.png) |
| Praia reta sul | emerald | peca-de-contorno | JourneySootopolisSouthChannel [10, 20, 1, 1] | [PNG](emerald/praias/reta-sul/source.png) |
| Canto externo sudeste | emerald | peca-de-contorno | JourneySootopolisSouthChannel [15, 18, 1, 1] | [PNG](emerald/praias/canto-externo-sudeste/source.png) |
| Canto externo noroeste | frlg | peca-de-contorno | Route20_Frlg [22, 4, 1, 1] | [PNG](frlg/praias/canto-externo-noroeste/source.png) |
| Praia reta norte | frlg | peca-de-contorno | Route20_Frlg [23, 4, 1, 1] | [PNG](frlg/praias/reta-norte/source.png) |
| Canto externo nordeste | frlg | peca-de-contorno | Route20_Frlg [24, 4, 1, 1] | [PNG](frlg/praias/canto-externo-nordeste/source.png) |
| Praia reta oeste | frlg | peca-de-contorno | Route20_Frlg [21, 6, 1, 1] | [PNG](frlg/praias/reta-oeste/source.png) |
| Praia reta leste | frlg | peca-de-contorno | Route20_Frlg [45, 9, 1, 1] | [PNG](frlg/praias/reta-leste/source.png) |
| Canto externo sudoeste | frlg | peca-de-contorno | Route20_Frlg [21, 8, 1, 1] | [PNG](frlg/praias/canto-externo-sudoeste/source.png) |
| Praia reta sul | frlg | peca-de-contorno | Route20_Frlg [22, 8, 1, 1] | [PNG](frlg/praias/reta-sul/source.png) |
| Canto externo sudeste | frlg | peca-de-contorno | Route20_Frlg [26, 8, 1, 1] | [PNG](frlg/praias/canto-externo-sudeste/source.png) |
| Encaixe interno noroeste | frlg | peca-de-contorno | Route20_Frlg [22, 5, 1, 1] | [PNG](frlg/praias/canto-interno-noroeste/source.png) |
| Encaixe interno nordeste | frlg | peca-de-contorno | Route20_Frlg [24, 5, 1, 1] | [PNG](frlg/praias/canto-interno-nordeste/source.png) |

## Regerar e conferir

```bash
python3 tools/hoenn/catalog_common_tiles.py --source .local/sevii-integrated-src --output assets/tiles
python3 tools/hoenn/catalog_common_tiles.py --verify assets/tiles
```

Consulta curta, sem carregar o catálogo inteiro no contexto:

```bash
python3 tools/hoenn/catalog_common_tiles.py --find "arvore"
python3 tools/hoenn/catalog_common_tiles.py --find "frlg praia canto"
```

O exportador exige o SHA do snapshot doador e não modifica o source. A verificação local confere arquivos, hashes, dimensões, matrizes completas e variação dos frames, e recompõe cada preview usando somente os bytes GBA e paletas exportados. Isso não substitui testar colisão, portas, Surf e camadas no mapa destino.
