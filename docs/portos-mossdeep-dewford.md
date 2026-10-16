# Prévia dos portos de Mossdeep e Dewford

Esta revisão foi integrada à ROM base local e conferida em mGBA. O pacote publicado das quatro edições ainda corresponde ao PR #88.

## Mossdeep

O terminal ocupa `(3,26)..(7,30)` e a ponte horizontal ocupa `(8,29)..(11,30)`. A porta está em `(5,30)`. Os tiles `(3,32)` e `(6,32)` copiam respectivamente `(4,32)` e `(9,31)`.

![Mossdeep](images/island-harbors/Mossdeep-grid.png)

## Dewford / Rota 107

Terminal original com telhado azul e torre náutica, construído com arte gerada e convertida em tiles GBA. A porta fica em `(5,2)` da Rota 107. O interior reutiliza o porto com navio S.S. Tidal e um capitão da rede mundial. Mr. Briney, seu barco e os treinadores nativos continuam nos locais originais.

A ponte é reta no trajeto, com piso contínuo e uma única base em cada extremidade. Sua representação tem o trecho central elevado. O piso ocupa as colunas `5..6`, linhas `4..14`; o Surf passa pelo nível inferior. Os cabos e os apoios laterais bloqueiam somente quem está no nível superior. O barco acrescentado sob a ponte foi retirado.

Os tiles `(4,10)`, `(5,10)` e `(5,11)` são água no nível inferior, sob a ponte preservada. As bordas retas e as curvas externas usam as peças inteiras de praia nativas, tomando como referência Rota 107 `(2,10)` e Dewford `(14,10)`. Os cantos internos mantêm os quadrantes nativos, no estilo da curva de Rota 107 `(8,18)`. A praia acompanha todo o contorno da areia exposta.

Foram acrescentadas 24 árvores completas no norte e no leste, deixando o prédio e os acessos livres. A conferência das pedras encontrou 52 grupos nativos completos: 48 preservados e quatro retirados por inteiro onde o porto ou a ponte ocupam seu espaço. O rochedo grande a sudeste da ponte foi preservado.

As árvores de `(3,13)..(7,16)` foram retiradas por unidades completas; as copas junto à borda da clareira foram fechadas. O novo trecho ao norte está conectado à Rota 107 e à Rota 106 por conexões normais de mapa.

![Porto de Dewford](images/island-harbors/Dewford-island-harbor.png)

![Interior](images/island-harbors/Dewford-harbor-interior.png)

[Imagem com coordenadas relativas à Rota 107](images/island-harbors/Dewford-island-harbor-grid.png).

A conferência usou caminhada no piso superior, Surf no inferior, entrada e saída pela porta, viagem para Pallet e retorno, e navegação pelas conexões ao norte. As primeiras posições e o estado inicial da história são fixtures. A reprodução independente confirmou a mesma preparação e os 31.067 arquivos não alterados; a arte dos outros mapas que continuam usando a paleta nativa ficou idêntica. Battle Frontier preservada.
