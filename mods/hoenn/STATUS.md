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
- Encontros com nível pela média da equipe e fase evolutiva pela média das
  insígnias das duas regiões; Pokédex Nacional desde o início.

Essas verificações cobrem casos e trechos específicos. Não representam duas
campanhas completas jogadas. Relatórios da base de mapas ficam em
`integration-validation`; os da candidata com habilidades ficam em
`abilities-validation`, com identificação da ROM própria e da base utilizada.

## Trabalho que falta antes do lançamento

1. Ampliar a validação de habilidades em batalhas duplas, trocas e desmaios,
   junto às demais habilidades do catálogo.
2. Auditar as Mega Stones e testar Mega Evoluções em batalhas reais, sem
   distribuir pedras ou liberar novos itens antes da decisão sobre acesso.
3. Conferir todos os estados das histórias e puzzles em ordens diferentes de
   ginásios, incluindo Ligas, concursos, bases secretas e Battle Frontier.
4. Revisar personagens, interiores e eventos dos mapas durante viagens reais;
   procurar bloqueios indevidos, recompensas repetidas e regressões de save.
5. Validar renderização dos sprites restantes e formas, além dos cabeçalhos
   já auditados. Testar sessões prolongadas e salvamento no navegador.
6. Jogar ambas as campanhas completas e revisar os resultados antes de
   substituir a ROM do player.

Não há estimativa confiável de porcentagem concluída: passar uma auditoria de
dados não mede o trabalho restante em eventos, batalhas e campanhas.
