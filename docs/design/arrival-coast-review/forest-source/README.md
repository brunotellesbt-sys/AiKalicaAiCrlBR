# Floresta e costa a leste de Fuchsia

Estas imagens são renders dos tiles e atores permanentes do source preparado da
camada `arrival-coast-review`. **Não são capturas do emulador.** A prova funcional
da ROM é produzida separadamente por `validate_arrival_coast_forest.py`.

Foram examinados o mosaico completo, os seis mapas alterados e seus vizinhos
físicos: Fuchsia, Route15, Route14, JourneyFuchsiaInlet, JourneyKantoSouthSea,
JourneyRoute13Coast, Route13, Route19 e JourneyKantoSouthWestSea. O espaço azul
escuro fora desses mapas no mosaico é apenas o fundo da montagem.

As cinco emendas identificadas no vídeo e no censo agora têm bases completas de
árvores e margens contínuas. Os recortes de Route14 mostram o fechamento sul e
leste; o recorte de Fuchsia mostra a quina do vídeo com os arbustos, árvores e
desembarque seco preservados. Cercas, caminhos, construções, atores permanentes e
as ilhas existentes permanecem no contexto de revisão.

O render mostra somente atores sem flag de ocultação. O fóssil variável de
Fuchsia usa Kabuto, conforme o estado inicial nativo sem a flag do Dome Fossil;
essa escolha é uma fixture visual declarada, sem editar o evento do jogo.

`review.json` registra os hashes de todos os PNGs, dos blocos e eventos de cada
mapa, do JSON de layouts e do marcador da camada preparada. A comparação com a
ROM compilada, as oito fases da água e os percursos pelos controles pertencem
às provas nativas, não a este render estático.

A prova nativa desta correção passou na ROM
`9ade93b456c32bc41868642dabb287e0297cba8ebbeda97aa478bd6b11c678f5`:
[relatório e capturas](../../../../mods/hoenn/arrival-coast-review-validation/common/photos/forest/arrival-coast-forest-native.json).
Foram 424 tiles pelos controles, dez tentativas bloqueadas na vegetação,
desembarque/retorno com Surf, duas travessias do mar, o gatehouse original e
oito fases de água. O relatório declara as fixtures de equipe/progresso/viagem;
não representa uma campanha completa.

Reprodução a partir da raiz do repositório:

```bash
python3 tools/hoenn/render_arrival_coast_forest.py \
  --source .local/arrival-coast-review-src \
  --output docs/design/arrival-coast-review/forest-source
```
