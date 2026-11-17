PEDIDO ATUAL — “Resolva essas 103 peças suspeitas” —17/11/2026

Prioridade atual: concluir as103peças antes de retomar as cavernas/câmaras.
Fonte:103fragmentos em52grupos/20mapas corrigidos;0restantes e462rochas grandes
inteiras preservadas. Altura, colisão, eventos, warps, posições, conexões e
arte do atlas intactos. Encostas/praias recompostas e quartos isolados trocados
por pedras nativas inteiras18C/194. Um doador193 de vegetação foi rejeitado
na prévia, corrigido antes de compilar. Todos os doadores são autenticados
pelos oito words e vistos; nenhuma definição gráfica ou animação muda.

Quatro testes de fontePASS. Auditoria atualPASS,1SCC jogável e0água decorativa
alcançável. Versão5 atualiza apenas o fundo salvo de baterias4, uma só vez,
preservando posições/NPCs/flags. Antes/depois completos e52recortes revisados
emdocs/design/native-rock-fragments-review. Resumo e manifestohash em
docs/design/atlas-surf-layout/rocks103-checkpoint.json; imagens completas
ficam no repositório, sem alegação de replay offline pelo ZIP das quatro ROMs.

AINDA NÃO compilado este reparo103. Próximo: fonte privada nova, build/freeze,
verificação das103células/BG/VRAM/paleta no emulador, colisões por controles,
SAVE/Continue e cinco edições; atualizar PR112. Não editar fontes congeladas.

O lote anterior de bordas/96nadadores/7sprites foi compilado em fonte separada
.local/atlas-borders-swimmers-src, ainda sem provas nativas novas. ROM65f11271630f6e5b212d2dabc28bc48570c883aa12427692b07b788b1c4e5b5b;
ELFe958471761613f50618bab7e977d8e8a9105e86c7a48aab18045e2e73807ba98;
marker2e6c26d45681533fe69f1533bd95668d1186031638b64d95fd3362cbc96ae6f8.
34080inputs exatos;532ativos/606slots; versão4;33207700bytes ROM. Preservar.
Públicos aindaf2; C8 e baselines permanecem. PR112 aberto, sem merge.
Trabalhos anteriores de cavernas grandes/diversas,105câmaras e demais gates
continuam pendentes após esta prioridade explícita do usuário.

HISTÓRICO PRESERVADO:

BUILD PRIVADO EM PREPARAÇÃO —17/11/2026

Fonte nova materializada em.local/atlas-borders-swimmers-src:2191outputs,
34080inputs conferidos sem divergência.499mapas inteiros comNPCs renderizados;
contatos00..04 e20 inspecionados. O renderer usa quadro estático padrão e não
certifica orientação/abordagem nativa. Comando reproduzível:
render_atlas_surf_redesign.py --source <fonte> --output <fora-da-fonte>.

Erro novo reproduzido no make-j4: process_groups chamava clean_heal_locations
em paralelo; mesmo42destinos válidos reescreviam o mesmoJSON autenticado.
Uma corrida retirou a vírgula entreRoute4/Route10. O gerador agora só valida,
e exige reparo explícito se referência inválida. JSON original exato restaurado
na preparação parcial, sem alterar C8/171. Dois testesC++ com chamadas paralelas
PASS; geração de mapas/learnsets repetidaPASS e34080inputs continuam exatos.

Caches derivados antigos foram regeneravelmente liberados; apenas exports
privados reproduzíveis das5ediçõesC8 foram retirados após conferir seusSHA.
ROMrawC8/ELF/fontes/manifests/provas preservados. PNGs imutáveis iguais entre
snapshots antigos compartilham inode somente leitura, com todos caminhos e
bytes preservados. A fonte nova permanece independente para escrita.

Próximo: compilar/congelar esta fonte e testar pelos controles. Essa nova
reforma ainda não tem prova nativa nem publicação. Exteriores/câmaras/rochas
globais/DEX e demais pendências listadas abaixo continuam em trabalho.

HISTÓRICO PRESERVADO:

REFORMA EM ANDAMENTO —17/11/2026 — BORDAS, NADADORES E SPRITES NA FONTE

O pedido literal mais recente continua registrado abaixo; o usuário confirmou
“Ok?”. Preparação nova reproduzível em prepare_atlas_surf_redesign.py, sem
editar171/C8, preserva todos os antigos IDs e células passáveis.66.669células
de enchimento viram água real além das linhas de recifes. Primeira análise
porSCC omitia atalhos deEmerge(3538células); corrigido com auditoria dirigida
e guardaC deDive/Emerge baseada na tabela real de água decorativa. Fonte
finalPASS,1SCC jogável,0células decorativas alcançáveis; obrigações antigas
continuamPASS. Halo indefinido muda só desenho; colisão/altura/BorderId intactos.

96nadadores distribuídos na água jogável, com corredor3x6 e quatro orientações.
Flags novas compiladas contra macros/aliases antigos, sem ampliar save. Sete
estátuas restantes trocadas pelos próprios sprites nativos, com todos os
scripts/flags/IDs de captura intactos. Versão4 preserva migração3 e renova
templates só nos mapas alterados, com96resgates laterais para saves exatamente
sobre um novo treinador.339casos na suíteAtlas:337PASS na primeira execução; dois erros eram fixtures
históricos ausentes no sparsecheckout. Restaurados3arquivos exatos doHEAD,
os5testes desse módulo passaram, incluindo os dois.6testes de fundo/lookupC/
ABIARM e3de migração4PASS. Não são provas nativas da ROM.

Evidências emdocs/design/atlas-surf-layout/boundary-swimmers-review. Ainda
NÃO compilado na ROM; público seguef2 eC8 congelada é o checkpoint anterior.
Próximo: materializar fonte privada, renderizar mapas inteiros, compilar,
congelar e testar bordas/Emerge/câmeras/sprites/batalhas/saves pelos controles.
Continuam pendentes39faces nativas/Dive da troca visual de recifes, exteriores
grandes/variados e105câmaras com entradas próprias, pedras globais,261declarações
DEX,5edições/release/browser. PR112 aberto; não houve merge nem release final.

HISTÓRICO PRESERVADO:

RETOMADA —17/11/2026 — C8 TESTADA; NOVA REFORMA AUTORIZADA

