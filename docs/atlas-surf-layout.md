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
