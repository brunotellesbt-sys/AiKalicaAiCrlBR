# Estado da integração

A candidata ainda não está pronta para lançamento. O player continua com sua
versão anterior. A candidata exige um novo jogo; não há conversão de saves.

## Etapas com verificações específicas

- Kanto, Hoenn e Sevii conectados, incluindo 96 travessias físicas por Surf.
- Histórias conectadas, insígnias e Ligas separadas, missões nas portas dos ginásios e ligação
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
- Liga de Kanto corrigida: a Pokédex Nacional inicial não ativa mais o bloqueio
  original de Lorelei ausente. A porta depende das oito insígnias de Kanto.
  O marcador de campeão/rematches também tem banco próprio, sem compartilhar
  a vitória de Hoenn; o Hall of Fame de Kanto agora registra esse marcador.
- Na candidata posterior, os 256 conjuntos de insígnias de Kanto e 20 casos
  físicos das portas das duas Ligas foram exercitados. Vitórias reais contra
  Lorelei e Sidney, portas para a sala seguinte, Battle Bond e save/reload
  passaram, com a outra região previamente campeã como estado de teste.
- Regressões posteriores: 4.096 decisões de missão, 97 referências de Megas,
  16 viagens de barco em nove portos e 18 travessias por Surf na ligação oeste.
  Ainda não são vitórias completas nas Ligas nem nas duas campanhas.

Essas verificações cobrem casos e trechos específicos. Não representam duas
campanhas completas jogadas. Relatórios da base de mapas ficam em
`integration-validation`; os da candidata com habilidades ficam em
`abilities-validation`; arte, Megas e regressões posteriores ficam em
`mega-validation`; o desfecho climático e as regressões posteriores ficam em
`aftermath-validation`, com identificação da ROM própria e da base utilizada.
A camada posterior `league-access` fica em `.local/hoenn-league-src`; seus
relatórios estão em `league-validation`, com base `c10695f` e candidata
`e2fb947f`. Os documentos de localização agora identificam essa candidata,
com a mesma distribuição de Pokémon e os mesmos santuários.

## Conclusão das Ligas e retorno à família

A camada posterior `league-completion` grava o quarto da residência escolhida
como destino de retorno após o Hall of Fame. Littleroot respeita o quarto de
Brendan ou May conforme o personagem. Sem uma casa válida, os destinos originais
de Pallet/Littleroot continuam como fallback. O layout do save não mudou.

A etapa anterior fica em `.local/hoenn-completion-final-src`, com relatórios em
`completion-validation`, base `e2fb947f` e ROM `f7110f29`. Há verificações de
62 destinos persistidos (31 casas × dois personagens), além das duas sequências
de Elite Four, campeão, Hall of Fame, créditos e Continue. Kanto retorna à casa
em Mauville e Hoenn à casa em Vermilion nos dois casos exercitados, mantendo
equipe, habilidade oculta e a outra região sem concluir.

Os níveis 100, as insígnias, a casa e a cura entre batalhas são fixtures de teste.
Esses percursos não equivalem a jogar as campanhas completas. Na etapa anterior, as duas sequências
foram exercitadas em saves novos separados.

A candidata da etapa anterior fica em `.local/hoenn-history-src`, base `f7110f29` e ROM
`73135dc67a53928b13bc4c36319e14b688848284cee42a304f84e6e56f92d5e0`, com
relatórios em `history-validation`. A primeira vitória na segunda região apagava
o histórico da primeira: a decisão usava uma flag regional para um arquivo
compartilhado. Agora usa o contador compartilhado de equipes efetivamente salvas.
As duas interfaces usam a mesma capacidade de 50 equipes; o formato do save e
as flags regionais permanecem iguais.

Foram vencidas as dez batalhas nativas em sequência no mesmo save, nos dois
sentidos, com créditos, Continue, retorno à residência e save/reload. A segunda
vitória preserva o primeiro registro byte a byte e mantém as duas regiões campeãs.
Com 50 equipes de fixture, novos registros nas duas interfaces removem somente
o mais antigo. Uma revanche real contra Lorelei usa o trainer 1470 após uma
flag de campeão de Kanto preparada pelo teste; a primeira visita continua usando
1164 mesmo após vencer Hoenn. A validação de revanche daquela etapa cobre apenas Lorelei; os testes completos e a consulta pelo PC
seguem na etapa abaixo.