Pedido literal atual do usuário:
“Ok vamos continuar os trabalhos, avance mais, verifique se tem mais coisas mal
feitas, até porque essa situação da pedra tem em outros lugares. Algumas massas
de terra em caves estão iguais, eu falei que queria aleatório como as outras
estão, e eu quero cavernas grandes, como as maiores dali, digo do lado de fora.
Sobre os lendários nas partes de dentro, gostaria que cada um deles tivesse uma
entrada e uma câmara dentro, no estilo dos lagos de pokemon platinum, só que
diversificado por dentro, cada caverna dessas tem mais de um lendário, então
deve ter uma entrada diferente pra cada câmara, certo? E dentro dessas câmaras,
o pokemon deve ter sua aparência, e não a de uma estátua. A propósito, nas rotas
de surf está faltando treinadores. Sobre as bordas de pedra, não precisa ser
amontoado de tudo ser pedra, basta as bordas limites de onde está a rota, o
resto deve ser água comum, do ambiente mesmo, só que bloqueadas de passar
devido as linhas de pedras.” Depois confirmou:“Ok?”

O usuário pediu abrir PR normal agora; PR112 aberto, sem merge:
https://github.com/brunotellesbt-sys/AiKalicaAiCrlBR/pull/112
A espera antiga pela release final para abrirPR foi substituída por esse pedido.
Objetivo original de validar/publicar aROM continua junto com as novas mudanças.

CHECKPOINT CONCLUÍDO, ANTES DA REFORMA NOVA
Fonte privada.local/atlas-unified-src congelada,532ativos/606slots/2180outputs.
ROMc8b38210ee63de35b7cb0e3a391626e603375f00e40b6280fd7ce8d30a4605b5;
ELFf0d58a150ecf0516b41ac8bf667855d20d232dc8ea022ca68cf678d86b0d2198;
marker400c392356c2db4ef3d60e0cccf280ba67116a28331ce27d50d3452809fb7f20.
34077inputs conferidos; manifesto7eb8c72a83cafd4b973ccf54fb2f36ec02ad451d9b32b57240462d058798a697.
Compilação33145420/33554432bytes(98,78%),409012livres. Não editar snapshots.
O primeiro erro de alinhamento ARM foi corrigido com RLEpacked6bytes e teste
real-mabi=apcs-gnu.322testes atlas PASS. Três cópias runtime532rows e quatro
arrays completos de migração conferidos byte a byte noROM/ELF compilados.
Fonte1SCC;34costas/18cavernas/5Dive/62testemunhas nativas/7portos PASS na fonte.

PROVAS NA MESMA ROMC8
Slateport8células/barreiras, pedra sul inteira/Route109 ida-volta PASS(11capturas).
CapitãoHouse3, ponte livre, porta, moradores/barco, ferryMossdeep ida-volta eSAVE
PASS(8capturas). ThreeSurf/terminal/recife/Coast/retorno/SAVE PASS(10capturas).
Birth saída/retorno/Harbor/madeira/avatar PASS. Quatro viagens reais deRoute12,
Treasure,Pacifidlog eBond às costas e de volta à origem seca PASS.
CincoDive do mundo verdadeiro, não probes isolados: mergulho, portal, santuário,
saída eEmerge aos donos físicos corretos PASS(5casos/25capturas). Rejeições de
Emerge em todos os limites ainda não cobertas por esse runner.
SaveTESTE público e save171 preservado: Continue→SAVE pelo menu→coldContinue
novamente PASS, sem segunda translação. Versão3 lida via offsetofARM+literal
GetVarPointer noELF, sem RAMwrites no coldboot. Não afirmar versão original
lida naROM171, apenas origem da bateria preservada e versão3 na saída.
Três saves produzidos por controles naROMe8(com a geometria533 publicada):
Sea000Surf inalterado,Sea004Surf aposentado,Scene002pé em terreno movido.
OldcoldContinue2→newContinue3→SAVE→newcoldContinue sem repetir migração PASS.
Inicialização de posição/versão/party nesses três casos é fixture declarada.
As cinco edições privadas C8 foram exportadas e todas passaram coldboot;TESTE
com save migrado e versão3 também PASS. Boot não certifica encontros/batalhas.

ECOLOGIA/DEX
Censo deC e gatilhos preservou190famílias493 e383famílias1025. Na componente
oceano há62/111famílias; todas as famílias das novas rotas têm testemunhas
alcançáveis. Campanha nativa fora desse grafo não foi revalidada integralmente.
O reparo deDEX bloqueia corretamente261declarações antigas de espécie/área
sem gatilho do proprietário esperado. Não são261espécies extintas: contagem
de famílias preservada não prova cada forma/área antiga. Falta atribuir donos/
substituições de área alcançáveis, sem esconder o bloqueio nem só apagar linhas.
Reprodutor novo diagnose_atlas_connected_ecology.py autentica freeze e produz
relatórios completos; não escreve fonte/ROM. Antes doDEX, donos das entradas
geométricas ordinárias são vinculados ao aliasC compilado, sem mover terreno.

REVISÃO E PRESERVAÇÃO
24mapas inteiros de fonte renderizados e contact sheet visto:6locais+18cavernas;
23comNPCs. Birth tem VAR_0 dinâmico não resolvido no renderer; arquivo dele está
explicitamente terrain-only, e a capturaROM existe separadamente. CapturasC8
deSlateport,House3 eDimensoes também vistas. Objetos/margens globais ainda
precisam da nova revisão pedida; não declarar todas as famílias de pedras limpas.
Provas, capturas, baterias, perfis,2180outputs exatos e freeze estão em
docs/design/atlas-surf-layout/unified-native-review. Baselines anteriores intactos.

O ambiente caiu por transporte exec-server. A causa de infraestrutura não foi
confirmada; o status do provedor chegou a dizer running enquanto comandos
falhavam. Recuperou. Antes da recuperação, o commit13cc14dbfc033f84a4f0b1113ec1569d84ad1363
preservou o reparo e runners pelaAPI. Após recuperar, backup tar+patch e stash
seletivo foram guardados, fetch/fast-forward aplicado, e os cinco arquivos
locais resultaram byte a byte MATCH com o commitAPI. Nada de reset/clean.
Boots/provas pendentes foram retomados e concluídos. O guia/estado/ZIP agora
recebem este checkpoint juntos. Dados locais não foram perdidos.

