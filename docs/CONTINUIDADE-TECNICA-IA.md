CATÁLOGO COMPLETO DO PWT — 24/11/2026

A camada `pwt-complete-rosters` sobre `2c38d692` conclui as 73 equipes
pendentes. Para cada treinador, o arquivo de referência identifica a batalha
usada e distingue Pokémon documentados de escolhas para completar a equipe.
As 162 identidades e o suporte às Megas de Legends Z-A continuam no elenco
existente. Gladion equipa Water Memory para Silvally do tipo Água.

O catálogo compilado foi conferido nas cinco edições. A Gen 1–4 tem 61 times
e a Gen 1–9 tem 162, assim como a TESTE. Os BPS cumulativos partem das
ROMs com as rotas H, J e K já removidas. A etapa de publicação reconstrói
essas edições antes de disponibilizar Play e Download.
[Reprodução, times e provas](../mods/hoenn/pwt-complete-rosters/README.md)

As nove copas regionais e as duas Copas Mundiais chegaram ao título no
mGBA. A matriz de 2.736 interações de batalha passou nas quatro edições de
jogo. O teste adicional em Paldea Hard registrou quatro vitórias e duas
derrotas sem reforço de atributos, com restauração da equipe ao sair. As
cinco edições abriram no navegador e a TESTE carregou o save de Mossdeep.

A revisão das histórias dos lendários, do mundo durante as missões e da
campanha completa fica para a etapa final, na ordem solicitada pelo autor.

GALAR E MEGAS DE LEGENDS Z-A NO PWT — 24/11/2026

O pedido atual é usar as Mega Evoluções de Legends Z-A quando couberem
nos times do elenco existente. A camada `pwt-galar-za-megas` parte do merge
`526876ca` do PR119. Revê 13 equipes do Champion Cup e usa os vínculos de
Mega e as pedras já compilados para equipar adversários compatíveis.

As quatro edições mostraram Raichu Mega Y do jogador e Raichu Mega X da IA
de Lt. Surge na mesma partida do PWT. A Gen 1–4 permite 17 formas e a Gen
1–9 permite 49, com 45 pedras no estoque de Ever Grande. A matriz conferiu
446 times nas quatro edições. Os relatórios e os patches cumulativos ficam
em [mods/hoenn/pwt-galar-za-megas](../mods/hoenn/pwt-galar-za-megas/README.md).

O catálogo completo acima registra as 73 equipes que restavam neste lote.

PWT E MECÂNICAS DE BATALHA — 23/11/2026

Pedido atual: “vamos primeiro sobre fechar o pwt e testar mais mecânicas no
jogo”. A prioridade das equipes é PWT oficial, equipes fortes dos jogos,
mangá e por último anime. As vagas precisam combinar com o treinador.

Na branch `work/pwt-mecanicas`, sobre o merge `48dfb952`, a camada
`pwt-official-parties` revisa 54 equipes de PWT e 14 de Liga. Quarenta e oito
equipes elegíveis têm dados próprios para Gen 1–4. A primeira compilação
revelou as repetições de Glalie e Drifblim. Os dados atuais corrigem os dois
casos e preservam a duplicação de Gengar da revanche oficial de Agatha.
Reprodução, fontes e patches de revisão ficam em
[mods/hoenn/pwt-official-review](../mods/hoenn/pwt-official-review/README.md).

As quatro edições passaram na matriz de 446 equipes, em 2.736 verificações
de batalha e em 70 verificações novas. As copas Normal de Kanto e Unova
chegaram ao título. Glacia e Shauntal foram derrotadas no Hard com equipes
sem reforço. Dipplin e Girafarig passaram pelos menus e pelo recarregamento
do save. A edição Gen 1–9 Normal testada tem SHA-256
`d5c1fa8b9490cdb72da76d2ce7bcadf272f85233c8252f09e795eb362b54a643`.

O próximo lote do PWT cobre 13 referências de Galar e o uso das Megas de
Legends Z-A pelos treinadores existentes. As histórias dos lendários, a revisão
do mundo durante as missões e a validação integral da campanha ficaram para o fim.

ROTAS H, J E K — 23/11/2026

H, J estendido até o cruzamento ao norte e K foram retirados da arte do
Atlas e dos corredores reais de Surf. A linha superior de Kanto–Sevii
e seu acesso sul continuam funcionais. A nadadora 39 foi movida dentro
do mesmo mapa. A migração 9 reposiciona saves nas áreas encerradas e
renova os blocos de câmera salvos. Pokédex de Finneon e Lumineon aponta
para um gatilho alcançável. A revisão foi compilada nas cinco edições,
com patches BPS e mapa em mods/hoenn/atlas-route-pruning.

A publicação do player reconstrói as cinco ROMs a partir desses patches
e valida seus hashes antes de servir Play e Download. O endereço
world-map.html abre a imagem do mesmo Atlas. As capturas do menu MAP
confirmam os cortes em 1× e 2×. As ROMs-base 172 e seus relatórios
continuam como referência de reprodução.

ATUALIZAÇÃO — FUNCIONALIDADE E TESTES DA CAMADA 172 — 23/11/2026

Pedido atual: “Quero a rom passando em todos os testes primeiro, pra depois
colocarmos essas funcionalidades.” Ideias futuras ficam documentadas.

A ROM de referência atual tem SHA-256
5d42387c5ec934239fcdeeb2e030ef3f3d4b763030b38f49538e3eb02fdf6cab.
Sete ilhas recuperaram o gatilho de encontro em areia seca e 66 referências
da Pokédex. As duas caps passaram na auditoria de espécies. Os testes de
câmaras, navegação, treinadores, pedras e saves usaram a compilação atual.
As cinco edições abriram no navegador, a TESTE preservou o save de
inspeção de Mossdeep e o player do GitHub Pages foi preparado localmente.

O contrato e as provas atuais estão em docs/design/atlas-functional-review-2026-11-23.
Os registros abaixo são históricos. A ROM C e os seus resultados permanecem
separados dos resultados atuais.

PRIORIDADE ATUAL — CONCLUIR FUNCIONALIDADE E TESTES —23/11/2026
Pedido literal: "Quero a rom passando em todos os testes primeiro, pra depois colocarmos essas funcionalidades."
Histórias/ideias futuras ficam guardadas; não implementar novas funcionalidades.
Branch:fix/final-rom-validation-2026-11-23, baseada emmainatual. Preservar fontes
congeladas e preparar PR normal apenas depois dos checks obrigatórios verdes.

NaROMC preservada passaram487/1025captura+SAVE+coldContinue,Pacifidlog,
ThreeIsland,7portos/14baterias dry/Surf e5edições com batalha+flag+coldContinue.
TESTE passou600frames sem abordagem e batalha manual. As chegadas de porto
precisam usar o marker atual; balsa mundial volta ao interior, Seagalloptem
outra chegada exterior. O validador novo comprovou percursos sem alterar aROM.

Bloqueio real novo: auditoria de todas as entradas AREA nativas encontrou9
espécies sem local naGen1–4 e36naGen1–9. Famílias terrestres declaradas emilhas
arenosas ficaram sem gatilho. Corrigir predicado nativo estreito e AREA com
censo real, gerar fonte privada nova e repetir provas pelos hashes novos.
Não afrouxar cobertura, selo ou testes; as ROMs públicas continuamV7.
Provas/diagnósticos:docs/design/atlas-functional-review-2026-11-23/README.md.
FonteC:.local/final-atlas-src;freeze:.local/final-atlas-frozen.json.
Próximo:reparo de habitats/Dex,censo/compilação/provas finais,contrato172,
publicação5edições,leitores históricos,browser/Pages e suíte completa.

HISTÓRICO PRESERVADO (pedidos anteriores de abrir PR de progresso não mudam a prioridade atual):

CHECKPOINT PARA PR DE PROGRESSO — 18/11/2026
Pedido literal mais recente: "ABRA UM PR COM TODO PROGRESSO ATÉ O MOMENTO POIS O LIMITE VAI ACABAR."
O autor agora solicita abrir o PR com todo o progresso existente, mesmo com
validação final pendente. Esta instrução substitui a espera anterior por todos
os testes para a abertura. PR normal, conforme sua preferência persistente;
registrar pendências explicitamente e não executar merge.

ROM privada C d296428c98f989a815e24d9def5a51bfd284c50f1ca9831547cb42fb7ce8c0ce:
105câmaras,9exteriores grandes,96vitórias Surf,34costas,5Dive,18baterias reais
V7→8→SAVE→Continue,103+6fragmentos e2divisas131 PASS. Articuno144 capturado
por controles, flag/ator/bola conferidos e equipe preservada em SAVE/Continue;
não foram certificadas105capturas. A Pokédex foi corrigida na fonte e compilada:
978referências efetivas realocadas(261trocam proprietário),72linhas antigas
ineficazes removidas; gatilhos exatos de espécie/cap alcançáveis, sem mudar encontros.
Prova compilada independente:34396entradas,2604saídas,2046mapas,3118warps,
401atores afetados e2473linhas AREA. Arte do atlas preservada.

Provas novas C, PNGs, baterias, delta completo, freeze, logs e SHA256SUMS:
docs/design/legendary-chambers-review/compiled-c-v8/README.md.
Fonte preservada:.local/final-atlas-src;freeze:.local/final-atlas-frozen.json.
As provas A/B permanecem históricas; nunca relabelar seus hashes como C.
Último subpedido concluído: preservar/rever as provas atuais da C e preparar o
checkpoint solicitado para o PR. Pedido principal incompleto: concluir a ROM.
Faltam487/1025,percurso dos7portos com ports.arrivals atual,capitão/ThreeIsland
na C,cincoedições/regras/caps/TESTE/coldboots,encontros,browser e contrato/publicador172.
O planejador dos7portos usa coordenadas históricas e falha antes dos controles;
a hipótese de pontes não resolveu e foi retirada. Não declarar defeito da ROM sem prova.
As cinco ROMs públicas continuamV7; os8FAIL+1ERROR do selo legítimo continuam
pendentes. Abrir PR de progresso não significa testes verdes ou ROM publicada.

Verificação deste checkpoint: Sea Routes12/12PASS; Hoenn1218testes em126.358s,
8FAIL+1ERROR+26skipped. Permanecem apenas as9recusas de selo; fixtures originais
ausentes no clone foram restaurados, sem modificar testes. Logs emcompiled-c-v8/checks/.

HISTÓRICO PRESERVADO (instruções antigas de esperar o PR foram substituídas):

EM ANDAMENTO — CONCLUIR A VALIDAÇÃO REAL —17/11/2026
Pedido literal mais recente: '"as 8 falhas e 1 erro continuam bloqueados pela validação final da Rom." o que falta pra solucionar, finalizar e concluir isso? Faça.'
Mantém a exigência: próximo PR somente depois de TODOS os testes obrigatórios.

Na ROM B aa258f74, passaram9exteriores (729células de montanhas completas,
189PNG),18baterias reais7→Continue8→SAVE pelo menu→Continue8,105flags de captura
preservadas por Continue, templates atuais e sem repetição da migração. O C
real passou1728posições antigas. Regressões:103+6fragmentos/54casos/210PNG,
48bumps;2divisas131;5Dive;2viagens do capitão dentro da casa dePacifidlog;
ThreeIsland e4percursos costeiros nativos ida/volta. Provas eSHA256SUMS:
docs/design/legendary-chambers-review/large-caves-v8/followup.

Falha de retorno diagnosticada no validador: usar0x500+ID para os novos IDs
ultrapassou o banco nativo e ativouFLAG_SYS_CRUISE_MODE. A CPU confirmou
SSTidalCorridor_EventScript_ReachedStepCount repetido. Corrigido o fixture para
as96flags privadas autenticadas. Os9percursos passaram após a correção, inclusive
Artisan após Alvorada. Não atribuir essa falha de preparação ao terreno daROM.
Alvorada conserva a entrada nativa inundada comSurf; as outras8são secas.

Auditoria compilada de ecologia preserva190/383famílias e todas as famílias das
rotas novas têmgatilhos alcançáveis. Ainda261linhasAREA apontam para mapas
aposentados; as261espécies/caps já têm gatilhos atuais reais, mas o cabeçalho
precisa ser corrigido e compilado. Não relabelar provasB como provas da novaROM.
Próximo: corrigirAREA, fonte nova privada, build/freeze e provas atuais,
treinadores/capturas/edições/browser/contrato172, suíte completa; então PR.
Os8FAIL+1ERROR finais não foram mascarados. CincoROMs públicas continuamV7.

HISTÓRICO PRESERVADO:

Atualização do mesmo lote: a matriz105 também PASSOU na ROMBaa258f74,
com210PNG novos e48600pixels de espécies, verificados independentemente.
ProvasB emdocs/design/legendary-chambers-review/large-caves-v8/native.
Os7testes anticorrupção dessas provas passaram. As demais pendências e a
exigência de abrir PR somente com toda a suíte aprovada continuam ativas.

EM ANDAMENTO — PR SOMENTE COM TODOS OS TESTES APROVADOS —17/11/2026
Pedido literal mais recente: “Ok, quero o próximo PR passando em todos os testes, já resolveu aquele?”
Resposta dada: ainda não; as8falhas+1erro continuam no gate final legítimo.
Não abrir o próximo PR enquanto toda a suíte e as verificações obrigatórias
não passarem. Commit/push de checkpoint na branch continuam autorizados.
Nenhum PR novo foi aberto. O avisoPython foi corrigido, mas isso não resolve
a aprovação final; não omitir testes, mudarflags ou reutilizar prova antiga.

