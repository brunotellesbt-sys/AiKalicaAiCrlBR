# O que falta para lançar a integração

A candidata ainda é de desenvolvimento. Kanto, Hoenn e Sevii estão ligados;
existem histórias conectadas com insígnias regionais, casas iniciais, família, encontros e
santuários. Há testes de trechos, batalhas e dados; ainda não houve duas
campanhas completas jogadas. O player não recebeu esta candidata.

## Prioridades

| Prioridade | Trabalho | Critério para concluir |
|---|---|---|
| 1 | Jogar as duas campanhas, começando em cada região e variando a ordem dos ginásios | Chegar aos dois Hall of Fame com missões cumpridas por interação, sem flags ou níveis de fixture |
| 2 | Revisar puzzles e estados de história originais | Remover dependências antigas de insígnias específicas, HMs terrestres e Acro Bike que ainda impeçam o caminho; manter as missões de ginásio e os três HMs aquáticos |
| 3 | Percorrer mapas e novos mares | Conferir colisões, NPCs, escadas, Dive, saídas de cavernas e destinos dinâmicos; os 14 acessos locais de santuário passaram, mas faltam as viagens completas até seus mares e demais percursos |
| 4 | Pós-jogo e demais instalações da Frontier | Exercitar concursos, bases secretas, serviços, recompensas e desafios nativos; conferir que não compartilham insígnias/conclusões indevidas |
| 5 | Balanceamento | Sessões com atributos normais para ginásios livres, equipes vilãs, encontros e PWT; as fixtures aceleradas não servem para avaliar dificuldade |
| 6 | Catálogo em batalha | Ampliar a cobertura de habilidades, formas, animações e Megas; a auditoria das 1.025 espécies e pixels não testa toda interação de batalha |
| 7 | Sessões no navegador e versão de lançamento | Rodar sessões prolongadas, exportar/importar saves e testar os dois finais no navegador antes de atualizar o player |

## Estimativa provisória

Mantendo o tamanho recente dos PRs, a previsão é de **10 a 20 PRs para uma
candidata de lançamento**, sujeita aos problemas encontrados nos percursos e
campanhas completas. A quantidade de PRs não mede a conclusão do jogo.

## Avanço atual: reencontro de Wanda sem HM terrestre

Corrigido o gatilho da cena de Rusturf Tunnel, que dependia das pedras removidas.
Passaram as caminhadas pelo oeste/leste, recompensa TM53, salvar/Continue e
revisita; progresso anterior do resgate ainda é fixture.
Candidata `407bd93b`; [RUSTURF-REUNION.md](RUSTURF-REUNION.md).
As campanhas completas e os demais eventos de puzzle continuam pendentes.

## Etapa anterior: acesso às duas Ligas com 16 insígnias

Corrigida a mensagem de líder ocupado nas Ligas. Ambas exigem oito insígnias
de cada região; as missões permanecem nos checkpoints dos ginásios.
Candidata `19a4cd8a`; [SIXTEEN-BADGE-LEAGUES.md](SIXTEEN-BADGE-LEAGUES.md).
Ainda falta jogar as duas campanhas completas sem fixtures.

## Etapa anterior: sete episódios originais com conclusão obrigatória

Mt. Moon, Rockets de Cerulean/Rota 24, resgate de Fuji, Petalburg Woods,
Rusturf/Peeko, carta a Steven e Museu de Slateport entram nas travas regionais
de ginásios. A regra de Liga desta etapa foi substituída pela exigência
das 16 insígnias descrita acima. Corrigidas a carta aceita sem item, a ativação Devon depois
de qualquer primeiro ginásio e o reinício indevido ao vencer Roxanne mais tarde.
Candidata `127e1f2a`; [MANDATORY-NATIVE-MISSIONS.md](MANDATORY-NATIVE-MISSIONS.md).

O objetivo é concluir todas as missões de história. A revisão dos demais
episódios e as campanhas completas permanecem trabalho obrigatório de
implementação/validação; não são missões deixadas opcionais por projeto.