INCOMPLETO E PRÓXIMO
A reforma nova do usuário AINDA NÃO está naROMC8. Criar fonte privada nova;
não modificarC8 nem171. Ampliar/diversificar18exteriores, dar entrada própria
para cada câmara/lendário, preservar105scripts/flags de captura e referências,
usar sprite próprio comprovado, adicionar treinadoresSurf e auditar rochas.
Substituir enchimentos de recifes por linhas contínuas nos limites das rotas,
com água normal além delas e prova física de que o jogador não atravessa as
linhas. Água decorativa inacessível precisa classificação explícita no grafo,
resgates de saves e ecologia; não fingir colisão em tiles de água passável.
Muitos eventos atuais já declaram OBJ_EVENT_GFX_SPECIES; verificar pixels e
resolução de sprite naROM, pois isso sozinho não prova ausência de estátuas.
Câmaras separadas exigem warps/retornos, IDs, geração, flags eDEX coerentes.
A arte fixa do atlas permanece intacta. Expansões de chão precisam preservar
acessos e migração única de saves2 e3; salvos171/publicados continuam suportados.
Depois: fechar261pendênciasDEX, viagens/câmeras/tempos restantes, encontros/caps
nas5edições, verifier/publisher172, browser/Pages e publicação final.8FAIL+1ERROR
finais evalidated=false não foram burlados. ROMs/save públicos seguem anteriores.

HISTÓRICO PRESERVADO:

MIGRAÇÃO533 — IMPLEMENTAÇÃO GUARDADA, ANTES DO BUILD UNIFICADO

Ferramentas novas:atlas_surf_candidate_history.py autentica fixture+freeze e
reconstrói1932inputs do terreno publicado; atlas_surf_candidate_migration.py
emite RLE/targets e instala migração3 sem alterar a migração1/2 histórica.
Versões0/1 vão direto à geometria atual; versão2 usa a tradução533 uma vez;
versão3 é idempotente. Posição salva é autoridade; preserva seguidores,
18IDs de portal e sentinelas, reconstrói templates só em nativos com atores
movidos e limpa o mapView antigo. Nenhum avanço de missão é alterado.

Oito testes de C de restauração passaram: versões, quatro registros de warp,
posição de objeto desatualizada, modoSurf/pé, seguidores, IDs/sentinelas,
capitão salvo antigo e retornoidempotente. A primeira tabela conferiu388660
casos/194330células/18portais emC+terreno; esse ensaio NÃO prova bateriaROM.
A preparação final adiciona filtro obrigatório: todo destino também precisa
ter ida/volta física à componenteoceano, inclusive destinos a pé. O resultado
dessa preparação e o build unificado ainda serão executados após este checkpoint.

prepare_atlas_connected_layout.py somente aceita o diagnóstico fontePASS1SCC,
IDs estáveis, viagens autenticadas, reconstrução1932inputs, migração com
censo exaustivo e destinos seguros com saída física. Cria cópia privada nova,
sem overwrites de preparações antigas nem hardlinks. Não publica ROM nem
marca validação nativa/final. Os testes rejeitam fonte/provas alteradas,
destino já existente e tentativa de escolher resgate sem grafo físico.
321testes atlas PASS (log local journey-v3-source-tools-tests.log).

Próximo: preparar.local/atlas-unified-src pelo novo comando, auditar o filtro,
compilar/congelar e testar os saves antigos naROM3. Último remoto confirmado
e97a1239e8083ecc5142863c1fede57372f93795. Fix visual já está lá; cincoROMs
públicas/8FAIL+1ERROR/PR ainda dependem das provas finais do trabalho original.

ESTADO ANTERIOR PRESERVADO:

REVISÃO COMPLEMENTAR — 16/11/2026 — pedido literal: “Ainda tem uma aqui ó”

A captura mostrou a fatia horizontal sob a plataforma nordeste deSlateport,
que a primeira correção dequatrocélulas deixou passar. Corrigidas também
(35,17)/(36,17):055A/055B→0589, e(3,57)/(4,57):0552/0553→052C na praia.
São oito células no total, com os bits físicos originais intactos. Censo
completo dos24metatiles General que usam os gráficos de rocha grande cinza:
8fragmentos→0, três objetos completos preservados, inclusive a divisaRoute109.
Isso certifica essa família emSlateport; não declarar todas as famílias do jogo.

ROM privada completa3cf3b629f294ac6c40970986da50370dd1d38773ed94bd512c4067355048b9e8;
ELFf0acdd5c37db32a5ad70e6d8dc4d34d6797d2691f4ed2736da56915d860e4f43;
marker18a507a63d2cfb995cec34ffbd26a45535d77d25bbccc72d58f3e9d2fdcf40fd.
Source.local/atlas-harbor-complete-src congelado,533mapas/1959inputs. Provas
nativas por controles das8células/barreiras e divisaSul PASS,11capturas;
capitão/ferryida-volta/SAVE/novo bootContinueHouse3 PASS; Three eBirth refeitos
PASS nos mesmos bytes. Cincoedições3cf ainda não exportadas; não confundir
com boot5ediçõese8 anterior. Fonte antes/depois inteira e capturasROM/inputs/
hashes emdocs/design/atlas-surf-layout/slateport-complete-review.

REDE NOVA: quatro viagens ROMe8(rota12,Treasure,Pacifidlog,Bond) comprovam
água nativa→saída física real→retorno à origem seca. Cada uma usa só uma
colocação inicial declarada e progresso de história real; depois controles,
sem escrever terreno/warp. Os12pixels isolados correspondentes são glifos
de mapas nativos, autenticados porUI+COracle+word+33857hashes+viagens, não
rotas oceânicas duplicadas. IlhaScene002/treinador movida inteira dentro da
região original, sem perder IDs/eventos. MB_ROCK_STAIRS é caminhável no
motor nativo e no percursoBond, não warp; demais escadas direcionais bloqueadas.

PRÉVIA532mapas: sourcePASS,1SCC de água;34costas,18cavernas,5Dive,62testemunhas
nativas e7portos PASS na fonte. Ainda NÃO está numaROM compilada. Fonte/provas
emdocs/design/atlas-surf-layout/native-chart-connected-review. Reproduzir com
--additional-native-edges --native-travel-proofs <native-trips-e8>
--native-travel-source .local/atlas-harbor-fixes-src --preserve-candidate-ids.
IDs antigos preservados:459ativos mantêm slot,74aposentados viram placeholders
bloqueados,73novos anexados;606slots/532ativos. Antes de materializar, falta
migração versão3 das coordenadas/warps de saves da candidata533 publicada.
Fixture portátil do preparador533 b8bdb774… e freeze04ddaea4… permitem refazer
seu terreno exato;1932inputs de mapas/layouts conferidos sem divergência.
Não usar os23hashes de cavernas/Dive de uma prévia antiga como terreno dof2.