Implementação concreta:105câmaras próprias em48cavernas, entrada/retorno
recíprocos,105sprites de espécie, flags/scripts de captura e NPCs/warps de
campanha preservados. Há7famílias nativas de salas,37geometrias completas,
sem recortar objetos. DEX consolidado em uma localização atual por espécie;
os quatro arrays de arte do atlas não mudam. IDs antigos mantidos e dois
grupos novos anexados; migração candidata8 renova os objetos somente nos mapas
alterados, preservando jogador/seguidores e os eventos de captura.

A primeira compilação privada(protótipoA) passou105viagens nativas de entrada,
aproximação e retorno por controles,210capturas e48600pixels visíveis das
espécies. O verificador independente lê cada PNG, seus hashes, OAM/frames e
as identidades ROM/ELF/marker; captura/batalhas/saves não foram certificados.
ROMprotótipoA:e8b3d8e5e009fe2c4f9c6ddc4521e1f2670d33a3e35ed73af83f70c20cbeedf5.
Provas/delta emdocs/design/legendary-chambers-review/prototype-v8a. Essas
provas são somente do protótipoA, não da compilação que inclui os exteriores.

A nova compilação privadaB integra nove massas costeiras ampliadas e variadas
por faixas nativas inteiras, e troca cada caverna3x3 pelo objeto Seafoam
completo de81células. Recifes, bocas de conexão e o pixel fixo do atlas ficam
preservados. Há1728posições antigas para resgate local uma vez, com destino
do mesmo modo; ainda exigir testes do C e baterias antigas reais.
FonteB:.local/legendary-caves-src;freeze:.local/legendary-caves-frozen.json.
ROM:aa258f7498df10f1fc4ea57104d499b474d837d6ba8f4b3484832f0e74471051
ELF:9b75417a2b2123e50c6a9b80abfe25c9b51527d225b3c6bbd46419d485d8977d
marker:9a1c2e7211e153155f18bfa03e1e6406d69a694c86b1844564ab1a495647c1e3
34396inputs/2604outputs;33367284bytes usados/33554432; uma componente Surf,
sem fuga para água decorativa na auditoria de fonte. Galeria dos9exteriores
inspecionada. Nova matriz105 está sendo executada na ROMB; outras provas de
costa, colisão, Surf, saves, edições e release continuam pendentes.

Corrigido também o renderizador: tabelas static de mesmo nome em unidades C
diferentes não podem ser concatenadas. Espécies usam as tabelas de pokemon.c,
e não a arte antiga do NPC clássico. Sete testes do renderizador e oito testes
portáteis das105salas passaram. Comparação nativa aceita os64x64 reais montados
por duas peças64x32; não reduzir a espécie para32x32 para contornar o teste.

As cinco ROMs públicas continuam no checkpointV7; não foram substituídas por
uma compilação sem as provas novas. A/B e os snapshots anteriores foram
preservados. Somente caches regeneráveis e pacotes.deb já instalados foram
reclamados por espaço, com hashes/proveniência em.local. A preparação B foi
retomada após ENOSPC conferindo todos os arquivos parciais antes da cópia.

Último subpedido concluído:105câmaras implementadas/compiladas e105entradas,
corpos de espécies e retornos provados no protótipoA. Pedido global incompleto:
concluir/provar exteriores e migração naB, repetir105/rochas/câmeras/costas,
treinadores, ecologia/DEX, cinco edições, browser e contrato172, passar TODA a
suíte e somente então abrir o PR. Não promover nativeA como prova deB.

HISTÓRICO PRESERVADO:

RETOMADA APÓS MERGE112 — CORRIGIR GATES E CAVERNAS —17/11/2026
Pedido literal: “Fiz o merge com esse erro. Corrija isso e as outras coisas que
pedi pfvr”. Depois:“Continue”. Merge confirmado emmain9dff8c370ddd6d718b1164cbaefa47050c88509e.
Branch nova:fix/cave-chambers-release-validation-2026-11-17, baseada nesse merge.

O log fornecido executou12testes sea_routesPASS e1173Hoenn, com8FAIL+1ERROR e
50skipped. As nove recusas são o selo final aindafalse (Unvalidatedrelease),
inclusiveSootopolis.validated. Não foi demonstrada nova regressão de pedra ou
câmera. Não trocarflags/SHAs, afrouxar contratos ou ignorar testes para aprovar.
A candidata atualc08cb777/versão7 e todas as suas provas continuam preservadas.

Corrigido oSyntaxWarning deescapes\l/\p no gerador do workshop, mantendo
exatamente osbytes do script emitido (SHA256d2a32a6d1a1891efb3cddd1699ce96133e88ef87467a16f5412406a1e474df4d).
CompilaçãoPython comSyntaxWarning comoerroPASS. Isso corrige o aviso; não o selo.

Trabalho retomado das cavernas: inventário confirma105eventos especiais em48
cavernas,14santuários,8cavernas costeiras e26grupos em mapas nativos. Há18
exteriores no atlas atual; nove usam o mesmo terreno compacto. Prévia técnica
dos interiores e bancos nativos preservada em.local/chamber-native-review.
Próximo: acessos próprios e105câmaras variadas com os próprios sprites,
exteriores maiores/distintos, migração8 e provas nativas; então completar
contrato/edições/ecologia/DEX/browser até a aprovação real dos gates.
Preservar IDs, NPCs de campanha, warps originais, flags de captura e arte doatlas.
Usar os lembretes deHere/AGENTS; não reutilizar provas antigas como atuais.

Último subpedido concluído: merge identificado, causa doCI confirmada e aviso
corrigido sem mudar saída do gerador. Pedido atual global ainda EM ANDAMENTO.
Nenhum PR novo aberto ainda, nenhum merge executado pelaIA e nenhum selo final.

HISTÓRICO PRESERVADO:

CONCLUÍDO — DUAS DIVISAS COM VISÃO DESATUALIZADA —17/11/2026
Pedido atual, trecho literal: “Consegue reparar isso em alguns lugares?
Identificar esse padrão, assim como identificou as rotas? Esses termos técnicos
tem que ser atualizados no aqui, como se fosse um lembrete skill pra não repetir isso”.

Identificado e reparado o desacordo entre layout declarado e ativo naRota131.
O cabeçalho agora aponta paraSkyPillar, já selecionado incondicionalmente pelo
script. Não redesenha terreno ativo, atlas, NPCs, warps ou flags. Os mapas
condicionais130/MirageIsland e111 não foram forçados a uma variante permanente.
Auditor reutilizávelaudit_neighbor_layouts.py:663mapas conectados; antes3variantes,
2com diferenças nohalo; após o reparo2variantes e1candidata comhalo diferente.
Os12patches literais próximos de conexões continuam candidatos para análise de
estado. O censo não certifica execução de todos os scripts nem alterações emC.

ROM congelada atual:c08cb7771a9731db995b7d99297c8b1ebcdd98d75a9ac5e50cdaef8dcff62c82
ELF:36989019fbf9b14e8ce93b96701c3c517bee965a6ab755d3c380ebcb9a16449f
marker:10a2b57e222d642aac218b0a4e04e4a296378fa0f5e237cff73c753123a97114
Fonte:.local/neighbor-layouts-src;freeze:.local/neighbor-layouts-frozen.json.
2212outputs,34080inputs exatos;532ativos/606slots;33207772bytes. Auditoria de
fontePASS, uma componente jogável e nenhum escape para aágua decorativa.

Na mesmaROM:Pacifidlog↔Rota131 eRota130↔Rota131 por controles. Quatro peças
de cada rocha corretas ANTES da entrada, depois e no retorno; três fases e18
capturas, BG/VRAM/paleta/pixels/quatro quadrantes conferidos. Dois bloqueios por
controles: um pela cidade e outro dentro da131; não atravessa as rochas. Uso de
fixtures iniciais declarado; após isso só controles/getters read-only. São dois
casos locais confirmados, não uma certificação de todas as divisas do jogo.
A regressão nativa das103peças+6extras passou novamente naROM atual:54casos,
210capturas e48aproximações de colisão; seis grupos sem aproximação segura.

Saves reais produzidos na6 junto às duas divisas reproduzem o fundo antigo.
Continue7 lê a rocha completa no grid; SAVE pelo menu e segundoContinue7
preservam o reparo, posição, altura eSurf. A versão7 limpa o fundo uma vez,
sem repetir traduções ou mudar atores/flags de saves6. Cinco edições candidatas
exportadas e coldbootsPASS; TESTE pública6→Continue7→SAVE→Continue7PASS.
356testes AtlasPASS; verificadores extras rejeitam prova de outraROM e água
antiga antes da entrada mesmo comflagfixed=true. Manifestos/ROMs/TESTE/save doPR
atualizados, sem selo final. Provas emdocs/design/neighbor-layout-camera-review,
referência compacta ematlas-surf-layout/neighbor-camera-checkpoint.json e cadeia
compilada ematlas-surf-layout/neighbor-layouts-v7. DeltaV7 reproduzível sobreV6/C8.

Lembrete obrigatório:Aqui/SKILL-DIVISAS-E-CAMERAS.md, apontado porAGENTS.md e
pela skillgba-map-review. Inclui apron/halo, map popping, layout declarado/ativo,
setmaplayoutindex, scripts condicionais, bancos/paletas/callbacks, diagonais e
cachemapView, com o roteiro antes/entrada/retorno/SAVE/Continue. O ZIP foi
sincronizado; nenhum freeze histórico foi substituído ou certificado como novo.

Último subpedido concluído: identificar o padrão, reparar essas duas divisas,
provar emROM/saves e registrar o lembrete técnico noAqui. Pendentes anteriores:
cavernas/câmaras, outros bancos/estados de mapas,39facesDive, treinadores/sprites,
DEX e release/browser globais. Continuamfalse os gates finais históricos.
PR112 normal aberto, sem merge; conferir SHA remoto após o commit deste lote.

HISTÓRICO PRESERVADO:

EM ANDAMENTO — VISÃO DO VIZINHO DESATUALIZADA —17/11/2026
Pedido atual (resumo): “Ok, uma coisa, temos que ter cuidado também com
rotas uma do lado da outra, modificadas, porque ao andar de um lado pro outro,
as vezes em uma rota, a visão da outra rota não fica carregada atualizada,
fica como se tivesse antes da edição, somente ao andar um pouco pro lado e
efetivamente chegar na rota modificada, que fica igual. Consegue reparar isso
em alguns lugares? Identificar esse padrão, assim como identificou as rotas?
Esses termos técnicos tem que ser atualizados no aqui, como se fosse um
lembrete skill pra não repetir isso”. Consulte a conversa para a formulação exata.

Censo fonte:663mapas conectados,3variantes declaradas por script,2com diferenças
na faixa de conexão e12patches literais perto de bordas. São candidatos, não
uma contagem de bugs confirmados. ROM5b5b confirmou duas divisas daRota131:
Pacifidlog→131 e130→131 exibem água onde o layout ativo tem uma rocha inteira.
Pela cidade, a faixa velha ainda é copiada para dentro pelo cache da travessia.
A Rota131 sempre selecionaSkyPillar; o cabeçalho estático aponta paraRoute131.

Reparo preparado: alinhar somente o cabeçalho131 ao layout já incondicional no
jogo e limpar uma vez o fundo salvo de6→7. Terreno ativo/NPCs/flags/warps não
são redesenhados. Rota130/MirageIsland eRota111 continuam condicionais. Quatro
testes da nova lógicaPASS. Fonte privada nova em preparação, sem editar freezes.
Nativebefore/after do reparo e publicação nova AINDA pendentes; atuais continuam
nas cinco candidatas103/versão6. Próximo: auditar/build/freeze novo; provar as
mesmas rochas antes/entrada/retorno, colisão, animação eSAVE/Continue; cinco edições.

Novo lembrete técnico obrigatório:Aqui/SKILL-DIVISAS-E-CAMERAS.md, vinculado por
AGENTS.md e gba-map-review. Cobre layout declarado/ativo, connectionapron/halo,
map popping, bancos/paleta/callback, diagonais e cachemapView. Auditor reutilizável:
audit_neighbor_layouts.py. Provas:docs/design/neighbor-layout-camera-review.
PR112 aberto; sem merge. Pedido anterior103+6concluído. Cavernas/câmaras e gates
globais anteriores seguem pendentes. Não alterar flags finais para mascará-los.

HISTÓRICO PRESERVADO:

CONCLUÍDO —103PEÇAS +6FRAGMENTOS DE VARIANTE —17/11/2026
Pedido literal: “Resolva essas 103 peças suspeitas”.

As103peças de52grupos/20mapas General foram reparadas; censo principal0órfãos,
462rochas completas preservadas. A revisão das12variantes de layout encontrou
mais6fragmentos reais naRota131, também reparados, com56instâncias completas
preservadas nas variantes. A rocha(2,7)..(3,8) daRota131/SkyPillar está inteira:
não foi apagada para imitar o layout principal. Altura, colisão, eventos, warps,
conexões, atlas e definições gráficas/paletas/animações existentes preservados.

ROM atual congelada:5b5b1ace4c9b681c22540168d0d142abd30b57628d26da9264d508a82bed929c
ELF:6242e03fda753aaf193ec584bcfe7494b15a7319f30e9f598728f913de487056
marker:6046b165b9fd07ff455f4eca7facc115e12827718a2735cee02e98ff70aef6d5
Fonte:.local/atlas-rocks103-runtime-src;freeze:.local/atlas-rocks103-runtime-frozen.json.
34080inputs conferidos;2211outputs;532mapas ativos/606slots;33207772bytes.
Versão6 limpa o fundo salvo de4/5 uma única vez e preserva migrações anteriores.

Prova na mesmaROM:54casos,103células originais+6extras, duas testemunhas da
rocha completa preservada,210capturas, três fases, quatro quadrantes/oito words,
BG/VRAM/paleta/scanout/RGB conferidos. Colisão lida em todas;48aproximações
seguras testadas por controles contra bloqueio. Nos outros6grupos, não havia
aproximação adjacente nessa componente física preservada; não inventar passagem.
Fixture de party/progresso/posição/modo declarada; após colocação só controles
e getters read-only. Isso não equivale a percorrer20mapas ou jogar a campanha.