Foram repetidas na candidata atual as 4.096 decisões de missão, 36 permissões,
o catálogo de 1.025 espécies-base, as 97 referências de Megas e a auditoria de
destinos dos mapas. A candidata ainda não foi publicada no player.

## Hall of Fame no PC e números da Pokédex acima de 999

A candidata atual fica em `.local/hoenn-display-src`, base `73135dc6` e ROM
`24858d6c4653152c4267fe4b3acbb8d4ac79a140640196d7d0cc7b0f5c922334`.
A camada `league-display` altera somente o formatador de números em
`src/hall_of_fame_frlg.c`: o nº 1025 aparecia como `!25`; agora aparece como
`1025`. O estilo de três dígitos dos números menores, as espécies desconhecidas,
as regras de batalha, os mapas e o formato do save permanecem iguais.

Relatórios em `postgame-validation` exercitam o PC físico dos Centros Pokémon de
Viridian e Oldale, com arquivos de uma e 50 equipes. A navegação visita todos os
registros, seleciona os seis membros, respeita os limites e sai por B ou por A
no registro mais antigo. O menu retorna e permite desligar o PC; o arquivo
permanece igual após save/reload. As equipes são fixtures com Bulbasaur, Pikachu,
Treecko, Turtwig, Greninja e Pecharunt, com Pokédex Nacional habilitada.

A comparação de pixels antes/depois limita a mudança ao número 1025 em Kanto.
O número de Bulbasaur e as telas equivalentes de Hoenn são idênticos. O limite
compartilhado de 50 equipes também foi repetido na nova candidata, com os dois
finais nativos, créditos, Continue e preservação dos outros 49 registros.

As duas Ligas e suas visitas seguintes foram vencidas em sequência na candidata
da etapa `league-display`, nos dois sentidos: Kanto → Hoenn → Kanto → Hoenn e Hoenn → Kanto → Hoenn
→ Kanto. Cada percurso contém 20 vitórias nativas, quatro Hall of Fame, créditos,
Continue e save/reload, mantendo os registros anteriores e as duas regiões campeãs.
A revanche de Kanto usa os trainers 1470, 1471, 1472, 1473 e 1476; Hoenn mantém
os trainers de Emerald 261, 262, 263, 264 e 335. As equipes de NPCs permanecem
originais. A equipe de teste usa golpes de cobertura contra o último campeão.

As capturas por região mostram a última visita de cada percurso. Os relatórios
completos distinguem as quatro sequências e seus IDs. Níveis, insígnias e cura
entre batalhas são fixtures; esses percursos não equivalem às campanhas completas
nem validam o balanceamento. As explorações interrompidas ficam ignoradas em
`.local`; os relatórios publicados identificam a ROM efetivamente exercitada.
A candidata ainda não foi publicada no player. Os demais eventos de pós-jogo
continuam pendentes de revisão.

## Pós-jogo da família e exclusão dos encontros errantes

Na candidata `family-postgame`, a mãe da casa escolhida entrega o S.S. Ticket
após a Liga de Hoenn, inclusive em Kanto, e apresenta a notícia de Latias/Latios.
Vencer apenas Kanto não libera essa entrega. A passagem não duplica e a bolsa
cheia permite tentar novamente. Passaram 248 estados das 31 residências e seis
diálogos completos com save/reload, incluindo os dois gêneros em Littleroot.

Os encontros errantes nativos de lendários nas rotas foram desativados.
Latias, Latios e os três cães usam os santuários com exigência das 16 insígnias.
A base produziu 30 encontros forçados de Latias em 100 tentativas; a candidata
produziu zero antes das conquistas e zero com 16 insígnias e ambas as Ligas.
As conquistas são fixtures. A matriz de missões e a auditoria do catálogo
passaram novamente; não houve alteração nas equipes, níveis ou locais comuns.

