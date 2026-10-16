# Portos de Cinnabar, Cerulean e Petalburg

As fachadas vermelhas de Slateport ocupam os limites indicados pelo jogador:

| Porto | Canto superior esquerdo | Canto inferior direito |
|---|---|---|
| Cinnabar | `(4,11)` | `(10,14)` |
| Cerulean Port / Rota 25 | `(61,6)` | `(66,9)` |
| Petalburg Coast / Rota 104 | `(15,47)` | `(19,50)` |

As fachadas têm quatro tiles de altura, com telhado, porta e janelas completas.
Cada terminal possui um interior com o S.S. Tidal grande, um barqueiro da rede
mundial e um barco médio Seagallop junto à ponte externa.

## Cinnabar

![Cinnabar](images/three-harbors/CinnabarIsland_Frlg.png)

A porta está em `(7,14)`, ligada à ponte existente por uma faixa de madeira.
O terreno da antiga casa foi restaurado onde ficou descoberto, e o acesso
ao laboratório, Centro Pokémon e Mart permanece livre. As pedras do mar
continuam completas. Saves na antiga casa ainda saem pelo acesso do porto.

## Cerulean Port

![Cerulean Port](images/three-harbors/Route25_Frlg.png)

O terminal fica acima da ponte existente, com a porta em `(64,9)`.
O barco médio está na água à direita da ponte. A casa de Bill e os
personagens da rota mantêm seus acessos.

## Petalburg Coast

![Petalburg Coast](images/three-harbors/Route104.png)

O terminal ocupa o lugar indicado para a casa do Mr. Briney, com a porta
original em `(17,50)`. A ponte, o barco local, Peeko e os eventos nativos
continuam disponíveis. O capitão do terminal oferece os portos mundiais e
`LOCAL SERVICES`, que dá acesso à sala original do Mr. Briney. O rival
aguarda em `(17,52)`, o mesmo ponto definido pelo script nativo de chegada.
O barco médio da rede fica na água a oeste da ponte existente.

## Interior dos três terminais

![Interior com navio grande e um barqueiro](images/three-harbors/JourneyCinnabarHarbor.png)

Os destinos da rede mundial chegam dentro dos respectivos terminais.
Vermilion, Pacifidlog, os demais portos e o mapa-múndi permanecem com os
mesmos dados. A reprodução independente confere os arquivos não alterados
e os mapas que compartilham as paletas modificadas.

A conferência em mGBA percorre a porta e a ponte por controles, verifica os
cascos sobre água, conversa com o capitão, viaja de cada terminal a Pallet
e volta, e salva e continua em cada interior, na base e nas quatro edições.
Também confere a saída da antiga casa de Cinnabar e o acesso ao serviço
local do Mr. Briney. As posições e o estado inicial são fixtures; não se
trata de uma campanha completa. Evidências anteriores mantêm seus hashes.