Cinco edições exportadas e coldboots PASS; TESTE pública2→Continue6→SAVE pelo
menu→coldContinue6 PASS. Baterias privadas4 e5 passaram o mesmo roundtrip.
Prova adicional junto ao fragmento: save real naROM4 com055A/055B naRota110,
Continue6 lê0589/0589, SAVE e segundoContinue mantêm o reparo e posição/modo.
Grid lido só daRAM, com offsetof da struct compilado emARM; nenhum setter no
coldboot.349testes AtlasPASS; depois10testes checkpoint e2de corrupção nativa
PASS, incluindo pixel adulterado comhash renovado e prova deROM antiga.

As cinco ROMs candidatas, bateriaTESTE, checksums e manifestos doPR112 foram
atualizados. Provas novas versionadas emdocs/design/atlas-surf-layout/rocks103-v6;
freeze históricof2 e seus testes permanecem intactos. Evidência completa em
docs/design/native-rock-fragments-review, incluindo antes/depois20mapas, variante,
54casos e saves. Snapshotdelta preparado contraC8 preserva todos os2211hashes.
O ZIP mantém referência autenticada ao material completo do repositório.
Reprodutores:prepare_atlas_surf_redesign.py;validate_atlas_103_rocks_native.py;
verify_atlas_103_rocks_native.py;validate_cold_boot.py --expect-cell X Y WORD;
verify_atlas_surf_checkpoint.py. Não compilar fontes congeladas.

Último subpedido concluído: corrigir/provar as103peças e os6extras encontrados.
Pendentes do pedido anterior: cavernas externas grandes/diversas,105câmaras com
entradas próprias, demais bancos de rochas,39faces de bordas/Dive, provas nativas
de96treinadores/7sprites,261declaraçõesDEX, browser e release global. Flags de
release continuamfalse;8FAIL+1ERROR históricos não foram mascarados. Sem merge.
PR112 normal:https://github.com/brunotellesbt-sys/AiKalicaAiCrlBR/pull/112

HISTÓRICO PRESERVADO:

CHECKPOINT 103 + VARIANTES REAIS —17/11/2026
Pedido literal: “Resolva essas 103 peças suspeitas”.

As103correções da fonte foram compiladas na preparação preservada
.local/atlas-rocks103-src (ROM1ab2baa41aac5b5bb4ea3d1bcb7866b5c6fa67f9c7280766d900747724f78fea).
O emulador verificou os47primeiros grupos, mas aRota131 carrega pelo script
LAYOUT_ROUTE131_SKY_PILLAR. A rocha(2,7)..(3,8) dessa variante está completa:
conservar suas quatro peças. O censo adicional das12variantesGeneral encontrou
seis fragmentos reais diferentes naRota131; todos recebem reparos explícitos.
Preservar as56instâncias de rochas completas nessas variantes, além das462
nos layouts principais. Seis testes de integridade/deriva/eventos/doadoresPASS.

Preparador e runner agora verificam layouts nativos ativos por ponteiroELF,
54grupos e109células, com duas testemunhas extras da rocha completa daRota131.
Versão6 preserva migrações anteriores e limpa só o fundo salvo de baterias4/5.
Fonte nova em preparação:.local/atlas-rocks103-runtime-src, sem alterar nenhum
snapshot congelado. Próximo: compilar/congelar, provar pixels/animação/colisão,
SAVE/Continue e cinco edições. NENHUM PASS nativo completo ou release final
é declarado neste checkpoint. PR112 aberto; públicos aindaf2. Cavernas,
câmaras individuais e demais requisitos anteriores permanecem pendentes.

HISTÓRICO PRESERVADO:

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

# Continuidade técnica de Pokémon Journey

## Retomada atual — 16/11/2026 (precede o histórico abaixo)

PEDIDOS ADICIONAIS: mover barqueiro para a casa mais próxima em Pacifidlog e
eliminar pedras partidas de Slateport. Implementados na fonte e ROM privada.
CapitãoTown(11,27)→House3(7,6), porta(12,24); mantémJourney_FerryPort11/ID4,
barcoID5, todos os outros atores/warps. A aproximação e saída ficam livres.
Slateport: duas fatias verticais0x164/0x16C na encosta em(36,6) e(38,15)
retiradas inteiras; quatro células viram0x190 do mesmo banco, mantendo todos
os bits físicos. Nada de prolongar pedra por cima de floresta/chão da cidade.
Renders inteiros fonte antes/depois de cidade/House3/Slateport revisados.

Build privado533mapas/1959inputs em.local/atlas-harbor-fixes-src, congelado:
ROMe8e0ae3d33c1b77d3cc5c6012a67f44f920ddd70fd40c46b4ffac781937fc413;
ELFdde63270413a14aa79350a05573f3b83a33d22711f26f04175fdbcbcd62c37b5;
marker6b7dd869595e21b9f90672fd1202fd08a3d79d32755a8598cb63aeb180cab411.
Uso32922104bytes. Derivados do build anterior foram COPIADOS para cache
privado após conferir hashes congelados; nenhum source verificado substituído.
Capitão PASS por controles: ponte nos dois sentidos, porta real/House3,
moradores1/2 ecapitão4 presentes, barco5 preservado, menu/port11,
ferryHouse3→Mossdeep e volta ao píer, reentrada na casa, SAVE pelo menu.
Boot novo sem writes de memória e Continue emHouse3[7,7], pedestre3 PASS.
Queries durante menus usam leitura direta de RAM; não usar a trampoline
de script paraVarGet enquanto o evento está ativo, pois interfere na conversa.
Encostas: quatro metatiles carregados0x190, colisão1/altura0, barreiras reais
por controles e capturas nativas revisadas PASS.
O quarteto sul150/151/158/159 foi conferido carregado na câmera deSlateport;
travessiaSlateport→Route109→Slateport por controles e capturas dos dois lados PASS.
As metades que atravessam essa conexão nativa pertencem ao mesmo objeto
completo. Preservadas; um render recortado na borda não autoriza apagá-las.
Three/Birth PASS na mesma ROM, sem reaproveitar8602. Cinco edições privadas exportadas e bootadas,
TESTE com save distribuído.302testes atlas PASS em77,902s. Evidência completa
e1959inputs exatos compactados:harbor-native-review. ROMs públicas continuam
anteriores; não declarar validação global ou novas ROMs públicas neste lote.
O grafo dessa composição533, igual aos inputs compilados, continua15SCCs.

Prévia nova separada: saída de Slateport na face leste em39,45..58, água
nativa real e livre de conexão; Route134 existente cobre só0..39. Doadores
Route109 dos mesmos bancosGeneral/Slateport, recife inteiro1tile0x1F9.
Guardas rejeitam contato inventado e sombreamento de conexão nativa anterior.
EverGrande: altura3 mantém face nativa completa; novos contatos laterais com
mar1 ganham transição0 só a partir do segundo passo, em água nova. Fonte
538mapas/5SCCs,18cavernas e7portos na maior componente, globalFAIL. Esse delta
NÃO está na ROMe8e0. Relatóriocoast-new-exit-review; reprodutor recebe
--additional-native-edges. Nova partição exige migração da candidata533 antes
de materializar. Restam4clusters: BondBridge,Pacifidlog,TreasureBeach e ilha
com treinador emRoute12. Projeção nativaUI localiza candidatos, não autoriza
exclusão completa nem substitui acesso físico/retorno por controles.

Detalhes emerrors/2026-11-16-harbor-actors-rocks.txt. As duas correções visuais
pedidas não encerram o objetivo anterior. Revisão global das outras famílias
de rochas, rede/migração/ecologia/saves/5edições/publicação/PR seguem em curso.
8FAIL+1ERROR finais persistem, flagsfalse preservadas, não abrir PR ainda.
Checkpoint remoto anterior3f77734dd98790e5feaa4a1a8033d24e3440b5e2.

Lotes anteriores:

Pedido atual: “Tá e por que não resolveu? Faz as ligações e valide a rom. Já pedi.”
Trabalho continua até ligações/provas finais; checkpoint parcial não encerra o pedido.

Three: oceano sul nativo de seis tiles contorna o terminal inteiro;48x20→48x27,
apenas nove recifes anteriores abertos. Eventos/barcos/terminal e coordenadas
preservados. Source171 imutável; source privado.local/atlas-connections-src,
1956inputs, ROM8602c36db5f3329d93f56d50138b6eb54785c8892fc7f6f2419b99e568675a81,
ELFb6087220302cc2263d98b6738afbedb98d9faa046b9cdb7a7ee4292e3d13dc82,
markera14a081092c7a545c33bec1a6787bfb7d550b2f6a71a1b0566014d6315c36776.
Build usado32922104/33554432bytes. Não escrever nesse source/ELF/ROM congelado.
Circuito Three por controles PASS: bloqueio de pedestre, promptSurf, contorno
leste→oeste, terminal bloqueado, conexão Coast31 e retorno, recife sul bloqueado,
oeste→leste, desembarque. SAVE real pelo menu/export131072bytes e novo boot
Continue(Three13,17,pedestre,altura3) PASS. Birth refeito na mesma ROM PASS;
boot sem bateria PASS. Cinco edições privadas exportadas/bootadas PASS,
TESTE com/sem bateria distribuída. Não extrapolar boot para gameplay completo.
Fonte preparada compactada e hashes/capturas/controles/saves em
docs/design/atlas-surf-layout/three-native-review. As cinco ROMs públicas/save
e gates de release continuam anteriores. Essa ROM não contém os deltas abaixo.

Titans NA FONTE: extração do stamp JourneyWorldSea03:000 incorporou as duas
colunas62/63 de recifes do limite antigo. No novo local,12células(y19..24)
atravessavam a rota literal. São12objetos completos0x243, words0x1643; oito
words BG conferidos: água41C6/41C7, recife superior41E2..41E5. Substituídos por
água0x112B do mesmo banco em(61,19), nunca por recorte da montanha/praia.
Guardas de hash/posições/doador/rota/eventos e teste real dos374stamps com
allowlist independente desses12. Migração exata pula bloqueios antigos e
continua rejeitando alteração de célula antiga transitável. Renders completos
fonte antes/depois revisados em titans-perimeter-review; ainda sem provaROM.

Costas NA PRÉVIA: esquinas molhadas do raster6/8 eram recusadas por não terem
vizinho antigo molhado. Reabertura exige opt-in explícito, componente/altura
nativos, conexão antiga recíproca limitada, words/hashes de ambos e nenhum
edit do nativo. Route105 encaixa a curva no pixel19,101. Route128 usa sua
saída sul real na mesma componente, em(128,95). As reservas de cenários/Dive
continuam protegidas. Franjas de cavernas agora se vinculam ao underlay atual
na prévia. Diagnóstico reproduzível, sem monkeypatch ou escrita na fonte:
python tools/hoenn/diagnose_atlas_connection_repairs.py --source .local/generated-area-review-src --output docs/design/atlas-surf-layout/coast-connection-review
Banco C real + censo nativo recalculado + grafo:7SCCs,537mapas gerados,
18cavernas e7portos na maior componente. Auditoria continuaFAIL porque ainda
há sete componentes. Não aceitar flags falsas nem reusar prova8602 para isso.
Ficam correntes oeste/Pacifidlog, pixels de mapas nativos, ilha com treinador
junto a Route12 e contato lateral altura3 em Ever Grande. ProjeçãoUI ajuda a
localizar, mas sozinha não autoriza excluir raster nem inventar conexão.
Nova partição altera identidades/retângulos da candidata533: migração dessa
candidata para geometria nova é obrigatória antes da materialização/entrega.
`compose(coast_proposals=...)` reautentica todos os inputs/bocas/bancos/planos;
prepare/publicação seguem sem atalho para essa prévia. PR continua adiado,
8FAIL+1ERROR finais ainda pendentes. Não houve publicação de ROM nova.
Testes do lote:297atlas PASS em56,496s. Os dois erros iniciais desse conjunto
eram arquivos rastreados ausentes pelo sparse checkout; recuperados do mesmo
HEAD e testes repetidos sem alterar seus contratos. Não confundir com os
8FAIL+1ERROR de aprovação final, que continuam pendentes.

Lotes anteriores:

Segundo lote concluído NA FONTE: franja nativa das18cavernas usa9tiles da
reserva existente em vez de3; todas as células precisam de palavra Surf
exata no parent. Nenhum core/objeto/evento foi cortado ou movido. São5126
células adicionais,19outputs alterados (18map.bin e tabela de migração).
Os533IDs/origens/dimensões permanecem iguais à candidata distribuída;
core de374stamps e todos os eventos continuam sujeitos ao teste real.
Auditor C de bancos e grafo físico:17->16SCCs, Alvorada reunida à maior
componente;15/18cavernas e6/7portos nela. Esse diagnóstico não éPASS global.
Titans/Artisan/Mare e Three ainda pendentes, além dos demais clusters regionais.

287testes atlas PASS; guarda adicional verifica cada palavra da franja contra
o parent e identidades da candidata172. Renderizadas/revisadas18cavernas
inteiras com NPCs de fonte antes/depois. Não são capturasROM, nem certificam
câmeras/animações/viagens. Relatório e provas em
docs/design/atlas-surf-layout/cave-fringe-review. Fonte privada materializada
em.local/atlas-fringe9-src,1955inputs preparados, sem compartilhar inodes.
Sem compilação/novaROM neste lote; não reutilizar Birth/capturas anteriores
como validação do reparo. Gates finais e cinco ROMs/save preservados.