Públicos continuamf2cac1ec… evalidated=false.8FAIL+1ERROR ePR permanecem
pendentes até migração, build final, provas nativas/visuais/ecologia/saves,
5edições/browser e publicação. Último remotoe2a6f31c42521128116a4d4ed1cf1f11b4199309.
Próximo: migração533→532 antes de permitir materialização; não encerrar o
pedido original de ligar e validar aROM com este checkpoint parcial.

ESTADO ANTERIOR PRESERVADO:

# Aqui — LEIA PRIMEIRO: retomada técnica de Pokémon Journey

## Estado mais recente — 16/11/2026

Pedidos adicionais já corrigidos e testados na ROM privada: barqueiro da
ponte de Pacifidlog dentro da House3, a casa mais próxima; quatro células
com fatias de rocha na falésia de Slateport agora formam a face reta nativa.
Barqueiro conserva serviço/ID4; barco conservaID5, moradores/warps preservados.
Ponte/porta/capitão/ferryMossdeep/volta/SAVE/novoContinue dentro da casa PASS.
Capturas e colisões das duas encostas PASS; mapas inteiros fonte revisados.
Three/Birth refeitos na ROMe8e0ae3d… PASS; cinco edições privadas bootadas,
TESTE com save.302atlasPASS. Provas e fonte preparada1959arquivos:
[harbor-native-review](../docs/design/atlas-surf-layout/harbor-native-review/review.json).
Detalhes/limites: [registro atual](../errors/2026-11-16-harbor-actors-rocks.txt).

Separar geometrias: ROM privada atual usa533mapas e tem15SCCs na análise
fonte. A prévia NÃO compilada usa538mapas e5SCCs, com a nova saída real de
Slateport além de Route134 e transição lateral em EverGrande.18cavernas/7portos
na maior componente da prévia; aindaFAIL global. Fonte/ROM/manifestos públicos
não foram trocados por essa prévia. Ela exige migração de saves533 e provas.
Não excluir fragmentos por projeçãoUI apenas nem enfraquecer os gates finais.
[coast-new-exit-review](../docs/design/atlas-surf-layout/coast-new-exit-review/review.json).
Ainda faltam classificação/acessos de trechos nativos, revisão global de
objetos, migração, rede/ecologia/edições e publicação.8FAIL+1ERROR pendentes;
PR permanece para depois da correção completa. Continuar o pedido original.

Lotes anteriores:

Lote em andamento após o pedido “Tá e por que não resolveu? Faz as ligações
e valide a rom. Já pedi.” Three foi corrigido fisicamente: terminal48x20
preservado e oceano nativo de seis tiles ao sul, mapa48x27. Nove recifes
completos abertos; prédio/barcos/NPCs/warps/coordenadas anteriores preservados.
ROM privada8602c36d… compilada: circuito por controles leste/oeste, Surf,
adaptador/retorno, desembarque, barreiras, SAVE pelo menu e Continue em boot
novo PASS. Birth repetido nessa mesma ROM PASS. Cinco edições privadas
exportadas e bootadas, TESTE também com bateria distribuída. Isso é prova
local; as ROMs públicas continuam anteriores. Provas e fonte preparada exata:
[three-native-review](../docs/design/atlas-surf-layout/three-native-review/review.json).

Titans:12recifes inteiros do antigo limite externo cruzavam a rota. Removidos
somente esses12, com água nativa0x112B; ilha/montanha/portal/NPC intactos.
Migração exata não aceita antiga posição bloqueada como posição de jogador.
Renders fonte inteiros antes/depois revisados; ainda sem provaROM deste delta.
[titans-perimeter-review](../docs/design/atlas-surf-layout/titans-perimeter-review/review.json).

Prévia explícita de costas/underlay:7SCCs,18/18cavernas e7/7portos na maior
componente, mas auditoria global continuaFAIL. Novas fases/cantos nativos e
saída sul de Route128 mudam a partição para537mapas. NÃO materializar/publicar
essa geometria antes da migração dos saves da candidata533. Diagnóstico:
`tools/hoenn/diagnose_atlas_connection_repairs.py`; evidências em
[coast-connection-review](../docs/design/atlas-surf-layout/coast-connection-review/review.json).
Continuar pelas ilhas nativas/fragmentos, corrente oeste de Pacifidlog e
encontro lateral de altura3 em Ever Grande. Depois migração/build/freeze e
provas completas atuais. Os8FAIL+1ERROR de release permanecem; PR só ao concluir.
297testes atlas PASS neste lote; inclui preservação dos374stamps, exceção
explícita dos12recifes, migração e rejeição de cantos não autenticados.

Os lotes anteriores abaixo são históricos:

Segundo lote: correção física das franjas nativas das18cavernas. O corte
artificial de3tiles foi substituído pela margem já reservada de9tiles,
copiando só células Surf comprovadas do parent e suas palavras inteiras.
Fonte passou de17 para16SCCs; Alvorada agora está na componente principal,
que contém15/18cavernas e6/7portos. São5126células de água nativa recuperadas,
sem mudar core/objetos/NPCs/IDs/origens/dimensões/arte do atlas.
287testes atlas passaram; renders fonte completos antes/depois das18cavernas
foram inspecionados. Provas e hashes:
[cave-fringe-review](../docs/design/atlas-surf-layout/cave-fringe-review/review.json).
Fonte privada preparada em.local/atlas-fringe9-src; AINDA sem build ou provaROM.
As cinco ROMs públicas/save continuam anteriores. O grafo global continua
FAIL;8FAIL+1ERROR de release não foram eliminados. Não abrir PR ainda.
Próximo: Titans/Artisan/Mare, ThreeIsland, redes regionais e provas nativas.

Primeiro lote desta retomada, preservado abaixo:

PR111 já integrado em main8a7b78a6. Continuidade em
`fix/atlas-continuity-2026-11-16`. Pedido novo: “Então bora progredir, comece
a fazer”. O usuário determinou **abrir o PR apenas após corrigir os8FAIL+1ERROR**;
isso substitui a orientação histórica de abrir PR com pendências. Fazer
checkpoints/pushes sem PR enquanto faltarem as provas reais.

Fonte171 reconstruída e conferida:171camadas,32250inputs, manifesto d3a06e90…
igual ao contrato. WIP de Ocaso corrigido: endpoint histórico(141,111), não
(140,111); sete pixels sob glifos autenticados por arte/branches/geradores
pinados. Fixture portátil e12testes próprios;285testes atlas passaram.

