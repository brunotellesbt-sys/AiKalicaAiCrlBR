# Contrato final da camada 163

O contrato contém 31 provas atuais: uma auditoria compilada da origem e seis
provas para cada uma das quatro edições e a TESTE. Cada relatório precisa
declarar `passed: true` e o SHA-256 da ROM congelada correspondente. A publicação
valida as 31 provas e seus anexos antes de substituir qualquer download.

| Prova por edição | Verificações exigidas |
|---|---|
| `six-coastal-closures` | 65 células de Six e 12 de Water Path; 12 árvores completas; cinco portas; caminhos secos, colisões e duas voltas de Surf com retorno ao mesmo píer |
| `dewford-movement` | 29 antigas divisões invisíveis; quatro acessos às escadas; 22 tiles dos trilhos; portas, dois vendedores e três saves/Continue em terra, ponte alta e Surf |
| `affected-coast-connections` | Três componentes nativos vinculados à mesma ROM: sete portos integrados, 26 emendas oceânicas nos dois sentidos e identidade/GPS das sete rotas de costa |
| `shore-animation` | Quatro mapas em oito fases, seis conexões nos dois sentidos, dez observações do primeiro frame carregado e 44 capturas nativas |
| `review-mode` | Comportamento normal de treinadores nas quatro edições; ausência de encontros e abordagem automática na TESTE; exportação nativa do save distribuído |
| `cold-boot` | Boot real até título e novo jogo com controles; na TESTE, Continue com a bateria distribuída, sem escrever callbacks ou memória do jogo |

Os três componentes de conexões conservam seus próprios JSONs, capturas e
hashes. O componente dos píeres cobre sete portos e 25 emendas; o oceânico
cobre 26 emendas e 52 travessias; o de identidade cobre sete nomes `ISLAND
COAST`, 14 percursos centrais, 25 emendas, 50 travessias e 64 capturas da ROM.
Os caminhos ficam relativos ao wrapper: `connections/ports/`,
`connections/ocean/` e `route/route-identity.json`. O publicador aceita a saída
nativa de animação em `shore/shore-animation.json`; rejeita uma cópia plana
concorrente que torne a escolha ambígua.

A auditoria da origem usa uma lista literal independente de 24 arquivos e
confere 32.230 hashes, reprodução atômica, idempotência, ABI dos saves/link,
67 constantes de itens e a preservação dos ginásios e da arte do atlas. As
adições em `src/main.c` e `include/tileset_anims.h` permitem somente a chamada
após `ProcessDma3Requests()` e sua declaração pública. O auditor reconstrói
integralmente esses arquivos e os callbacks a partir do parent, rejeitando
alterações de menus, batalha, áudio, link, DMA ou animações de outros bancos.

A correção da animação marca uma atualização pendente ao carregar o banco
privado. Depois de concluir todas as requisições nativas de DMA, aplica uma
única vez a fase global atual à água, areia molhada e composições privadas.
O banco privado e o callback General são guardas obrigatórias. A prova nativa
observa o contador secundário inicial em zero, a fila de DMA e o primeiro
frame pronto: a atualização já precisa estar concluída, com a fase correta.
Também confronta os pixels de água e espuma ao longo das oito fases e exige
que terra, ponte e outras peças estáticas conservem os pixels.

O schema foi fechado após a auditoria compilada do parent
`cd5187f43d33b80e5ba2130c9e4e31a4d5a9a0e2504d8b71517da7d13814d9c6`
e a passagem nativa completa de animação na Gen 1–9 Normal
`34db0771f86b8c491830c80e4afbbac84eda72e1e765049e3529234d1af6ead1`.
As cinco edições passaram o mesmo teste completo de animação, totalizando
220 capturas nativas com hashes conferidos contra suas ROMs congeladas.
A revisão independente final confirmou as 31 provas atuais das cinco edições,
incluindo 46 relatórios JSON com seus componentes, 1.720 capturas PNG e um vídeo
nativo. Os 1.767 arquivos dessa cadeia tiveram seus hashes conferidos, com ROM
e ELF congelados preservados antes e depois da leitura. A publicação repete
essa verificação; uma prova de outra compilação falha mesmo que os mapas
pareçam iguais. A projeção OAM/VRAM é comparada aos pixels reais do jogador,
inclusive seus pés. Renderizações da origem ficam identificadas como tal.

As 42 provas da camada 162 permanecem históricas, com seus relatórios e hashes
originais. O baseline fixa `versions.json`, `review.json` e `test.sav` byte por
byte. O verificador 162 usa explicitamente esse review e save, preservando
também seu comportamento padrão para a entrega 162. Review relabelado e save
diferente são rejeitados. A campanha inteira e os recursos anteriores não
são declarados como novamente testados nas ROMs atuais.

O ZIP inclui exatamente as quatro ROMs normais, as provas atuais com seus
componentes e anexos, os 253 relatórios históricos, os 907 anexos originais
da camada 162 e os manifestos, reviews, saves e capturas de baseline
referenciados. Inclui também os 608 arquivos do catálogo `assets/tiles/`, o
guia `docs/AJUSTES-GBA.txt` e a documentação atual desta revisão. A TESTE fica
separada no repositório e no player: `TESTE-DOWNLOAD.md` registra o link e o
SHA-256, enquanto seu review, checksum e save acompanham o ZIP.

Quatro vídeos mais antigos ficam em `HISTORICAL-MEDIA.json`, com SHA-256 e URL
de commit conferidos contra os bytes originais. O pacote não representa uma
reprodução completa do histórico sem acesso ao repositório. O publicador
confere todos os hashes do ZIP, sua integridade e o limite de 100 MiB antes
de substituir o arquivo anterior. Os testes também rejeitam caminhos externos,
componentes corrompidos ou cíclicos, capturas duplicadas, provas de preflight e
qualquer relaxamento das guardas de atualização após DMA.