Checkpoint anterior confirmado4aeaaa5a2ced857137fb63595376ff54f75add50.
Pedido principal continua incompleto; PR só após corrigir os nove bloqueios,
conforme pedido atual. Próximo: ligações restantes, build privado/freeze,
provas por controles e saves/edições, depois publicação/PR.

Registro do primeiro lote:

Pedido literal mais recente: “Então bora progredir, comece a fazer”. Antes:
“Ok corrigiu os erros? Aqueles 8 erros em código e + 1? Abra o pr ao corrigir”.
Não abrir PR enquanto os8FAIL+1ERROR de release persistirem. Checkpoints/pushes
continuam autorizados. PR111 integrado em main8a7b78a6ca59bdc0d16c112093866cc127c157c8;
branch nova fix/atlas-continuity-2026-11-16. Workspace antigo não recuperado.

Base171 reconstruída por restore_generated_area_review.py e conferida:
171camadas/32250inputs/manifesto d3a06e90f222f83a3e7778df52895594f6bd02719a8bc925151d7d80bfa1fed7.
ToolchainARM14.2.1 instalado; ainda não há novo build. Ocaso WIP reparado com
endpoint histórico(141,111) e contrato exato das nove branches publicadas,
sem modificar os hashes da arte ou os geradores históricos. Divergência do
marker completo foi registrada, não aprovada trocando seu pin.

Diagnóstico independente baseline/prévia:533mapas,622mapas auditados,
86175células de água,17SCCs nos dois;1955outputs idênticos byte a byte, IDs,
origens/dimensões preservados. Os sete pixels autenticados não viram conserto
físico porque estão nas máscaras nativas das reservas. Não atribuir os15->10
componentes do raster abstrato à rede do jogo. Fonte/graficamente histórico,
não prova de viagemROM.285testes atlas passaram neste primeiro lote.

Arquivos novos: atlas_surf_occluded_routes.py, diagnose_atlas_occluded_routes.py,
test_atlas_surf_occluded_routes.py, fixture portátil171, relatório/gz em
docs/design/atlas-surf-layout/occluded-routes-review e registro em
errors/2026-11-16-cave-underlay.txt. Prévia exige preview_output e não pode
materializar fonte. Fonte normal e cinco ROMs/save mantidos.

Último concluído: reparar/reproduzir a extração WIP e provar seu efeito nulo
na candidata física atual. Incompleto: as17SCCs, Three/costas/projeções,
saves/ecologia/visuais/edições e provas de release. Próximo: estudar e testar
a franja nativa completa das cavernas, mantendo core/bancos/atlas, depois
build privado/freeze e provas reais. Não abrir o PR nem promover flags finais.

> Entrada consolidada e atual para a próxima janela: [Aqui/README.md](../Aqui/README.md).
> Estado até o checkpoint1bf71eda2d8276a377e38e84cc4baaaad070c085.
> Atualização atual: guia e pasta Aqui sincronizados também no ZIP; integridade conferida. ROMs/save não foram alterados.

Atualizado em 15/11/2026 (UTC). Este é o ponto de entrada permanente para
outra IA ou outro ambiente. Atualize-o a cada lote verificado, antes do
checkpoint remoto. Mantenha o pedido pendente até a entrega completa.

## Estado executivo verificável

As **cinco ROMs desta branch foram atualizadas** para a candidata **172 /
atlas-surf-layout**: quatro edições, TESTE, save e ZIP. A base anterior validada
é **171 / generated-area-review**. A geografia global continua em correção;
não existe release 172 final validado. O workspace antigo não foi recuperado e não foi
apagado, resetado, substituído nem arquivado por esta tarefa.

