# Imagens das novas rotas marítimas

Imagens geradas diretamente dos mapas, blocos e tilesets da candidata
`407bd93bf4ee7e01878cdf3186a2a3a5b3d15f6954c8de6dcce942599ef9f3d9`.
São vistas completas do terreno de cada mapa. NPCs, sprites de objetos e
animações não fazem parte dessa exportação; não são capturas do PokéNav.
Os nomes na borda são os identificadores internos; as ligações vêm do JSON
real de cada mapa. A antiga passagem JourneyHoennCrossing está desativada
e foi excluída desta galeria.

## Cinnabar, rio da Rota 114, Rustboro e Dewford

![Passagem oeste Kanto–Hoenn](sea-map-gallery/oeste-kanto-hoenn.png)

Cinnabar liga ao novo mar ao sul; este chega ao rio da Rota 114, que continua
para a costa de Rustboro e, depois, para a costa de Dewford. As passagens
terrestres JourneyRustboroGate/JourneyDewfordGate desembarcam nas rotas
originais de Hoenn. O percurso completo anterior está em [OCEAN-JOURNEY.md](OCEAN-JOURNEY.md).

## Hoenn leste, Fuchsia e passagem para Pacifidlog

![Rotas do leste](sea-map-gallery/leste-hoenn-sevii.png)

O mar norte liga a Rota 125 à área marítima de Vermilion; o mar intermediário
liga a Rota 127 a Sevii 4; o mar sul liga a Rota 129 a Sevii 6. A passagem
para Pacifidlog liga a Rota 131 ao mar de Sevii 6. Fuchsia liga a Rota 19
ao mar de Vermilion. Há saídas Dive nas áreas profundas indicadas no terreno.

## Mares de Vermilion e Sevii

![Mares de Vermilion e das ilhas](sea-map-gallery/mar-sevii.png)

WorldSea00 é o mar de Vermilion. WorldSea01–07 dão acesso aos portos das
ilhas 1–7. WorldSea08/09 completam a borda leste e conectam Navel Rock e
Birth Island. Os canais abaixo unem as linhas do conjunto.

![Canais verticais de Sevii](sea-map-gallery/canais-sevii.png)

As áreas novas ainda usam ilhotas semelhantes entre si. A conectividade
foi implementada e testada em percursos anteriores; o acabamento visual e
variedade dos desenhos continuam pendentes. Estas imagens permitem revisar
o terreno existente, sem apresentar um desenho conceitual como mapa pronto.

## Reprodução

`python3 tools/hoenn/render_sea_maps.py --source <fonte-compilada> --output <pasta>`

A galeria inclui PNGs individuais em resolução de 16 pixels por tile,
pranchas reduzidas com nearest-neighbor e [metadados](sea-map-gallery/maps.json)
com dimensões, conexões, SHA-256 de cada mapa/blocos e da ROM candidata.
