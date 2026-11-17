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
