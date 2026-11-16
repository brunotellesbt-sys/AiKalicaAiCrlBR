# Aqui — LEIA PRIMEIRO: retomada técnica de Pokémon Journey

## Estado mais recente — 16/11/2026

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
