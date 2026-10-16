# Porto de Fuchsia / Rota 19

O terminal de Slateport substitui a casa antiga, agora sobre a água a oeste
da praia, na área da pedra que estava cortada. O telhado vermelho e a fachada
são os mesmos usados no terminal de Pallet. A borda da montanha foi completada,
e a antiga casa na areia foi removida.

![Exterior com barco médio junto à ponte](images/fuchsia-harbor/Route19_Frlg.png)

A passarela em L dá acesso ao prédio. O barco externo agora é o Seagallop
médio, na horizontal, ao lado da extremidade da ponte. O único barqueiro
fica dentro do terminal, onde está o S.S. Tidal grande.

![Interior com navio grande e barqueiro](images/fuchsia-harbor/JourneyFuchsiaHarbor.png)

O destino Fuchsia da rede mundial desembarca dentro do novo terminal.
Entradas e saídas preservam o índice do acesso antigo, permitindo que saves
que estavam dentro da antiga casa saiam pela nova porta. Os treinadores da
rota continuam em seus lugares. Pallet, Sootopolis, Lavender, Sevii e o
mapa-múndi conservam seus dados.

Validação em mGBA: caminhada desde a praia, entrada e saída pela porta,
colisão dos dois barcos sobre a água, conversa com o barqueiro, viagem
Fuchsia ↔ Pallet e save/continue no terminal, na compilação base e nas quatro
edições. As posições e o estado inicial são fixtures; os trajetos e menus
usam comandos do controle. A camada foi reproduzida independentemente,
conferindo os arquivos não alterados e os demais mapas que compartilham
a paleta de Fuchsia.

As evidências anteriores permanecem vinculadas aos hashes das ROMs nas quais
foram executadas. Não são apresentadas como uma nova campanha completa.

Para reproduzir em um ambiente ARM preparado:

```sh
python3 tools/hoenn/build_integration_candidate.py --source .local/hoenn-route12-src --jobs 8
python3 tools/hoenn/render_fuchsia_harbor.py --source .local/hoenn-route12-src --output docs/images/fuchsia-harbor
python3 tools/hoenn/validate_fuchsia_harbor.py --source .local/hoenn-route12-src --library .local/mgba-bridge.so --output mods/hoenn/fuchsia-harbor-validation/validation
```