**A extração sozinha não corrige a rede.** Comparação dos overlays reais:
ZERO diferenças nos1955arquivos preparados,533mapas e IDs/origens/dimensões
iguais;17SCCs persistem. Os pixels recuperados ficam nas reservas de cenário,
onde a máscara nativa prevalece. Não apagar o corpo da caverna para abrir água.
Relatório reproduzível e hashes em
[occluded-routes-review/review.json](../docs/design/atlas-surf-layout/occluded-routes-review/review.json).
Detalhes/guardas em [errors](../errors/2026-11-16-cave-underlay.txt).

Próximo trabalho: franja nativa de cavernas dentro da reserva existente,
ThreeIsland e demais ligações. Sem novo build nem prova na ROM neste lote;
as cinco candidatas/save continuam com os hashes anteriores. Os nove
bloqueios da release continuam pendentes. O restante deste documento conserva
o histórico de15/11 e não revoga este estado atual.

> [Erros atuais da CI, log completo e roteiro de correção](ERROS-PARA-PROXIMA-IA.md).

Atualizado em 15/11/2026 UTC, incluindo a sincronização do pacote pedida após os logs. Este é o guia consolidado para a próxima janela
de IA/Codex. Leia integralmente antes de alterar, gerar, compilar ou publicar.

## 1. Projeto, objetivo e situação atual

Repositório: https://github.com/brunotellesbt-sys/AiKalicaAiCrlBR
Branch: fix/atlas-surf-layout.
PR normal, sem rascunho: https://github.com/brunotellesbt-sys/AiKalicaAiCrlBR/pull/111
Checkpoint confirmado antes deste documento:
1bf71eda2d8276a377e38e84cc4baaaad070c085.

O jogo é Pokémon Journey, GBA, baseado numa cadeia de geradores/overlays.
A revisão171/generated-area-review foi integrada pelo PR108, commit
7ec174b8f7d0c621ec9a60d8b771619e86628889. A revisão172/atlas-surf-layout foi
RECONSTRUÍDA a partir dela. O workspace antigo NÃO foi recuperado. Clonar o
GitHub não recupera os arquivos locais perdidos nem confirma resultados antigos.

Pedido principal: corrigir geografia física de Surf conforme o mapa-múndi,
acessos e defeitos visuais; preservar conteúdo/saves/ecologia; compilar e validar
cinco edições; entregar ROMs, TESTE/save, ZIP, manifestos, navegador e Pages.
Trabalhar autonomamente, sem pedir novamente o histórico, e preservar avanços
com commits/pushes frequentes no PR normal. Não fazer merge automaticamente.

A candidata atual tem cinco ROMs recompiladas e enviadas, mas NÃO é release
final validada. O grafo fonte continua fragmentado. PR normal não significa
aprovação para merge/publicação final. A main só recebe o que for integrado.

Pedido do commit29b1dca, já concluído: criar Aqui apenas com documentação.
Pedido MAIS RECENTE: atualizar o guia antes do merge e sincronizar a cópia
dentro do ZIP. Neste lote, inclusão/verificação de Aqui no empacotador e
documentação do pacote são atualizadas; ROMs/save/source/ELF não mudam.

## 2. Resultado correto exigido pelo usuário

A arte do mapa-múndi é a referência correta: preservar suas quatro arrays
byte a byte. Ajustar posição, formato, dimensão, conexões e acessos das rotas
físicas. Direção e distância viajadas devem coincidir com o atlas.
Nunca corrigir apenas GPS para disfarçar terreno fisicamente errado.

Ciano/azul-claro é a posição real do jogador; quadrado vermelho é o cursor.
O nome sob o cursor não comprova localização. Reprodução antiga:
JourneyWorldSea01(44,10), GPS(137,55); dez passos UP levavam aproximadamente
a(157,44). Pequenos saltos nas emendas não provavam direção/distância global.

Garantir conexões verticais/horizontais reais e continuidade antes/depois das
divisas. Pedrinhas inteiras nos limites sem fechar canais, desembarques ou
barcos. Surf de ida e volta; bloquear caminhada na água, Surf na terra e
travessia de estruturas. Árvores, rochas, encostas, cavernas, cercas, pontes e
construções inteiras. Preservar praias/água animadas, bancos, paletas, NPCs,
eventos, missões, barcos, encontros e progresso dos saves.

O usuário dispensou desenhos: usar mapas nativos e capturas reais, identificando
source versus ROM. Não reabrir ginásios/torneio/conteúdo já integrado sem
regressão demonstrada. Conservar restauração de Dewford/Route107, sete portos
de madeira sem metal na ponta, ginásios extras distintos com quatro trainers,
guia fora da porta e sem puzzles complicados, qualificador na18ªinsígnia,
Galactic na22ª, rivais e escala de Luffy/Eren.

## 3. O que já existe e foi feito

| Item | Estado verificável |
| --- | --- |
| Fonte171 | Cadeia de171 camadas e hashes históricos reproduzidos. |
| Fonte172 |533 mapas novos,1955 inputs preparados; não confundir com o plano436 do ambiente perdido. |
| Geometria | Sistema físico global:8tiles/pixel, corredor principal6tiles, chunks usuais32×32 e menores quando necessário. |
| Cenário/eventos |374 stamps completos;74 eventos, incluindo56 NPCs, preservados na composição registrada. |
| Obrigações |33 adaptadores,18 cavernas de superfície,5 Dive; conectividade global incompleta. |
| IDs/saves |273 IDs antigos preservados; migração versionada2 conserva a migração histórica1. |
| Runtime | Índice por grupo/número, índice espacial32tiles, halo físico e prioridade da conexão nativa. |
| ARM | Build integral concluído; structs de migração de6 bytes são packed porque APCS arredondava para8. |
| ROMs | Gen1–4/Gen1–9 Normal/Hard e TESTE atualizadas no PR, como candidatas. |
| Boot/save |5 cold-boots por controles passaram; TESTE passou Continue→salvar pelo menu→exportar bateria→novo boot→Continue. |
| Birth Island | Na ROM integral atual: rampa, Surf ida/volta, corpo do desembarque bloqueado, Harbor/retorno e visibilidade real do avatar passaram. Ponta de madeira inspecionada. |
| CI/histórico | Referências pinadas restauradas; erros KeyError e seleção errada de provas antigas corrigidos. |
| Pesquisa interrompida | Módulos dos pixels ocultos preservados como texto WIP; não integrados. |

O save TESTE testado está em Mossdeep,mapa[0,6],tile[28,18],a pé,altura5 nativa.
Isso não certifica todos os saves nos273 mapas aposentados. Provas antigas dos
diagnósticos de3 mapas,5 Dive isolados ou candidato448 não validam a rede533.

