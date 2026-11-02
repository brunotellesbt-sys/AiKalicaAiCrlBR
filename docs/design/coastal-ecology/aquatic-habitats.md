# Habitats aquáticos da camada 166

Esta revisão preenche lacunas reais nas rotas aquáticas e diversifica três
corredores de mar aberto. O inventário considera os comportamentos dos tiles,
colisões e conexões físicas; o desenho do mapa-múndi permanece igual.

O inventário cobre 434 mapas com superfícies aquáticas, incluindo 55 exceções
explicitadas. O preparo de encontros abrange 379 mapas: 335 de mar aberto, 18 costas de cidades, 14 rios e
12 áreas subaquáticas. Antes desta camada, 307 desses mapas não tinham tabela
nativa de encontros na água; 278 sequer tinham um cabeçalho nativo de encontros.
Considerando também os pools próprios de famílias, havia 337 lacunas na edição
Gen1–4 e 312 na Gen1–9. Esses números medem entradas preparadas; a prova de que
os encontros realmente iniciam vem dos relatórios da ROM compilada.

[O inventário por mapa](aquatic-habitats.csv) registra as famílias das duas
edições e as lacunas anteriores. Mauville está incluída: os oito tiles de água
no canto sudeste continuam na água da Rota 118; não são uma fonte decorativa.
Rustboro também conserva encontros em sua costa.

| Corredor | Gen1–4 | Gen1–9 |
| --- | --- | --- |
| Mar norte de Hoenn | Tentacool / Tentacruel | Tentacool / Tentacruel |
| Mar central de Hoenn | Staryu / Starmie | Bruxish |
| Mar sul de Hoenn | Qwilfish | Wailmer / Wailord |

As famílias preservam seus habitats proprietários. Um corredor conectado pode
ampliar a lista de mapas do mesmo habitat, sem cadastrar a família novamente
com outro ID. Permanecem 212 famílias comuns na Gen1–4 e 424 na Gen1–9;
nenhuma família antes alcançável foi removida. Fósseis, lendários e espécies de
eventos continuam com suas regras próprias. As entradas terrestres, de Rock
Smash, ocultas, locais fixos da Pokédex e o workshop foram preservados. A nova
cobertura acrescenta 1.219 registros de localização na Pokédex e remove 13
indicações comuns que deixaram de corresponder às famílias dos três mares.
A remoção considera a geração e o mapa exatos; inclui as formas regionais da
família deslocada, como Wooper de Paldea. A família continua alcançável em seus
outros locais, e os registros fixos continuam intactos.

A tabela sozinha não resolve tiles que nunca verificavam encontros. O runtime
passa a consultar encontros em `MB_FAST_WATER` somente nas costas Sevii abertas;
nos cinco `JourneyDepth*`, em piso `MB_NORMAL`; e nas versões subaquáticas das
Rotas 105, 125, 127 e 129, em `MB_NO_SURFACING`. Os pisos comuns das rotas
subaquáticas originais continuam com o comportamento original. O teste por
mapa e tipo de terreno impede ativar encontros em pisos interiores ou nas
barreiras de água rápida de outros eventos.

Os locais [fora deste preenchimento](aquatic-exceptions.csv) são instalações
com regras próprias, interiores, águas de cavernas originais e protótipos sem
conexões de jogo. Suas tabelas anteriores continuam intactas: “exceção” não
significa que seus encontros existentes foram removidos. A ROM TESTE conserva
a supressão de encontros aleatórios e abordagens automáticas de treinadores.

A validação inclui preservação das tabelas anteriores, famílias e Pokédex,
leitura independente das tabelas compiladas, batalhas iniciadas por movimento
real nos controles e teste da supressão na TESTE. O
[censo compilado](../../../mods/hoenn/coastal-ecology-validation/common/census/coastal-ecology-census.json)
confirma os 379 mapas obrigatórios nos quatro períodos nativos, sem lacunas
de tabelas, famílias, pesca ou gatilhos de encontros.

As matrizes da
[Gen1–9](../../../mods/hoenn/coastal-ecology-validation/common/native/coastal-ecology-native.json)
e da [Gen1–4](../../../mods/hoenn/coastal-ecology-validation/Gen1-4-Normal/native/coastal-ecology-native.json)
iniciaram dez batalhas selvagens reais, com o menu visível, em costa Sevii,
mar aberto, rio, área subaquática nova e rota subaquática original. Foram
300 e 325 passos efetivos, respectivamente. Na
[TESTE](../../../mods/hoenn/coastal-ecology-validation/TESTE/native/coastal-ecology-review.json),
1.100 passos e 1.000 consultas nativas de encontro não iniciaram batalha;
pesca e Sweet Scent também conservaram a supressão. Os três relatórios
registram os SHA da ROM e do ELF finais, além dos hashes das capturas nativas.
