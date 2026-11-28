---
name: divisas-e-cameras
description: Revisar mapas vizinhos, layouts ativos e a faixa de câmera antes de editar rotas, cidades, portos e cavernas.
---

# Lembrete permanente: o vizinho deve mostrar a edição antes da entrada

Pedido do autor em 17/11/2026: ao andar entre rotas modificadas, às vezes a
visão da outra rota mostra a versão anterior e só muda depois de entrar.
Identificar e reparar esse padrão; conservar este roteiro para não repeti-lo.

Use junto com [gba-map-review](../.agents/skills/gba-map-review/SKILL.md).
Uma edição só está concluída quando o mesmo objeto aparece corretamente
antes da primeira entrada, durante a travessia, após entrar e ao retornar.

## Termos e causas que precisam ser distinguidos

- **Salto visual na divisa (map popping):** o mesmo ponto físico muda de
  aparência quando muda o mapa dono da câmera. Anote mapa, coordenadas,
  direção e SHA; não conclua que seja um problema de desempenho.
- **Faixa de conexão (connection apron/halo):** o motor copia até sete tiles
  do vizinho para a grade local. Uma curva pode mostrar um terceiro mapa na
  diagonal, fora dos retângulos carregados. Borda repetida não é terreno real.
- **Layout declarado versus layout ativo:** `map.json`/`MapHeader.mapLayout`
  pode apontar para um desenho, enquanto `MAP_SCRIPT_ON_TRANSITION` usa
  `setmaplayoutindex` e escolhe outro. Editar só o desenho errado deixa a
  câmera do vizinho e o interior discordando. Confira o ponteiro no emulador.
- **Estado condicional:** Mirage Island, marés, portas e progressão dependem
  de flags, variáveis ou horário. Não fixe uma variante condicional como
  permanente nem execute scripts de entrada no vizinho para obter sua arte.
- **Banco gráfico carregado (tileset):** o ID de um metatile não é universal.
  Compare os oito words, atributos/camadas, gráficos, paletas RGB555 e callback
  de animação na câmera de cada lado. Bytes iguais não provam ponteiros iguais.
- **Cache da visão (`mapView`):** `SaveMapView`/`MoveMapViewToBackup` pode
  recopiá-lo na transição; `LoadSavedMapView` pode restaurá-lo no Continue.
  Um cabeçalho correto sozinho não prova que o fundo salvo já foi renovado.
- **Alterações por script (`setmetatile`) e decoração por OBJ:** podem não
  existir no arquivo estático. Diferencie cenário permanente de portas,
  quebra-cabeças, NPCs e treinadores. Não generalize spawn do vizinho a atores
  interativos nem apague eventos para uniformizar as câmeras.

## Roteiro obrigatório

1. Leia os mapas inteiros e conexões recíprocas, offsets, dimensões, layouts
   alternativos e scripts. Examine as bordas e os cantos diagonais. Preserve
   objetos completos, o atlas, acessos, colisões e alturas reais.
2. Rode `tools/hoenn/audit_neighbor_layouts.py --source FONTE --output RELATORIO`.
   Ele procura variantes em mapas compilados conectados e patches literais
   perto da divisa. Candidatos não são defeitos nativos confirmados. Mudanças
   geradas em C e condições ainda exigem análise específica.
3. Reproduza antes da primeira entrada. Compare o mesmo ponto físico em ambas
   as câmeras; não compare apenas tiles de mesmo ID ou nomes do GPS. Confira
   a grade realmente carregada, o layout ativo, BG/VRAM/paleta e pixels.
4. Corrija a origem: layout permanente canônico, resolução do estado correto,
   compatibilidade de bancos, halo diagonal ou invalidação específica do cache.
   Não force redraw por teletransporte, setters de câmera ou edição da VRAM.
   Uma correção apenas visual não pode liberar colisão/altura/BorderId.
5. Teste ida e volta por controles, três fases de animação, barreiras e acessos.
   Declare fixtures iniciais e getters read-only. Não consulte VarGet nativo
   com menus ou diálogos ativos. Não compile enquanto um leitor usa a fonte.
