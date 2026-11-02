# Água contínua de Kanto e Sevii; animação nativa de Hoenn

Nos bancos FRLG, a mesma água animada (`454/455`) usava a paleta 6 sob
praias, encostas e pedras, mas a paleta 4 no mar adjacente. Isso causava um
retângulo de outra cor ao redor dos píeres. A correção usa a paleta 4
somente nas quatro peças inferiores desses metatiles; conserva as peças
superiores dos objetos, os flips, as colisões, os comportamentos e a animação.

A revisão abrange 28 mapas de Sevii e 15 mapas marinhos de Kanto. Dez costas
nativas de Sevii e as quinze de Kanto recebem referências a bancos privados
compatíveis. Quatro bancos secundários privados de Kanto conservam os
originais de Cinnabar, Pallet, Lavender e Vermilion. Os mapas de água doce
listados em `coastal_ecology_kanto_sea.py` conservam seus bancos originais.
São 498 palavras de água corrigidas: 338 nas sete tabelas de Sevii e 160 nas
quatro tabelas secundárias novas de Kanto. Nenhuma geometria é redesenhada
por esse reparo de paletas.

Os vídeos `Screenrecorder-20261028-155423.mp4` e
`Screenrecorder-20261028-155440.mp4` mostram Mossdeep e o mar externo.
A investigação distingue esse caso: ambos carregam os mesmos bancos
`General/Mossdeep`, e os oito quadros originais do oceano Emerald incluem
ondas diagonais e quadros pontilhados. O censo de Hoenn verifica os usos
reais da água nas camadas inferiores; o teste nativo verifica os oito quadros
carregados na VRAM e pixels visíveis, além de atravessar a conexão de Surf
nos dois sentidos, observando o contador de animação em cada frame da
travessia para detectar reinício do mar na emenda. Não se troca a arte ou o relógio de animação nativo para
esconder uma fase normal do mar.

A prova final `common/ocean-palette/coastal-ocean-palette.json` deve corresponder ao
SHA da ROM e ao ELF finais. Ela reúne 43 câmeras carregadas na ROM, as onze
tabelas compiladas, oito pares de pixels simultâneos na baía de Treasure
Beach e a verificação nativa de Mossdeep. Capturas de source são identificadas
como tal e usadas somente para revisar os mapas inteiros; não substituem as
provas do emulador.

## Resultado na ROM final

ROM: `f7af65b4856e6697d5d972f48f8699c7c6b7d4b277ea19cfa3949926265d1b89`.
ELF: `3f8ba485b37d17f58f7c7a5a64b1a8dd28492a9ea612afdead2487ceef3d1f9e`.

A prova passou: 43 mapas, onze tabelas, oito compatibilidades de cabeçalhos,
25 referências de costas nativas e 61 capturas reais. Em Treasure Beach,
oito pares de amostras simultâneas da baía e do oceano têm RGB idêntico.
Em Hoenn, 85 mapas usam a paleta esperada; os oito quadros originais aparecem
na VRAM e nos pixels visíveis. O Surf cruza Mossdeep ↔ mar externo nas
coordenadas previstas e o contador de animação continua sem reiniciar em
ambas as conexões.

- `native-ocean-phases.png`: montagem identificada de capturas reais das duas
  regiões e das travessias; `native-review.json` contém os hashes.
- `before-source/`: os mesmos 43 mapas reais da camada 165 imutável, com
  os defeitos anteriores preservados para comparação e rótulo de baseline.
- `whole-source/`: 43 mapas finais inteiros com oito folhas de contato inspecionadas;
  `source-provenance.json` registra os arquivos de entrada e seus hashes.
  O seletor variável de Deoxys em Birth Island depende do script nativo e é
  declarado como tal; a captura correspondente da ROM também está na prova.

Para repetir a prova na mesma versão congelada:

```sh
python3 tools/hoenn/validate_coastal_ocean_palette.py \
  --source .local/coastal-ecology-final-src \
  --library .local/mgba-review.so \
  --output mods/hoenn/coastal-ecology-validation/common/ocean-palette
```

Não execute esse comando enquanto houver compilação ou regeneração do mesmo
source. Uma nova ROM exige nova prova e novos hashes; uma montagem anterior
não valida a versão seguinte.

O ápice de Birth Island e sua área bloqueada de 3 × 3 tiles já existem no
upstream e na camada 165. O evento original faz Deoxys aparecer ali e descer
sete passos por movimento de script; esse ponto não é um destino de caminhada
do jogador. A revisão não troca o banco 67 original nem altera esse evento.
