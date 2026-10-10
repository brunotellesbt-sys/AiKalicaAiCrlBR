# Mapa do mundo integrado

Abra **Start → MAP** no jogo. A mesma tela integrada é usada pelo Town Map e pelo mapa do Pokénav. Os nomes e controles dentro do jogo estão em inglês.

O mar usa uma cor azul uniforme; as rotas aquáticas navegáveis são azul escuro. As marcações não cobrem o terreno das ilhas nem as cidades. O mapa inclui Lavender Port, as novas costas e passagens marítimas, as Sevii e os santuários. O mar azul escuro entre Fuchsia, Lavender e o oceano leste representa agora uma área contínua de Surf. A ligação amarela ao norte do cais corresponde à ponte a pé.

As linhas indicam conexões existentes nos mapas do jogo; o mapa regional não representa cada pedra ou cada tile de praia.

O antigo botão amarelo de troca de região, com o centro branco, foi removido somente da arte do mapa integrado. O terreno das ilhas ao redor permanece preservado.

A saída à direita de Fuchsia é uma faixa azul escura estreita. Lavender Port ocupa um pequeno marcador e uma ponte curta; as Sevii ficam próximas de Mossdeep e Ever Grande, com suas linhas marítimas chegando aos portos. Essa disposição ajusta a representação regional; as conexões físicas preservam os percursos validados.

As novas ligações aparecem como faixas horizontais e verticais de espessura constante, com cruzamentos alinhados e ramais até as ilhas. O mar ao redor permanece azul claro. As faixas de terra originais de Kanto, incluindo a costa abaixo de Lavender Port, são preservadas.

O indicador ciano é a posição do jogador e o cursor vermelho permite consultar lugares. Use as setas para mover, **Select** para voltar à sua posição e **B** para retornar. Fly usa esse mesmo mapa integrado: Lavender Port e as sete cidades das Sevii aparecem como destinos depois de visitados. As cavernas novas têm marcadores azuis claros, mas não são destinos de Fly. A animação de voo usa o sistema nativo.

![Mapa integrado dentro do jogo](playable-validation/world-map/world-map-JourneyRoute12Shipyard.png)

![Arte do mapa ampliada](world-map-gallery/world-map-art.png)

A validação nativa abre MAP com controles reais em Kanto, Hoenn, Sevii e Lavender Port, move e recentraliza o cursor e retorna sem alterar a posição do jogador. Viagem e configuração inicial desses cenários são fixtures; esse teste não equivale a concluir as campanhas.

A costa oeste mantém a faixa de Cinnabar pelo Western River, Rustboro Coast e Dewford Coast. Os ramais chegam à Route 115 e à Route 105/106, junto a Rustboro e Dewford. Uma travessia de ida e volta por controles reais verifica essas bordas sem teleporte durante o percurso. As massas de terra ao norte de Hoenn e a oeste de Kanto completam somente o contorno regional, sem criar estradas.

A subida do rio oeste conserva o requisito de Waterfall; a descida e a subida são exercitadas no emulador com zero insígnias. O grafo de colisões e comportamentos aquáticos da ROM confirma que os nove novos canais da costa de Kanto são alcançáveis pela rede de Surf.

A conferência abrange os 54 mapas de mar integrado: todos têm tiles de areia e são alcançáveis pela rede de conexões. Os blocos de borda impedem avançar além de lados sem conexão. A barreira de dois pedregulhos da Rota 20 foi aberta para que Fuchsia e Cinnabar façam parte da mesma rede contínua de Surf. [Detalhes e imagens](SEA-NETWORK-AUDIT.md).
