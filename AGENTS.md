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

Exigência mais recente do autor(17/11): o próximo PR só pode ser aberto depois
de TODOS os testes e verificações obrigatórias passarem. Nenhum PR novo aberto.
Checkpoint/push na branch são permitidos; não mascarar os8FAIL+1ERROR de selo.

Retomada mais recente: [docs/RETOMADA-2026-11-17.md](docs/RETOMADA-2026-11-17.md).
PR112 foi merged pelo autor emmain9dff8c3. Branch atual de trabalho:
fix/cave-chambers-release-validation-2026-11-17. Gates finais e cavernas em trabalho.

# Instruções persistentes do projeto

Antes de editar mapas conectados, aplique também [Aqui/SKILL-DIVISAS-E-CAMERAS.md](Aqui/SKILL-DIVISAS-E-CAMERAS.md): layout declarado/ativo, faixa do vizinho, bancos, diagonais e cache `mapView` precisam concordar antes e depois da travessia.

Antes de qualquer tarefa, leia [docs/CONTINUIDADE-TECNICA-IA.md](docs/CONTINUIDADE-TECNICA-IA.md)
e o JSON histórico lá vinculado. Após cada lote coerente, atualize esse guia e
`errors/ESTADO-DA-TAREFA.txt` com o pedido literal mais recente, o último pedido
concluído, o pedido ainda incompleto, arquivos, provas/hashes, limitações e
próximo passo. Faça checkpoint e push verificado antes de operações longas.
O usuário pediu explicitamente PR normal, sem rascunho, nesta continuidade;
descreva as pendências sem confundir abertura do PR com validação/publicação
das ROMs. Preserve o ambiente antigo e as preparações parciais.

Para qualquer alteração de cidades, portos, ginásios, interiores, terreno, praias ou rotas de Surf, leia e aplique [.agents/skills/gba-map-review/SKILL.md](.agents/skills/gba-map-review/SKILL.md).

Consulte também [errors/README.md](errors/README.md) e o registro de erros relevante antes de editar; atualize-o com reprodução, causa, solução e provas da ROM final para evitar regressões já documentadas.

O usuário exige revisão visual do mapa inteiro, objetos completos e validação de colisões, acessos e conexões na ROM. A preferência anterior por gerar uma proposta inspirada em GBA foi dispensada explicitamente pelo usuário nesta revisão: não gere novas propostas sem um novo pedido. Não apresente imagem gerada como captura do jogo. Não altere o mapa-múndi sem autorização explícita.

Para diagnóstico preciso sem repetir o histórico, consulte primeiro a seção RESUMO de [docs/AJUSTES-GBA.txt](docs/AJUSTES-GBA.txt) e apenas as seções relevantes. Use `tools/hoenn/inspect_map_tile.py` para obter bloco, altura, colisão, camadas e gráficos reais. Os exemplos reutilizáveis ficam em [assets/tiles/](assets/tiles/), com mapa doador e banco explícitos; nunca trate IDs como universais nem copie somente parte de um objeto.
