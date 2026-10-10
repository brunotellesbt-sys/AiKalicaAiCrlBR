# Entrada leste de Ever Grande e chegada a Vermilion

A faixa de mar a leste de Hoenn chega ao oceano das Sevii. A ligação com
Vermilion é **pela borda sul da cidade, no canal de Surf da costa sudeste**:
Vermilion `(34, 38)` → borda sul `(34, 39)` → `JourneyWorldSea00 (34, 0)`.
O cais original e seus eventos permanecem. A seta vermelha indica esse canal.

![Traçado amplo, incluindo Vermilion](ever-grande-entrance-gallery/eastern-union-labelled.png)

Este recorte usa os tiles reais e as coordenadas das conexões do jogo.
Inclui Vermilion, o mar leste de Hoenn e as faixas marítimas das Sevii;
ainda não é o mapa completo de Kanto nem a nova tela do PokéNav.

## Abertura do recife

Foram retirados 27 tiles de rochas no mar abaixo da costa, na lateral leste
da entrada original de Ever Grande. O canal permite navegar entre a base da
cachoeira e o mar atrás da ilha. A cachoeira, a piscina superior, as montanhas,
os eventos e a exigência de 16 insígnias para a Liga permanecem.

Antes:

![Recife antes](ever-grande-entrance-gallery/entrance-before.png)

Depois:

![Canal aberto](ever-grande-entrance-gallery/entrance-after.png)

Camada `ever-grande-entrance`, aplicada após `eastern-sea-union`.
A preparação modifica apenas `data/layouts/EverGrandeCity/map.bin`;
reprodução determinística e idempotência registradas em
[ever-grande-entrance-validation/preparation](ever-grande-entrance-validation/preparation).

```sh
python3 tools/hoenn/prepare_ever_grande_entrance.py --source <fonte>
make -C <fonte> -j8
python3 tools/hoenn/validate_ever_grande_entrance.py --source <fonte> --library <mgba-bridge.so> --output <resultados>
python3 tools/hoenn/render_eastern_union.py --source <fonte> --output <galeria> --include-vermilion
```

Candidata compilada: `abd8ad32504714f884048fc0aa14884194bec6a0caaf615428a0da407e172c56`.

A validação de viagem usa equipe, posição inicial, treinadores já derrotados
e encontros selvagens desativados como fixtures. Não representa duas campanhas
completas nem valida o balanceamento. Não há publicação da ROM ou do player.

Viagem nativa de ida e volta concluída: Vermilion → mar das Sevii → costa
leste de Hoenn → entrada leste de Ever Grande → base da cachoeira → Vermilion.
Foram registradas 15 mudanças de trecho e um save/Continue junto à cachoeira.
253 testes de Hoenn e 12 de rotas marítimas passaram.