## Etapa anterior: ferramentas antecipadas e história preservada

Silph Scope, Devon Scope e Wailmer Pail vêm da mãe desde o início, nas duas
regiões, sem concluir as missões originais. Poké Flute continua após o primeiro
ginásio. Encontros fixos de história permanecem como exceções à regra de
habitat único dos selvagens. A candidata é `ba38f2ff`; testes de entrega nas
31 casas, continuações dos três donos, mochila/PC, salvar/carregar e recompensa
nos 16 ginásios. [EARLY-STORY-TOOLS.md](EARLY-STORY-TOOLS.md).

## Etapa anterior: Pokémon Tower e inventário de encontros fixos

Cubone/Marowak fica reservado para a Pokémon Tower; Nidoran♀ e evoluções
passam para Diglett’s Cave. Corrigida a reconstrução do fantasma com Silph
Scope, que voltava ao nível 30 e ignorava a faixa da equipe. Passaram fuga,
quatro vitórias, Continue e escada para o sétimo andar, além dos 135 habitats.
Candidata `cccad98c`; [TOWER-HABITATS.md](TOWER-HABITATS.md).

O inventário estático inclui scripts compartilhados e o callback de Sudowoodo.
As repetições nos encontros fixos de história foram autorizadas como exceções.
Continuam pendentes a revisão de outros callbacks, suas condições de acesso
e as campanhas completas.

## Etapa anterior: resgate de Lostelle e entrega do Meteorite

Drowzee/Hypno fica reservado para Berry Forest, incluindo o Hypno de Lostelle;
Skorupi/Drapion passa para Mt. Pyre. Foram atualizados encontros, Pokédex e
documentos, com os 135 habitats conferidos no motor ARM. Candidata `0f1df908`;
[LOSTELLE-HABITATS.md](LOSTELLE-HABITATS.md).

Bill/Celio, pedido do pai, quatro motoqueiros, caminhada por Bond Bridge,
Hypno e escolta original passaram, seguidos pela entrega e Moon Stone.
Hypno manteve a faixa da média da equipe; oito batalhas e oito Continues,
com revisita sem repetir o encontro. Candidata `0f1df908`.
Missões de Ruby/Sapphire, minigames e outras áreas de Sevii, campanhas
completas e balanceamento seguem pendentes. [LOSTELLE-STORY.md](LOSTELLE-STORY.md).

## Etapa anterior: cidades e Centros Pokémon de Sevii

As sete cidades foram alcançadas desde o mar, com cura nativa pela enfermeira,
Continue no Centro, saída pela cidade/porto e Continue em Surf. Passaram
34 mapas, 62 transições, sete curas e 14 Continues. O validador usa os
ponteiros reais dos tilesets de interiores; viagem oeste repetida.
Missões de Celio/Lostelle, outros serviços, cavernas e exploração completa
das ilhas continuam pendentes. [SEVII-TOWN-ACCESS.md](SEVII-TOWN-ACCESS.md).

## Etapa anterior: travessia contínua Kanto–Sevii–Hoenn

Corrigido o canal no layout alternativo da Rota 131, que voltava a fechar
após recarregar o mapa. Passaram Vermilion, os sete portos de Sevii,
Pacifidlog, Rota 127 e retorno: 24 mapas, 42 bordas, seis batalhas e oito
Continues. Sky Pillar e idioma verificados na candidata `2f53d410`.
Exploração completa das ilhas, outras saídas do mar e campanhas completas
seguem pendentes. [EASTERN-OCEAN-JOURNEY.md](EASTERN-OCEAN-JOURNEY.md).

## Etapa anterior: viagem contínua no mar oeste

Cinnabar–lago da Rota 114–Rustboro–Dewford–Cinnabar passou sem
teletransportes intermediários: 13 mapas, 24 travessias, cinco batalhas e
seis Continues. O planejador passou a respeitar conexões e elevações,
com regressões de santuários e Sky Pillar. A candidata em inglês foi
preservada. Os outros percursos e as campanhas completas
seguem pendentes. [OCEAN-JOURNEY.md](OCEAN-JOURNEY.md).