## 4. Artefatos e hashes atuais

Fonte dos hashes: [roms/CANDIDATA-172.json](../roms/CANDIDATA-172.json).
As quatro ROMs estão em roms/ e mods/hoenn/versions/. TESTE/save ficam em
roms/rom-de-teste/. ZIP: mods/hoenn/versions/Pokemon-Journey-Four-Editions.zip.

| Artefato | SHA-256 |
| --- | --- |
| ROM bruta172 | f2cac1ecb79e23c3b6a6a43e07568b7c5b03579dc265ba99d33bc3bad7940c0e |
| ELF172 |618b0556e031fee25a1aace83f33bb8491b7e316ebd910a34f968098b135ba73 |
| Marker172 | dede6825a87fd08742f369478f2004a70b9e7d2b8f1a6c0aa44ad43d559328f8 |
| Gen1–4 Normal | a24b7304d4dda4a7d1abd60849161409468a4a29d00528a9549643333e7cb40d |
| Gen1–4 Hard | a2103c4bebe2f8fecc12d863b16f7e0971fb35040b6cf15bf2f0a95f5275146c |
| Gen1–9 Normal |47a3a75c36b50bcd96584bd7c7ced7f121f68b8e5b14e93338f503c17b7f951f |
| Gen1–9 Hard |14ebe89fc88f3d4d55cc8a48f7ed1edf36bf997a26d397a8c653e5d6320bf36d |
| TESTE | b7445c29804f36f188e0b753849ac4bb55fa605218c7486c04ee73d3fc7945ae |
| Save TESTE128 KiB |36ace517a44bc0315a4a5309054a4913f39e0f1872a073763ba685c3421e5861 |

ROM usada:32.920.992/33.554.432bytes(98,11%). EWRAM245456;IWRAM28660.
Arquivos exportados têm32 MiB. Quatro perfis mudam somente regras/cabeçalho
previstos. TESTE conserva modo e identidade de save separados e supressão
existente de encontros/abordagens automáticas. Não simular sua regra com Repel.

Hashes da arte são dos bytes interpretados das arrays, não do header inteiro:

| Array | SHA-256 |
| --- | --- |
| sWorldTiles |09e5334176c31cc5c6fa30ed9a2e46b6f90df524ebfa0a92b3f2403742fa7b9f |
| sWorldTilemap | ae2c327dad6d9ab1a1897369b793969e1229d18f45d0add22a79e4ba5a7a3196 |
| sWorldDetailPixels | a7a9ce35ca044ee2df75bd49878a79536fa42f05fb1cdb0cd0593593db3b58f2 |
| sWorldPalette | da38567f7f701d0d76c5c53ef00407fc6eeb75632efdf6121590b9b2f7aca73a |

## 5. Como funciona tecnicamente

1. GPS gerado é afim: floor((originX+localX)/8),floor((originY+localY)/8),
   inclusive negativos. Sem interpolação antiga controlando viagens novas.
   Sem novos arrays GPS por célula; limite de32 MiB.
2. IDs append-only. Mapas aposentados continuam para saves. Novos grupos
   têm no máximo100mapas; WarpData.mapNum/mapGroup são assinados, nunca128+.
   Respeitar buffer: (width+15)*(height+14)<=10240 nos mapas gerados.
3. Word: ID=word&0x03FF; colisão=word&0x0C00; altura=word>>12. IDs dependem
   do banco. Conferir8words gráficos, atributos completos, símbolos/ponteiros,
   callbacks, RGB555, comportamento e animações. Usar inspect_map_tile.py.
4. Água gerada usual altura1/colisão0/Surf real; piso seco usual altura3.
   Água nativa transicional0, interiores0 e outros níveis válidos existem.
   Não normalizar tudo. Pontes com Surf por baixo podem exigir15, não0.
5. Halo/câmera não criam conexão de movimento. Exigir dono global real,
   offsets recíprocos e bancos corretos; preservar mudanças runtime do core.
6. Migração: VAR_JOURNEY_SEVII_GEOMETRY_VERSION/0x40DC,versão2. TreasureBeach
   versão1 deve deslocar só uma vez. Relocar antes de LoadObjectEvents,
   atualizar posição, warps, objetos, templates e visão; provar salvar/Continue.
7. Ecologia não é só wild_encounters.json: pools/habitats compilados precisam
   de aliases novos→donor; restrição de eventos precede alias. Preservar
   níveis, pesca, famílias e geração.383/190famíliasGen9/Gen4 e269células de
   grama vieram de auditoria fonte SEM filtroSCC; não provam capturabilidade
   global.403/200 eram união de pools, não famílias efetivamente capturáveis.
8. Fixtures iniciais de party/progresso/posição devem ser declaradas. Após
   partida, controles; getters readonly com trampoline declarado. Não escrever
   posição, altura, câmera, VRAM, callback ou flags para passar. A bridge não
   passa automaticamente mais de4 argumentos ARM.
9. Não gerar, compilar ou empacotar enquanto um leitor usa o mesmo source,
   ELF ou ROM. Congelar e conferir hashes antes/depois das provas.

## 6. O que falta, em ordem

1. Rede física:17 SCCs de água gerada;14/18 cavernas e6/7 portos na componente
   principal. O auditor global retornaFAIL. Diagnóstico da maior componente
   não éPASS. Não forçar contagens antigas436/449 nesta reconstrução.
2. Pixels ocultos: [WIP preservado](../docs/design/atlas-surf-layout/WIP-occluded-routes/README.md).
   Os arquivos .py.txt NÃO estão integrados nem compilados. Teste falha antes
   dos casos: ValueError: Recorded branch endpoints changed Ocaso.
   Corrigir interpretação do marker171, sem relaxar hashes/asserts. Testar
   antes de integrar ao compose. Sete pixels propostos:(109,49),(210,65),
   (210,86),(141,110),(200,110),(119,104),(119,105). Exigir prova da linha
   literal e ordem de pintura sob ícones; não abrir oceano/terra por proximidade.
3. ThreeIsland_Port_Frlg48×20: embarque(14,17) na componente0/leste;
   adaptador entra na1/oeste. Terminal/ponte e recifes separam as águas.
   Correção ainda não aplicada. Revisar boca autêntica conforme atlas e
   preservar objeto/eventos; não apagar terminal ou rasgar canal arbitrário.
