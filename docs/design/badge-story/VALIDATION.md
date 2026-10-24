# Contrato de publicação da camada 164

O publicador exige 26 provas da compilação final: uma auditoria de source e
cinco relatórios por edição, nas quatro ROMs normais e na TESTE. As provas
precisam declarar o SHA-256 correto, `passed: true`, execução nativa e ausência
de preflight. A lista literal e os schemas foram confrontados com as 26 provas
efetivamente executadas nas ROMs finais. Os 53 testes do contrato incluem
controles negativos que alteram resultados, itens, identidades, capturas e
referências históricas para confirmar sua rejeição.

| Prova | Cobertura exigida |
|---|---|
| `badge-story-source` | Lista literal de 50 arquivos, 32.240 hashes de source, reprodução, idempotência, ABI preservada e quatro sprites compilados com nove quadros inteiros de 20 pixels |
| `qualifier-event` | Eliminação no grupo, derrota na final e título: 2/3/3 batalhas reais, seis partidas registradas por tentativa, pontuação recalculada, cura, itens, EXP, retry, save e cinco cumprimentos externos |
| `rival-identities` | 12 contextos, 684 observações de treinadores, 300 de mapas, 12 da Rota 22 tardia, 24 controles Wally/Blue e quatro encontros por controles com fala, sprite, retrato e batalha |
| `badge-gates` | 40 permissões, 72 estados de grunts, oito guardas físicos, duas recusas, oito resultados nas Ligas e três no compartimento Galactic; limites 17/18 e 21/22 e distribuições mistas |
| `review-mode` | Encontros e abordagens normais nas quatro edições; ausência na TESTE; save de inspeção exportado pelo emulador |
| `cold-boot` | Abertura real com controles, título e novo jogo; Continue da TESTE com a bateria distribuída |

As posições iniciais, o progresso, a equipe e os seeds usados para tornar os
cenários reproduzíveis são fixtures declaradas. Relatórios distinguem chamadas
diretas às APIs compiladas, inspeções de tabelas e percursos ou batalhas com
controles. Uma imagem de source nunca conta como captura do emulador.
As equipes do jogador recebem atributos acelerados para concluir as batalhas;
o teste da berry também prepara HP baixo e status. Os resultados e a flag da
vitória são produzidos pelo jogo. A perda de dinheiro por derrota segue a
regra normal e continua explícita nos valores antes/depois.

O estado do evento e os resultados da competição não podem usar os registros
de PWT. A arena física é compartilhada, mas não seu controlador, seleção,
normalização de nível, BP, histórico ou restauração integral da equipe. A
validação também precisa observar os seis personagens na mesma escala e
os cinco cumprimentos fora dos prédios.
O consumo de um X Attack ocorre na Bag nativa; a berry é consumida em batalha
e reposta pelo evento. Uma troca real do Pokémon ativo verifica a reposição
por identidade, com HP, PP, status, itens e experiência observados a cada
entrada. As capturas atuais precisam ser PNGs de 240 × 160, com hashes corretos
e conteúdo visível; quadros uniformes ou quase totalmente pretos são rejeitados.

O baseline fixa byte por byte `versions.json`, `review.json` e `test.sav` da
camada 163. Os 284 relatórios principais históricos conservam seus hashes;
os 15 componentes nativos da camada 163 também permanecem. A verificação
histórica recebe explicitamente o review e o save fixados, sem consultar a
ROM TESTE nova para aprovar uma prova antiga.

Antes de substituir um download, o publicador confere as 26 provas e cada
componente, imagem ou vídeo referenciado. Ele rejeita provas de outra ROM,
capturas alteradas, caminhos externos, ciclos e publicações com contrato
inacabado. O ZIP guarda exatamente as quatro edições normais e fica abaixo de
100 MiB; a TESTE tem download separado, com link e SHA-256 dentro do pacote.
Capturas históricas ficam em um registro de hashes e URLs do commit anterior,
verificadas contra os bytes desse commit. As provas e capturas atuais são
incluídas, não substituídas por links históricos.

Os testes de boot e Continue descrevem o observado no mGBA e no navegador.
A causa específica da antiga tela azul no My Boy não foi reproduzida nesses
emuladores. Também não há alegação de uma nova campanha inteira jogada nem de
uma auditoria exaustiva de todas as interações de batalha.

## Verificação final da entrega

Após a publicação dos arquivos locais, passaram 453 testes de Hoenn, 12 de
rotas marítimas e 6 das ferramentas de CI. O player abriu as cinco ROMs no
mGBA do navegador e rejeitou manifestos inválidos, arquivos incompletos e uma
TESTE associada à edição normal errada. A preparação estática do Pages também
passou, com os hashes atuais. Isso valida a entrega para o fluxo de publicação;
o site público recebe os arquivos pelo workflow após o merge do PR.