## Etapa anterior: idioma e capturas persistentes

O jogo passa a usar inglês também nos 97 textos/rótulos novos que estavam
em português. A auditoria textual, duas casas iniciais e inscrição PWT
passaram. Corrigida a penalidade indevida da Master Ball contra Ultra Beasts.
Pecharunt, Lugia e Nihilego passaram por fuga, nocaute, nova tentativa,
captura, retorno e sete Continues, sem duplicação. Os outros 102 especiais,
balanceamento e campanhas completas seguem pendentes.
[ENGLISH-GAME.md](ENGLISH-GAME.md).

## Etapa anterior: percursos dos 14 santuários

Os nove acessos de ilha e cinco submersos passaram da aproximação no mar
até os altares e de volta ao ponto inicial, sem colocações internas ou
entrada direta de efeitos/scripts. Passaram as 105 interações bloqueadas
com zero insígnias e 33 Continues. O planejador passa a ler formatos FRLG
e Emerald; Sky Pillar foi repetido como regressão. A ROM permaneceu igual.
Viagens completas entre regiões, batalhas e capturas de todos os especiais
e campanhas completas seguem pendentes. [SANCTUARY-ROUTES.md](SANCTUARY-ROUTES.md).

## Etapa anterior: Sky Pillar e proteção da sequência climática

A porta externa da torre abre sem esperar Wallace. Uma visita antecipada
não desperta Rayquaza: o evento exige sete insígnias de Hoenn, requisitos
da aliança, Archie e o confronto inicial em Sootopolis. Passaram o percurso
pelos cinco andares, queda, topo, retorno e três Continues. O desfecho nativo
Archie–Rayquaza–paz–último ginásio também passou na nova candidata. Os layouts
rachados posteriores, outras viagens e as campanhas completas ainda precisam
ser percorridos. [SKY-PILLAR-ACCESS.md](SKY-PILLAR-ACCESS.md).

## Etapa anterior: duas passagens antigas de pós-jogo

Altering Cave e Desert Underpass ainda dependiam da vitória na Liga de
Hoenn. Essa dependência foi retirada dos dois scripts de entrada. Passaram
ida, volta e nova entrada após Continue com zero insígnias, além da descoberta
nativa de Desert Underpass. Recompensas, encontros e missões foram preservados;
Sootopolis e a matriz regional passaram na nova candidata. O interior completo
da caverna, as campanhas e outros caminhos seguem pendentes.
[CAVE-ACCESS.md](CAVE-ACCESS.md).

## Etapa anterior: acesso e retorno de Sootopolis

A Rota 126, a passagem submersa e as duas margens de Sootopolis foram
percorridas no motor, com visita à casa oeste e ao Centro Pokémon leste.
Passaram 190 mudanças de posição e seis Continues, mantendo zero insígnias
e o episódio de Kyogre pendente. O planejador de testes foi compartilhado
com a Seafloor Cavern; a candidata permaneceu igual. Isso não cobre todos
os interiores nem a campanha. [SOOTOPOLIS-ACCESS.md](SOOTOPOLIS-ACCESS.md).

## Etapa anterior: Continue submerso e volta da caverna

Os dois personagens de Kanto retomavam um save submerso em Surf. A restauração
agora respeita o tipo do mapa; 16 casos de terra/Surf/Dive/subida passaram para
os quatro personagens. A volta da Seafloor Cavern também passou pelos controles
normais, com três Continues conservando posição, modo, insígnias e pendências.
A matriz regional passou novamente na candidata. Outros percursos, campanhas
completas e balanceamento seguem pendentes. Os estados iniciais, viagens e
equipe são fixtures; evidências em [WATER-CONTINUE.md](WATER-CONTINUE.md).

## Etapa anterior: acesso à Seafloor Cavern

