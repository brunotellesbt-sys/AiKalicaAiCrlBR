---
name: gba-map-review
description: Planejar e revisar mapas GBA completos antes de alterar cidades, portos, ginásios, praias e rotas de Surf.
---

# Desenho primeiro; revisão do mapa inteiro

Use esta habilidade em toda alteração de terreno ou construção deste jogo. É uma preferência permanente do usuário.

## Antes de editar

1. Confira a branch, alterações locais e PRs recentes para preservar o trabalho paralelo do usuário. Leia os mapas e conexões reais envolvidos.
2. Renderize o mapa inteiro e as bordas dos mapas vizinhos usando os tiles nativos. Inspecione essas imagens. Identifique árvores, cercas, montanhas, rochas e construções como objetos completos, com sua largura, altura, colisão e acesso.
3. Gere uma **imagem de proposta inspirada em GBA** com a ferramenta de geração de imagens antes de alterar o terreno. Baseie a proposta na área real e nos pedidos do usuário. Mostre-a como **proposta visual**, nunca como captura da ROM. Salve a proposta em `docs/design/` e registre as decisões que ela orienta. Se a ferramenta estiver indisponível, informe a limitação; não alegue que gerou a imagem.
4. Inspecione também a proposta gerada: rejeite fachadas, Centros Pokémon, árvores ou contornos cortados na própria imagem; ajuste-a antes de tratá-la como referência de acabamento.
5. Planeje caminhos, portas, rampas, desembarques e corredores de Surf. Preserve eventos, NPCs existentes, missões e conexões. Aumente espaço vazio quando necessário e autorizado. Não redesenhe o mapa-múndi sem pedido explícito.

## Ao implementar

- Preserve a fachada inteira, a base e a entrada de cada Centro Pokémon; grama, árvores e terreno nunca podem apagar paredes nem cobrir a porta.
- Em desembarques, areia/grama deve usar a altura de terra correspondente (normalmente 3) e água a altura de Surf (normalmente 1). Teste a mudança de estado nos dois sentidos; não copie os bits de altura do mar para a praia.
- Confira o comportamento nativo antes de definir a altura. Arte de praia pode representar água: na borda sul de Dewford, `0x12C` é água (altura 1), enquanto `0x124` é areia seca (altura 3). O desembarque deve terminar na areia seca, não num tile de água elevado artificialmente.
- Ao ampliar um mapa, preserve também o relevo encostado às construções originais. Mover a borda externa não pode apagar a montanha junto à Lavender Tower; feche a massa, frente e cantos antes de encaixar o novo prédio.
- Identifique o objeto nativo inteiro em vez de supor tamanho ou paridade das coordenadas. Árvores FRLG isoladas usam pares de copa e base em 2 × 2 tiles; os metatiles intermediários de uma floresta sobreposta não são troncos isolados.
- Use conjuntos completos de tiles nativos. Não apague apenas parte de uma árvore, prédio, cerca, falésia ou rocha para encaixar outra coisa.
- Em interiores, confira o conjunto inteiro do móvel no mapa doador antes de copiar: computadores, estátuas e estantes podem ocupar dois ou três tiles de altura. Preserve corredores de visão dos treinadores sem apagar peças de objetos. Pisos decorativos devem conservar comportamento comum de caminhada, salvo pedido explícito.
- Nos oito ginásios extras, mantenha quatro treinadores e o guia afastado da entrada. As divisórias devem obrigar a cruzar separadamente os quatro campos de visão nas ROMs normais. Confira o alcance inteiro sem móveis ou NPCs bloqueando, prove que retirar cada linha de visão corta todos os caminhos até o líder e percorra a sala no emulador, vencendo os quatro em sequência. Não aceite uma proposta que permita desvios laterais ou prenda um treinador sem saída. A TESTE continua sem abordagem automática.
- Em sprites indexados de NPCs, confira a transparência nativa do índice zero antes de converter a imagem. A falta de transparência PNG não torna o fundo da paleta parte do personagem. Combine largura dos quadros, OAM e tabela de animação; não comprima um corpo de 32 pixels em um quadro de 16.
- Não coloque treinadores em nichos de um tile. Reserve uma faixa livre de pelo menos três tiles de largura em toda a aproximação, incluindo as laterais do NPC. Confira a direção do sprite e o espaço à frente no mapa inteiro e na câmera nativa; as paredes que definem o percurso nunca podem ocupar a faixa entre treinador e jogador.
- Ao mover um objeto, mova também copa, tronco, base, sombra, cantos, fundo e colisões. Finalize pontas de cercas e contornos de montanhas.
- Faça praias e margens com lados e cantos coerentes. Evite água no telhado, grama dentro da ponte, ilhas quadradas acidentais e mudanças bruscas de cor no mar.
- Pontes que permitem Surf por baixo devem usar o nível múltiplo nativo (15), preservando o nível 3 do pedestre e o nível 1 de quem surfa. Não use nível de transição (0) como substituto: isso pode permitir sair do píer caminhando sobre o oceano. Teste vindo da terra, sem escrever a altura do personagem.
- Confira na captura nativa se o personagem inteiro aparece acima das tábuas ao caminhar, e se quem surfa mantém a camada inferior. Colisão e estado corretos não bastam: verifique também a prioridade de desenho e os pés do personagem.
- Una pontes sem frestas; barcos precisam de água livre ao redor e não podem ficar presos entre ponte e areia.
- Bloqueie áreas externas com pedras inteiras sem fechar passagens existentes. Não permita caminhar sobre água nem surfar em terra ou estruturas.
- Verifique transições nos dois sentidos. Distância e direção percorridas devem corresponder às conexões físicas do mundo.

## Revisão obrigatória antes de concluir

1. Renderize novamente os **mapas inteiros**, com NPCs, e compare antes/depois. Examine os quatro lados das novas construções e todas as emendas, além da câmera de entrada. Uma captura pequena não basta.
2. Revise também interiores: objetos de dois ou mais tiles devem estar inteiros; corredores, saída, líderes e treinadores precisam ser acessíveis.
3. Percorra na ROM as entradas, saídas, pontes, desembarques e conexões afetadas nos dois sentidos. Confira colisões, bancos gráficos e paletas carregados durante a transição. Salve e continue sobre um píer ou ponte alterados e confirme visibilidade, altura e bloqueio de caminhada para a água.
4. Separe evidência visual de evidência funcional. Testes de passagem não certificam acabamento visual, e uma proposta bonita não certifica a ROM.
5. Não compile, regenere nem empacote uma ROM enquanto um validador estiver lendo essa ROM, seu ELF ou o mesmo source. Preserve snapshots históricos e evite editar arquivos compartilhados por hard links.
6. Corrija defeitos vistos, atualize as ROMs e capture provas com o SHA da versão final. Não reaproveite prova de uma ROM anterior como validação da nova.
7. Registre em `docs/design/` os mapas revisados, imagens reais, verificações executadas e limitações. Só então conclua o PR normal solicitado.

Não crie uma etapa de aprovação obrigatória: mostre a proposta e prossiga dentro do escopo autorizado, incorporando as correções do usuário.
