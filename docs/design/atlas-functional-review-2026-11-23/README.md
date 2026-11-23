# Validação funcional da camada 172

A versão atual passou no mGBA nas cinco edições. Os encontros na areia
de sete ilhas permitiram restaurar 66 referências da Pokédex. Todas as
espécies permitidas pelas duas caps voltaram a ter pelo menos um local
na Pokédex nativa.

A validação por controles abrange 105 entradas e retornos de câmaras,
três capturas representativas, nove exteriores de cavernas, 109 peças
de rocha, 96 treinadores de Surf, 34 travessias costeiras, cinco
mergulhos, sete portos e 18 saves migrados. O save de inspeção da TESTE
continua em Mossdeep. Os cinco arquivos abriram no navegador com mGBA.

- [Contrato da versão](final-contract.json)
- [Provas da versão atual](../../../mods/hoenn/versions/evidence/atlas-surf-layout/)
- [Manifesto das edições](../../../mods/hoenn/versions/versions.json)

## Registro da compilação anterior

Retomada funcional da ROM em 23/11/2026. As histórias futuras permanecem guardadas.

As provas deste lote pertencem à ROM C
`d296428c98f989a815e24d9def5a51bfd284c50f1ca9831547cb42fb7ce8c0ce`
ou às cinco edições obtidas dela apenas pelos patches de perfil autorizados.
As ROMs públicas continuam V7, sem selo final.

Passaram na C: capturas reais de Giratina487 e Pecharunt1025 com SAVE/Continue,
barqueiro de Pacifidlog, circuito Surf de ThreeIsland, sete terminais com viagens
de ida/volta, desembarque/reembarque e14baterias reais em terra/Surf com cold Continue.
Nas cinco edições passaram uma batalha de treinador e o Continue preservando
a flag; naTESTE,600frames sem abordagem automática seguidos de batalha manual real.

A conferência nativa de todas as entradas AREA revelou um bloqueio real:
9espécies sem local naGen1–4 e36naGen1–9. As famílias terrestres estão declaradas,
mas algumas ilhas de areia não possuem gatilhos terrestres de encontro.
O reparo deve habilitar o encontro nativo somente nesses habitats e restaurar
linhas AREA com testemunhos reais. Não trocar a expectativa de cobertura por zero.
`editions/*/rules-census/native-Dex-diagnostic.json` preserva os resultados completos.

O teste histórico dos portos usava coordenadas antigas: OneIsland17,6 ficou
inadequado, enquanto o ponto atual20,6 permite caminhar da cidade ao terminal.
A balsa mundial retorna dentro do terminal; a tabela Seagallop possui outra
chegada exterior. O validador atual distingue os percursos, sem alterar a ROM.

`progress.json` registra resultados e pendências. Os JSONs grandes foram
comprimidos integralmente; PNGs e baterias conservam seus bytes originais.
As tabelas de perfil em`five-editions.json` usam cache temporário em/dev/shm;
podem ser reproduzidas da fonte C preservada com package_versions/package_review_rom.
Não compilar fontes congeladas enquanto leitores as usam. Uma ROM nova precisa
de provas novas vinculadas aos seus próprios hashes.