4. Outras lacunas: Cinnabar, oeste deHoenn, Pacifidlog/Route130, stubsRoute128,
   cavernasTitans/Artisan/Mare/Alvorada. Testemunhas e tamanhos no
   [checkpoint urgente](../docs/design/atlas-surf-layout/urgent-progress-checkpoint.json).
   IDs deSCC são daquele diagnóstico, não constantes permanentes.
5. Interfaces nativas:32/33discordam dos GPS históricos; revisar registros e
   propriedade física. atlas_surf_regional_projection.py reproduz cursor UI
   quantizado, não embedding8tiles/pixel nem propriedade de cada pixel.
   Centros, nearestpoints, labels ou GPS inventado não comprovam geografia.
6. Fonte/retirement/ecologia: repetir auditoria global/bancos depois de mudanças,
   conferir referências C/scripts aposentadas, migração de todas as posições/
   warps, pools por edição e DEX com gatilho realmente alcançável.
7. ROM final: provar que a pausa antiga de~300frames desapareceu na rede toda;
   C equivalente ou timeout maior não bastam. Provar18 cavernas,33 adaptadores,
   7 portos,5 Dive, barreiras, mapas estreitos, cantos/diagonais, viagens contínuas
   Aurora/One/Two/Three/Hoenn↔Kanto. Repetir Birth se os bytes finais mudarem.
8. Baterias antigas/novas, modos/altura e Continue→menuSalvar→Continue.
   Repetir ecologiaGen9/Gen4/TESTE e renderização integral de mapas/vizinhos.
9. Congelar cinco edições reais; review-mode e cold-boot, TESTE com/sem save.
   Somente depois publicar ROMs/save/ZIP/manifestos, conferir navegador,
   stage_pages e Pages. Release prevista:12 provas principais, fonte+nativa
   comuns e2 provas por edição; nativa agrega superfície/Dive/ecologia/baterias.
   Completar o fluxo estrito, sem presumir recuperados os validadores perdidos.

## 7. CI: não confundir integridade com aprovação