Evidências em [family-postgame-validation](family-postgame-validation/reproduction.json).
Candidata: `4f3b1fc8412fdf783494b219b3366669dcbab22c2a3e1cfb0699ea7a0d3b87d8`.
Os oito percursos de Liga da etapa anterior não foram repetidos nesta candidata;
a alteração desta etapa foi conferida pelos scripts e helpers do pós-jogo.
O embarque original do S.S. Tidal, Battle Frontier e os demais eventos de
pós-jogo ainda precisam de validação. O player permanece sem atualização.

## PWT Singles como módulo da Battle Frontier

O guia no lobby do Battle Dome leva a uma recepção própria do PWT. São oito
participantes, seis Pokémon por equipe, nível 50 e três rodadas. Há torneios
de Kanto, Hoenn e Misto, com 18 entradas de líderes/campeões. Vitória dá 3 BP;
derrota, cancelamento e desistência restauram a equipe sem avançar a história.
O Dome original continua disponível. Regras e reprodução em [PWT.md](PWT.md).

A candidata `4f1a70a006854cf304c32a5cdb80bd7009d779dddc5a6a43f573bbb7a6610b56`
passou nove vitórias nativas, derrota, forfeit, sete guardas de entrada, 18
equipes com golpes e acesso físico pela recepção/porta. Battle Bond, habilidade
Hidden, BP e equipe original foram conferidos com save/reload. As batalhas
usam atributos aumentados na fixture; falta conferir a dificuldade sem ela.
As outras instalações da Frontier e campanhas completas continuam pendentes.

## Revisão para seis Pokémon e viagens nativas à Frontier

O PWT foi ajustado para Singles **seis contra seis**, incluindo o quinto/sexto
slot do menu, ordem dos seis e adversários com suas seis espécies. A candidata
PWT `4f1a70a0` passou os três torneios, nove vitórias, derrota, forfeit,
cancelamentos e sete guardas adicionais dos slots finais, além das 18 equipes.
Os relatórios PWT foram reexecutados para esta candidata.

A camada seguinte `frontier-travel` corrige o embarque sem S.S. Ticket nos dois
portos de Hoenn, que podia deixar o jogador sem o bilhete exigido para voltar
da Frontier. Requer a Liga de Hoenn e o bilhete entregue pela família. Mantém
a primeira cena de Scott e o cruzeiro original. Houve testes físicos de oito
estados de embarque, cabine/cama/marinheiro e quatro trechos de ferry entre
Lilycove, Slateport e Frontier, com Continue e bilhete preservado.

Candidata mais recente: `92c95316b5019ac31cfde8e3cc4476895e61f33714b18ec27478b702cc54a335`.
Uma batalha adicional seis contra seis do PWT passou nessa ROM, incluindo
Battle Bond e restauração da equipe após desistência na rodada seguinte.
Os três torneios completos são da camada PWT anterior; os dois scripts de
porto constituem a diferença desta camada. As fixtures não validam dificuldade
ou campanhas completas. Reprodução e limites em [FRONTIER-TRAVEL.md](FRONTIER-TRAVEL.md).
Prioridades para continuar em [REMAINING-WORK.md](REMAINING-WORK.md).

## Progressão das histórias conectadas

A auditoria atual distingue a ligação obrigatória Silph–Giovanni–Archie dos
bancos regionais de insígnias, missões e Ligas. Passaram 28 vitórias nativas
nas incursões/base Rocket, avanço das seis missões, portas físicas e Continue.
Um teste adicional venceu Giovanni pelo evento da Silph após pegar o Card Key,
confirmou a recusa com cinco insígnias e a liberação do aliado em Hoenn com seis.
A candidata e as regras do jogo são as mesmas `92c95316`; esta revisão amplia
as evidências, sem alterar a ROM. Os atributos aumentados, viagens e estados
iniciais de fixture não validam balanceamento nem campanhas completas.
Sequência e reprodução em [INTEGRATED-STORY.md](INTEGRATED-STORY.md).

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
