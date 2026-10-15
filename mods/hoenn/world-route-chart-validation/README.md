# Atlas e passagens costeiras

`layout.json` registra as conexões reais de mapas, os traçados ortogonais,
as áreas consolidadas e a geometria de GPS das três passagens novas.
`world-route-chart.json` vincula as provas abaixo ao hash da ROM final:

- pixels azuis nas dez amostras das áreas marcadas em vermelho;
- cursor dentro dos limites geográficos de cada passagem;
- arrays compilados do atlas e do zoom iguais aos dados preparados;
- todas as ligações do desenho correspondem a conexões nativas;
- sete bocas de passagem cruzadas por Surf na ida e na volta;
- 17 aberturas do MAP durante os percursos, comparando o cursor com o tile
  atual, além de movimento manual, SELECT, zoom e retorno sem deslocar o jogador;
- mudança da posição do cursor em diferentes pontos de cada rota.

A posição inicial em cada passagem, equipe, história, Repel e treinadores
são fixtures. As travessias e os percursos posteriores usam os controles do
mGBA; não há escrita de coordenadas durante cada percurso. Não é uma prova de
campanha completa. As capturas mostram o menu nativo da ROM.

Os nomes ficam na seleção do MAP e no [índice de rotas](../../../docs/rotas-maritimas.md),
sem rótulos pintados sobre o atlas.

```sh
python3 tools/hoenn/validate_world_route_chart.py \
  --source .local/sootopolis-src --library .local/mgba-bridge.so \
  --output mods/hoenn/world-route-chart-validation
```
