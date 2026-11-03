# One Island e vizinhos físicos

Renders estáticos da fonte nativa, **não capturas do emulador**. `before/`
representa a ROM 166; `after/` usa os 16 inputs finais da camada 167.

Os mapas completos incluem One Island, Treasure Beach, Kindle Road e a rota
a oeste nas posições determinadas pelas conexões reais. O fundo azul escuro
é área fora da montagem, não terreno incompleto do jogo. Atores permanentes
usam seus sprites nativos; eventos condicionais ficam declaradamente ocultos.

Foram examinados o mosaico inteiro e o detalhe da face oeste: frente, cantos,
área das árvores, casa, terminal e rocha de limite estão completos. O limite
norte do novo corredor de Surf tem rocha visível inteira, alinhada ao recife
da rota; não há um bloqueio invisível sobre água vazia. A rocha que continua
em Treasure Beach tem seus quatro quartos. Três fragmentos sem objeto foram
removidos junto ao telhado, sem apagar o porto.

`review.json` em cada pasta vincula imagens, blocos, eventos e layouts por SHA.
A fonte estática não demonstra animação, prioridade nem Surf: essas provas
ficam em `mods/hoenn/arrival-coast-review-validation/common/photos/one/`,
na ROM base 9ade93b456c32bc41868642dabb287e0297cba8ebbeda97aa478bd6b11c678f5.