Repositório: https://github.com/brunotellesbt-sys/AiKalicaAiCrlBR
Branch de trabalho: `fix/atlas-surf-layout`.
Base do jogo: `7ec174b8f7d0c621ec9a60d8b771619e86628889` (PR #108).
Checkpoints de reconstrução: `c03dac777eae6199d4be2643f77d4c862c111851` e
`f0860a7434112f0a16ed0f413322ee3240479a6b`.
O [PR #109](https://github.com/brunotellesbt-sys/AiKalicaAiCrlBR/pull/109)
foi integrado externamente em `9db77933fba27108b00e4d717219e5d01c165df6`.
Esse merge preservou ferramentas e documentação, sem atualizar as ROMs.
O pedido mais recente exige **PR normal, sem rascunho**, mesmo durante a
continuidade; suas pendências devem estar explícitas no corpo do PR.
O PR normal [#110](https://github.com/brunotellesbt-sys/AiKalicaAiCrlBR/pull/110)
foi integrado externamente em `5dc9e1b1273515f7837c1ba7013273157e641aec`.
Ele incluiu diagnóstico, ferramentas e documentos, sem publicar ROM172.
A branch foi atualizada por fast-forward, preservando o trabalho. O [PR normal #111](https://github.com/brunotellesbt-sys/AiKalicaAiCrlBR/pull/111)
está aberto para a integração, com pendências explícitas. Push conferido:
`3ae46505cc076d0ad9a9582f0791f1fd6f3ca860` (inclui as cinco ROMs).
O reparo atual da consulta às provas históricas está descrito no fim deste guia.
Os binários atuais e suas provas estão em [roms/CANDIDATA-172.json](../roms/CANDIDATA-172.json);
boot passou nas cinco e a TESTE passou Continue → salvar pelo menu → Continue.
O ZIP contém este guia e as provas atuais. A publicação final/Pages permanece
pendente, sem promoção artificial dos contratos.

O documento histórico completo recebido está em
[RETOMADA_TECNICA_POKEMON_JOURNEY.json](RETOMADA_TECNICA_POKEMON_JOURNEY.json).
Leia as 35 seções e siga `recovery_plan`, usando este arquivo para distinguir
o estado atual dos relatos do ambiente antigo. Só os dois identificadores
privados foram omitidos da cópia pública; o original integral foi salvo fora
do Git como `/workspace/RETOMADA_TECNICA_POKEMON_JOURNEY.json`.

O usuário acrescentou o delta integral
[ULTIMO_PEDIDO_POS_PR108.json](ULTIMO_PEDIDO_POS_PR108.json), com 21 seções.
Ele fixa o pedido principal: corrigir a malha física gerada conforme o atlas,
sem mexer na arte e sem usar apenas GPS para esconder o defeito. Suas
contagens e resultados de execução são históricos; não substituem provas
atuais. A referência histórica a rascunho não revoga o pedido posterior de
PR normal. Último checkpoint remoto conferido antes deste lote: `bd8c477d9145e44e56e687900de35f7f67220537` (integrado no merge110 acima).

## Pedidos do usuário e resultado

### Último pedido de continuidade, completo

> Continue o progresso, o outro ambiente deixou esse documento. Abra um pr de verdade, e não um em rascunho. Crie um documento dentro no jogo tbm, totalmente técnico, pra próxima I.A. em outros ambientes entender do que se trata, dessas regras, do que fazer, e do último pedido completo, resolvido e do último pedido incompleto, não finalizado também, sempre atualizando ele.

Atendimento nesta etapa: JSON histórico salvo, este guia criado, leitura
obrigatória registrada em AGENTS.md e inclusão dos documentos no empacotador
do jogo. O PR #110 foi aberto como normal e seu estado foi confirmado.
A manutenção contínua deste guia
é um requisito permanente, não uma tarefa que termina com sua criação.

### Últimos pedidos resolvidos

- “Mas eu quero que atualize as roms com as modificações feitas, já pedi.”:
  as cinco ROMs foram recompiladas e substituídas nesta branch, com ZIP, save
  TESTE e manifestos de candidata. O PR normal #111 recebe esses arquivos.
  Isso conclui o checkpoint de binários solicitado, sem concluir a correção
  global do jogo; os resultados e hashes atuais estão no fim deste guia.

- “Conecte ao meu github” e seleção do repositório: conta e acesso de
  leitura/escrita confirmados para `brunotellesbt-sys/AiKalicaAiCrlBR`.
- Subtarefa da retomada: reconstruir uma base operacional verificável da
  revisão 171. As 171 camadas, os 32.250 inputs e a compilação ARM foram
  reproduzidos. ROM e ELF coincidem exatamente com os hashes históricos.
- Preservação remota dos dois primeiros lotes: pushes confirmados, PR #109
  criado e posteriormente integrado. Isso não recuperou os arquivos antigos.
- Pedido de 14/11 para documentação técnica permanente e PR normal: guia e
  JSON no repositório, AGENTS atualizado, inclusão no ZIP verificada,
  checkpoint 6aa7e90 e PR #110 normal confirmado. O pedido principal de
  corrigir e entregar o jogo continua incompleto, como descrito abaixo.

### Pedido principal incompleto — manter aberto

> O trabalho pendente é corrigir o jogo, especialmente a geometria das rotas de Surf, os acessos e os defeitos visuais, validar as ROMs e entregar as alterações pelo GitHub. Configure apenas o necessário para executar esse trabalho e prossiga autonomamente.

O escopo completo desse pedido, regras e roteiro constam no JSON histórico,
especialmente `primary_user_goal`, `latest_generation_plan`,
`completion_order`, `release_contract` e `earlier_user_requirements_to_preserve`.
A entrega só termina com geografia correta, cinco edições atualizadas,
provas atuais, save TESTE, ZIP, manifestos, navegador, Pages e PR. Não pedir
ao usuário que reconte o histórico ou execute os comandos técnicos.

Resumo fiel confirmado no último delta recebido:

> Consertar as rotas de Surf geradas para corresponderem ao mapa-múndi. Não alterar o mapa-múndi. Se necessário, mudar posição, formato, dimensão, conexões e acessos das rotas físicas.

Essa confirmação preserva o escopo principal. Não reiniciar ginásios, torneio
ou conteúdo integrado, nem reduzir o problema a mais uma passagem local.

## Regras permanentes

Leia `AGENTS.md`, `.agents/skills/gba-map-review/SKILL.md`, `errors/README.md`
e o RESUMO de `docs/AJUSTES-GBA.txt` antes de modificar mapas. Consulte
`assets/tiles/` e `tools/hoenn/inspect_map_tile.py`; IDs dependem dos bancos.

1. **Não alterar a arte do mapa-múndi.** Corrigir posições físicas, formatos,
   distâncias, direções, conexões e acessos. Ciano é o jogador; vermelho é o
   cursor. O nome sob o cursor não prova a localização do jogador.
2. Não usar GPS para esconder uma rota física errada. O erro de referência é
   Sea01(44,10), GPS(137,55): dez passos UP deslocavam vinte pixels para leste.
3. Escala de oito tiles por pixel; corredores de seis; posição afim global.
   Evitar tabelas novas de GPS por célula; limite da ROM: 32 MiB.
4. IDs append-only; manter IDs aposentados para saves. Nos grupos novos,
   `mapNum<100`; tanto `WarpData.mapNum` quanto `mapGroup` são `s8`.
5. Preservar objetos inteiros, eventos, NPCs, barcos, grafismos, atributos,
   paletas, animações e missões já integradas. Não gerar desenhos novos.
6. Não apagar ou limpar preparações parciais sem diagnóstico e preservação.
   Não editar árvores congeladas por hardlinks compartilhados.
7. Não compilar, gerar nem empacotar enquanto leitores usam o mesmo source,
   ELF ou ROM. Congelar bytes antes das provas e conferir hashes ao terminar.
8. Declarar fixtures iniciais. Depois delas, viajar por controles; getters
   read-only podem usar trampoline declarado. Não escrever posição, altura,
   câmera, VRAM ou resultado para aprovar um percurso. A bridge não passa
   automaticamente argumentos extras além dos quatro registradores ARM.
9. Não promover hashes, flags de aprovação ou NATIVE_CONTRACT_FINALIZED para
   aceitar trabalho incompleto. Capturas antigas não validam uma nova ROM.
10. Atualizar este guia e `errors/ESTADO-DA-TAREFA.txt`, verificar, commitar,
    fazer push e conferir SHA remoto a cada lote. PR normal foi pedido
    explicitamente; abrir o PR não significa publicar uma ROM incompleta.

## Arte imutável: hashes dos bytes reais

Os hashes são dos bytes little-endian das arrays interpretadas, não do
header completo nem de sua serialização JSON. A base reconstruída coincide
com os quatro valores recebidos:

| Array | SHA-256 |
| --- | --- |
| sWorldTiles | 09e5334176c31cc5c6fa30ed9a2e46b6f90df524ebfa0a92b3f2403742fa7b9f |
| sWorldTilemap | ae2c327dad6d9ab1a1897369b793969e1229d18f45d0add22a79e4ba5a7a3196 |
| sWorldDetailPixels | a7a9ce35ca044ee2df75bd49878a79536fa42f05fb1cdb0cd0593593db3b58f2 |
| sWorldPalette | da38567f7f701d0d76c5c53ef00407fc6eeb75632efdf6121590b9b2f7aca73a |

## Arquivos reais desta reconstrução

| Módulo | O que existe agora | Limitação |
| --- | --- | --- |
| restore_generated_area_review.py | Reaplica/valida a cadeia 171, preserva e recusa inputs alterados | Não recupera o ambiente antigo |
| atlas_surf_truth.py | Decodifica arte, hashes dos bytes e classificação com testemunhas explícitas | A classificação física dos 45 pixels nativos falta |
| atlas_surf_geometry.py | Raster afim e chunks/conexões sem GPS por célula | Não integra cenário, atores ou adaptadores |
| validate_atlas_surf_layout_plan.py | Auditor independente do raster, eixos, distâncias, IDs e emendas | Prova do plano, sem certificação source/ROM |
| atlas_surf_layer.py | Materializa chunks com doadores de banco explícitos e IDs preservados | Não aposenta a rede antiga nem move os eventos |
| atlas_surf_runtime.py | Índice direto de mapa, bins espaciais de 32 tiles, GPS e hook visual | C dos chunks com stride 8; desempenho na rede final pendente |
| atlas_surf_physical.py | Clipping de cópia, halo físico por dono global, prioridade de costa nativa e guarda de conexão | C e travessias nativas de três mapas passaram; repetir na rede final |
| prepare_atlas_surf_diagnostic.py | Prepara três mapas privados em L, um com quatro tiles de largura | Fixture sintética, sem substituir a geografia real ou release |
| atlas_surf_ecology.py | Aliases explícitos dos pools/habitats e header nativo | Auditoria de gatilhos, áreas Dex e Gen4/Gen9/TESTE final falta |
| atlas_surface_batteries.py | Código da migração 2 e validação dos destinos | Não é o harness histórico de baterias; Save/Continue nativo falta |
| atlas_surf_source.py | Lê bancos/terreno e compila o enum/flags C nativo, detectando alterações dos inputs | Componentes locais, sem certificado do motor |
| atlas_surf_coasts.py | Inventário dos 273 IDs antigos e fechamento exato de duas células de Route114 em overlay | Não aposenta nem reloca mapas na candidata |
| atlas_surf_adapters.py | 33 componentes costeiras candidatas em 29 hosts; 32 com contato de altura compatível | Ever Grande requer revisão; nenhum novo destino atribuído |
| atlas_surf_pois.py | 18 portais recíprocos, cinco Dive e sete portos com terreno real | Inventário, sem criação dos novos acessos |
| inventory_atlas_surf_parent.py | Relatório reproduzível vinculado a 1.699 inputs e ao contrato completo 171 | Não prova conectividade global nem ROM |
| atlas_surf_native_scenery.py | 17 células e gráfico privado de Birth, corpo bloqueado | Prova do corpo passou no diagnóstico v2; repetir na candidata final |
| validate_atlas_surf_physical_native.py / verify_atlas_surf_physical_native.py | Quatro travessias, timing em frames, direção, diagonal, bloqueio e pixels | Diagnóstico de três mapas, sem certificar escala436 ou release |
| validate_atlas_surf_birth_native.py | Viagem por controles, avatar, bloqueio, Surf e Harbor | Repetir sobre o artefato final |

As APIs reconstruídas diferem das antigas descritas no JSON. Não supor que
um nome de módulo significa recuperação ou equivalência de implementação.
POIs/costas/adaptadores têm inventários e APIs de integração. Dive, cenário,
SCC e auditoria ecológica agora existem, com testes C/source; a aplicação à
rede completa ainda está pendente. Faltam registros concretos de todas as
costas, colocação completa de cenário e candidata integral, contrato172 e
pipeline final de publicação. Não confundir módulos existentes com release.

O diagnóstico de todos os pixels azuis produz 347 chunks, 74.688 células de
água e 15 componentes. Inclui pixels nativos e ícone; **não é plano final**.
Não alterar regras para obter os números históricos 436/273/33/171.

## Base e diagnósticos disponíveis nesta máquina

Não presumir que `.local` existe no ambiente seguinte. Verifique cada arquivo.

| Caminho | Conteúdo |
| --- | --- |
| .local/generated-area-review-src | Fonte 171 estável, sem compilar nessa árvore |
| .local/generated-area-review-restored.json | Relatório dos 32.250 inputs e 171 markers |
| .local/review171-build-src | Cópia privada compilada, ROM/ELF 171 exatos |
| .local/review171-build.log | Build base; ROM usada 32.647.568 bytes (97,30%) |
| .local/atlas-smoke-build-src | Dois pixels de atlas num chunk isolado, sem ligação à rede completa |
| .local/atlas-smoke-build.log | Build diagnóstico; não é candidata final 172 |
| .local/atlas-birth-smoke-native/birth-native.json | Prova nativa de Birth e capturas ligadas à ROM diagnóstica |
| .local/atlas-smoke-v2-src | Nova cópia com corpo de Birth bloqueado, stride 8 e guard ecológico corrigido |
| docs/design/atlas-surf-layout/diagnostic-birth-native | Relatório e capturas v2 preservados no Git; explicitamente diagnósticos |
| .local/atlas-reconstruction-tests.log | Testes atuais da infraestrutura de reconstrução |
| .local/ci-python/bin/python | Python com Pillow 13.0.0, numpy 2.3.5 e scipy 1.16.3 |
| .local/ci-env.sh | Toolchain ARM 14.2.1, binutils e dependências locais |
| .local/mgba-bridge-ci.so | Núcleo mGBA 0.10.5 e bridge preparada |

Base 171:

```text
ROM:    52156af727381fb5b47dacf83f8f57696e05dae05c4971368310b98515eba935
ELF:    000a4795be90877c83c4b133b3efa5234d042e8414e832d5e0e687ae4304bd46
marker: a5e99f28bc3fbb682a496561a48a0334609afe4c4651cf6b5f8b5a015ad34fa9
inputs: d3a06e90f222f83a3e7778df52895594f6bd02719a8bc925151d7d80bfa1fed7
```

Diagnóstico de integração (marker `.journey-atlas-stage-smoke`):

```text
ROM: f424aaf4511161d83f6bf87f886e4665e5a82e6f0b8310ae2476f92ce57daeda
ELF: 02f7af0b36a04101e9365894f1caecf9a66a6bffb3ed645d581d3f8cf10d2358
```

Esse smoke usa um chunk isolado e uma relocação sintética. Não distribuir
essa ROM, não transformar o mapeamento sintético em migração final e não
reutilizar suas provas para outra candidata. Sua compilação precede os
ajustes posteriores do stride 8 e da ordem do guard de espécies de evento.

O novo smoke v2 também usa dois pixels de atlas em **um único chunk**;
não há prova de travessia entre chunks nesse diagnóstico. Compilou com
stride 8 e o guard ecológico corrigido:

```text
ROM: b058983d8c07cb7a501d426592dd1ed574cd4858880da94cd52c5f63d8c29fa7
ELF: 8fc3803a6cec06ff72ca07eae435658b6e29836d7abaaa6d99b94daec8c6ccb0
ROM usada: 32.649.504 bytes (97,30%). EWRAM: 245.436; IWRAM: 28.660.
```

Fonte, ROM e ELF v2 ficaram estáveis durante a prova de Birth. Ela passou
com bloqueio do corpo contra Surf, saída/retorno pelo lado, Harbor nos dois
sentidos, pixels de cabeça/corpo/pés e bloqueio de pedestre na borda.
O relatório e seis capturas estão no diretório diagnóstico versionado acima;
o resultado mantém `diagnostic_build=true` e `final_release_validated=false`.
Uma repetição com vínculos completos conferiu, antes e depois do percurso,
os hashes da ROM, ELF, marker e dos 21 inputs preparados desse smoke. Seu
relatório local está em `.local/atlas-birth-smoke-v2-bound-native`.

Comandos úteis, sem substituir a inspeção dos arquivos:

```sh
git status --short --branch
git ls-remote origin refs/heads/main refs/heads/fix/atlas-surf-layout
df -h /workspace
df -i /workspace
free -m
.local/ci-python/bin/python tools/hoenn/restore_generated_area_review.py --source .local/generated-area-review-src --verify-only
.local/ci-python/bin/python -m unittest discover -s tools/hoenn -p 'test_atlas_*.py' -v
```

O proxy do sandbox recusava Git e o socket Docker; as mesmas operações
funcionaram fora do sandbox com autorização da plataforma. Não extrair tokens
nem contornar TLS/proxy. Esse problema não explica o 404 do ambiente antigo.

## Provas atuais e limites

64 testes de plano, geradores, materialização, runtime, halo físico, ecologia,
migração C e inventário nativo passaram no lote atual. Runtime: todos os 65.536 IDs e centenas de milhares
de coordenadas; divisão negativa usa floor verdadeiro. Migração C: versões
0/1/2, Treasure +8 uma vez, jogador, cinco referências, warp por ID, view e
idempotência. Um teste adicional verifica documentos legíveis no plano do ZIP.
Esses testes não são baterias do emulador.

Birth na primeira ROM diagnóstica: ponta de madeira, avatar com pixels nativos,
pedestre bloqueado na borda, saída com prompt Surf, retorno para Harbor,
volta à ilha por controles e hashes ROM/ELF intactos. NPC/progresso/posição
inicial e supressão de encontros foram fixtures. Não é campanha completa,
nem prova final das cinco edições, animação de todas as praias ou Save/Continue.
O JSON posterior esclareceu que o corpo 5x3 deve continuar bloqueado. O
primeiro reparo abria água nesse espaço; foi substituído por corpo inteiro de
madeira preservando todos os bits de colisão/altura. A prova foi repetida e
passou na v2, incluindo o corpo bloqueado, sem reciclar o resultado v1.

## Inventário físico da base 171, reproduzido nesta etapa

Relatório versionado: [parent-inventory.json](design/atlas-surf-layout/parent-inventory.json).
SHA-256: `19c48184ecc6e3ab80e30cf0f2ec387af50a4cdd616adc721677f9cccb81eeac`.
Manifesto dos 1.699 inputs lidos pelo inventário:
`90f69251d9080c45778560214cfe1c39bf74d7f11544ee15f578e78ed13bc8e7`.
O contrato completo dos 32.250 arquivos da base 171 foi verificado antes e
depois; nenhuma fonte foi alterada e as quatro arrays do atlas coincidem.

Os 273 IDs derivam dos dados: 266 mapas oceânicos Journey ativos e sete
exteriores de portos antigos sem eventos. O protótipo isolado HoennCrossing
fica fora. O Shipyard (96,40) conserva porto, nove atores e warp completos;
seu centro azul autenticado de ícone não vira rota oceânica duplicada.

Das 56 interfaces antigas com mapas preservados, as células de Surf reais
formam 33 componentes candidatas em 29 mapas nativos. Uma tem revisão de
altura pendente: EverGrandeCity, componente 2, 16 células; os 11 contatos em
(39,60)..(39,70) têm `0x3170` (altura 3), enquanto JourneySurfLink00500 tem
`0x1170` (altura 1). Não mudar alturas nativas indiscriminadamente nem contar
essa borda como passagem aprovada. As seis interfaces sem par de água e o
fechamento rejeitado de Route114 também estão explícitos no relatório.

As 18 entradas têm warps de retorno verificados contra os eventos reais.
As cinco Depth preservam portal, entrada/saída e âncoras fixas. Os sete portos
usam sementes secas/molhadas reais e o deslocamento histórico Treasure +8
uma única vez na leitura dos metadados. Isso ainda não redireciona a balsa.
A âncora fixa do interior Artisan é (119,105); ela não substitui o ponto de
acesso (119,104) na borda do ícone nem autoriza abrir oceano sob a caverna.

Nove testes novos cobrem enum C implícito, cutoff/width de banco, colisão,
alturas 0/1/3, piscinas separadas, offsets positivos/negativos, conexão sem
retorno, portal com piso 0, alteração durante leitura, Route114 exata e
Treasure +8 sem mutação do parent. Total atual: 55 testes atlas e um teste
de empacotamento da documentação. Nenhuma ROM pública foi substituída.

Comando de reprodução somente de leitura:

```sh
.local/ci-python/bin/python tools/hoenn/inventory_atlas_surf_parent.py --source .local/generated-area-review-src --output .local/atlas-parent-inventory.json
```

## Halo físico: diagnóstico compilado e validado

`atlas_surf_physical.stage(layer, plan)` deve rodar após o runtime indexado.
Limita fonte/destino antes de formar ponteiros em FillConnection, preenche o
halo pelos retângulos globais reais e preserva todas as células do mapa atual.
O índice direto por layout evita depender de uma posição de save intermediária.
Costa nativa direta precede o background Atlas; tradução desconhecida ou
conflito fica indefinido. Bits de altura/colisão são preservados, inclusive0.
Uma célula diagonal visível não cria conexão de movimento: a borda exige o
vizinho direto correto naquele offset. Cópias entre mapas históricos preservados
continuam no caminho original do motor.

Cinco testes C executados:500 retângulos solicitados com origens negativas e
limites independentes, mapa estreito, célula diagonal, costa nativa, terreno
runtime, caminho sem conexão, alvo errado, header obsoleto,64 combinações de
altura/colisão e tradução desconhecida. São shims do motor no host; não provam
câmera, VRAM, desempenho ou viagens na ROM. A prova nativa abaixo cobre o
diagnóstico. Mais quatro testes rejeitam evidências alteradas ou promoção a
release. Total atual:64atlas+1continuidade.

Comando reproduzível do preparador, exigindo um destino novo:

```sh
.local/ci-python/bin/python tools/hoenn/prepare_atlas_surf_diagnostic.py --source .local/novo-diagnostico-privado --clone-from .local/review171-build-src
```

O preparador verifica o parent171 antes/depois, cria cópia sem hardlinks e
recusa qualquer destino já existente, inclusive parcial. A fixture tem três
mapas em L, um com largura4, derivada de cinco pixels sintéticos. Não é a
classificação real do atlas. A migração limitada incluída é fixture sintética,
**nunca mapeamento de saves para release**. O build diagnóstico e as provas
abaixo já terminaram; não extrapolar seus resultados para a rede completa.

## Próximo trabalho técnico, em ordem

1. Conferir o merge do PR normal #110 e o PR seguinte de integração; preservar cada
   novo lote antes de operações longas; os artefatos diagnósticos estão no Git.
2. Repetir as provas em cada candidata que mudar: o guard de espécie/evento
   e o stride 8 passaram nos testes C e no build ARM diagnóstico v2.
3. Completar a classificação física dos pixels nativos e do ícone (96,40).
   Costa: quatro pixels oceânicos interiores entre (128,89) e (133,89).
   Artisan: endpoint (119,104) é ícone de caverna, não oceano livre.
   Inventário formalizado e testado: 273 IDs, 18 warps recíprocos de cavernas,
   cinco Dive e sete portos. Há 33 componentes costeiras candidatas em 29
   hosts; 32 têm contato com altura compatível e uma exige revisão em Ever
   Grande. Isso não prova conectividade final nem novas posições.
4. Integrar 157 conjuntos autenticados e 14 ilhotas de trainers, POIs,
   eventos, 18 cavernas e 33 adaptadores. Preservar os 273 IDs históricos.
   Route114: conferir (0,17)/(0,18), 0x1170→0x15F9, sem tocar a margem y16.
5. Integrar o clipping de FillConnection e halo **físico** à candidata final.
   O módulo já compilou em ARM e passou quatro travessias nativas de três
   mapas, incluindo largura4 e terreno diagonal. Repetir com toda a rede,
   bancos/costas, cenários e carga de mapas reais; escala436 ainda não provada.
6. Integrar cinco Dive conforme âncoras/fórmulas do JSON e migração segura de
   todas as posições/warps/saves, incluindo atualizações de templates.
7. Auditoria independente da SCC global e ecologia por gatilho: 383/190
   famílias são metas históricas; 403/200 eram só união de pools. Preservar
   269 células de grama sem criar ilhas arbitrárias; corrigir áreas Dex.
8. Preparar candidata final identificada, medir recursos, compilar, conferir
   32 MiB e congelar source/ELF/ROM. Provar a eliminação da pausa real, sem
   aumentar só o timeout. Repetir Birth, sete portos, viagens, colisão/câmera,
   cavernas, Dive, ecologia, animações e baterias antigas/novas pelos controles.
9. Congelar cinco edições, executar 12 provas principais, revisar mapas
   inteiros, atualizar ROMs/save TESTE/ZIP/manifestos, navegador e stage_pages.
10. Atualizar docs/errors/este arquivo com hashes finais e limites; enviar
    checkpoint remoto e manter PR normal com descrição do resultado real.

## Como manter este documento

Após cada lote, registrar data, pedido literal novo, escopo autorizado,
último pedido totalmente concluído, pedido ainda incompleto, commits/PRs,
arquivos reais e ausentes, comandos/resultados, hashes, fixtures, limitações
e próximo passo concreto. Nunca substituir pendências por um resumo vago.
O JSON recebido é um relato histórico; atualizar o estado aqui e em
`errors/ESTADO-DA-TAREFA.txt`, preservando essa distinção.

Este guia e o JSON técnico integram a documentação do pacote ZIP do jogo.
Mudanças só de continuidade não justificam recompilar ou publicar ROMs.


Registro da preparação do diagnóstico físico: o primeiro destino
`.local/atlas-physical-smoke-src` foi preservado sem marker, após a guarda do
preparador rejeitar uma suposição incorreta sobre o banco doador. A fonte
real171 usa `gTileset_General_Frlg` + `gTileset_IslandHarbor_Frlg` em Sea00;
a guarda agora confere esse par e o comportamento Surf compilado.
Nova cópia `.local/atlas-physical-smoke-v2-src` preparada com28inputs e3mapas.
Marker SHA256 `1d38cf4d7ce85cb4bebb122fb6338efeb797a16c18d56758f712015d3bc84f17`.
Parent171 íntegro antes/depois. Esse foi o checkpoint anterior ao build;
a execução posterior foi concluída, como registrado abaixo. Nenhum destino anterior foi apagado ou reutilizado.


Resultado atual do diagnóstico físico, congelado antes das provas:

```text
Fonte: .local/atlas-physical-smoke-v2-src (28 inputs preparados)
ROM: 3e4cd81123c776de390c13f6f8c628ed275106ff7fe3c6e07ded4c05e53b081b
ELF: 7429b6ad085531ae5690a1d1496f1216dcc2ac6bfecc74d253cde2f67036c8ad
Marker: 1d38cf4d7ce85cb4bebb122fb6338efeb797a16c18d56758f712015d3bc84f17
ROM usada: 32.652.272 bytes (97,31%); EWRAM245436; IWRAM28660.
```

Prova exportada em `docs/design/atlas-surf-layout/diagnostic-physical-native`:
seis capturas e relatório. A→B, B→C, C→B e B→A passaram por controles; A tem
largura4. Coordenadas coincidiram com o novo mapa3–5frames após publicar o ID;
total24–33frames por caso, incluindo20frames consecutivos de estado estável.
Nenhuma consulta nativa roda no intervalo cronometrado: leitura direta e
controles somente, com timestamps no relatório. O teste rejeita atraso acima
de30frames entre ID e coordenadas, sem aumentar timeout para aceitar pausas.
Isso mede três mapas e **não certifica desempenho da rede final com436**.

Oito tiles para norte mantiveram X e reduziram Y em8; GPS afim reduziu apenas
um pixel emY. Recifes bloquearam Surf. Água/collision/altura do vizinho de
largura4 apareceram antes da entrada. O terceiro mapa diagonal teve terreno
físico correto, quatro quadrantes BG e64pixels nativos conferidos; sua célula
não ganhou conexão de movimento. Avatar Surf teve pixels de cabeça/corpo/pés
comparados com a captura, além de flags/altura.

O verificador independente confere frames, ausência de queries durante o
timing, direção, capturas, pixels BG/OBJ e vínculos com os28inputs, marker,
ROM e ELF atuais. Os quatro testes de contrato rejeitam adulteração de pixels,
hashes, direção, pausa longa, query no intervalo ou promoção desse diagnóstico
para release. O primeiro export sem timestamps foi preservado localmente;
a prova versionada foi repetida com os vínculos completos.

Birth foi repetida na MESMA ROM nova e passou, com seis capturas adicionais
em `diagnostic-physical-birth`; relatório anterior v2 permanece preservado.
Ponta/corpo de madeira, pedestre/Surf bloqueados, saída/retorno pelo lado,
Harbor nos dois sentidos e pixels do avatar. Isso continua sendo prova local
de fixture, sem Save/Continue, campanha completa ou cinco edições finais.

Reverificação somente de leitura:

```sh
.local/ci-python/bin/python tools/hoenn/verify_atlas_surf_physical_native.py --report docs/design/atlas-surf-layout/diagnostic-physical-native/physical-native.json --source .local/atlas-physical-smoke-v2-src
```

O ambiente reiniciou durante a exportação e voltou disponível; os arquivos
foram conferidos novamente. O ambiente antigo perdido não foi recuperado.
Última medição:1,7GiB e97.983inodes livres; medir antes da próxima preparação.


## Última instrução do usuário e checkpoint de integração

O usuário observou literalmente: “Continue, só achei estranho uma coisa,
nenhuma rom atualizada. Última semana passada.” Em seguida: “Continue os
trabalhos”. A observação é correta: as ROMs públicas ainda são171. A ROM nova
compilada e provada até agora é o diagnóstico de três mapas, sem a rede
completa. Não foi entregue172 final. Prosseguir integrando o jogo; não voltar
à configuração de editores nem encerrar o pedido principal como resolvido.

Última entrega totalmente concluída: PR normal110 integrado, base171
reproduzida, diagnóstico do halo físico e Birth com hashes/capturas preservados.
Último pedido incompleto continua a rede de Surf conforme arte fixa, com
acessos/save/ecologia e todas as cinco ROMs/publicação verificadas.

O lote posterior ao merge110 passou141 testes atlas e1 teste de continuidade.
Inclui código pronto para integração, ainda sem nova ROM integral:

- `atlas_surf_plan.plan_reserved_geometry`: recorta retângulos ordinários ao
  redor de reservas exclusivas de objetos completos, sem cortar cenário para
  caber em32 tiles. Máscara de água nativa é autoritativa; terra nunca vira água
  porque o raster passava ali. Obstrução de corredor exige evidência explícita
  e continua sujeita à SCC/ROM. Margem gráfica de 9 tiles evita banco desconhecido antes
  de mudar de mapa. Grupos seguem100 mapas e coordenadas assinadas válidas.
- `atlas_surf_scenery`: extrai terreno, bancos, callbacks, sprites e eventos;
  preserva 379 componentes candidatas (18 com portal, 140 de terreno, 196 de decoração e 25 de atores),
  com 478 componentes de limites registradas separadamente. Isso não força os
  números perdidos157 + 14; colocação final e exceções Dive ainda são auditadas.
- `atlas_surf_adapters`: ligações nativas recíprocas e transições locais3→0→1
  somente no adaptador novo, sem nivelar a água nativa. Registros concretos33
  ainda em elaboração. Continentes nativos NÃO têm embedding uniforme de 8 tiles por pixel; a
  escala de 8 é da malha nova. Registrar interfaces locais por arte/âncora/costa,
  com direção e terreno autênticos; não inventar prova de antigoGPS.
- `atlas_surf_dives`: cinco patches/75células, transformação global↔Depth,
  GPSDepth afim e hook anterior a GetMapConnection. Preserva DoDiveWarp,
  Depth/NPC/portais; remove somente 5 pares antigos. Treze testes em C e no source
  passaram; ainda precisa execução na ROM final. Doador Emerald autenticado;
  nunca copiar0x14F para FRLG como IDuniversal.
- `atlas_surf_reachability`: CSR/SCC compacta, alturas/colisão/bancos,
  conexões/warps reais e requisitos explícitos. Dezessete testes iniciais e
  diagnóstico real3 mapas passaram source-only. O suporte às transformações
  Dive novas está sendo integrado; não aceitar falsas conexões iguais antigas.
- `validate_atlas_surf_ecology_source`: enums, predicados e pools C reais
  reproduziram383 na Gen9 e 190 na Gen4; união403/200 não significa gatilho. Na fonte 171,
  as 269 células de grama estão em3 mapas: Sea05 = 17 (bbox [6,38]..[12,42]),
  Sea08 = 126 (9,31..27,42), Sea09 = 126 (9,26..27,37). A divisão em 6 trechos era
  do plano 172 perdido. Preservar essas três fontes/donos em reservas específicas.
  O DEX remove somente claims ordinárias aposentadas sem gatilho demonstrável
  e exige testemunhas finais alcançáveis para substituir as efetivas.
- `atlas_surf_classification`: proveniência gráfica de 19 pixels azuis regionais
  foi reconstruída semGPS. Isso NÃO prova propriedade física desses 19, nem a
  contagem histórica de 45. A classificação nativa final depende das interfaces
  e testemunhas físicas/retorno. Não forçar número para aprovar candidata.
- `atlas_surf_ports`: sete destinos C do Seagallop e sete warps de chegada antigos
  passam aos tablados secos autênticos, com Treasure +8 lido uma vez. Stage em
  memória da fonte 171 passou; cena, NPCs, terminais e outros destinos intactos.
- `atlas_surf_overlay.OverlaySource`: audita a camada staged sem escrever a
  fonte; qualquer input modificado exige uma visão nova. Enum C staged diferente
  do header realmente compilado é rejeitado.
- `atlas_surf_names`: registra labels dos novos mapas, mantendo as quatro
  arrays da arte byte a byte. Label/posição do cursor não prova local do jogador.

Relatórios completos preservados em JSON.gz determinístico, comSHA do JSON
original e do arquivo comprimido em
[integration-source-checkpoint.json](design/atlas-surf-layout/integration-source-checkpoint.json).
São relatórios do source171 e extração/investigação, NÃO provas de ROM 172.
Leitura portátil: `json.loads(gzip.decompress(Path(caminho).read_bytes()))`.

Trabalho seguinte já atribuído e ainda não certificado: GPS legado em RLE
para migração apenas, retirada dos grids aposentados da navegação, fallback
seguro para os 273 IDs, preenchimento das reservas e registros de costa. Depois,
preparar candidata íntegra, auditar e compilar; as cinco ROMs só mudam após as
provas finais. Não publicar o diagnóstico como se resolvesse a rede completa.


Diagnóstico dos cinco Dive, preparação em andamento posterior ao checkpoint111:
`prepare_atlas_dive_diagnostic.py` criou cinco probes isolados, sem classificar
ou publicar a rede final. A cópia privada anteriormente chamada
`.local/atlas-physical-smoke-src` foi verificada novamente:32.250inputs e ROM/ELF
171 exatos; não continha camada172parcial. Foi preservada por renomeação para
`.local/atlas-dive-smoke-src`, sem apagar arquivos. O marker histórico
`.journey-atlas-route-tracking` pertence à cadeia171 e foi autenticado; só
markers Atlas novos impedem reutilizar uma cópia limpa.

A primeira seleção do doador mostrou que Route127 não contém a pedrinha1F9,
embora tenha o banco correto. O preparador agora lê água/pedra inteiras de
JourneyHoennNorthSea e o DeepWater real de Route127(72,49), com os MESMOS
bancos Emerald General/Mossdeep. Log da tentativa sem pedra foi preservado.
São42inputs preparados, incluindo cinco transforms Dive e os sete destinos
de balsa. Marker SHA256:
`977de91864b104dcfa8f1f8d791075d9a618db0c20f86abf9b4172292880de4c`.
Build ARM e prova nativa desse diagnóstico ainda pendentes neste checkpoint.
Essa preparação não comprova geografia global, migração ou publicação172.


## Resultado nativo dos cinco Dive no diagnóstico

A preparação anterior já compilou e seus bytes ficaram congelados:

```text
Fonte: .local/atlas-dive-smoke-src;42 inputs preparados.
ROM: dc80c3a05901ba2dcf0e963d7002ac1b884ad674eb9d4239a01e513d7355a016
ELF: 2c55a6dd4251cd52ab6ab5843c0e90f92b22d4caeb856426cfa02304702cf13c
Marker: 977de91864b104dcfa8f1f8d791075d9a618db0c20f86abf9b4172292880de4c
ROM usada:32.653.064bytes(97,31%);EWRAM245432;IWRAM28660.
```

`validate_atlas_surf_dives_native.py` passou os cinco casos por controles:
Surface→Depth, entrada real no santuário, saída e Emerge→Surface. O deslocamento
local foi preservado nas duas direções. B não emergiu sobre recife nem célula
sem dono. Cada caso teve fixture inicial explícita de party/progresso/posição,
Surf e encontros; após a partida não usou setters, warps, FieldEffectStart ou
TrySetDiveWarp como consulta. Dive e Emerge foram iniciados por A/B e diálogos
nativos. O piso0x0364 do santuário foi aceito em altura0; avatar/pixels reais
foram conferidos. Isso é prova local, não campanha completa ou Save/Continue.

Quarenta capturas, relatório e runner exatamente executado estão em
`docs/design/atlas-surf-layout/diagnostic-dives-native`. O verificador separado
confere as40capturas/pixels, destinos, estados e todos42inputs/marker/ROM/ELF
com o source atual. Índice com hashes em `diagnostic-dives-review.json` e
`diagnostic-dives-frozen.json`.145testes atlas e1decontinuidade passaram;
quatro testes novos rejeitam destino/modo/piso adulterados, imagem inválida,
consulta mutável ou promoção desse diagnóstico a release.

O perfil lido no ROM congelado é maxNational1025, perfectTrainerIvs=true,
reviewMode0. Não é uma prova das outras edições, da TESTE ou dos encontros.
A rede completa ainda não foi preparada/publicada; as ROMs oficiais continuam
171. Conservar este resultado como diagnóstico e repetir no artefato final.


## GPS legado compacto para migração (checkpoint posterior à prova Dive)

`atlas_surf_legacy.py` separa os 273 mapas aposentados da navegação ativa.
Mantém seu GPS exato em RLE indexado e uma máscara nativa de água para auxiliar
migração; bit seco NÃO certifica chão seguro. Os IDs, eventos, layouts e arte
permanecem intactos. Comparação do C real: todas as 235.650 células antigas,
65.536 IDs, clamps e 149 grids retidos passaram. Os dados diminuem de
1.057.272 para 784.870 bytes, economia de 272.402 bytes antes de código/padding.
Isso ainda precisa ser integrado, compilado e validado no Continue real.

Relatório íntegro comprimido e hashes em
`docs/design/atlas-surf-layout/legacy-navigation-review.json`. A visão de fonte
staged também preserva os quatro JSONs nativos sem identidade compilada,
rejeita novos mapas não registrados e qualquer reordenação dos IDs antigos;
a leitura do registro original confere o hash do parent antes da auditoria.

167 testes atlas passaram neste checkpoint (incluindo os registros costeiros
em elaboração); os arquivos concretos desses registros ainda serão congelados
no lote seguinte. Pedido literal mais recente: “Continue os trabalhos”.
Último lote concluído: GPS legado compacto e guarda da auditoria staged.
Pedido principal incompleto: geometria integral, cenários, classificação,
migração funcional, provas finais e atualização das cinco ROMs públicas.
O PR normal111 continua aberto; ROMs públicas seguem171. Próximo: materializar
os 33 acessos e posicionar todos os objetos completos na rede física.


## Colocação concreta de costas e cenário completo

Pedido literal atual: “Continue”. O PR normal111 permanece aberto. Foram
registrados os 33 acessos de costa por arte e terreno reais, com boca, direção,
offset, banco e retorno local autenticados. Nenhum dado de GPS antigo escolheu
os encaixes. Onze testes costeiros passaram. Quatro bocas são mais estreitas
por causa do terreno nativo, e Ever Grande mantém altura3 com transição3→0→1
somente no adaptador novo. A análise separada do GPS antigo encontrou saltos
em32/33 bocas: integração da projeção nativa ainda PENDENTE. Não ocultar esse
problema nem declarar as viagens aprovadas por ter encaixes source-only.

O empacotamento colocou374 componentes inteiras:18 cavernas nas âncoras
originais e356 componentes em82 reservas decorativas. Objetos do mesmo banco
E mesmo dono ecológico compartilham a margem de câmera9, mantendo cada core
inteiro e IDs de NPC sem colisões. Decoração fica ao lado do corredor real,
em oceano da arte, num raio autoral de12pixels da âncora lógica do mapa antigo;
não usa seu GPS interpolado. Os cinco quadrados Dive antigos5x5 são substituídos
explicitamente pelos cinco patches nativos5x3, total75células; nenhum evento
é descartado. Zero componentes sem colocação. Sete testes de empacotamento
passaram. Os13 conflitos residuais entre corredor e terreno seco de cavernas
fixas estão registrados; precisam de SCC e percurso real, sem chamar terra de água.

Relatórios integrais comprimidos, imagem do atlas REAL anotada e hashes em
`docs/design/atlas-surf-layout/whole-layout-placement-review.json`.
Limite: geometria conjunta ainda não materializada/auditada/compilada. Faltam
classificação nativa, ajuste funcional da projeção nas costas, migração real,
ecologia alcançável, ROMs finais e publicação. Último lote concluído:33acessos
e inventário inteiro com colocação. Próximo: aplicar reservas/objetos/eventos
no source staged e auditar acessos globais antes de compilar.


## Composição integral e migração — 15/11/2026 UTC

Pedido literal atual: “Continue”. Último lote concluído: composição em memória,
sem escrita na fonte171, de533 mapas novos/1955inputs preparados,74eventos
(56NPCs) transferidos,273IDs aposentados preservados e migração v2 completa
implementada. Os33 retângulos nativos têm propriedade exclusiva:1.018células
do raster gerado foram removidas, incluindo o recorte dos próprios retângulos
dos mapas novos. Não basta deixar água bloqueada dentro de um mapa sobreposto.
O censo encontra9pixels comnúcleo totalmente nativo e12parciais;35tocamraster,
47incluemfranjas. Esses números são novos, NÃO o histórico45 forçado.

O reempacotamento conserva374stamps em18cavernas+83reservas decorativas;cinco
marcasDive5x5 viram cinco patches5x3 explícitos. Acrescenta7.590células de franja
molhada copiadas de testemunhas nativas adjacentes, preservando palavra inteira,
para não criar piscinas isoladas nos cantos dos objetos. As533 dimensões cabem
no buffer nativo10.240células comhalo (máximoatual5.120), além de coordenadas s8.

O backend mapjson agora aceita native_local_id numérico e mantém local_id como
nome de macro; seu C++ real foi compilado e a saída171 padrão inteira continuou
idêntica. Grupos acumulam os vários objetos no mesmo map.bin sem sobrescrever
os anteriores. IDs, scripts, trainers e flags sobrevivem à troca de índices.
Retirement exige cobertura exata antes de limpar os eventos antigos, desconecta
as faces antigas já bloqueadas e o acesso falso autorizado de Route114; somente
suas duas células pedidas mudam, mantendo a margem y16 e o restante da lagoa.

A migração usa GPS legado RLE uma vez, prioridade de translação dos cores
seguros e destinos reais para todos273IDs. A comparação C conferiu235.650células;
5117pixels legados usam1985destinos (380pedestres/1605Surf),42.612bytes de tabela,
mais980retângulos exatos para6781células. Resgate aproximado máximo22pixels,
declarado para posições sem correspondência segura; não é GPS de viagem nova.
A migração histórica1 permanece uma vez; ID de warp desconhecido usa resgate
explícito pelo mapa, nunca interpreta coordenadas sentinela como posição.
Continue→salvar→Continue no emulador continua PENDENTE.

O auditor Dive lê as tabelas C/índices reais e o hooktri-state antes do lookup
antigo:5sites/75pares transformados passaram sem conexões JSON falsas.38testes
desse auditor e13testes do C gerado passaram. A suíte atlas completa atual
passou244testes; a composição real confere cada palavra dos374stamps, os IDs
numéricos, bancosDive e a ausência de sobreposição com os33patches nativos.
Índice dos relatórios integrais e hashes: whole-layout-composition-review.json.

Pedido principal AINDA INCOMPLETO: SCC global, bancos nas câmeras/divisas,
projeção geográfica NATIVA (grids antigos tinham reconciliação incorreta),
DEX/ecologia alcançável, referências C pendentes, build/capturas/baterias e
cinco edições finais. Não tratar sWorldPoints como coordenadas locais exatas:
o gerador antigo truncava Y>107 e fazia centros artificiais. A auditoria dos
landmarks nativos está em andamento; não esconder conflito ajustando sóGPS.
Os 273 mapas/arquivos antigos permanecem para migração; layouts/IDs não foram
apagados. ROMs oficiais seguem171. PR normal111 aberto. Próximo: concluir
auditoria física global, materializar candidata privada e medir o buildARM;
publicação segue bloqueada até provas atuais, sem promover contratos à força.


## Pedido explícito de atualizar as ROMs — 15/11/2026

Últimos pedidos literais: “Abra o pr com tudo que implementou e modificou nas
roms pra guardar o progresso.”; depois: “Mas eu quero que atualize as roms com
as modificações feitas, já pedi.” A prioridade agora é compilar a candidata
INTEGRAL atual e enviar as CINCO ROMs modificadas no PR normal111, não apenas
código ou diagnósticos antigos. O usuário foi informado de que essa candidata
terá testes/falhas pendentes e não será apresentada como release final aprovada.
Essa instrução permite preservar binários em andamento na branch/PR; não
promover NATIVE_CONTRACT_FINALIZED nem inventar validação ou publicar Pages
como release final. Preservar a171 e seus hashes/bateria para retorno e testes.

Checkpoint anterior remoto c162689b58bceb73923e18077361a7c62c26cc90 confirmado.
Novos códigos: prioridade física da primeira conexão no halo nativo quando há
Atlas, reaplicação depois de LoadSavedMapView mantendo core/runtime, ciano
clipped em y111/desenhado sobre cursor sem mudar coordenadas, auditor C real
entre bancos, obrigações marítimas e acessos curtos autenticados dos cinco
Dive (Origens evita a terra abaixo do glifo). A expansão de água nativa de
cavernas usa somente células Surf reais do doador e respeita os limites do atlas.

A auditoria com bancos autenticados reduziu110componentes para22; os cinco
acessos Dive corrigidos reduziram para17. Isso é FALHA global ainda aberta,
não PASS:14/18 cavernas no diagnóstico de pertinência à componente principal. Seis
portos têm dry/wet na componente principal; Three ainda está isolado na fonte.
O censo sem filtro SCC confirmou383/190famílias e269células de grama novas;
não é prova de alcançabilidade ou ROM. O projetor regional nativo e a proveniência
de rotas ocultas por glifos seguem em desenvolvimento. A arte continua fixa.

Próximo imediato: checkpoint de código atual, clonar PRIVADAMENTE a cópia171
compilada/verificada, preparar, make -j4 com recursos medidos, corrigir erros
ARM, congelar ROM/ELF/marker, exportar quatro regras de geração/dificuldade e
TESTE mantendo supressão, fazer smoke/coldboot possível e atualizar os arquivos
e manifestos no PR com status de candidata e as pendências reais. Não editar
ou compilar enquanto um leitor usa o MESMO source/ELF/ROM; o parent171 segue
intocado. Depois continuar os consertos até a validação final pedida originalmente.


## Cinco ROMs recompiladas para o checkpoint solicitado

Pedido literal: “Mas eu quero que atualize as roms com as modificações feitas,
já pedi.” A candidata integral foi compilada e exportada nas cinco edições;
esta atualização de binários no PR é autorizada mesmo com validação global
pendente. Não é uma publicação final aprovada. Foram261testes atlas aprovados
antes do build e os oito testes da migração passaram após corrigir um erro real
do ABIARM: structs de seis bytes precisam de __attribute__((packed)), pois
APCS arredondava para oito. O compilador confirmou os asserts após a correção.
O parent171 foi preservado; o build usou cópia privada com cache derivado
verificado e nenhum inode gravável compartilhado. O primeiro preparo com o
cache como source foi recusado por um agregado gerado não autenticado; log
preservado, e a fonte passou a ser a171 congelada, com cache só para derivados.

ROM bruta compilada:f2cac1ecb79e23c3b6a6a43e07568b7c5b03579dc265ba99d33bc3bad7940c0e
ELF:618b0556e031fee25a1aace83f33bb8491b7e316ebd910a34f968098b135ba73
Uso:32.920.992/33.554.432bytes(98,11%);EWRAM245456;IWRAM28660.
Três cópias reais da tabela de533chunks/stride8 foram extraídas da ROM e
comparadas com todos os IDs/origens/dimensões preparados; passaram. Relatório:
`candidate-compiled-tables.json`. Os1955inputs preparados foram conferidos.

SHA256 das CINCO ROMs atuais:
Gen1-4Normal:a24b7304d4dda4a7d1abd60849161409468a4a29d00528a9549643333e7cb40d
Gen1-4Hard:a2103c4bebe2f8fecc12d863b16f7e0971fb35040b6cf15bf2f0a95f5275146c
Gen1-9Normal:47a3a75c36b50bcd96584bd7c7ced7f121f68b8e5b14e93338f503c17b7f951f
Gen1-9Hard:14ebe89fc88f3d4d55cc8a48f7ed1edf36bf997a26d397a8c653e5d6320bf36d
TESTE:b7445c29804f36f188e0b753849ac4bb55fa605218c7486c04ee73d3fc7945ae

As cinco passaram cold-boot real por controles até NovaPartida. A TESTE também
passou com a bateria171:Continue→campo→salvar pelo menu→exportar pela API de
bateria→novo boot→Continue. Manteve Mossdeep[0,6],tile[28,18],a pé,altura5 nativa;
não impor altura3 a essa cidade. Bateria nova131072bytes:
36ace517a44bc0315a4a5309054a4913f39e0f1872a073763ba685c3421e5861.
A primeira extensão do runner teve erro de closurePython; corrigido, execução
válida repetida e runner exatamente executado preservado. Nenhuma escrita de
callback/posição/flags/EWRAM foi usada nestes cold-boots ou no menuSalvar.
A supressão global da TESTE foi mantida via sua regra real de ROM; a suíte
completa de encontros/trainers da candidata continua pendente.

Estado de entrega:roms/ e os quatro espelhos de mods/hoenn/versions recebem
os binários novos, a TESTE/save/hash recebem seus bytes atuais, ZIP inclui as
quatro edições e este documento técnico (TESTE separada). Manifesto fica
explicitamente candidate=true,validated=false,scope atlas-surf-layout-candidate.
Não alterar contratos finais ou forçar CI/Pages a aprovar. A171 anterior está
preservada no históricoGit e seus manifests/save em atlas-surf-layout-validation/baseline.

Último pedido concluído neste lote: compilar/exportar/testar boot e salvar as
cinco ROMs modificadas no PR normal111. Último pedido AINDA INCOMPLETO: consertar
e validar toda a geografia/acessos/visuais/ecologia e entregar release final.
A fonte ainda tem17componentes de água gerada;14/18cavernas e6/7portos estão na
componente principal no diagnóstico, mas o validadorglobal permanece FAIL por
não haver uma únicaSCC. Não confundir esse diagnóstico com aprovado. Faltam
underlay autenticado de glifos, propriedade nativa/projeção/registros costeiros,
ThreeIslandPort e demais ligações, revisão visual integral, provas por controles
e edição/TESTE completas, DEX e Pages. Trabalhos readonly de projeção regional
e glifos ainda não aplicados em runtime precisam ser preservados como WIP,
sem afirmá-los incluídos nos binários. Próximo passo: seguir esses consertos
sobre este checkpoint verificável; cada novo build precisa de provas próprias.

Revisão dos auxiliares deste checkpoint: o empacotador vincula cada arquivo
real ao freeze de cinco ROMs antes da cópia; os hashes públicos e o conteúdo
do ZIP são conferidos depois. O projetor regional readonly foi preservado
como pesquisa WIP, sem alterar a candidata: filtra mapas sem identidade
compilada e seu shim define os tipos usados no C nativo. Dois testes, incluindo
cinco casos comparados com o C real da171, passaram. Isso não prova domínio
físico de pixels nem resolve as ligações nativas.


## Continuidade de 15/11: falha de CI recebida após atualizar as ROMs

Última mensagem do usuário: log integral da Actions iniciado em
2026-11-15T16:24:20Z; resumo literal: "Ran 1074 tests in 32.571s / FAILED
(failures=12, errors=13, skipped=34)". Retomar a correção desse diagnóstico
sem desfazer o checkpoint de binários solicitado.

Último checkpoint remoto conferido antes deste lote:
3ae46505cc076d0ad9a9582f0791f1fd6f3ca860 no PR normal111. As cinco ROMs e a
bateria preservam todos os hashes registrados acima. Este lote altera cadeia
histórica, ferramentas, metadados, documentos e ZIP; não recompila o jogo.

Causa confirmada: ao gerar versions.json da candidata, as referências a
provas históricas foram descartadas. Leitores esperavam proofs/previous_* e
flags antigas, ou escolhiam layout202 por não reconhecer o novo escopo. A
comparação221/202 e o SHA203c... se referem ao histórico; não provam regressão
nova da arte, que não mudou. O bloqueio "Unvalidated release" é correto:
as viagens e demais validações172 ainda não terminaram.

Correção: proofs=[] explícito e ponte171 pinada SHAeca26adf...; somente refs
historical_validation e previous_validation são herdadas. Resolvedores
validam caminho/hash/retested=false/ancestral aprovado/prefixo. Históricos
usam seus próprios bytes e SHA, nunca a ROM172. Onze testes anticorrupção do
resolvedor e nove de integridade da candidata passaram. Três casos de atlas
passaram com leitura readonly dos blobs históricos. O novo CLI
verify_atlas_surf_checkpoint.py verifica bytes/profíles, TESTE/save, cinco
coldboots, freeze, tabelas compiladas e ZIP/docs; não aprova gameplay global.

A suíte completa foi tentada localmente via harness readonly de sparse Git:
1011testes,8FAIL,381ERROR,27skipped. A maior parte dos erros locais corresponde
a blobs históricos não materializados no clone parcial, sem fetch automático;
esse resultado NÃO é CI aprovada nem prova de regressão da ROM. Relatório local
.local/CI-repro-hoenn.log. A execução integral de Actions deve confirmar a
correção dos leitores num checkout com todos os arquivos. Não substituir
arquivos ausentes por fixtures inventadas nem omitir falhas do resultado.

CI agora registra integridade do checkpoint, alpha histórica e gate final em
passos distintos. verify_versions(require_seal=True) permanece intocado e
DEVE recusar a candidata; browser/Pages continuam condicionados ao sucesso.
Não marcar validated=true, fabricar provas ou pular o gate para Actions ficar
verde. Registro técnico: errors/2026-11-15-candidate-history-ci.txt, incluído
no ZIP juntamente com este guia e a baseline171 pinada.

Último pedido concluído: atualização e preservação remota das cinco ROMs,
TESTE/save e guia. Lote atual: reparo dos leitores históricos em validação.
Último pedido incompleto continua corrigir todas as rotas/acessos/visuais,
ecologia/DEX, saves e provas172 para a release final. Há17componentes no
último diagnóstico fonte,14/18cavernas e6/7portos na componente principal.
Próximo passo: conferir Actions após o checkpoint deste reparo e seguir as
ligações nativas/ThreeIsland/underlay, sem tratar smoke/boot como prova final.

Classificação dos381erros locais:380FileNotFoundError sobmods/ (237paths) e
1gateExtraGyms legítimo. Dos8FAIL,7são Unvalidatedrelease e1não encontra
shore-animation por sparse. Não houve KeyError nem rejeição de hash/prefixo
no resolvedor. Relatório enxuto:docs/design/atlas-surf-layout/ci-history-repair.json.


Resultado remoto confirmado — reparo dos metadados
Actions43737388074/job132882888189, commit8d1164f296d76294a570c1cff2fcd06b452bda60:
12/12testes sea_routes PASS. Hoenn executou1094testes em30,306s:
8FAIL,1ERROR,34skipped. ZEROKeyError. Os6casos históricos de Fuchsia/atlas
passaram no checkout integral. Os12erros de integração anteriores desapareceram.
A integridade da candidata (cincoROMs/perfis/TESTE/save/boots/freeze/tabelas/ZIP)
e a alpha histórica passaram em passos próprios. O job global continua FAIL:
7casos rejeitam Unvalidatedrelease; Sootopolis exige manifest.validated=true;
ExtraGyms.setUpClass é o únicoERROR e também rejeita Unvalidatedrelease.
São9exigências de aprovação final ainda não satisfeitas. Não torná-las verdes
apenas editandoflags, trocandoSHA, ignorandotestes ou pulandoo gate. Browser e
Pages ficaram bloqueados. Nenhum defeito funcional novo da ROM foi demonstrado
por essas9recusas; a rede física172 já tinha suas pendências reais conhecidas.

Último subpedido concluído: reparar os leitores/metadados históricos do log
recebido e verificar o resultado na CI integral. Último pedido incompleto:
concluir e provar geografia, cenas, saves/ecologia/edições para release172.
Os5binários e a bateria preservam os hashes do checkpoint3ae4650; este lote
finaliza documentação e ZIP e registra a evidência remota acima. A próximaIA
deve seguir o conserto da rede e a validação nativa, não remover os gates.


## Checkpoint urgente solicitado: PR antes do limite

Pedido literal mais recente: “Abre o pr, meu limite vai acabar”. O PR111 já
está aberto como NORMAL, sem rascunho; este lote preserva os novos arquivos.
Último remoto confirmado antes dele:f5e9ef0a4adf788a44cc29bfb40bc1afaaf962a6.

Progresso REAL desta etapa: BirthIsland passou na ROM integral atual533mapas,
rawROMf2cac1ecb79e23c3b6a6a43e07568b7c5b03579dc265ba99d33bc3bad7940c0e.
Fonte/ELF/marker e1955preparedinputs foram conferidos antes/depois. Percurso
por controles: rampa/ponte, pedestre bloqueado na lateral, Surf saída/retorno,
corpo de madeira bloqueado, Harbor e volta à ilha, avatar visível por pixels
reais de OBJ/VRAM/scanout. Captura birth-wood-tip.png foi inspecionada: madeira
inteira sem metal na ponta. Prova/copias no diretório current-ROM-birth-native.
Não é aprovação da rede inteira, das cinco edições nem do release final.

Diagnóstico fonte confirmado: ThreeIsland_Port_Frlg48x20 tem duas componentes
água; embarque(14,17) na0/leste, adaptador na1/oeste. Terminal/ponte separa as
águas e os recifes fecham embaixo. Nenhuma correção foi aplicada ainda. Avaliar
redirecionar boca do adaptador com referência ao atlas; não apagar terminal,
NPCs ou abrir canal arbitrário. As17SCCs e demais clusters foram preservados
em urgent-progress-checkpoint.json, sem promover diagnóstico a PASS.

A pesquisa dos7pixels escondidos por glifos foi interrompida pelo limite dos
agentes. Os arquivos completos existentes foram preservados byte a byte em
WIP-occluded-routes/*.py.txt, com hashes no relatório. NÃO estão integrados
nem compilados. Seu teste ainda falha antes dos casos: endpoints Ocaso.
A próximaIA deve corrigir essa interpretação contra o marker171, testar e só
então integrar. Não enfraquecer contratos para passar. Outros agentes não
chegaram a escrever seus relatórios; os achados recebidos estão registrados.

Último subpedido concluído: guardar o progresso atual no PR normal, com prova
Birth e pesquisa WIP preservada. Pedido original INCOMPLETO: corrigir e provar
a rede Surf,17SCCs, acessos restantes, visuais, saves/ecologia e release172.
As5ROMs continuam atualizadas com os mesmos hashes; nenhum novo build neste
lote. CI ainda8FAIL+1ERROR de release não validada. Próximo: consertar Ocaso/
glifos, Three e lacunas nativas; repetir fonte/bancos, preparar/build privado,
congelar e repetir todas as provas/edições antes da publicação final.

## Atualização exclusivamente documental — pasta Aqui

Pedido literal mais recente:
“Ok, uma coisa, atualiza o documento técnico especificando o que falta, crie
uma pasta dentro do repo com nome "Aqui" pra eu indicar pra próxima janela
de I.A codex sobre do que se trata, como funciona, como atualizar, o que foi
feito, o que falta, o que não fazer (coisas erradas que não são pra serem
feitas) e como é o correto que eu quero. Tudo de forma técnica nesse arquivo.
Atualize bem feito, cuidado com meu limite, faça apenas isso nesse commit
dentro do mesmo pr.”

Aqui/README.md consolida identidade, arquitetura, requisitos do usuário,
hashes/provas, pendências concretas Ocaso/Three/17SCCs, CI, ambiente, erros
proibidos e operação correta. Último remoto anterior:
1bf71eda2d8276a377e38e84cc4baaaad070c085. PR111 normal permanece aberto.
Último subpedido documental atendido neste lote; pedido de terminar e validar
o jogo continua incompleto. Apenas documentação: sem builds/provas novos,
código/ROM/save/ZIP/manifestos/workflow intocados. O ZIP conserva o texto
anterior; a comparação estrita contra documentos do HEAD pode acusar
Stale archive entry. Reempacotar com Aqui/guia atualizado somente na próxima
etapa autorizada do pacote, sem relaxar verificador.


15/11/2026 — erros recebidos para a próxima IA
Pedido: criar documento de erros na mesma pasta Aqui e preservar os três
logs de CI para corrigir em outra janela. Criados Aqui/ERROS-PARA-PROXIMA-IA.md
e Aqui/LOG-CI-2026-11-15.txt, com origem Actions43761665375/job132957596992,
commit29b1dca, log completo e SHA. README aponta para o registro.
Resultados recebidos:1094testes,8FAIL,1ERROR,34skipped; Unvalidated release
na suíte/gate e Stale archive entry no guia dentro do ZIP. O último decorre
da atualização somente documental sem reempacotamento. Correções pendentes:
sincronizar pacote quando autorizado e concluir as provas reais da release.
Subpedido atendido: documentação dos erros. Erros NÃO corrigidos neste lote;
código/ROMs/save/ZIP/manifestos/workflows intocados. Conferir push ao entregar.


15/11/2026 — sincronização do guia antes do merge solicitado pelo usuário
Último remoto anterior:846aa59b0d2d2e6d00babb7bca259eb9ef251d9d.
O guia no Git estava atualizado, mas o ZIP preservava a edição anterior por
pedido de somente documentação. Nova solicitação autoriza sincronizar o
pacote. Guia Aqui atualizado; README/erros/log entram no ZIP; empacotador e
verificador incluem Aqui e conservam comparação estrita. Regressão testa
alteração do guia e dos registros após empacotar. Hash/tamanho externos do
ZIP atualizados. ROMs/save/source/ELF não foram modificados ou recompilados.
Este lote resolve o desencontro documental do pacote, não a release172:
17SCCs/Ocaso/Three/lacunas e provas finais continuam pendentes, assim como
8FAIL+1ERROR do gatefinal. Logs originais preservados com seu SHA. O usuário
pretende fazer o merge, sem autorizar a IA a marcar release validada.
Após reempacotar: verificar integridade, commit/push e conferir SHA remoto.
