# Porto de Lavender

A casa no centro de Lavender Port foi substituída pelo mesmo terminal de
Pallet: fachada de Slateport com telhado laranja, interior com o S.S. Tidal
permanente e um único barqueiro interno. As passarelas e os sete barcos do
estaleiro continuam nos mesmos lugares. O acesso passa pela ilha central.
O terminal foi deslocado dois tiles para baixo e dois para a esquerda
em relação à primeira posição, com a porta em `(11,40)`.
O fundo acima do telhado usa areia nativa, assim como a faixa antes verde
ao lado do prédio; não há borda de água sobre o telhado.

![Exterior](images/lavender-harbor/JourneyRoute12Shipyard.png)

![Interior](images/lavender-harbor/JourneyLavenderHarbor.png)

O destino estável `0` da rede geral agora desembarca dentro do terminal.
Os dois warps de saída devolvem o jogador à nova porta. O antigo interior
da casa mantém sua saída para preservar saves que estavam lá dentro.
Pallet e Sootopolis conservam seus mapas e acessos.

A camada `lavender-harbor` sucede `world-route-chart`. Para reproduzir no
ambiente ARM já preparado:

```sh
python3 tools/hoenn/build_integration_candidate.py --source .local/sootopolis-src --jobs 4
python3 tools/hoenn/render_lavender_harbor.py --source .local/sootopolis-src --output docs/images/lavender-harbor
python3 tools/hoenn/validate_lavender_harbor.py --source .local/sootopolis-src --library .local/mgba-bridge.so --output mods/hoenn/lavender-harbor-validation/validation
```

A validação física percorre o cais, cruza a porta nas duas direções, confere
a colisão do navio, conversa com o barqueiro e viaja Lavender ↔ Pallet pelos
menus reais. Também salva e continua dentro do novo terminal. A posição
inicial e o estado inicial da história são fixtures; os percursos usam os
comandos do controle. Não se afirma uma campanha completa.
