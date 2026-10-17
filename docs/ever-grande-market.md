# Casas e feira de Ever Grande

A feira de Mega Stones permanece em Ever Grande. A loja de itens competitivos fica separadamente no [exterior da Battle Frontier](vendinha-dewford.md); o Hyper Training permanece em Dewford.

![Casas e barraca junto ao Centro Pokémon](images/ever-grande/plaza.png)

Duas casas ficam nos antigos canteiros em frente ao Centro Pokémon de Ever Grande. Cada uma tem dois moradores e um interior mobiliado diferente. O caminho central, as duas escadas e os acessos ao Centro Pokémon e à Victory Road continuam livres.

| Casa | Presente |
| --- | --- |
| À esquerda | 1 Full Restore |
| À direita | 1 Max Revive |

Os presentes são únicos por save. Se a mochila estiver cheia, o morador guarda o item até haver espaço. Conversar novamente ou salvar e continuar não duplica o presente.

![Interior da casa da esquerda](images/ever-grande/house1.png)
![Interior da casa da direita](images/ever-grande/house2.png)

A barraca azul ao lado do Centro Pokémon usa o modelo da feira de Slateport. O vendedor oferece as Mega Stones do jogo por **₽200.000 cada**. O preço é exclusivo dessa barraca; os valores comuns dos itens e das outras lojas continuam os mesmos.

![Mega Stones e preços no jogo](images/ever-grande/shop.png)

O marcador vermelho de Sootopolis foi restaurado no mapa e no zoom. A Cave of Origin continua dentro da cidade, com seu nome e posição cadastrados; seu símbolo não cobre mais a cidade.

![Sootopolis com o marcador da cidade](images/ever-grande/sootopolis-map.png)

As quatro [ROMs normais](../roms/README.md) e a [ROM de teste](../roms/rom-de-teste/LEIA-ME.md) incluem esta atualização. A ROM de teste continua sem encontros selvagens nem abordagem automática de treinadores.

A validação em mGBA percorre as portas das duas casas e do Centro Pokémon, testa a mochila cheia, a entrega única, conversas repetidas, uma compra por ₽200.000, a recusa com ₽199.999 e o save/continue. As cinco ROMs têm relatórios próprios com seus hashes em `mods/hoenn/ever-grande-market-validation/`. A reprodução independente da camada verifica todos os arquivos anteriores. A correção do Western River e da Rota 114 tem testes novos de praia, Surf, desembarque, limites e ligações regionais; as demais rotas conservam seus dados. Os testes extensos anteriores continuam anexados à compilação testada, com os hashes originais.

O PR #93 também está incluído: a feira de Dewford, o Hyper Training por Bottle Caps, o TM Play Rough e as formas Origin pelos Orbs foram preservados e exercitados novamente nas cinco ROMs.

## Ligação do rio de Fallarbor

[Vídeo real de Surf e Waterfall](videos/western-river-fallarbor.mp4), na edição Gen 1–9 Normal desta atualização. Western River já se liga ao lago da Rota 114 abaixo da cachoeira, e a margem do lago dá acesso a Fallarbor. Waterfall sobe ao lago superior, um desvio que não é obrigatório para chegar à cidade. O vídeo começa na praia a pé, ativa Surf pela margem e mostra a travessia, a subida, a descida, o desembarque e a chegada à cidade a pé. O paredão e os arbustos recortados foram restaurados, a praia tem elevação de terra e a pequena poça do caminho foi fechada. Nenhum porto foi adicionado ao rio.

A posição inicial, o grupo com Surf/Waterfall, os eventos anteriores, o relógio ao meio-dia e a ausência de encontros durante a gravação são fixtures. Depois da partida, os deslocamentos e as ações de campo são feitos por controles no mGBA, sem teletransporte ou escrita de coordenadas. O relatório `fallarbor-river.json` vincula a gravação ao SHA-256 da ROM normal.

[Imagens e validação da correção do rio de Fallarbor](fallarbor-river.md).
