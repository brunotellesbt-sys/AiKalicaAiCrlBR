# Posição do personagem no mapa integrado

A tela MAP usava apenas o centro associado ao identificador de cada mapa. Entrar em outra rota selecionava imediatamente esse centro, mesmo depois de andar um único tile. Em Mossdeep, o centro da rota marítima também estava deslocado para noroeste.

A camada `world-map-position` calcula a posição usando as coordenadas reais do personagem. Cada tile de borda tem uma coordenada compartilhada pelos mapas conectados, calculada com o offset e as dimensões desses mapas. Isso inclui os cantos com três ou quatro rotas. As coordenadas são suavizadas ao longo das bordas para evitar saltos nas interseções. A posição dentro de cada mapa interpola seu centro e essas âncoras pela distância em tiles. Os centros das extensões marítimas próximas de Mossdeep foram realinhados. SELECT retorna à posição calculada, e o ponto ciano usa a mesma posição que o cursor inicial. Interiores sem conexões conservam o ponto da sua seção regional.

O desenho do atlas permanece idêntico: a paleta, os tiles e o tilemap compilados foram comparados byte a byte com a ROM anterior. Fly continua usando os destinos e as regras de visita existentes.

## Validação

- Execução da função compilada em 572 conexões de superfície, incluindo os portos de Sevii, comparando posições dos dois lados das bordas, incluindo seus cantos. A tabela compilada de coordenadas foi conferida; tiles vizinhos de borda variam no máximo dois pixels.
- Travessia curta para leste de Mossdeep por controle normal, com Surf, sem reposicionar o personagem no meio do percurso. O marcador não saltou ao mudar de mapa.
- Abertura do MAP, movimento do cursor e SELECT na ROM.
- Evidências e imagem: `playable-validation/world-map-position/`.

Os testes de projeção usam posições preparadas para cobrir as bordas; a travessia curta usa uma única posição inicial preparada e depois apenas os controles. Isso não representa uma campanha completa jogada do começo ao fim.
