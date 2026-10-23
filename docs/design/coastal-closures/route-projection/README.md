# GPS das sete rotas costeiras

As sete áreas externas antes chamadas de portos recebem os nomes `ONE ISLAND COAST` até `SEVEN ISLAND COAST`, banner habilitado e tipo `MAP_TYPE_OCEAN_ROUTE`. Os IDs internos continuam os mesmos. Elas permanecem fora dos destinos de Fly e da tabela de cura; as cidades das ilhas mantêm seus destinos próprios.

O reparo altera 1.013 células de GPS somente nessas sete grades de 17 × 13. Todos os pixels das 25 fronteiras conectadas permanecem idênticos, assim como as demais grades, os pontos cartográficos e as três matrizes gráficas do mapa-múndi. A geometria física, conexões, eventos e warps dessas rotas não mudam.

A interpolação harmônica usa as fronteiras conectadas como condições fixas. Uma restrição adicional conserva o limite de dois pixels por movimento cardinal de um tile e o progresso na direção principal dos dois trajetos centrais. As bordas sem conexão podem acompanhar o novo interior. Não há busca pelo ramo cartográfico mais próximo nem alteração do desenho do atlas.

| Rota | Células alteradas | Retorno artificial leste antes → depois | Retorno artificial sul antes → depois |
| --- | ---: | ---: | ---: |
| One | 165 | 10 → 0 px | 2 → 0 px |
| Two | 195 | 11 → 0 px | 4 → 0 px |
| Three | 137 | 1 → 0 px | 1 → 0 px |
| Four | 30 | 0 → 0 px | 0 → 0 px |
| Five | 164 | 8 → 0 px | 6 → 0 px |
| Six | 165 | 4 → 0 px | 6 → 0 px |
| Seven | 157 | 9 → 0 px | 5 → 0 px |

Esses números usam a direção principal entre os extremos reais de cada linha central, não presumem que toda saída local leste avance para a direita no atlas esquemático. O eixo secundário pode conservar uma curva pequena exigida pelas fronteiras fixas: um pixel em One/leste, Six/sul e Seven/leste; dois em One/sul. O trecho vertical curto de Three quantiza para um único pixel. As bordas conectadas que já representam curvas não recebem uma promessa de monotonicidade global.

`route-projection-source-audit.json` compara diretamente os arquivos do pai imutável da camada 162 e do candidato preparado. Os sete PNGs `*-gps-before-after.png` mostram esses dados sobre o mesmo atlas, com leste em magenta e sul em amarelo. São **diagramas de dados do source, não capturas da ROM**. `unchanged-atlas-source.png` mostra a imagem reconstruída das matrizes preservadas.

A prova nativa fica em `mods/hoenn/coastal-closures-validation/<edição>/route/route-identity.json`, vinculada ao SHA da ROM daquela edição. Ela percorre com controles os trajetos de Surf x=2…14/y=6 e x=8/y=2…10, lê a função compilada `JourneyWorldMapPosition`, abre o MAP pelo menu no local real do jogador e verifica o cursor, recentralização, rótulo, banner e bloqueio de Fly. Cada uma das 25 conexões é percorrida nos dois sentidos. A posição inicial, a equipe, o progresso, o estado inicial de Surf e a solicitação de exibição do banner são fixtures declaradas; os trajetos medidos usam controles.

O controle negativo está em `mods/hoenn/coastal-closures-validation/baseline/route-projection-negative-control.json`. A ROM obsoleta da camada 163, com os nomes novos e o GPS anterior, reproduz o retorno de seis pixels no trecho real x=2…14 de One Island Coast e é rejeitada pelo mesmo validador. Esse diagnóstico não é uma prova da ROM final.

Comandos reproduzíveis, a partir da raiz:

```sh
python3 tools/hoenn/audit_coastal_route_projection.py \
  --before .local/sevii-integrated-src \
  --after .local/coastal-closures-release-src \
  --output docs/design/coastal-closures/route-projection
python3 tools/hoenn/validate_coastal_route_identity.py \
  --source .local/coastal-closures-release-editions/Gen1-9-Normal \
  --library .local/mgba-review.so \
  --output mods/hoenn/coastal-closures-validation/Gen1-9-Normal/route
```