[Actions do reparo](https://github.com/brunotellesbt-sys/AiKalicaAiCrlBR/actions/runs/43737388074):
12/12sea_routesPASS; Hoenn1094 testes,8 FAIL,1 ERROR,34 skipped,zero KeyError.
Os6casos históricos Fuchsia/atlas passaram;20 testes de histórico/integridade
foram adicionados. Checkpoint das5 ROMs e alpha histórica passaram.

SeteFAIL rejeitam Unvalidated release; Sootopolis exige manifest.validated;
oERROR ExtraGyms.setUpClass tem a mesma recusa. Esses9 bloqueios continuam
reais: não demonstram por si só9 novos bugs físicos, nem autorizam aprovação.

verify_atlas_surf_checkpoint.py confere bytes/perfis, TESTE/save, boots,
freeze/tabelas e ZIP/docs. Não certifica viagens globais, visuais ou campanha.
verify_versions(require_seal=True) é o gate final; não alterá-lo para aceitar
candidata. Manifesto: candidate=true,validated=false,final_release_validated=false,
proofs=[]. Ponte171: mods/hoenn/atlas-surf-layout-validation/baseline/versions.json,
SHAeca26adfcb0b15f9da78aadec1b8738f66288fcc58d4d727ee2ea2a6274e29ec,
retested_on_current_rom=false. Históricos mantêm seus donos e SHA.

Para aprovar: concluir correções e produzir/revisar provas da ROM FINAL, depois
finalizar contrato e manifesto pelo fluxo adequado. Não forçar flags/pins,
misturar ELF/ROM, reutilizar capturas antigas, pular testes ou usar
continue-on-error. Renomear casos como históricos não substitui prova atual.
Browser/Pages continuam bloqueados atrás do gate final.

## 8. Onde ler e como retomar em outro ambiente

Leituras obrigatórias:

- [AGENTS.md](../AGENTS.md).
- [Guia detalhado e cronologia](../docs/CONTINUIDADE-TECNICA-IA.md).
- [Handoff histórico](../docs/RETOMADA_TECNICA_POKEMON_JOURNEY.json) e
  [pedido pósPR108](../docs/ULTIMO_PEDIDO_POS_PR108.json): relatos históricos,
  não evidências atuais. Identificadores privados foram omitidos do Git.
- [Skill de mapas](../.agents/skills/gba-map-review/SKILL.md),
  [errors](../errors/README.md), [guiaGBA](../docs/AJUSTES-GBA.txt),
  [estado](../errors/ESTADO-DA-TAREFA.txt), [catálogo](../assets/tiles/README.md).
- [Resultado CI](../docs/design/atlas-surf-layout/ci-history-repair.json),
  [Birth atual](../docs/design/atlas-surf-layout/current-ROM-birth-native/birth-native.json).

Checkout conhecido:/workspace/AiKalicaAiCrlBR. Verificar o que realmente existe:

| Caminho local | Papel |
| --- | --- |
| .local/generated-area-review-src | Fonte171 imutável; não editar/compilar. |
| .local/review171-build-src | Cache compilado171 verificado; preservar. |
| .local/atlas-current-rom-src | Fonte/ELF/ROM533 congelados. |
| .local/atlas-current-rom-frozen.json | Vínculo de hashes da compilação. |
| .local/atlas-current-rom-artifacts | Exportações atuais. |
| .local/atlas-current-rom-editions | Views por edição; não compilar/gravar. |
| .local/ci-python/bin/python | Python deste ambiente. |
| .local/ci-env.sh | AmbienteARM local; conferir antes de usar. |
| .local/mgba-bridge-ci.so | Bridge mGBA local. |

Esses arquivos locais podem faltar em outra máquina. Primeiro conferir
branch/HEAD/PR, alterações locais, markers, hashes, disco/inodes/memória e
leitores ativos. Não apagar/resetar workspace antigo nem preparação parcial.
Não atribuir o404 de provisionamento antigo a disco, Microsoft, uso ou
corrupção sem prova; a causa não foi determinada.

Workspace é sparse checkout e clone parcial: rastreado ausente não implica
perda. Evitar git ls-tree -l/-rl, que pode baixar blobs enormes. Consultar
arquivos de forma dirigida. Manter TLS/autenticação da plataforma, sem extrair
tokens ou contornar proxy. GitHTTPS funcionou;403 de api.github.com no proxy
era outro problema. Última medição histórica:~278MiB/~16,8mil inodes livres;
medir novamente. Não iniciar outro clone/build completo sem espaço.

Sem fonte171, consultar restore_generated_area_review.py --help e usar
--source <diretório-novo> --acquire. Conferir contrato; --verify-only e
--verify-built verificam fonte/build histórico quando presentes. Compilar
somente cópia privada, nunca a171 congelada.

prepare_atlas_surf_layout.compose() monta a candidata em memória; OverlaySource
permite auditoria do terreno real sem gravar o parent. Para materializar,
usar prepare_atlas_surf_layout.py --source <NOVO-diretório-privado>
--clone-from .local/generated-area-review-src. Cache opcional:
--build-cache-from .local/review171-build-src, com parent autenticado.
Configurar dependências/ARM reais; começar build com make -j4 após preflight.

Módulos: atlas_surf_truth/plan/layer/scenery/scenery_pack/adapters/registrations;
runtime/physical/legacy/migration; ports/dives/dive_access/ecology;
reachability/layout_requirements. Conferir nomes/CLI existentes: o handoff
antigo lista ferramentas que não foram recuperadas. Usar tiles e renderer
nativos, revisar mapa inteiro e vizinhos, colisão, altura, bancos e animação.

## 9. Erros proibidos e forma correta de trabalhar

- Não redesenhar atlas ou só mudar marcador/GPS: corrigir mundo físico.
- Não abrir água arbitrária para unirSCC: exigir referência gráfica/nativa.
- Não usar tileID universal nem recortar objeto: conferir banco e objeto inteiro.
- Não apagarNPC/evento/barco/missão para teste passar: preservar e provar acessos.
- Não usar foto estática para afirmar passagem, nem source como capturaROM.
- Não mascarar pausa com timeout: corrigir runtime e medir travessia real.
- Não impor altura1/3 indiscriminadamente: respeitar comportamento nativo.
- Não injetar posição/estado no percurso: fixtures iniciais, depois controles.
- Não copiar só wildJSON: conferir pools compilados, gatilhos, geração e DEX.
- Não reaplicar migração a cada entrada: versão persistente e Save/Continue real.
- Não inventar PASS, pins, flags ou captura: provas vinculadas aos bytes finais.
- Não compilar/regenerar/empacotar com leitores ativos do mesmo artefato.
- Não deixar único exemplar local: commit/push por lote e SHA remoto conferido.
- Não chamar PR aberto, boot ou grafo fonte de release/campanha validada.
- Não executar git reset --hard/git clean nem limpar preparações sem preservação.

## 10. Como atualizar documentação e avanço

A cada lote coerente, manter este arquivo, docs/CONTINUIDADE-TECNICA-IA.md e
errors/ESTADO-DA-TAREFA.txt atualizados: data/pedido literal, último concluído,
incompleto, arquivos, testes/resultados, hashes/ROM alvo, limitações e próximo
passo concreto. Separar recebido/histórico, observado na fonte, observado na
ROM e não testado. Manter aqui um resumo atual; a cronologia fica no guia
detalhado. Não manter pendência já concluída como estado executivo atual.

Conferir links/diff, rodar checks adequados, commitar, fazer push e comparar SHA
remoto. Atualizar o mesmo PR normal, sem duplicata/merge automático. Se outro
chat integrou a branch, inspecionar remoto e preservar alterações antes de agir.

ATUALIZAÇÃO MAIS RECENTE: o usuário pediu sincronizar o guia antes do merge.
O ZIP foi reempacotado com a documentação atual e a pasta Aqui completa,
incluindo o registro de erros e o log original. O empacotador agora inclui
Aqui e o verificador exige seus bytes atuais; não foi afrouxada a comparação.
ROMs/save/source/ELF preservam os mesmos hashes. Só documentação, integração
documental do pacote e hash/tamanho externo do ZIP mudaram neste lote.

O erro Stale archive entry relatado anteriormente é histórico e foi tratado
por sincronizar o pacote, não por ignorar checks. A verificação de integridade
é executada após empacotar. Os8FAIL+1ERROR de aprovação final continuam
pendentes, pois a rede e as provas172 ainda não foram concluídas.
Futuras edições destes textos devem entrar no ZIP antes de declarar o pacote
sincronizado. Depois atualizar hash/tamanho externos e repetir a verificação.

## 11. Último concluído e último incompleto

- Antes deste lote: cinco ROMs/save/ZIP enviados; histórico/CI reparados;
  Birth na ROM atual passou; pesquisa WIP preservada no PR111/checkpoint1bf71ed.
- Mais recente: guia no Git e dentro do ZIP sincronizados, com Aqui/erros/log
  incluídos e comparação estrita testada; enviar ao mesmo PR e conferir push.
- INCOMPLETO: consertar toda a geografia/acessos/visuais/saves/ecologia e provar
  a release172. Próximo trabalho útil: corrigir/testar Ocaso/underlay, resolver
  Three e lacunas nativas, repetir grafo/bancos, só então nova candidata,
  compilação privada, congelamento e provas finais das cinco edições.

## Histórico: erros enviados às21:06–21:07 UTC, antes da sincronização

Consultar ERROS-PARA-PROXIMA-IA.md e LOG-CI-2026-11-15.txt nesta pasta.
Naquela execução:1094testes,8FAIL,1ERROR,34skipped; gate final rejeitou release
não validada. Além disso, o checkpoint FALHOU por Stale archive entry
no guia técnico: o Git foi atualizado, mas o ZIP não, conforme o pedido
documental. Não extrapolar o PASS anterior do pacote para este HEAD.
Naquele lote o pedido era somente registrar os três erros; o pacote não foi
corrigido então. A sincronização mais recente, descrita abaixo, resolve o
erro documental; as provas finais da release continuam pendentes.

## Situação final desta entrega de guia

Último pedido: “Vou fazer o merge do pull request mesmo com esses erros pq
vai acabar o limite. E pq o guia tá desatualizado? Atualize o guia po, antes
de acabar o limite, quando acabar vou fazer o merge, pode deixar o guia
nessa página também.”

O guia no Git já havia sido atualizado. A cópia antiga era a do ZIP,
preservada pelos pedidos anteriores de somente documentação. Esta nova etapa
sincroniza ambas e acrescenta toda a pasta Aqui ao pacote, sem recompilar ou
trocar as cinco ROMs/save. O usuário pretende realizar o merge por conta
própria; não fazer merge automático nem interpretar isso como release validada.

Concluído: guia/erros/log no Git e ZIP, integração documental e check de
integridade do pacote. INCOMPLETO: rede17SCCs, Ocaso/underlay, Three, demais
lacunas e provas da release172. O registro de erros conserva os logs originais;
o erro2 tem atualização de estado no topo do documento.
