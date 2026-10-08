# Estado da integração

A candidata ainda não está pronta para lançamento. O player continua com sua
versão anterior. A candidata exige um novo jogo; não há conversão de saves.

## Etapas com verificações específicas

- Kanto, Hoenn e Sevii conectados, incluindo 96 travessias físicas por Surf.
- Histórias e insígnias separadas, missões nas portas dos ginásios e ligação
  obrigatória entre Giovanni na Silph e a batalha final contra Archie.
- Ginásios em ordem livre com níveis por quantidade de insígnias da região.
- Casas fixas, escolha da cidade antes da chegada por caminhão ou barco,
  família, iniciais regionais e bicicleta compartilhada.
- Surf, Dive e Waterfall como os únicos HMs; presentes da família e conversão
  dos antigos HMs terrestres em TMs.
- Catálogo de 1.025 espécies-base, 920 comuns em 135 habitats e 105 especiais
  em 14 santuários. Locais documentados em `POKEMON-LOCATIONS.md`.
- Habilidades Ocultas nos encontros, slots Torrent/Protean/Battle Bond para
  a família de Greninja e transformação após nocaute com reversão ao fim
  da batalha; validação da forma de evento e de Froakie.
- Arte de Mega Garchomp Z completada; ligações e referências das 97 Megas
  auditadas, cinco transformações reais e dois casos negativos verificados.
- Trocas e desmaios: limite de uma Mega por batalha e permanência/reversão
  de Ash-Greninja verificados pelo menu nativo.
- Descompressão ARM de 3.323 imagens de 1.571 espécies/formas comparada aos
  pixels originais, incluindo as Megas e variantes femininas; 3.154 paletas
  carregadas pela rotina ARM, sem índices de cores fora de seus limites.
- Matriz de 3.840 decisões de missões com todos os conjuntos regionais de
  insígnias, mais 36 permissões de Silph e da aliança contra Archie.
- Batalhas duplas reais contra Tate e Liza: Battle Bond e uma Mega coexistem;
  Torrent/Protean não geram Ash-Greninja, e a vitória/save preservam a insígnia.
- Steven contra Maxie/Tabitha: seleção real da equipe, vitória, pós-batalha,
  chamada do rival e conclusão permanente confirmados no save nativo.
- Desfecho de Archie e Shelly com Giovanni exercitado até a Rota 128,
  despertar de Rayquaza e cena de paz. O último ginásio em ordem livre só abre
  após a crise terminar; a casa de Sootopolis continua acessível durante ela.
- Matriz posterior de 4.096 decisões de missão, incluindo a crise climática.
- Encontros com nível pela média da equipe e fase evolutiva pela média das
  insígnias das duas regiões; Pokédex Nacional desde o início.
- Guia por região e habitat em [POKEMON-LOCATIONS.md](POKEMON-LOCATIONS.md),
  índice de 71 lendários, 23 míticos e 11 Ultra Beasts com entradas e altares
  em [SPECIAL-LOCATIONS.md](SPECIAL-LOCATIONS.md), e planilha filtrável em
  [pokemon-locations.csv](pokemon-locations.csv). São 1.025 espécies-base e
  55 variantes regionais; Megas e outras formas de batalha não são encontros
  independentes. `location-documentation.json` identifica a candidata e os
  arquivos utilizados para gerar os documentos.
- Auditoria estática dos 1.046 mapas: 2.800 passagens e 372 conexões têm
  destinos válidos, considerando os 29 interiores residenciais substituídos
  pela escolha inicial. Não comprova colisões ou acesso jogável. Há 64 destinos
  dinâmicos e sete origens fora dos limites normais para revisar no motor,
  registrados em `aftermath-validation/map-destinations.json`.

Essas verificações cobrem casos e trechos específicos. Não representam duas
campanhas completas jogadas. Relatórios da base de mapas ficam em
`integration-validation`; os da candidata com habilidades ficam em
`abilities-validation`; arte, Megas e regressões posteriores ficam em
`mega-validation`; o desfecho climático e as regressões posteriores ficam em
`aftermath-validation`, com identificação da ROM própria e da base utilizada.

## Trabalho que falta antes do lançamento

1. Ampliar a validação para as demais habilidades do catálogo e combinações
   de batalhas duplas; os casos de Battle Bond e Megas não cobrem todas elas.
2. Renderizar e conferir animações e efeitos de todas as Megas em batalha.
   Os pixels foram descomprimidos e cinco formas passaram por batalhas reais.
   Não distribuir pedras ou liberar novos itens antes da decisão sobre acesso.
3. Conferir todos os estados das histórias e puzzles em ordens diferentes de
   ginásios, incluindo Ligas, concursos, bases secretas e Battle Frontier.
4. Revisar personagens, interiores e eventos dos mapas durante viagens reais;
   procurar bloqueios indevidos, recompensas repetidas e regressões de save.
   Conferir também os destinos dinâmicos e as sete origens indicadas pela
   auditoria estática (Battle Dome, Slateport e seu porto); não reposicionar
   essas entradas sem verificar os scripts que as utilizam.
5. Validar as animações e renderização em batalha das espécies e formas
   restantes, além dos pixels e cabeçalhos já conferidos. Testar sessões prolongadas e salvamento no navegador.
6. Jogar ambas as campanhas completas e revisar os resultados antes de
   substituir a ROM do player.

Não há estimativa confiável de porcentagem concluída: passar uma auditoria de
dados não mede o trabalho restante em eventos, batalhas e campanhas.
