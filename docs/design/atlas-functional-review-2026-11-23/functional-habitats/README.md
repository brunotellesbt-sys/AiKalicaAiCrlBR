# Reparo funcional de habitats terrestres

Compilação privada D: `5d42387c5ec934239fcdeeb2e030ef3f3d4b763030b38f49538e3eb02fdf6cab`. A fonte C foi preservada.

O predicado nativo habilita areia seca em altura3 somente nas sete ilhas
com famílias terrestres já declaradas. Não altera terreno, colisões, altura,
pools, regras de geração ou arte do atlas. StandardWildEncounter e Sweet Scent
compartilham a guarda. O censo alcançável restaura66referências AREA;1044linhas
são realocadas e apenas6linhas historicamente ineficazes ficam removidas.

Passaram nas sete ilhas: caminhada por controles, encontro nativo de espécie
do pool real, fuga pelo menu, retorno a pé e SAVE/coldContinue ao final. Uma
fuga recusada foi tratada com nova tentativa por controles, sem escrever na batalha.
As consultas nativas das1025espécies encontraram zero lacunas em ambas as caps.
A matriz de regras foi ampliada para auditar também os novos pools terrestres.

Ainda faltam a conclusão das matrizes nativas da D, cinco edições, contratos
finais, publicação, browser e suíte completa. Nenhum selo foi alterado; as
ROMs públicas continuam no checkpoint V7. Não promover provas da C como da D.

O delta deve ser aplicado sobre o snapshot autenticado C, não sobre uma fonte
original. A preparação reproduz C independentemente antes de compor o reparo.
Arquivos alterados: include/journey_atlas_ecology.h, src/journey_atlas_ecology.c, src/wild_encounter.c, src/data/journey_world_dex_locations.h.