6. Teste bateria antiga → Continue → SAVE pelo menu → segundo Continue. Se a
   versão do save mudar, limpe só o cache necessário, uma vez; preserve posição,
   NPCs, capturas e missões. Não aplique translações repetidamente.
7. Repita as provas com os hashes das ROMs atuais. Atualize as cinco candidatas,
   manifestos, `Aqui`, erros e ZIP; confira integridade, commit e push. Preserve
   freezes/provas anteriores e não converta casos locais em aprovação global.

## Caso desta revisão

Na ROM `5b5b1ace…`, o censo examinou 663 mapas conectados: três variantes de
layout, duas com alterações na faixa da câmera, e 12 patches literais próximos
de conexões. As duas divisas da Rota131 foram reproduzidas no mGBA. A rota
declara `LAYOUT_ROUTE131`, mas sempre ativa `LAYOUT_ROUTE131_SKY_PILLAR`.
A correção alinha o cabeçalho ao layout já usado no jogo; a Rota130/Mirage
Island e a Rota111 continuam condicionais. Consulte o estado mais recente em
[RETOMADA](../docs/RETOMADA-2026-11-17.md) para hashes e provas finais.

Prova final desta revisão: ROM `c08cb777…`, duas divisas, três fases por
observação, ida/volta, bloqueios e saves6→7→SAVE→Continue7 passaram. As cinco
candidatas do PR foram atualizadas; outras divisas/estados continuam exigindo
seus próprios casos. Evidência: `docs/design/neighbor-layout-camera-review`.

## Fixture de treinadores também pode falsear uma falha de caminho

Não use TRAINER_FLAGS_START + ID para treinadores novos sem conferir o
resolvedor nativo JourneyBeachTrainerFlag. Os IDs novos usam flags privadas.
Uma preparação assim ativou FLAG_SYS_CRUISE_MODE, e a CPU repetia
SSTidalCorridor_EventScript_ReachedStepCount após o limite de passos.
Colisão/altura/câmera corretas não bastavam para o jogador andar. Use as flags
exatas do manifesto ou SetTrainerFlag durante o fixture; depois só controles
e getters. Preserve o trace do diagnóstico e repita os percursos afetados.

Atualização de 18/11/2026: depois de mudar chegadas de portos ou aposentar
mapas, o validador deve ler ports.arrivals do marker atual. Coordenadas de
metadados antigos não certificam o caminho atual; NoRoute antes do primeiro
controle ainda é falha de planejamento, não prova de colisão no jogo.
Cabeçalhos com shared_scripts_map/shared_events_map precisam ser comparados
aos ponteiros e contagens do dono compartilhado declarado. Nunca aceitar um
ponteiro divergente nem presumir que todo mapa possui seus próprios símbolos.

## Retirada de uma rota navegável

- Relacione os pixels do Atlas aos metatiles e aos mapas físicos que os
  contêm. Remova também os pequenos segmentos de ligação na boca do corredor.
  Preserve os entroncamentos que servem aos trajetos mantidos.
- Confira a arte normal e o zoom 2× da ROM compilada. Mantenha conexões
  de câmera que ainda exibem o terreno vizinho. A colisão do recife deve
  fechar o caminho nas duas direções e o mar comum pode continuar visível
  atrás dele.
- Procure treinadores, eventos e referências AREA da Pokédex nas células
  afetadas. Teste cada boca, os desvios e o Continue de um save feito tanto
  dentro da rota retirada quanto em uma área que perdeu seu acesso.

## Personagens que entram pelo limite da câmera

Na arena do PWT, `SpawnSpecialObjectEventParameterized` recebe coordenadas que incluem `MAP_OFFSET`. Conferir a posição local inicial e final do objeto no mapa, sua identidade gráfica e a imagem no instante em que o jogador deve vê-lo. A câmera pode descarregar um personagem criado cedo demais, mesmo quando a posição de destino está correta. Reproduzir o caminho do jogador e verificar o adversário no campo antes de abrir a caixa de escolha. [Capturas e reprodução](../mods/hoenn/pwt-arena-positions/README.md)
