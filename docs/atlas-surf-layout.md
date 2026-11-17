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

# Rotas físicas segundo o atlas — camada 172

**Em reconstrução. Sem ROM 172 validada ou publicada.**

O ambiente que continha a implementação anterior está indisponível. A base
recuperada é a revisão 171, commit `7ec174b8f7d0c621ec9a60d8b771619e86628889`.
Os scripts, relatórios e candidatos locais da camada 172 não foram recuperados.
O estado verificável e as exigências recebidas estão em
[ESTADO-DA-TAREFA.txt](../errors/ESTADO-DA-TAREFA.txt).

A arte original do mapa-múndi é a referência imutável. A nova rede deve
respeitar direção, distância, conexões e posições físicas, com escala de oito
tiles por pixel e corredores de seis tiles. O marcador do jogador precisa
derivar das coordenadas globais afins; mover só o GPS não corrige geografia.

A entrega exige prova independente da classificação da arte e da rede,
migração versionada de saves, índices de consulta compactos, ecologia com
gatilhos efetivos, revisão dos mapas inteiros e travessias reais na ROM.
Relatórios estáticos ou de candidatos anteriores não substituem essas provas.

O código será preservado em checkpoints remotos. Enquanto houver pendências,
o usuário pediu PR normal com pendências explícitas. As ROMs públicas
continuam na revisão 171 até a conclusão das provas finais.

## Checkpoint da reconstrução

A fonte upstream recebeu novamente as 171 camadas. Os 32.250 arquivos de
entrada e o contrato fixado da revisão 171 coincidem; isso é reconstrução
verificada da base, sem recuperar o workspace perdido. O comando de retomada
é `tools/hoenn/restore_generated_area_review.py`; ele recusa fontes alteradas
ou preparações incompletas sem apagá-las.

Os módulos geométricos usam oito tiles por pixel, corredores de seis tiles,
grupos de até cem mapas e coordenadas afins. A auditoria do plano é separada
do gerador e exige classificação externa. Os módulos de ecologia usam donos
históricos explícitos; aliases não certificam que o terreno tem gatilhos de
captura. A migração de saves 2 passou testes C de versões e registros;
as provas nativas Save/Continue continuam pendentes.

O diagnóstico que trata **todos** os 1.529 pixels azuis como água gerada
produz 347 mapas de até 32 tiles e 15 componentes. Ele inclui pixels nativos
e um ícone e **não é o plano final**. Não se deve ajustar regras para obter
as contagens do trabalho perdido. Ainda faltam a classificação física, os
adaptadores e a integração de eventos, cenário e ecologia.

## Birth Island

O telhado isolado foi identificado no mapa inteiro da fonte 171. O gerador
novo troca as quinze células do objeto por um corpo completo de madeira
nativa, mantendo colisões e alturas, e substitui as duas pontas metálicas.
O metatile do warp possui uma única referência
nesse banco e recebe madeira sem alterar seu comportamento ou evento.
Navel Rock mantém a embarcação completa.

[Antes](design/atlas-surf-layout/birth-source-before.png) ·
[Depois](design/atlas-surf-layout/birth-source-after.png) ·
[Registro das células](design/atlas-surf-layout/birth-source-review.json).

São renders de fonte sem os NPCs dinâmicos; não são capturas do jogo nem
provas de travessia. A correção ainda não foi publicada numa ROM 172.

O primeiro diagnóstico abriu água no lugar do telhado e passou o percurso
local; o JSON técnico recebido depois esclareceu que o corpo deve continuar
bloqueado. O gerador e o render acima já foram corrigidos. Aquele diagnóstico
anterior não valida o corpo de madeira atual. A prova foi repetida e passou
na nova ROM diagnóstica `b058983d…`: corpo bloqueado contra Surf, saída e
retorno pelo lado, Harbor nos dois sentidos e pixels do avatar. O
[relatório e capturas](design/atlas-surf-layout/diagnostic-birth-native/birth-native.json)
estão preservados com os hashes. Continuam sendo prova diagnóstica; repetir
na candidata final e nas edições pertinentes.


Atualização de14/11: o halo físico agora tem módulo próprio e prova diagnóstica
nativa de três mapas em L (incluindo largura4). Quatro divisas ida/volta,
coordenadas consistentes3–5frames após trocar ID, oito tiles norte sem deriva,
recifes, diagonal BG e avatar passaram. Birth foi repetida na mesma ROM.
64testes atlas e1teste de continuidade aprovados. Índice das12capturas e dois
relatórios: `docs/design/atlas-surf-layout/diagnostic-physical-review.json`.
A candidata real completa e as cinco edições continuam pendentes. O diagnóstico
não autoriza publicação172 ou afirmação de desempenho na escala436.