O grunt que fechava a entrada foi movido para o lado, mantendo sua conversa
e o evento de Steven. O percurso nativo passou por Dive com zero insígnias,
subida, salas 1/2/6/3/8/9, correntezas e batalha dupla de Shelly. Archie
continuou recusando o confronto sem os requisitos de história; Save/Continue
conservou o estado. A matriz regional passou novamente na nova candidata.
A posição inicial no mar, equipe, atributos e cura são fixtures. Outros
caminhos internos e as campanhas completas continuam pendentes.
Evidências e reprodução em [SEAFLOOR-ACCESS.md](SEAFLOOR-ACCESS.md).

## Etapa anterior: sequência do submarino

Maxie, entrevista de Stern, roubo do submarino, entrada por Surf e percurso
até Matt passaram pelos eventos nativos. Foram 138 passos, oito transições
nos três andares. A volta também passou: mais 49 passos, duas transições,
Surf pela interação da margem e saída para Lilycove. Foram seis batalhas,
incluindo duas duplas. Save/Continue já no mar
conservou a progressão sem alterar as insígnias ou a pendência de Kanto.
As viagens entre cidades, etapas anteriores, cura e atributos de batalha continuam
como fixtures; as campanhas completas seguem pendentes.
Evidências e reprodução em [SUBMARINE-STORY.md](SUBMARINE-STORY.md).

## Etapa anterior: passagens e episódios Aqua

Três passagens dos Regis abrem ao ler suas inscrições, sem exigir golpes
terrestres. Shelly após quatro insígnias de Hoenn e Matt após seis passam a
bloquear ginásios ainda não vencidos, com orientação do guia. Houve vitórias
nativas, recompensas/desfechos originais, travessia das portas e Continue,
mais a matriz de todos os conjuntos de insígnias. A revisão geral de puzzles,
rotas e campanhas continua pendente. Detalhes em
[PUZZLES-AND-AQUA.md](PUZZLES-AND-AQUA.md).

## Revisão anterior de progressão das histórias

Foram conferidas 28 vitórias reais das incursões de Kanto/base Rocket de Hoenn,
com missões regionais separadas, abertura das portas e salvamento/Continue.
Giovanni também foi vencido pelo evento original da Silph, liberando sua aliança
obrigatória em Hoenn e conservando-a após Continue. As campanhas completas
continuam como primeira prioridade: viagens, insígnias e episódios anteriores
foram preparados como fixtures, e os atributos foram aumentados para acelerar
os confrontos. Guia e evidências em [INTEGRATED-STORY.md](INTEGRATED-STORY.md).

## Etapa anterior: PWT e embarque

- PWT Singles passa a **seis contra seis**, com seleção da ordem dos seis,
  normalização no nível 50 e restauração completa. Adversários usam as seis
  espécies de sua equipe própria. Não existe Doubles neste módulo.
- Inscrição e regras também verificam o quinto/sexto Pokémon: equipes
  incompletas, ovos, repetição de espécies/itens e espécies banidas.
- Embarque nativo de Hoenn confere o S.S. Ticket antes de oferecer destinos,
  evitando chegar à Frontier sem o bilhete exigido na volta. A entrega pela
  família após a Liga de Hoenn e a primeira visita de Scott foram preservadas.

Resultados e limites específicos estão em [PWT.md](PWT.md),
[FRONTIER-TRAVEL.md](FRONTIER-TRAVEL.md) e [STATUS.md](STATUS.md).

## Decisões já estabelecidas

Surf, Dive e Waterfall são os únicos HMs. As regiões mantêm suas oito insígnias
separadas e a ligação obrigatória de Giovanni com a Silph. Os especiais exigem
16 insígnias antes da Liga; Drowzee/Hypno e Skorupi/Drapion trocaram de habitat.
Não distribuir Mega Stones/itens de ativação nesta revisão: a instrução anterior
foi preparar a mecânica sem liberar esses itens. A candidata exige novo jogo;
não existe migração dos saves antigos.

Não há porcentagem confiável de conclusão. O principal risco restante está
na interação entre eventos durante campanhas reais, não na contagem de mapas.
