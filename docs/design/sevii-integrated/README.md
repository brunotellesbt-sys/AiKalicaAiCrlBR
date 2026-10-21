# Terminais ligados às pontes das sete ilhas

Cada terminal fica na própria ilha, ao final de sua ponte. A antiga passagem
da ponta da ponte para um porto distante foi substituída pela porta do terminal,
que leva diretamente ao interior existente. O capitão, a rede de viagens e os
destinos internos foram preservados. Os antigos mapas externos agora são mar;
seus IDs e suas conexões continuam presentes para não romper as rotas de Surf.

As imagens abaixo são **renderizações dos tiles nativos de origem, com NPCs**,
não capturas de emulador nem propostas geradas. As provas na ROM ficam nos
relatórios próprios da entrega.

| Ilha | Revisão do mapa inteiro | Posição do terminal |
| --- | --- | --- |
| One | [Antes/depois](One-comparison.png) | Treasure Beach, `(14,0)` |
| Two | [Antes/depois](Two-comparison.png) | Two Island, `(2,8)` |
| Three | [Antes/depois](Three-comparison.png) | Three Island Port, `(4,13)` |
| Four | [Antes/depois](Four-comparison.png) | Four Island, `(2,28)` |
| Five | [Antes/depois](Five-comparison.png) | Five Island, `(14,13)` |
| Six | [Antes/depois](Six-comparison.png) | Six Island, `(3,23)` |
| Seven | [Antes/depois](Seven-comparison.png) | Seven Island, `(17,13)` |

One usa a ligação existente entre a cidade e Treasure Beach. Em Seven, a
porta fica na linha 18 e o tablado de entrada na linha 19 da cidade. O tablado
continua pelas duas primeiras linhas de Sevault Canyon Entrance; o acesso
anterior ao cânion, à esquerda, permanece. A porta fica antes da conexão,
permitindo que o passo de entrada ative a passagem nativa para o interior.
Nenhum mapa teve suas dimensões ou conexões alteradas.

As fachadas têm os mesmos 7 × 6 tiles do terminal nativo. Três bancos gráficos
privados preservam as paletas dos outros mapas de Sevii, incluindo Mt Ember.
Os pixels de cada fachada são comparados com o doador nativo. A revisão final
também inclui as árvores e falésias completas de Six Island e a continuidade
da arte do mar nas emendas, verificadas em relatórios próprios.

Os barcos pequenos e médios foram reposicionados nas seis ilhas com espaço,
com uma faixa de água livre ao redor dos cascos. Six não recebe barco externo:
não há espaço para um cais seguro sem tocar a falésia ou a cidade. O terminal,
seu interior e a passagem de Surf são preservados.

A [revisão estática](static-review.json) verifica caminhos secos da cidade à
porta, ao tablado frontal e ao ponto de embarque, além da água ao redor dos
barcos. Isso verifica a geometria de origem; não substitui os percursos na ROM.
As [coordenadas e alterações](layout-metadata.json) registram os bancos, os
tablados, os barcos, os pontos de Surf e a limpeza dos portos antigos.
O [contrato de validação](VALIDATION.md) descreve as 42 provas atuais, os
testes de rejeição e a preservação dos relatórios históricos.
