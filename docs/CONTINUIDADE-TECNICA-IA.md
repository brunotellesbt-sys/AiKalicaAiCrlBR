# Continuidade técnica de Pokémon Journey

Atualizado em 14/11/2026 (UTC). Este é o ponto de entrada permanente para
outra IA ou outro ambiente. Atualize-o a cada lote verificado, antes do
checkpoint remoto. Mantenha o pedido pendente até a entrega completa.

## Estado executivo verificável

O jogo publicado continua na revisão **171 / generated-area-review**. O
trabalho aberto é **172 / atlas-surf-layout**, em reconstrução. Não existe
release 172 final validado. O workspace antigo não foi recuperado e não foi
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
PR normal aberto e confirmado: [#110](https://github.com/brunotellesbt-sys/AiKalicaAiCrlBR/pull/110),
`draft=false`, a partir do checkpoint remoto
`6aa7e90b8ec1db3948a38b7c3b5398dc089e7d86`.

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
PR normal. Último checkpoint remoto conferido antes deste lote: `b7bb3f225d42f5fa99bb51cd05da7d17f24c37e0`.

## Pedidos do usuário e resultado

### Último pedido de continuidade, completo

> Continue o progresso, o outro ambiente deixou esse documento. Abra um pr de verdade, e não um em rascunho. Crie um documento dentro no jogo tbm, totalmente técnico, pra próxima I.A. em outros ambientes entender do que se trata, dessas regras, do que fazer, e do último pedido completo, resolvido e do último pedido incompleto, não finalizado também, sempre atualizando ele.

Atendimento nesta etapa: JSON histórico salvo, este guia criado, leitura
obrigatória registrada em AGENTS.md e inclusão dos documentos no empacotador
do jogo. O PR #110 foi aberto como normal e seu estado foi confirmado.
A manutenção contínua deste guia
é um requisito permanente, não uma tarefa que termina com sua criação.

### Últimos pedidos resolvidos

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
| atlas_surf_physical.py | Clipping de cópia, halo físico por dono global, prioridade de costa nativa e guarda de conexão | Cinco testes C aprovados; integração/build/prova nativa pendentes |
| prepare_atlas_surf_diagnostic.py | Prepara três mapas privados em L, um com quatro tiles de largura | Fixture sintética, sem substituir a geografia real ou release |
| atlas_surf_ecology.py | Aliases explícitos dos pools/habitats e header nativo | Auditoria de gatilhos, áreas Dex e Gen4/Gen9/TESTE final falta |
| atlas_surface_batteries.py | Código da migração 2 e validação dos destinos | Não é o harness histórico de baterias; Save/Continue nativo falta |
| atlas_surf_source.py | Lê bancos/terreno e compila o enum/flags C nativo, detectando alterações dos inputs | Componentes locais, sem certificado do motor |
| atlas_surf_coasts.py | Inventário dos 273 IDs antigos e fechamento exato de duas células de Route114 em overlay | Não aposenta nem reloca mapas na candidata |
| atlas_surf_adapters.py | 33 componentes costeiras candidatas em 29 hosts; 32 com contato de altura compatível | Ever Grande requer revisão; nenhum novo destino atribuído |
| atlas_surf_pois.py | 18 portais recíprocos, cinco Dive e sete portos com terreno real | Inventário, sem criação dos novos acessos |
| inventory_atlas_surf_parent.py | Relatório reproduzível vinculado a 1.699 inputs e ao contrato completo 171 | Não prova conectividade global nem ROM |
| atlas_surf_native_scenery.py | 17 células e gráfico privado de Birth, corpo bloqueado | Prova do corpo passou no diagnóstico v2; repetir na candidata final |
| validate_atlas_surf_birth_native.py | Viagem por controles, avatar, bloqueio, Surf e Harbor | Repetir sobre o artefato final |

As APIs reconstruídas diferem das antigas descritas no JSON. Não supor que
um nome de módulo significa recuperação ou equivalência de implementação.
Os módulos de POIs, costas e adaptadores agora existem como inventários e
um fechamento em overlay. Ainda faltam suas integrações físicas finais,
Dive, SCC global, contrato 172, preparação/freeze/publicação e verificadores
finais. Não tratar inventário como reposicionamento de eventos ou mapas.

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

60 testes de plano, geradores, materialização, runtime, halo físico, ecologia,
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

## Halo físico: código em checkpoint antes de compilar

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
câmera, VRAM, desempenho ou viagens na ROM. Total60atlas+1continuidade.

Próxima execução autorizada, sem sobrescrever diagnósticos antigos:

```sh
.local/ci-python/bin/python tools/hoenn/prepare_atlas_surf_diagnostic.py --source .local/atlas-physical-smoke-src --clone-from .local/review171-build-src
```

O preparador verifica o parent171 antes/depois, cria cópia sem hardlinks e
recusa qualquer destino já existente, inclusive parcial. A fixture tem três
mapas em L, um com largura4, derivada de cinco pixels sintéticos. Não é a
classificação real do atlas. A migração limitada incluída é fixture sintética,
**nunca mapeamento de saves para release**. Build, hashes, provas nativas e
vínculos precisam ser registrados após executar; não há resultado pressuposto.

## Próximo trabalho técnico, em ordem

1. Conferir o checkpoint mais recente no PR normal #110 e preservar cada
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
5. Integrar e provar o novo clipping de FillConnection e halo **físico** por
   dono global. O código e cinco testes C já existem; ainda não há build ARM
   nem prova de travessia nativa desse módulo. Executar o preparador diagnóstico
   em uma cópia nova e preservada antes de aplicá-lo à candidata final.
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
