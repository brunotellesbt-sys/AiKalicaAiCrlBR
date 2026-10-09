# Mundo conectado — candidata experimental, não é a versão final

Drowzee/Hypno fica reservado para Berry Forest, incluindo o Hypno de Lostelle;
Skorupi/Drapion passa para Mt. Pyre. Foram atualizados encontros, Pokédex e
documentos, com os 135 habitats conferidos no motor ARM. Candidata `0f1df908`;
[LOSTELLE-HABITATS.md](LOSTELLE-HABITATS.md).

O resgate de Lostelle passou pela apresentação de Bill/Celio, Meteorite,
quatro motoqueiros, Berry Forest, Hypno, escolta, entrega e Moon Stone:
15 mapas, oito batalhas e oito Continues. [LOSTELLE-STORY.md](LOSTELLE-STORY.md).

As sete cidades de Sevii e seus Centros Pokémon passaram por entrada desde o
mar, cura nativa, Continue e retorno: 34 mapas, 62 transições e 14 Continues.
[SEVII-TOWN-ACCESS.md](SEVII-TOWN-ACCESS.md).

A passagem da Rota 131 para Sevii permanece aberta também no layout alternativo
usado por Sky Pillar. Passou a viagem Vermilion–portos de Sevii 1–7–Pacifidlog–
Rota 127–Vermilion: 24 mapas, 42 bordas e oito Continues. Candidata `2f53d410`;
[EASTERN-OCEAN-JOURNEY.md](EASTERN-OCEAN-JOURNEY.md).

A viagem contínua pelo mar oeste até o lago da Rota 114, Rustboro e Dewford
e de volta a Cinnabar passou: 13 mapas, 24 bordas e seis Continues.
[OCEAN-JOURNEY.md](OCEAN-JOURNEY.md).

O jogo usa inglês, incluindo os diálogos novos de família, professores,
santuários e PWT. Foram corrigidos 97 textos e a Master Ball contra Ultra
Beasts. Três capturas e sete Continues passaram na candidata `15f9edd8`.
[ENGLISH-GAME.md](ENGLISH-GAME.md).

Os acessos locais e retornos dos 14 santuários passaram pelos controles,
incluindo as 105 interações bloqueadas com zero insígnias e 33 Continues.
A candidata permaneceu igual. [SANCTUARY-ROUTES.md](SANCTUARY-ROUTES.md).

Sky Pillar abre desde o início, mas Rayquaza só desperta após os requisitos
da aliança com Giovanni, Archie e o confronto em Sootopolis. O percurso
antecipado e o desfecho correto passaram. [SKY-PILLAR-ACCESS.md](SKY-PILLAR-ACCESS.md).

Altering Cave e Desert Underpass deixam de exigir vencer a Liga. Os dois
acessos e seus retornos passaram com zero insígnias, sem liberar capturas
especiais antecipadamente. [CAVE-ACCESS.md](CAVE-ACCESS.md).

Acesso e volta de Sootopolis pela Rota 126 passaram no motor com zero
insígnias, visitas às duas margens e seis Continues. Não houve alteração
na candidata. [SOOTOPOLIS-ACCESS.md](SOOTOPOLIS-ACCESS.md).

Continue submerso restaura Dive para os personagens de Kanto que compartilham
o sprite com Surf. Os quatro personagens e a volta da Seafloor Cavern foram
exercitados na nova candidata. [WATER-CONTINUE.md](WATER-CONTINUE.md).

O grunt da entrada da Seafloor Cavern foi deslocado para o lado. O caminho
até a sala final passou com Dive sem insígnias e sem golpes terrestres;
Archie conserva as exigências de história. [SEAFLOOR-ACCESS.md](SEAFLOOR-ACCESS.md).

O trecho Maxie–Stern–roubo do submarino–Matt foi exercitado com caminhada
nativa pelos três andares do esconderijo Aqua, incluindo batalhas duplas e
Continue. Evidências e limites em [SUBMARINE-STORY.md](SUBMARINE-STORY.md).

## Cidade inicial, família e viagem de mudança

A escolha acontece **antes da viagem**, na abertura de um save novo. São
**16 opções em Kanto/Sevii e 15 em Hoenn**, com uma casa fixa por cidade:
[birth-preparation.json](integration-validation/birth-preparation.json).
Só a residência escolhida recebe quarto e sala naquele save; as outras
mantêm seus eventos. Casas de Fuji, Warden, Lostelle, Lorelei, Copycat,
rival, Wally/Wanda, Cozmo e Steven ficam preservadas. Cinnabar, Indigo e
Ever Grande não têm residência elegível. Em Seven Island, apenas um
apartamento é convertido. Itens e serviços opcionais da residência
selecionada, como Coin Case, troca, tutor ou Move Relearner, cedem lugar à família.

Pallet, Viridian, Pewter, Cerulean, Vermilion, Lavender, Celadon, Fuchsia e
Saffron usam **caminhão**, assim como as cidades continentais de Hoenn com
espaço. **Todas as Sevii, Dewford, Mossdeep, Sootopolis e Pacifidlog usam
barco**. As Sevii aproveitam seus portos e barcos nativos. Nos outros
casos, o barco aparece numa costa conectada à casa; o desembarque ocorre
em terra caminhável. As passarelas de Pacifidlog permanecem intactas.
O interior da mudança reutiliza a sala de carga e as caixas da abertura
original; o trajeto marítimo usa sons de barco. Não há uma cabine nova
nem animação de navegação pelo mapa inteiro.

A mãe recebe você na chegada e leva ao quarto da casa. Fora de Pallet e
Littleroot, **Oak ou Birch espera na sala**, conforme a região, com maleta
ou bolsa e três iniciais regionais no **nível 5**, Pokédex e cinco Poké Balls.
É preciso conversar antes de sair; depois ele retorna ao laboratório.
Pallet conserva o inicial no laboratório. Littleroot conserva a chegada
original de caminhão, a mãe, o relógio e o resgate de Birch. Visitar outra
cidade posteriormente não muda a residência nem reabre a escolha inicial.

A família tem de uma a três pessoas, conforme os moradores humanos.
Uma pessoa é a mãe; os outros se tornam pai, irmão ou irmã. Com uma pessoa,
ela entrega **Surf, Dive e Waterfall**. Com duas, a mãe entrega Surf/Dive
e a outra Waterfall. Com três, entregam um HM cada. Isso vale nas duas
regiões, inclusive Pallet/Littleroot. A entrega registra cada item,
permite retomar com bolsa cheia e evita duplicações. A mãe mantém os
diálogos e a cura da mãe nativa de sua região. Whirlpool fica fora dos HMs.

Dewford, Mossdeep, Sootopolis e Pacifidlog têm um capitão adicional com
viagem gratuita a Slateport, para permitir sair mesmo sem um Pokémon
compatível com Surf. As Sevii já oferecem WORLD FERRY desde o início.
Esse transporte local não altera os barcos e eventos originais de Hoenn.

[Chegada de caminhão em Pallet](integration-validation/family-00-arrival.png),
[desembarque nas Sevii](integration-validation/family-09-arrival.png),
[chegada em Pacifidlog](integration-validation/family-30-arrival.png) e
[Birch na sala](integration-validation/family-30-oak-living-room.png).
O [teste no mGBA](integration-validation/family.json) percorre as 30 casas
fora da introdução de Littleroot em processos separados: escolha real,
chegada, escadas, presentes sem duplicação, porta bloqueada antes do
inicial, saída e entrada depois, iniciais, Pokédex, cura e save/reload.
Um controle separado verifica caminhão e presentes nativos de Littleroot,
e ausência de outra escolha ao visitar Pallet. Cerulean testa bolsa cheia
e entrega parcial. Warps encurtam deslocamentos dos testes; as campanhas
completas ainda não estão certificadas.

## Inicial da segunda região e bicicleta compartilhada

Começando em Hoenn, Oak oferece em Pallet um inicial de Kanto no nível 5,
sem substituir a equipe existente. Começando em Kanto, o resgate original
de Birch na Rota 101 oferece o inicial de Hoenn e inicia a batalha selvagem.
Cada região entrega uma vez. Equipe cheia impede o presente e permite
voltar depois; não apaga nem envia a equipe antiga ao PC.

**Só Mach Bike** é obtida nas duas regiões. Rydel e o vendedor de Cerulean
consultam o mesmo recibo salvo e a bicicleta na bolsa/PC. Após receber em
um lugar, o outro não entrega outra. A missão do voucher de Kanto continua;
bolsa cheia não consome o voucher nem marca a bicicleta como recebida.
Os Pokémon **não seguem mais o jogador**; acompanhantes humanos de eventos
permanecem disponíveis.

[birth-rules.json](integration-validation/birth-rules.json) exercita os dois
sentidos da entrega de bicicleta, bolsa cheia/repetição, bicicleta no PC,
recibo salvo, Oak com equipe cheia e preservação do Pokémon anterior,
resgate/batalha de Birch e saída de Pacifidlog sem Pokémon ou Surf. A
batalha de Birch foi iniciada e renderizada; sua vitória e os eventos
posteriores ainda não foram validados nesse teste.

## Rival de Kanto com a aparência do personagem do sexo oposto

O rival agora usa **Leaf para jogador masculino** e **Red para jogadora
feminina**, nos mapas e nos retratos de todas as suas 27 equipes, incluindo
campeão e revanche. A introdução do Oak usa a arte correspondente, e o
ícone na tela de nome também usa o personagem do sexo oposto. Oak diz
“grandchild” em vez de “grandson”. O nome escolhido pelo jogador continua.

Blue tem um ID gráfico próprio no ginásio de Viridian e preserva seu
retrato original de campeão. A mudança visual do rival não altera Blue,
Giovanni, Aqua/Magma ou o rival de Hoenn. As equipes e os scripts originais
do rival foram preservados por hash; esta camada não muda iniciais,
insígnias, níveis, missões ou condições de batalha.

Os testes usam processos independentes do mGBA para os dois gêneros:
comparam os 3.102 resultados de retrato (1.551 treinadores por gênero),
verificam os gráficos de mapa e seus IDs dinâmicos, conferem os pixels
descomprimidos e a paleta do retrato da introdução e iniciam a batalha
nativa do laboratório nos dois casos, sem simular vitória. O teste de
arte da introdução fornece recursos temporários ao carregador; não é um
teste completo da introdução e do fluxo interativo da tela de nome.

[Leaf como rival](integration-validation/opposite-rival-player-0-battle.png)
e [Red como rival](integration-validation/opposite-rival-player-1-battle.png).

Passaram **28 testes offline, 110 verificações nativas do mundo, 30 fluxos
de casa inicial, o controle de Littleroot e cinco cenários de viagem**,
incluindo as 96 travessias de Surf e as 840 equipes de ginásio. As 21 camadas
reproduzem 505 arquivos byte a byte,
com 117 conexões recíprocas. A candidata exige
save novo; as campanhas completas e outras migrações permanecem pendentes,
e a ROM publicada no player continua na versão anterior.

## Linha de barco entre Kanto, Hoenn e Sevii

Uma linha WORLD FERRY liga Vermilion, o interior do porto de Slateport e
os portos das sete ilhas Sevii. Fale com o novo marinheiro: ele entrega
gratuitamente o **World Ticket**, um item-chave próprio e reutilizável,
e abre o menu de destinos. Se a bolsa estiver cheia, libere um espaço e
fale novamente com ele. O bilhete não é consumido nas viagens.

No menu principal, escolha Vermilion, Slateport ou SEVII ISLANDS. A segunda
página lista as sete ilhas e BACK; B também volta. CANCEL/B no menu
principal encerra a conversa. Escolher o porto atual informa que você já
está ali. O serviço funciona desde o início, independentemente de insígnias,
Bill/Celio, passes antigos, League ou do progresso de Aqua/Magma/Rocket.

Os novos marinheiros ficam ao lado dos acessos existentes, com desembarque
em piso caminhável. O transporte usa diálogo de embarque e transição de
mapa; **ainda não há interior de barco nem animação de navegação própria**.
Não altera a viagem ou o ticket do S.S. Anne, os barcos originais, os eventos
do submarino de Stern, as batalhas ou os canais de Surf. Todos os scripts
originais dos nove portos foram preservados por hash.

O mGBA exercita as interações reais dos nove NPCs e os menus por botões:
16 viagens de ida/volta, troca dos formatos Emerald/FRLG, desembarque a pé,
bilhete sem duplicação, bolsa de itens-chave cheia, cancelamento, retorno
da segunda página e save/reload. As flags de insígnias e missões monitoradas
permanecem iguais. As capturas mostram o [menu principal](integration-validation/ferry-vermilion-destinations.png)
e o [menu das ilhas](integration-validation/ferry-seven-island-menu.png).

Na candidata atual passaram **25 testes offline e 109 verificações nativas**,
com as 96 travessias de Surf e as 840 equipes de ginásio. As 17 camadas
reproduzem 359 arquivos byte a byte e 117 conexões recíprocas. Continua
necessário iniciar um save novo; as campanhas completas ainda não foram
validadas e a ROM publicada no player permanece na versão anterior.

## Surf, Dive e Waterfall no início; antigos HMs terrestres como TMs

No início nativo de Hoenn, a mãe de Littleroot oferece **Surf, Dive e
Waterfall**, antes de qualquer insígnia. Ao escolher uma cidade de Kanto/Sevii,
a família escolhida divide esse pacote como descrito acima; as mães das
outras casas não antecipam os presentes dos familiares. Os diálogos e
os eventos seguintes das mães continuam.

Dive fica liberado desde o início, assim como Surf e Waterfall. Continua
necessário ensinar o golpe a um Pokémon compatível e encontrar o terreno
aquático apropriado. Whirlpool permanece como golpe de batalha, **não é HM**
e não foram adicionados redemoinhos aos mapas, conforme solicitado.

Os únicos HMs são HM01 Surf, HM02 Dive e HM03 Waterfall. Os antigos HMs
terrestres agora são máquinas normais:

| TM | Golpe | Tipo |
| --- | --- | --- |
| 51 | Cut | Grass |
| 52 | Fly | Flying |
| 53 | Strength | Rock |
| 54 | Flash | Normal |
| 55 | Rock Smash | Fighting |

Esses cinco golpes podem ser substituídos normalmente, sem a restrição de
esquecimento dos HMs. Sua distribuição original passa a entregar as TMs;
os textos de instrução foram atualizados. Potência, precisão e demais
efeitos de batalha continuam como na base. Os índices anteriores dos
50 TMs são preservados. O teste de bolsa da base usa os novos nomes dos
HMs em vez dos números antigos; a suíte completa de testes da base não
foi executada nesta etapa.

A entrega da família verifica cada item individualmente, permite retomar
uma entrega parcial e só marca o pacote como concluído depois dos três
HMs. Os professores originais de Surf/Waterfall e Steven verificam se o
item já está na bolsa antes de entregar outra cópia. Não há novas travas
terrestres nem alteração das missões obrigatórias. Giovanni permanece
obrigatório contra Archie, após a Silph Co. e seis insígnias de Kanto.

O emulador confere a tabela compilada de máquinas, os tipos de Cut/Strength,
a classificação de HM, a compatibilidade dos três HMs com Squirtle e as
duas mães. Exercita também mergulho e retorno à superfície sem insígnias,
entrega com bolsa cheia e parcial, troca de região e revisitas.
A nova numeração de HMs exige save novo. A ROM do
jogador web continua na versão publicada anterior.

## Vitória permanente no Centro Espacial

A flag original `FLAG_DEFEATED_MAGMA_SPACE_CENTER` é temporária: a chamada
do rival sobre Rayquaza a apaga depois de 250 passos. Usá-la nas travas de
ginásio e na autorização de Dive poderia revogar o progresso, especialmente
se Tate e Liza fossem o último ginásio da ordem livre.

Agora a integração consulta `VAR_MOSSDEEP_SPACE_CENTER_STATE == 3`, o estado
permanente que a cena original de vitória já grava. A chamada original
permanece intacta; o presente de Dive do Steven evita duplicar o item
recebido da família. A chamada acontece uma vez; sua flag
temporária pode ser apagada sem reabrir a missão Magma, fechar o último
ginásio, revogar Dive ou impedir a aliança contra Archie. Não há novos IDs
de flags nem mudanças no formato do save.

O emulador testa as 72 combinações de estados, flag temporária e quantidade
de insígnias, executa a chamada nativa e o presente do Steven, entra no
ginásio restante e salva/recarrega a flash. A vitória em batalha é simulada
para isolar esses eventos; o teste não valida toda a campanha.

Na candidata atual passaram **24 testes offline e 108 verificações nativas**,
incluindo 96 travessias de Surf e 840 equipes de ginásio. As 16 camadas
reproduzem 355 arquivos byte a byte e verificam 117 conexões recíprocas.
Esses resultados validam os cenários isolados descritos, não uma partida
completa das duas histórias.

A orientação do checkpoint do Monte Chimney agora também indica visitar
Meteor Falls pelas Rotas 114/115, onde ocorre o evento original do meteorito.

## Poké Flauta e orientação da missão Magma

A primeira insígnia da jornada, em qualquer um dos 16 ginásios de Kanto ou
Hoenn, entrega a Poké Flauta. A recompensa usa a flag original compartilhada
que os dois Snorlax consultam. As insígnias continuam separadas por região;
essa entrega não conclui missões, não remove os Snorlax e não altera os
níveis dos ginásios.

Com a bolsa cheia, a recompensa fica pendente. Falar novamente com um líder
permite recebê-la depois de liberar espaço. A flag só é marcada quando o
item foi recebido ou já está na bolsa; as revisitas não duplicam a Flauta.
O resgate do Sr. Fuji permanece, e ele reconhece a Flauta recebida em Hoenn.
Antes de qualquer insígnia, ele orienta vencer um ginásio primeiro.

O guia do checkpoint do esconderijo Magma agora explica também o pré-requisito
original: visitar os anciãos no Monte Pyre, pela Rota 122, e obter o Magma
Emblem para abrir a entrada em Jagged Pass. Essa missão não é concluída
automaticamente. A nova camada é reproduzível a partir das 13 anteriores.

Passaram 22 testes offline e 106 verificações nativas, incluindo a entrega
nos 16 ginásios, bolsa cheia, duplicatas, reconhecimento pelo Sr. Fuji e
ausência de recompensa antes da primeira insígnia. As 96 travessias Surf e
840 equipes de ginásio continuam passando. As 14 camadas reproduzem 336
arquivos e mantêm as 117 conexões recíprocas verificadas.

Os testes nativos desta etapa isolam os comandos de entrega da insígnia e
da recompensa; não representam vitórias reais em todas as batalhas nem uma
validação completa das duas campanhas. A candidata continua exigindo save
novo e não substitui a ROM publicada no jogador web.

## Escada amarela em todas as antigas passagens de salto

As **seis passagens de Acro Bike** agora usam o desenho da escada amarela:
cinco em Jagged Pass e uma na Safari Zone norte. Jagged Pass mantém seus
cinco patamares livres. Na Safari, os dois desníveis recebem degraus amarelos
e o quadrado intermediário volta a ser chão, preservando seu nível original.
São 11 tiles de degrau e seis tiles de patamar; todas as passagens são a pé.

A preparação importa os dois tiles de primeiro plano de Lavaridge e a sua
paleta para Lilycove, usada pela Safari. Os pixels e as cores originais do
degrau são idênticos. A paleta 12 estava livre e é carregada pelo motor; não
são usados os slots reservados além das 13 paletas de terreno. Os pixels
anteriores de Lilycove são preservados integralmente, sem substituir prédios,
NPCs, outros terrenos ou seus eventos. As pontes dos antigos trilhos e as
missões de bicicleta nas ciclovias continuam.

O emulador subiu e desceu nas seis passagens, totalizando 12 travessias sem
bicicleta. Conferiu também a paleta efetivamente carregada, os tiles e a
colisão. Encontros selvagens ficam desativados somente durante esse teste
isolado de geometria e são reativados depois; a ROM mantém seus encontros.
Na etapa das escadas, passaram 21 testes offline e 105 verificações nativas, incluindo as 96
travessias Surf e as 840 equipes de ginásio. As treze camadas reproduzem
323 arquivos, mantendo as 117 conexões recíprocas da rede preparada.

[Safari com escadas amarelas](integration-validation/stair-review/SafariZone-North.png),
[segunda passagem de Jagged Pass](integration-validation/stair-review/JaggedPass-2.png),
[terceira](integration-validation/stair-review/JaggedPass-3.png),
[quarta](integration-validation/stair-review/JaggedPass-4.png) e
[quinta](integration-validation/stair-review/JaggedPass-5.png).

Esta continua sendo uma candidata experimental: a ROM/player publicados
permanecem na versão anterior e a integração completa das histórias ainda
precisa das migrações e validações listadas abaixo.

## Bicicleta única e passagens — continuação

As ciclovias continuam exigindo a missão da bicicleta: receber a bicicleta de
Rydel em Mauville ou trocar o Bike Voucher em Cerulean. Ambos entregam **Mach
Bike**, que libera as quatro entradas das ciclovias nas duas regiões. Sem ela,
os guardas continuam impedindo a passagem; depois de recebê-la também é possível
passar a pé. Rydel não oferece troca por Acro Bike. A bicicleta registrada no
SELECT não é trocada por um item que o jogador não possui.

Foram inspecionados 452 layouts Emerald. Os **81 trechos transitáveis que
exigiam Acro Bike** viram pontes de madeira ou escadas: Rota 119, Safari Zone
norte/sul e Jagged Pass. Os desenhos usam metatiles nativos, com comportamento
normal de caminhada; as escadas conectam os níveis dos terrenos originais.
Em Jagged Pass, o degrau usa exatamente o tile amarelo da escada lateral
(Lavaridge `0x2AF`). Os cinco antigos enfeites de salto sobre o patamar viram
chão normal (`0x271`), deixando livre o quadrado acima da escada. Somente os
trechos da encosta recebem degraus. Essa passagem é a pé, sem exigir Mach Bike.
As escadas usam a camada coberta nativa, abaixo dos sprites.
Um vão de salto lateral na Rota 119 ganha um segmento de ponte. Quatro tiles
decorativos debaixo da ponte permanecem separados do caminho elevado.
Não foram removidas as ladeiras que usam a Mach Bike.

Sete objetos Aqua das rotas 110 e 119 foram deslocados para fora dos caminhos.
Seus IDs, scripts, diálogos e flags de visibilidade continuam; caminhar entre
eles não conclui a missão do museu ou do instituto meteorológico. Os Snorlax,
checkpoints regionais das equipes, exigências das Ligas e a escala dos líderes
e treinadores internos dos ginásios permanecem nesta etapa.

A validação verifica no motor os 81 tiles, atravessa cinco trechos a pé,
atravessa as duas passagens Aqua e testa oito situações das ciclovias: quatro
sem bicicleta e quatro com ela. Os dois scripts de recompensa entregam Mach
Bike e não entregam Acro Bike; esses testes começam nos ramos de recompensa,
portanto não certificam as duas missões completas desde o primeiro diálogo.
As doze camadas reproduzem **321 arquivos** byte a byte, mantendo as 117
conexões recíprocas da rede preparada.
Passaram 20 testes offline e 104 verificações no emulador na ROM recompilada,
incluindo as 840 equipes geradas dos ginásios e as 96 travessias de Surf.

[Ponte da Rota 119](integration-validation/Route119-walkable-Acro-replacement-10.png),
[escadas em Jagged Pass](integration-validation/JaggedPass-walkable-Acro-replacement-10.png),
[degrau amarelo e patamar livre](integration-validation/JaggedPass-yellow-stair-and-clear-landing.png),
[preparação da bicicleta](integration-validation/mach-bike-preparation.json) e
[deslocamentos Aqua](integration-validation/road-access-preparation.json).

Esta continua sendo uma candidata que exige save novo. A ROM publicada não
foi substituída; a validação completa das histórias e as migrações listadas
abaixo continuam pendentes.

## Acessos e Viridian — etapa anterior

Viridian agora tem **Blue como líder normal**, sem contar como enfrentamento
Rocket. Giovanni permanece no esconderijo, na Silph e na aliança contra Aqua.
O prêmio de Blue não oculta membros Rocket nem conclui essas missões. Blue
permanece no ginásio depois da vitória. Os nomes históricos de alguns flags
internos foram preservados para não renumerar eventos, mas não representam
uma nova vitória contra a Rocket.

Os níveis continuam pela ordem da jornada **na própria região**:

| Ginásio enfrentado | Nível do Pokémon mais forte do líder |
| --- | --- |
| 1º | 14 |
| 2º | 21 |
| 3º | 28 |
| 4º | 35 |
| 5º | 42 |
| 6º | 48 |
| 7º | 54 |
| 8º | 60 |

Os treinadores internos usam a mesma escala com dois níveis a menos; as
variações entre os Pokémon de cada equipe são preservadas, até seis níveis.
Blue entra nessa regra como os demais líderes. Suas equipes foram geradas
pelo motor real nas oito etapas, dentro das **840 equipes verificadas**.
O rival final de Route 22 é preparado somente com as oito insígnias de Kanto,
e uma cena já concluída não é reiniciada.

A preparação inspeciona os **939 mapas originais** e retira da renderização
e colisão **336 obstáculos de HMs terrestres em 77 mapas**: 82 árvores,
141 pedras de Rock Smash e 113 blocos de Strength. Os IDs e scripts dos objetos
continuam registrados; um flag reservado os mantém ausentes desde o novo jogo.
Os NPCs que entregam esses golpes continuam presentes. Nove mapas deixam de
exigir Flash. Os oito tiles das barreiras de Strength em Victory Road são
abertos explicitamente, e as correntes de Seafoam são interrompidas sem
exigir empurrar blocos.

Os guardas de Saffron diante do ginásio e da Silph, e os dois Magma junto ao
teleférico de Route 112, foram deslocados para espaços livres. Seus diálogos
e estados de missão continuam. Os portões de Saffron não exigem Tea; o velho
de Viridian fica fora do caminho; o deserto de Route 111 não exige Go-Goggles.
Lilycove não cria a parede de Wailmer que fechava a passagem marítima.
Nenhuma dessas mudanças concede vitória contra Aqua, Magma ou Rocket.

Norman mantém o tutorial de Wally, mas depois aceita o desafio sem quatro
insígnias. Fortree não exige Devon Scope para alcançar o ginásio; Cinnabar
não exige Secret Key; a porta de Viridian não exige seis insígnias específicas;
e a porta de Sootopolis não acrescenta a trava antiga de clima. **Os guias
das missões regionais continuam bloqueando o próximo ginásio quando há um
checkpoint pendente.** As duas Ligas continuam exigindo as oito insígnias da
própria região; a candidata não concede nenhuma insígnia para abrir acessos.

Surf e Waterfall passam a exigir o golpe no Pokémon, sem insígnias. O teste
ativou Surf pelo diálogo real do botão A com zero insígnias. Terrenos de água,
cachoeiras e áreas submersas permanecem. A camada atual também libera Dive
sem insígnias. Whirlpool permanece somente como golpe de batalha; sua
implementação como HM foi cancelada.

A compilação passou. O mGBA entrou fisicamente nos **16 ginásios** sem a
ordem antiga, verificou os quatro estados antigos de Norman, seis exemplos
de obstáculos entre os dois formatos e os oito tiles de barreiras abertos.
O prêmio de Blue foi executado com uma vitória simulada para conferir seus
flags; esse teste não equivale a vencer sua batalha completa. Permaneceram
aprovados os 16 guias/checkpoints, 96 travessias de Surf, bancos regionais/save,
missões e a tela da aliança com Giovanni. Passaram **18 testes offline**.
As dez camadas reproduzem **304 arquivos** byte a byte; 117 conexões da rede
preparada são recíprocas e não se sobrepõem. Mudanças de eventos são registradas
por campo, e a reprodução desfaz apenas essas alterações explícitas para
conferir os hashes das etapas anteriores.

[Surf sem insígnias](integration-validation/Surf-without-badges-active.png),
[entrada de Viridian](integration-validation/ViridianCity_Frlg-free-gym-entry.png),
[barreiras de Victory Road](integration-validation/VictoryRoad_2F_Frlg-open-boulder-barriers.png),
[preparação de acessos](integration-validation/free-access-preparation.json) e
[Blue](integration-validation/blue-gym-preparation.json).

**Ainda não é a versão final publicada.** A auditoria das demais restrições
de NPCs/eventos e as campanhas completas continuam pendentes. Também falta
migrar a jornada personalizada, o rival do sexo oposto, o catálogo anterior,
encontros adaptativos e viagens/tickets. A candidata continua exigindo save
novo; a ROM e o player publicados preservam a versão anterior.

## Histórias regionais conectadas e ordem livre

Cada região deve preservar sua própria campanha, próxima do jogo original.
Os oito ginásios de Kanto valem apenas para a Liga de Kanto; os oito de
Hoenn valem apenas para a Liga de Hoenn. Ordem livre significa que o jogador
escolhe a ordem, sem sorteio obrigatório. As insígnias e títulos de campeão
já têm bancos separados. Isso não significa que todos os acessos e eventos
das duas campanhas já estejam adaptados.

A auditoria de dependências registra os sete encontros originais com os
chefes, as condições dos 18 mapas/andares de ginásios e os oito requisitos
de cada Liga. A sequência habitual em LeafGreen é Giovanni no esconderijo
Rocket após Surge e normalmente antes de Erika; Giovanni na Silph Co. antes
de Sabrina, com a ordem de Koga variável; Giovanni como oitavo líder em
Viridian. Em Emerald, Maxie no Monte Chimney fica entre Wattson e Flannery;
no esconderijo Magma entre Winona e Tate & Liza; no Centro Espacial entre
Tate & Liza e Juan. Archie na Caverna Submarina também fica entre o sétimo
e o oitavo ginásio. Viridian foi substituída por Blue nesta etapa, preservando Giovanni nos
eventos Rocket e na aliança.

A candidata agora usa os seguintes checkpoints por quantidade de insígnias
**da própria região**, independentemente da identidade dos ginásios vencidos:

| Região | Próximo ginásio bloqueado | Evento exigido |
| --- | --- | --- |
| Kanto | 3º | Esconderijo Rocket de Celadon |
| Kanto | 5º e seguintes | Magma em Pewter e Rock Tunnel; Aqua em Vermilion e no corredor marítimo oeste; invasores nas rotas 3, 6, 8 e 15 |
| Kanto | 7º e 8º | Giovanni na Silph Co., após seis insígnias de Kanto |
| Hoenn | 3º | Maxie no Monte Chimney |
| Hoenn | 5º e seguintes | Base Rocket sob o cassino de Mauville |
| Hoenn | 6º e seguintes | Maxie no esconderijo Magma |
| Hoenn | 8º | Maxie/Tabitha no Centro Espacial; depois Archie/Shelly na Caverna Submarina |

As incursões de Kanto não são exigidas para o 5º ginásio de Hoenn, e a base
Rocket de Hoenn não é exigida para o 5º de Kanto. Cada adversário da missão
precisa ser derrotado: vencer apenas o administrador não libera o próximo
checkpoint. É possível enfrentar os invasores antes da quarta insígnia;
a obrigatoriedade começa depois dela. Ginásios já vencidos ficam disponíveis
para revisitas. O treinador na entrada informa equipe, rota e local; o motor
também verifica o warp da porta, que ocorre antes da colisão normal com NPCs.

### Incursões e cassino

Foram acrescentados 28 adversários obrigatórios: três Magma em Pewter,
três Aqua em Vermilion, quatro Magma nos dois andares do Rock Tunnel,
cinco Aqua no rio/costa entre Cinnabar, Rustboro e Dewford, quatro invasores
nas rotas de Kanto e nove Rocket na base de Hoenn. Vermilion menciona
Magma nas proximidades sem revelar sua localização no Rock Tunnel.

O cassino existente de **Mauville** ganha uma passagem ao fundo para dois
novos andares da base Rocket. São quatro grunts no B1F e quatro grunts mais
o administrador ATLAS no B2F. As escadas usam o comportamento de porta
sem animação nativo; entram pelo lado norte. A entrada, descida ao segundo
andar e ambas as saídas foram exercitadas por movimento real no emulador.

Os 27 setores marítimos ativos recebem ilhotas copiadas de terrenos costeiros
nativos e 42 nadadores comuns. As bordas dos mapas permanecem livres para
as travessias. Os novos grunts/administradores têm níveis fixos 32/36 e os
nadadores nível 28; a adaptação de níveis desta etapa continua restrita aos
ginásios. Os eventos originais mantêm seus IDs; os novos objetos são anexados.

### Aliança com Giovanni

O confronto final de Archie passa a ser uma batalha verdadeira **2 contra 2**:
jogador e Giovanni contra Archie e Shelly. Giovanni tem Nidoking, Nidoqueen
e Rhydon. O jogador usa os três primeiros Pokémon da equipe; o motor salva
e restaura a equipe original. Derrotas seguem para o desmaio, sem avançar Kyogre.
Como esta base não tem sprite traseiro de Giovanni, a apresentação usa seu
retrato frontal nativo espelhado, pelo mecanismo já usado no Battle Frontier.
Seu diálogo reconhece o dano causado pela Rocket, explica a
intenção inicial de defender Kanto e admite como poder e ganância a corromperam.
Após a luta, o roteiro original de Kyogre, Maxie e Sootopolis continua.

**Esta aliança exige vencer Giovanni na Silph Co. primeiro.** Portanto, o
último evento de Hoenn depende desse encontro de Kanto, embora as incursões
após a quarta insígnia sejam independentes. O guia informa esse requisito.
Silph rejeita o confronto prematuro, e Archie exige sete insígnias de Hoenn,
Centro Espacial concluído e a missão Rocket de Mauville concluída.

A invasão do Centro Espacial é iniciada após **sete** insígnias de Hoenn,
com o esconderijo Magma concluído, preservando cenas em andamento e concluídas.
Vencer Mossdeep posteriormente não reinicia o evento. A permissão de Dive
após o Centro Espacial permanece; ainda é necessário um Pokémon com o golpe.

### Validação e limites desta etapa

A compilação nativa passou. A reprodução das dez camadas compara 304 arquivos
byte a byte com a candidata; 117 conexões dos mapas oceânicos preparados são
recíprocas e não se sobrepõem. As verificações de preservação usam os prefixos
dos arrays de eventos, incluindo o warp adicional do cassino, preservando IDs.
Conexões nativas fora da rede preparada não são certificadas por esse relatório.

O mGBA verifica 180 combinações de insígnias/eventos, as 16 portas e diálogos
dos guias, cada um dos 28 adversários exigido isoladamente, quatro travessias
físicas nas escadas e a tela de combate real com os quatro participantes de Giovanni/Archie/Shelly.
Os testes configuram estados de missão diretamente na memória; **não simulam
uma campanha completa nem comprovam a vitória e o roteiro posterior à dupla**.

**A etapa de acessos descrita acima remove essas travas antigas de ginásio.**
A auditoria das demais restrições de NPCs/eventos e a jornada anterior ainda
precisam de adaptação e validação completa; esta candidata não é o jogo final.
Os diálogos novos seguem em inglês, como o restante desta base.

[Base Rocket: segundo andar](integration-validation/JourneyRocketBaseB2F-rocket-basement.png),
[aliança com Giovanni](integration-validation/Giovanni-Archie-Shelly-tag-battle.png) e
[preparação das missões](integration-validation/team-stories-preparation.json).

[Aviso de Kanto](integration-validation/PewterCity_Frlg-checkpoint-dialogue.png)
e [destino em Hoenn](integration-validation/RustboroCity-checkpoint-location.png).

Reproduzir a auditoria:

```sh
python tools/hoenn/audit_campaigns.py --source .local/hoenn-multiregion-src --output mods/hoenn/integration-validation/campaign-dependencies.json
```

[Dependências registradas](integration-validation/campaign-dependencies.json).

## Integração marítima atual

A rede agora tem saídas nas rotas **125, 127 e 129**, além da 131.
As rotas nativas 124–131 integram o mesmo componente marítimo de Sevii,
Vermilion e da **Rota 19, no mar ao sul de Fuchsia**, sem alterar a rota
terrestre 15 ou a entrada de Ever Grande. Quatro novos setores oceânicos
fazem essas ligações; as duas entradas oeste do setor de Vermilion usam
faixas separadas, sem sobreposição.

Na candidata atual passaram **96 transições Surf novas**, nos dois sentidos,
e **840 gerações de equipes reais dos ginásios**, abrangendo 105 treinadores
e as oito contagens de insígnias. Líderes usam níveis máximos 14, 21, 28, 35,
42, 48, 54 e 60; treinadores comuns ficam dois níveis abaixo, conservando
diferenças internas de até seis níveis. As insígnias da outra região não
alteram esses níveis. Batalhas fora dos ginásios mantêm os níveis originais.
Há cobertura de 18 mapas/andares para os 16 ginásios, inclusive subsolos.

**Escalar níveis não libera o acesso em ordem livre.** Portas, cenas de
Norman, Sootopolis e demais requisitos da história ainda precisam ser
adaptados e testados. Blue, rival e as demais regras da jornada anterior
continuam pendentes de migração. Não foram alterados os times, espécies,
golpes ou puzzles dos ginásios nesta etapa.

Os oito overlays atuais foram reproduzidos em **222 arquivos**. Foram verificadas
117 conexões dos mapas oceânicos preparados sem sobreposição e a conectividade de todo o mar
leste de Hoenn com a rede de Kanto/Sevii. Os números de etapas anteriores
abaixo são históricos. A ROM publicada continua separada.

[Veja a projeção quadrada](validation/connected-world.png), também disponível
em `web/world-layout.html`. Kanto fica ao norte, Hoenn ao sul e Sevii a leste:
ilhas 1–3 na primeira faixa, 4–5 na segunda e 6–7 na terceira. Birth Island
e Navel Rock permanecem ligadas ao setor leste. Não há teleporte nas novas
conexões oceânicas: o jogador atravessa as bordas dos mapas por Surf.

A ligação de Hoenn com Sevii usa a Rota 131, à direita de Pacifidlog.
As ligações nativas Rota 131–Pacifidlog–Rota 130 e Rota 128–Ever Grande
permanecem intactas. Uma malha de dez setores e seis corredores verticais
substitui, na candidata, a cadeia linear da versão publicada.

A travessia norte foi revisada conforme solicitado: agora sai **ao sul de
Cinnabar**, entra no lago da **Rota 114**, a oeste da região de Lavaridge,
e continua por uma costa nova até a Rota 115 (Rustboro) e Rota 105 (Dewford).
O canal remove os tiles bloqueadores apenas nas faixas registradas. Mantém
a base secreta em (11,27), o Revive escondido em (7,30), NPCs e warps.
A conexão terrestre original da Rota 114 com a Rota 115 também permanece.

**80 transições Surf novas passaram em mGBA**, nos dois sentidos. Isso não
equivale a validar caminhadas completas de todas as cidades até o mar,
as campanhas, entregas de HM ou todos os sistemas de Emerald.
[Teste atual](integration-validation/connected-world.json).

## Estados regionais

O upstream colocava 763 flags de eventos de FRLG em posições já usadas por
Hoenn, inclusive sua faixa de treinadores. A candidata realoca essas flags
para um banco persistente exclusivo e separa as oito insígnias e o estado
de campeão de Kanto. Dados globais, como equipe e Pokédex, permanecem comuns.
O guarda da Liga de Hoenn agora verifica as oito insígnias, não apenas Winona.

Passaram testes de concessão, consulta, limpeza e alternância das insígnias
em ambas as regiões, independência dos campeonatos, não alteração do flag
de treinador coincidente e salvamento/carregamento nativo da flash do
emulador. **Este motor exige um novo save.** Não há conversão de saves antigos.

Na etapa histórica de quatro overlays, 131 saídas foram reproduzidas em arquivos originais
do commit fixado. Foram verificadas 84 conexões recíprocas, sem sobreposição
de entradas, e a reaplicação da última camada é idempotente.
[Reprodução](integration-validation/world-reproduction.json).

## Histórico: primeira travessia, agora desconectada

A primeira passagem aprovada usava a borda leste da Rota 127, ao sul de Mossdeep,
e a borda oeste da Rota 21 Sul, ao norte de Cinnabar. Uma rota marítima
intermediária conecta os mapas fisicamente, sem teleportar o jogador.
A Rota 128 e a ligação com Ever Grande permanecem intactas. A camada oeste
desconecta esse protótipo e o substitui pela saída ao sul de Cinnabar.
Os relatórios antigos de quatro travessias são históricos, de outra ROM.

## Base experimental

O protótipo usa [`eonlynx/pokecrossroads`](https://github.com/eonlynx/pokecrossroads/tree/e05c82865d38a6638173fd30b2c830d1250aa50d),
commit `e05c82865d38a6638173fd30b2c830d1250aa50d`, com 518 mapas de
Emerald e 421 mapas de FRLG antes da nova passagem. Essa base já contém
os sistemas nativos de Emerald; a presença dos mapas não demonstra que
as duas campanhas completas funcionam juntas.

**A ROM publicada, o player e seus saves não foram substituídos.** As
modificações anteriores de LeafGreen ainda não foram migradas para esse
motor. Saves antigos não têm compatibilidade validada: a proposta é
preservar a versão atual separadamente e exigir um novo jogo na futura versão.

Os oito flags de insígnias eram compartilhados entre as regiões no upstream.
A separação implementada acima não conclui a migração: ainda é necessário
migrar a jornada personalizada, validar as campanhas e adaptar os ginásios
de Hoenn para ordem livre e níveis escaláveis, conforme solicitado.

## O que foi implementado e testado

- Canal marítimo sem interseção com eventos; NPCs, warps e triggers das
  duas rotas preservados por hash.
- Conexões de mapa nos dois sentidos, mantendo Surf durante a passagem.
- Conversão dos metatiles na prévia e no trecho de câmera salvo entre
  os formatos Emerald/FRLG; recarga de tilesets, paletas e animações.
- Redesenho da tela após a troca de formato, corrigindo as texturas
  incorretas na entrada de Kanto.
- Compilação nativa e quatro travessias físicas em mGBA aprovadas:
  Hoenn → passagem → Kanto → passagem → Hoenn.
- Preparação reproduzida em arquivos originais do commit fixado, com
  comparação byte a byte dos 14 arquivos resultantes e idempotência.

[Preparação](integration-validation/preparation.json),
[teste de travessia](integration-validation/crossing.json) e
[captura da chegada em Kanto](integration-validation/Route21_South_Frlg-arrival.png).

O teste injeta uma equipe e ativa Surf **somente na memória do emulador**
para isolar as conexões. Não comprova entrega dos HMs, dispensa de insígnias,
ferry/ticket, campanhas, pós-jogo, compatibilidade de saves ou as regras
personalizadas. Nenhuma dessas funcionalidades deve ser anunciada como pronta.

## Reproduzir

Reserve pelo menos 400 MB livres e use o toolchain ARM moderno preparado
no ambiente. A aquisição exige uma pasta nova; não sobrescreve um checkout.

```sh
python3 tools/hoenn/acquire_multiregion.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_crossing.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_worldsea.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_westsea.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_region_state.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_east_coast.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_gym_scaling.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_campaign_gates.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_team_stories.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_free_access.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_blue_gym.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_road_access.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_mach_bike.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_yellow_stairs.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_story_access.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_story_completion.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_water_hms.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_ferry.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_rival.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_family.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_travel_rules.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_birth.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_wild.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_habitats.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_sanctuaries.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_ecology.py --source .local/hoenn-multiregion-src
```

Na pasta de fonte, compile com os caminhos do compilador ARM, binutils,
libpng e pkg-config do ambiente. `make modern -j4` é o alvo validado.
Após editar mapas binários, force sua recompilação com `make modern -W data/maps.s -j4`.

```sh
python3 tools/hoenn/validate_crossing.py \
  --source .local/hoenn-multiregion-src --library .local/mgba-bridge.so \
  --worldsea --westsea --region-state --east-coast --gym-scaling --campaign-gates --free-access --road-access --team-stories --story-access --story-completion --water-hms --ferry --rival
python3 tools/hoenn/verify_worldsea.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/validate_family.py --source .local/hoenn-multiregion-src --library .local/mgba-bridge.so
python3 tools/hoenn/validate_birth_rules.py --source .local/hoenn-multiregion-src --library .local/mgba-bridge.so
python3 tools/hoenn/world_layout.py
node tools/hoenn/validate_world_layout.cjs
```

O validador depende do ELF correspondente à ROM, de `arm-none-eabi-nm`
em `.local/arm-binutils/usr/bin` e da ponte mGBA preparada pelos testes
anteriores. Ele é específico ao ABI desta base fixada.

## Trabalho obrigatório antes do lançamento

1. Preservar a versão anterior; a candidata exige um novo jogo, sem conversão.
2. Completar a auditoria de variáveis e todos os estados das histórias; validar
   ginásios livres, níveis adaptativos e bloqueio correto de cada Liga.
3. Migrar catálogo/sprites, Habilidades Ocultas/Battle Bond, Megas e
   encontros adaptativos.
4. Validar as conexões Sevii e o serviço de barco durante uma campanha
   completa e auditar os demais eventos de puzzles e das casas iniciais.
5. Validar Aqua/Magma, concursos, bases secretas, Frontier, viagens,
   salvamento e campanhas completas, antes de trocar a ROM no player.


## Encontros e santuários na candidata

As camadas `sanctuaries` e `ecology`, posteriores a `habitats`, corrigem a
classificação dos tipos nativos e distribuem 920 espécies comuns em 135
habitats, sem repetir famílias entre locais diferentes. São 444 famílias:
18 habitats terrestres com cinco, 79 com quatro e 38 exclusivamente marinhos
com uma família cada. Andares de cavernas e zonas de Safari contam como um
habitat. Vinte mapas com água secundária ficam sem encontros aquáticos para
preservar a exclusividade das 77 famílias aquáticas disponíveis; a passagem
continua livre. Ramos aquáticos, como Vaporeon, são filtrados na água.

Os níveis permanecem entre a média da equipe menos cinco e mais dois. A fase
evolutiva usa a média inteira das insígnias das duas regiões. Famílias raras
recebem menos slots e menor frequência de encontros aquáticos e de mordidas.
A Pokédex Nacional inicial consulta os locais de todos os estágios.

Os 105 lendários, míticos e Ultra Beasts têm altares em nove ilhas montanhosas
acessíveis por Surf e cinco cavernas acessíveis por Dive. Exigem oito insígnias
em cada região, sem exigir a Liga. Capturas antigas também respeitam essa
trava. Fugir ou derrotar permite tentar novamente; capturar desativa o altar.
Os locais e espécies estão em [POKEMON-LOCATIONS.md](POKEMON-LOCATIONS.md) e
[pokemon-locations.csv](pokemon-locations.csv). O índice separado de lendários,
míticos e Ultra Beasts está em [SPECIAL-LOCATIONS.md](SPECIAL-LOCATIONS.md),
com coordenadas externas e posição de cada altar.

Para regenerar os documentos e auditar os destinos na candidata posterior:

```sh
python3 tools/hoenn/document_habitats.py --source .local/hoenn-completion-final-src
python3 tools/hoenn/audit_map_destinations.py --source .local/hoenn-completion-final-src --output mods/hoenn/completion-validation/map-destinations.json
```

A auditoria verifica índices de destinos e conexões; mantém separadas as
entradas dinâmicas e origens fora dos limites para revisão no motor.

As regressões de casas, nascimento e mundo foram concluídas na mesma ROM
SHA-256 `9227bb707e24e0c86f92ba92e56c76ee3131d14f760740e22ffd9fb6cff0699a`,
incluindo 96 ligações físicas por Surf. Os testes offline exigem que os
relatórios de catálogo, encontros, casas, nascimento, mundo e santuários
correspondam à mesma candidata. Não substituem uma campanha jogada inteira.

A validação nativa confirmou as 14 travessias de ida e volta e uma captura real
de Pecharunt, incluindo fuga, nova tentativa e persistência da captura em save.
A auditoria do catálogo verifica referências e cabeçalhos; não comprova a
renderização de todos os sprites. Campanhas completas, Megas e Battle Bond
continuam exigindo validação. A ROM do player não foi publicada nesta etapa.

Depois das camadas anteriores, preparar e verificar:

```sh
python3 tools/hoenn/prepare_sanctuaries.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_ecology.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/document_habitats.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/validate_sanctuaries.py --source .local/hoenn-multiregion-src --library .local/mgba-bridge.so
python3 tools/hoenn/validate_sanctuary_capture.py --source .local/hoenn-multiregion-src --library .local/mgba-bridge.so
python3 tools/hoenn/validate_wild.py --source .local/hoenn-multiregion-src --library .local/mgba-bridge.so
python3 -m unittest discover -s tools/hoenn -p 'test_*.py'
```

## Habilidades Ocultas e Battle Bond na candidata de batalhas

A camada `abilities`, aplicada depois de `ecology`, migra a regra solicitada:
Froakie, Frogadier e Greninja usam Torrent no primeiro slot, Protean no segundo
e Battle Bond no slot oculto. Greninja transforma em Ash-Greninja ao nocautear
um adversário enquanto a batalha continua. Torrent e Protean não transformam;
as pré-evoluções também não. A espécie e o slot original retornam ao encerrar
a batalha. A forma separada de evento com Battle Bond é preservada.

Encontros criados por `CreateWildMon` têm 5% de chance de habilidade oculta
quando a espécie possui uma. A herança usa a implementação nativa da geração
6 ou posterior, com 60% para habilidade oculta. Não se aplica esse sorteio a
presentes ou equipes de treinadores. Nenhuma pedra ou novo recurso de batalha
é entregue por esta camada.

Os relatórios estão em `abilities-validation`. Essa candidata tem uma ROM
própria; `reproduction.json` registra também o hash da base de mapas utilizada.
A base em `integration-validation` continua identificada pelo hash anterior:
não se reetiquetam resultados antigos como testes da nova ROM. O replay
reproduz todos os arquivos alterados pela camada e verifica sua idempotência.
As campanhas completas ainda precisam ser jogadas na candidata final.

Preparação e validação, depois da compilação com o toolchain documentado:

```sh
python3 tools/hoenn/prepare_abilities.py --source .local/hoenn-battle-bond-src
python3 tools/hoenn/verify_abilities.py --source .local/hoenn-multiregion-src --candidate .local/hoenn-battle-bond-src --output mods/hoenn/abilities-validation
python3 tools/hoenn/validate_abilities.py --source .local/hoenn-battle-bond-src --library .local/mgba-bridge.so --output mods/hoenn/abilities-validation --ability-slot 2
python3 tools/hoenn/validate_abilities.py --source .local/hoenn-battle-bond-src --library .local/mgba-bridge.so --output mods/hoenn/abilities-validation --ability-slot 0
python3 tools/hoenn/validate_abilities.py --source .local/hoenn-battle-bond-src --library .local/mgba-bridge.so --output mods/hoenn/abilities-validation --ability-slot 1
python3 tools/hoenn/validate_abilities.py --source .local/hoenn-battle-bond-src --library .local/mgba-bridge.so --output mods/hoenn/abilities-validation --ability-slot 0 --event-form
python3 tools/hoenn/validate_abilities.py --source .local/hoenn-battle-bond-src --library .local/mgba-bridge.so --output mods/hoenn/abilities-validation --ability-slot 2 --pre-evolution
```

Veja [STATUS.md](STATUS.md) para as etapas restantes antes do lançamento.

## Arte de Megas e regressões na candidata de batalhas

A camada `mega-art`, depois de `abilities`, completa frente, costas e ambas
as paletas de Mega Garchomp Z. Os quatro arquivos vêm de uma revisão fixada,
com verificação de SHA-256 e Git blob; não altera atributos ou distribui pedras.
A auditoria compilada passa para as 97 formas Mega. O diagnóstico original
continua em `mega-validation/base-catalog.json`.

A nova candidata usa `.local/hoenn-mega-src`. Clone a árvore preparada de
habilidades, aplique a camada e compile usando o toolchain já documentado.
Os relatórios dessa ROM ficam em `mega-validation`; não substituem a
proveniência dos testes das duas bases anteriores.

```sh
python3 tools/hoenn/prepare_mega_art.py --source .local/hoenn-mega-src
# Compilar a nova árvore antes das validações nativas.
python3 tools/hoenn/verify_abilities.py --source .local/hoenn-battle-bond-src --candidate .local/hoenn-mega-src --layer mega-art --output mods/hoenn/mega-validation
python3 tools/hoenn/audit_megas.py --source .local/hoenn-mega-src --output mods/hoenn/mega-validation/catalog.json
python3 tools/hoenn/validate_sprite_codec.py --source .local/hoenn-mega-src --library .local/mgba-bridge.so --output mods/hoenn/mega-validation
python3 tools/hoenn/validate_palettes.py --source .local/hoenn-mega-src --library .local/mgba-bridge.so --output mods/hoenn/mega-validation
python3 tools/hoenn/validate_campaign_matrix.py --source .local/hoenn-mega-src --library .local/mgba-bridge.so --output mods/hoenn/mega-validation
```

Executar `validate_megas.py` com os mesmos parâmetros de árvore, biblioteca e
saída para cada `--case`: `charizard-x`, `charizard-y`, `rayquaza`, `greninja`,
`garchomp-z`, `no-ring` e `wrong-stone`. Executar
`validate_battle_transitions.py` para `mega-switch`, `mega-faint`, `ash-switch`
e `ash-faint`. Reexecutar os cinco casos de `validate_abilities.py` acima,
substituindo a árvore e saída por esta candidata.

Os testes usam Pokémon de nível 100 recebidos em nível 5, para respeitar a
regra nativa de obediência; fornecem os itens somente na memória da equipe de
teste. Transformações, nocautes e trocas acontecem pelo menu real. Não se
forçam resultados de batalha. A matriz de missões usa flags de estado inicial
para conferir decisões ARM, sem representar campanhas jogadas.

[Inventário, resultados e limites](MEGA-STATUS.md).

## Desfecho de Hoenn e batalhas duplas

A camada `story-aftermath`, depois de `mega-art`, mantém o último ginásio
livre de Hoenn fechado enquanto a crise climática original está ativa. Após
Archie, o guia aponta a Cave of Origin, Wallace e o Sky Pillar na Rota 131.
A cena original de Rayquaza em Sootopolis encerra a crise e libera qualquer
último ginásio escolhido. A missão não exige capturar Rayquaza nem vencer uma
Liga; as capturas especiais continuam exigindo as 16 insígnias.

As casas de Sootopolis permanecem abertas durante a crise, incluindo a casa
que pode ser escolhida como residência inicial. As cenas de Archie, Kyogre e
Rayquaza e a batalha com Steven mantêm seus scripts anteriores. Nenhuma nova
trava de rota, insígnia ou flag foi criada.

Essa candidata fica em `.local/hoenn-aftermath-src`, copiada da árvore preparada
de Megas. Seus relatórios ficam em `aftermath-validation`; os relatórios das
bases anteriores mantêm seus hashes próprios.

```sh
python3 tools/hoenn/prepare_story_aftermath.py --source .local/hoenn-aftermath-src
# Compilar antes de executar os validadores nativos.
python3 tools/hoenn/verify_abilities.py --source .local/hoenn-mega-src --candidate .local/hoenn-aftermath-src --layer story-aftermath --output mods/hoenn/aftermath-validation
python3 tools/hoenn/validate_campaign_matrix.py --source .local/hoenn-aftermath-src --library .local/mgba-bridge.so --output mods/hoenn/aftermath-validation
python3 tools/hoenn/validate_archie_aftermath.py --source .local/hoenn-aftermath-src --library .local/mgba-bridge.so --output mods/hoenn/aftermath-validation
```

Executar `validate_double_battles.py` com os mesmos parâmetros para cada
`--case`: `hidden`, `torrent`, `protean` e `event`. São batalhas reais contra
Tate e Liza com uma Mega ao lado de Greninja; os casos normais não transformam
em Ash-Greninja. A vitória concede uma insígnia real de Hoenn e passa pelo
save/load nativo. Os itens Mega são fornecidos somente às equipes de teste.

O teste de Archie inicia com seis insígnias de Kanto, sete de Hoenn e missões
anteriores concluídas como fixtures. Joga a batalha em parceria com Giovanni,
passa pelo despertar de Kyogre e saída para a Rota 128, executa o despertar e
retorno de Rayquaza e entra fisicamente em Rustboro como último ginásio. A
casa de Sootopolis é acessada fisicamente durante a crise; a equipe mantém
suas seis espécies, personalidades, IDs de treinador e slots de habilidades.
O save preserva o desfecho. Isso cobre esses trechos, sem representar as duas
campanhas completas ou o percurso inteiro dos puzzles.

O teste `validate_maxie_aftermath.py`, com os mesmos parâmetros de árvore,
biblioteca e saída, passa pelo convite de Steven, escolha real de três Pokémon,
vitória contra Maxie e Tabitha e pós-batalha. A chamada original do rival
consome a flag temporária sem apagar a conclusão permanente. A permissão para
Archie, as seis espécies/personalidades da equipe e o slot oculto sobrevivem à
restauração da equipe e ao save/load. As missões anteriores e insígnias também
são fixtures iniciais; essa validação não cobre todo o percurso do Centro Espacial.


## Entrada e estados independentes das Ligas

A camada `league-access`, posterior a `story-aftermath`, corrige dois problemas
reproduzidos na candidata anterior: a Pokédex Nacional inicial acionava o
bloqueio de Lorelei ausente em Indigo Plateau mesmo com oito insígnias; e
`FLAG_IS_CHAMPION`, usado para rematches, era compartilhado pelas duas regiões.

O guarda de Indigo agora verifica as oito insígnias de Kanto e ocupa a porta
somente quando falta alguma delas. A Pokédex e a vitória da outra região não
alteram essa decisão. A porta de Hoenn preserva seu script original de oito
insígnias. O marcador de campeão de Kanto usa `0x1AC2`, dentro do banco de flags
já reservado, e é gravado pela rotina de conclusão do Hall of Fame de Kanto.
O layout do save não mudou; a candidata continua exigindo um novo jogo.

Prepare em uma cópia da árvore anterior, preservando os artefatos e relatórios:

```sh
cp -a --reflink=auto .local/hoenn-aftermath-src .local/hoenn-league-src
python3 tools/hoenn/prepare_league_access.py --source .local/hoenn-league-src
# Compile com a mesma toolchain e variáveis locais das camadas anteriores.
python3 tools/hoenn/verify_abilities.py --source .local/hoenn-aftermath-src --candidate .local/hoenn-league-src --layer league-access --output mods/hoenn/league-validation
python3 tools/hoenn/validate_league_access.py --source .local/hoenn-aftermath-src --library .local/mgba-bridge.so --output mods/hoenn/league-validation --baseline
python3 tools/hoenn/validate_league_access.py --source .local/hoenn-league-src --library .local/mgba-bridge.so --output mods/hoenn/league-validation
python3 tools/hoenn/validate_league_battles.py --source .local/hoenn-league-src --library .local/mgba-bridge.so --output mods/hoenn/league-validation --region kanto
python3 tools/hoenn/validate_league_battles.py --source .local/hoenn-league-src --library .local/mgba-bridge.so --output mods/hoenn/league-validation --region hoenn
python3 tools/hoenn/validate_crossing.py --source .local/hoenn-league-src --library .local/mgba-bridge.so --westsea --ferry --output mods/hoenn/league-validation/travel
```

Os testes de portas cobrem 256 conjuntos de insígnias de Kanto e 20 entradas
físicas, incluindo cada insígnia faltante com a outra região completa. As rotinas
de conclusão dos dois Hall of Fame foram executadas para verificar flags e
save/reload; isso não representa derrotar todos os membros das Ligas.

As batalhas reais contra Lorelei e Sidney entram pelas portas, vencem o primeiro
membro, contornam o NPC pela lateral e atravessam a porta seguinte. A outra
região campeã é um estado de fixture; em Kanto a batalha continua sendo a primeira
Lorelei (trainer 1164), sem antecipar o rematch. Battle Bond transforma Greninja
após nocaute e reverte no final. Equipe e progresso da sala persistem no save.

A candidata `e2fb947f96eb0b31a6934441c2731500259a52a45e2bafe20a3a20fc6542ef93`
ainda não foi publicada no player. As demais batalhas de Elite Four, campeões,
créditos e retorno ao jogo precisam de verificação completa.


## Concluir uma Liga e continuar na residência escolhida

A camada `league-completion` segue `league-access`. Os dois finais originais
salvavam um destino fixo em Pallet/Littleroot; agora guardam o quarto da casa
escolhida antes da viagem inicial. O novo helper retorna FALSE quando não existe
uma escolha válida, preservando o fallback original. Não teleporta durante os
créditos: o destino é gravado antes do save do Hall of Fame e usado pelo Continue.
Littleroot usa a casa de May para o personagem feminino e a de Brendan para o
masculino. Nenhuma insígnia, missão ou flag de campeão é concedida pelo helper.

```sh
cp -a --reflink=auto .local/hoenn-league-src .local/hoenn-completion-final-src
python3 tools/hoenn/prepare_league_completion.py --source .local/hoenn-completion-final-src
# Compile modern com a mesma toolchain e as variáveis locais anteriores.
python3 tools/hoenn/verify_abilities.py --source .local/hoenn-league-src --candidate .local/hoenn-completion-final-src --layer league-completion --output mods/hoenn/completion-validation
python3 tools/hoenn/validate_home_resume.py --source .local/hoenn-completion-final-src --library .local/mgba-bridge.so --output mods/hoenn/completion-validation
python3 tools/hoenn/validate_league_completion.py --source .local/hoenn-completion-final-src --library .local/mgba-bridge.so --output mods/hoenn/completion-validation --region kanto
python3 tools/hoenn/validate_league_completion.py --source .local/hoenn-completion-final-src --library .local/mgba-bridge.so --output mods/hoenn/completion-validation --region hoenn
```

O teste de destinos salva e recarrega as 31 casas para cada gênero, incluindo
Littleroot, e verifica que as flags não mudaram. Não executa 62 sequências de
créditos. Os testes das Ligas passam pelas portas físicas de todas as salas,
vencem os cinco treinadores pelo menu normal, seguem os finais originais, deixam
os créditos terminarem e selecionam Continue no menu. O personagem reaparece
na casa de outra região; o progresso regional e a equipe são verificados após
o retorno e novo save/reload.

Os níveis, as insígnias e a escolha da residência são estados iniciais de fixture.
A cura entre as batalhas também é fixture; o teste não mede dificuldade, gestão
de itens ou o balanceamento das Ligas. As trocas obrigatórias percorrem o menu
normal e escolhem um membro vivo considerando a ordem exibida na batalha.

Relatórios finais identificam a ROM
`f7110f297426cfbeda762ab3874df5d7191240b1b453a88317dad8f6bceefcee`.
A subpasta `baseline` registra as sequências até o início dos créditos na base
anterior, sem o retorno à residência escolhido nesta camada. Artefatos de
exploração intermediários ficam ignorados em `.local`, fora desses relatórios.
Ainda é necessário validar as duas Ligas vencidas sequencialmente no mesmo save,
as revanches, o histórico do Hall of Fame e os eventos posteriores ao final.


## Histórico compartilhado após as duas Ligas

A camada `league-history` segue `league-completion`. Os dois Hall of Fame
escrevem nos mesmos setores de flash. A primeira conclusão de outra região
usava sua própria flag de jogo concluído e zerava esse arquivo. A decisão agora
usa `GAME_STAT_ENTERED_HOF`, incrementado pelo salvamento nativo do Hall of Fame;
a flag de conclusão continua sendo concedida somente à região atual. O loader
mantém seu fallback original para um arquivo inválido. Não há novos campos de save.

O limite de Hoenn era 30 e o de Kanto 50, apesar de compartilharem o arquivo.
As duas interfaces agora importam `HALL_OF_FAME_MAX_TEAMS` do mesmo header, com
50 equipes. Os dois asserts nativos de tamanho continuam verificando o espaço
nos setores existentes. Ao lotar, somente a equipe mais antiga é removida.

```sh
cp -a --reflink=auto .local/hoenn-completion-final-src .local/hoenn-history-src
python3 tools/hoenn/prepare_league_history.py --source .local/hoenn-history-src
# Compile modern com a toolchain e variáveis locais anteriores.
python3 tools/hoenn/verify_abilities.py --source .local/hoenn-completion-final-src --candidate .local/hoenn-history-src --layer league-history --output mods/hoenn/history-validation
python3 tools/hoenn/validate_league_history.py --source .local/hoenn-completion-final-src --library .local/mgba-bridge.so --output mods/hoenn/history-validation/baseline --first-region kanto --baseline
python3 tools/hoenn/validate_league_history.py --source .local/hoenn-history-src --library .local/mgba-bridge.so --output mods/hoenn/history-validation/kanto-first --first-region kanto
python3 tools/hoenn/validate_league_history.py --source .local/hoenn-history-src --library .local/mgba-bridge.so --output mods/hoenn/history-validation/hoenn-first --first-region hoenn
python3 tools/hoenn/validate_hall_capacity.py --source .local/hoenn-history-src --library .local/mgba-bridge.so --output mods/hoenn/history-validation/capacity
python3 tools/hoenn/validate_league_battles.py --source .local/hoenn-history-src --library .local/mgba-bridge.so --output mods/hoenn/history-validation/rematch --region kanto --rematch
```

As duas ordens percorrem dez batalhas reais no mesmo core e save, com créditos
e Continue entre as Ligas. A base reproduz um único registro após a segunda
vitória; a candidata conserva dois, com o primeiro intacto. Os badges, os níveis
e a cura entre batalhas são fixtures. O teste de capacidade prepara 50 equipes
no arquivo e executa os dois finais nativos, sem alegar mais duas vitórias.
A consulta do histórico pelo PC ainda não foi exercitada.

A auditoria de catálogo pode gerar um relatório compacto mantendo a hash das
linhas completas, além do índice de espécies canônicas e dos erros de assets:

```sh
python3 tools/hoenn/audit_native_catalog.py --source .local/hoenn-history-src --output mods/hoenn/history-validation/catalog.json --summary
python3 tools/hoenn/audit_megas.py --source .local/hoenn-history-src --output mods/hoenn/history-validation/megas.json
python3 tools/hoenn/audit_map_destinations.py --source .local/hoenn-history-src --output mods/hoenn/history-validation/map-destinations.json
python3 tools/hoenn/validate_campaign_matrix.py --source .local/hoenn-history-src --library .local/mgba-bridge.so --output mods/hoenn/history-validation
```

O teste de revanche prepara as flags de campeão e vence apenas Lorelei, usando
trainer 1470, com passagem para Bruno e save/reload. Não cobre uma revanche
completa. As sequências principais confirmam que vencer Hoenn primeiro não
antecipa a revanche de Kanto. Nenhuma ROM foi publicada no player.


## Consulta pelo PC e números de quatro dígitos

A camada `league-display` segue `league-history`. O formatador de Kanto dividia
o número por 100 e somava o resultado ao caractere zero. Acima de 999, o
primeiro caractere saía da faixa dos dígitos: Pecharunt aparecia como `!25`.
Agora a função nativa de conversão decimal usa quatro posições quando necessário,
preservando três posições para os números menores e `???` para espécies sem
número. O mesmo formatador atende às telas de registro e de consulta pelo PC.
Não altera as batalhas, os arquivos do Hall of Fame ou os mapas.

```sh
cp -a --reflink=auto .local/hoenn-history-src .local/hoenn-display-src
python3 tools/hoenn/prepare_league_display.py --source .local/hoenn-display-src
# Compile modern com a toolchain e as variáveis locais anteriores.
python3 tools/hoenn/verify_abilities.py --source .local/hoenn-history-src --candidate .local/hoenn-display-src --layer league-display --output mods/hoenn/postgame-validation
python3 tools/hoenn/validate_hall_pc.py --source .local/hoenn-history-src --library .local/mgba-bridge.so --output mods/hoenn/postgame-validation/baseline-pc
python3 tools/hoenn/validate_hall_pc.py --source .local/hoenn-display-src --library .local/mgba-bridge.so --output mods/hoenn/postgame-validation/pc
python3 tools/hoenn/validate_hall_capacity.py --source .local/hoenn-display-src --library .local/mgba-bridge.so --output mods/hoenn/postgame-validation/capacity
python3 tools/hoenn/validate_league_history.py --source .local/hoenn-display-src --library .local/mgba-bridge.so --output mods/hoenn/postgame-validation/kanto-first --first-region kanto --rematches
python3 tools/hoenn/validate_league_history.py --source .local/hoenn-display-src --library .local/mgba-bridge.so --output mods/hoenn/postgame-validation/hoenn-first --first-region hoenn --rematches
```

O teste de PC procura o tile pela rotina nativa de comportamento do mapa,
posiciona o personagem diante dele e interage com A. O arquivo e as flags de
campeão são fixtures; o menu, a seleção do Hall of Fame, os sprites, a navegação,
o retorno ao menu e o desligamento são nativos. A saída aguarda o fade do menu
antes de pressionar B. São visitados todos os registros de arquivos de uma e
50 equipes, e os seis membros podem ser selecionados sem ultrapassar os limites.
A Pokédex Nacional é habilitada, como ocorre na jornada ao receber a Pokédex.

As equipes de fixture incluem espécies de diferentes gerações e Pecharunt,
nº 1025. Capturas `dex-1025` mostram o erro na base e a correção na candidata.
Os testes comparam os pixels: apenas o retângulo do número muda em Kanto; as
capturas equivalentes de Hoenn e do número de Bulbasaur permanecem iguais.

O modo `--rematches` mantém o mesmo core e save por quatro conclusões de Liga.
Na revanche de Kanto, a equipe de teste recebe Surf e Aerial Ace além de
Dark Pulse e seleciona golpes pelo menu conforme o oponente. Isso evita que a
fixture use exclusivamente um golpe resistido por Heracross. O resultado nativo
da batalha deve ser vitória antes de registrar o percurso como aprovado.
As insígnias, os níveis e a cura continuam sendo fixtures de teste.


Passaram os dois percursos de quatro Ligas na candidata
`24858d6c4653152c4267fe4b3acbb8d4ac79a140640196d7d0cc7b0f5c922334`:
20 vitórias por ordem, quatro registros preservados, ambas as regiões campeãs,
quatro créditos/Continue e retorno à residência escolhida. Kanto usa o conjunto
de revanche 1470/1471/1472/1473/1476; Hoenn mantém o conjunto nativo de Emerald.
Os IDs e as conquistas aparecem separados nos quatro elementos de `sequences`.
As capturas por região mostram a última visita. Não são campanhas completas ou
testes de balanceamento, e os demais eventos do pós-jogo continuam em revisão.

## Recompensa da mãe após a Liga de Hoenn e lendários errantes

A camada `family-postgame` segue `league-display`. O evento original do S.S.
Ticket pressupunha a mãe, Norman e coordenadas fixas da casa em Littleroot.
As casas escolhidas em outras cidades não tinham esse evento. Agora falar
com a mãe da residência escolhida, após vencer a Liga de Hoenn, entrega o
S.S. Ticket enviado por Briney e apresenta a notícia original de Latias/Latios.
A escolha vermelho/azul continua gravada no save. O evento é um diálogo da
família, sem colocar Norman no papel do pai de todas as residências nem mover
NPCs pelas coordenadas da casa original. Depois dele, a mãe retorna aos seus
outros diálogos. A passagem antecipada das viagens entre regiões permanece
separada do S.S. Ticket de Emerald.

A consulta lê a conquista de Hoenn diretamente do seu banco de flags: vencer
apenas Kanto não entrega essa recompensa, mesmo morando em Kanto. Bolsa cheia
mantém a entrega pendente. Um S.S. Ticket já presente é reconhecido sem criar
outro, e a flag de recebimento só avança após a entrega bem-sucedida. A preparação
original do Hall of Fame permanece como alternativa para um save sem casa
selecionada; com casa selecionada, não inicia a coreografia de Norman.

Também foi corrigida uma alternativa que escapava à regra dos encontros:
o dispatcher nativo ainda permitia lendários errantes em rotas. Agora ele
não inicia esses encontros, antes ou depois das 16 insígnias e das Ligas.
Latias, Latios, Raikou, Entei e Suicune permanecem disponíveis nos altares
indicados em [SPECIAL-LOCATIONS.md](SPECIAL-LOCATIONS.md), com a exigência das
16 insígnias. A notícia da família não cria encontros errantes adicionais.

Reprodução e validação:

```sh
cp -a .local/hoenn-display-src .local/hoenn-family-postgame-src
python3 tools/hoenn/prepare_family_postgame.py --source .local/hoenn-family-postgame-src
# Compilar `modern` com a toolchain documentada acima antes dos testes nativos.
python3 tools/hoenn/verify_abilities.py --source .local/hoenn-display-src --candidate .local/hoenn-family-postgame-src --layer family-postgame --output mods/hoenn/family-postgame-validation
python3 tools/hoenn/validate_family_postgame.py --source .local/hoenn-display-src --library .local/mgba-bridge.so --output mods/hoenn/family-postgame-validation/baseline --baseline
python3 tools/hoenn/validate_family_postgame.py --source .local/hoenn-family-postgame-src --library .local/mgba-bridge.so --output mods/hoenn/family-postgame-validation/native
python3 tools/hoenn/validate_campaign_matrix.py --source .local/hoenn-family-postgame-src --library .local/mgba-bridge.so --output mods/hoenn/family-postgame-validation
python3 tools/hoenn/audit_native_catalog.py --source .local/hoenn-family-postgame-src --output mods/hoenn/family-postgame-validation/catalog.json --summary
python3 tools/hoenn/document_habitats.py --source .local/hoenn-family-postgame-src --output mods/hoenn
```

A candidata `4f3b1fc8412fdf783494b219b3366669dcbab22c2a3e1cfb0699ea7a0d3b87d8`
passou 248 estados de recompensa: 31 casas, dois mapas regionais e quatro
combinações de conquistas. Seis execuções dos scripts da mãe passaram até o
fim, incluindo as duas casas de Littleroot conforme o gênero, Pallet,
Viridian, Rustboro e Pacifidlog; a passagem, a notícia e sua escolha persistiram
após save/reload nativo. As capturas mostram o menu original vermelho/azul.
A bolsa cheia é uma fixture de slots ocupados por bicicletas repetidas, escritos
pela rotina nativa de criptografia; não representa itens obtidos na campanha.

Com Latias ativo e forçado à rota, a base gerou 30 encontros em 100 tentativas.
A candidata gerou zero antes das conquistas e zero nas 100 tentativas adicionais
com as 16 insígnias e ambos os campeonatos como fixtures. Passaram também as
4.096 decisões de missão, 36 permissões e a auditoria das 1.025 espécies-base.
Os diálogos usam warps e invocação do script com o contexto da sala/mãe; não
comprovam um percurso completo de campanha, embarque do S.S. Tidal, Battle
Frontier ou todos os eventos de pós-jogo. A ROM do player permanece anterior.

## Módulo PWT na Battle Frontier

A camada `pwt` segue `family-postgame` e acrescenta duas salas e um módulo C
próprio. O guia no lobby do Battle Dome leva à recepção do torneio; o Dome
continua com seus desafios originais. A pedido do usuário, há apenas Singles:
oito participantes, seis Pokémon por equipe, todos no nível 50, três rodadas
eliminatórias, bolsa bloqueada e restauração entre partidas.

Os conjuntos Kanto, Hoenn e Misto sorteiam sete adversários distintos de 18
entradas de líderes e campeões. O vencedor recebe 3 BP. As batalhas não concedem
insígnias, eventos de história, experiência ou dinheiro. Ao concluir, perder
ou desistir, a equipe completa volta exatamente ao estado da inscrição.
Formas da mesma espécie obedecem à cláusula pelo número Nacional. Um bit
próprio distingue as regras do PWT, mantendo os identificadores e retratos
nativos dos treinadores. O layout dos saves e o escalonamento dos ginásios
permanecem preservados.

Regras, participantes, reprodução, capturas e limites em [PWT.md](PWT.md).
Na candidata `4f1a70a006854cf304c32a5cdb80bd7009d779dddc5a6a43f573bbb7a6610b56`,
passaram três torneios completos (nove vitórias), derrota, forfeit, cancelamentos,
sete guardas de entrada, 18 equipes com golpes e acesso físico pela recepção
até a porta de retorno. BP, equipe, habilidade Hidden e flags de história foram
conferidos. Os atributos aumentados da fixture aceleram as batalhas, sem validar
balanceamento. O player continua com a ROM anterior.

## S.S. Tidal e retomada do embarque após Continue

A camada `frontier-travel` segue o PWT com seis Pokémon e confere a posse do
S.S. Ticket nas recepções de Slateport e Lilycove, mantendo a exigência de
campeão de Hoenn. A primeira cena de Scott, cabine/cama, saída pelo marinheiro
e menus nativos são preservados. A viagem e a volta da Frontier exigem o mesmo
bilhete, que não é consumido. O layout dos saves permanece igual.

Candidata `92c95316`, com replay de dois scripts, oito casos de embarque e
percurso físico pelo primeiro cruzeiro e quatro trechos da Frontier. O Continue
reconstrói os NPCs antes do reembarque. Há uma batalha PWT adicional nessa
candidata, com seis Pokémon e Battle Bond, sem alterar a distribuição por rota.
Detalhes em [FRONTIER-TRAVEL.md](FRONTIER-TRAVEL.md); trabalho restante em
[REMAINING-WORK.md](REMAINING-WORK.md). O player permanece sem atualização.

## Revisão da ligação entre histórias e progressão nativa

As campanhas compartilham a ligação obrigatória da Silph com Giovanni aliado
contra Archie/Shelly. A auditoria foi corrigida para registrar histórias
conectadas com insígnias, missões e Ligas separadas; a antiga classificação de
campanhas independentes era imprecisa. As regras e a candidata `92c95316`
permanecem iguais. Relatórios históricos conservam suas evidências originais.

Passaram 28 vitórias nativas nas seis missões adicionais, cinco verificações
de portas físicas, revisitas sem nova batalha e Continue entre missões. Outra
execução pegou o Card Key original, abriu a porta da Silph, recusou o confronto
com cinco insígnias e venceu Giovanni com seis, confirmando que a conclusão
libera sua participação em Hoenn e persiste após Continue. Insígnias iniciais,
episódios anteriores, viagens e atributos aumentados são fixtures; não houve
campanhas completas nem validação de dificuldade. Sequência, comandos e
relatórios em [INTEGRATED-STORY.md](INTEGRATED-STORY.md).

## Inscrições dos Regis e episódios nativos de Aqua

A camada `story-puzzles` abre três portas ao ler as inscrições: Desert Ruins,
Ancient Tomb e Sealed Chamber externa. Usa os metatiles e flags nativos, sem
Rock Smash, Flash ou Dig. Mantém Dive, a ordem Wailord/Relicanth na sala interna,
o puzzle de Regice e a trava de captura das 16 insígnias.

A camada `aqua-episodes` exige Shelly e a conclusão do Instituto Meteorológico
após quatro insígnias de Hoenn; Matt e a fuga do submarino após seis. Os guias
indicam Team Aqua, local e andar, fechando apenas ginásios ainda não vencidos.
O motor exige vitória e desfecho original; o início da invasão ao Centro
Espacial e a aliança de Giovanni contra Archie também verificam os episódios.
Os níveis dos ginásios, rotas, duas Ligas e banco de insígnias de Kanto são
preservados. A candidata final é `0e4626b0`.

Passaram travessias físicas e Continue das três portas nas duas candidatas,
as batalhas nativas de Shelly/Matt, Castform, fuga do submarino, portas de
ginásios e salvamento. A matriz passou 5.120 decisões e 44 permissões ARM.
Viagens, insígnias e estados anteriores/posteriores de fixture são explicitados;
não houve balanceamento ou campanhas completas. Detalhes e reprodução em
[PUZZLES-AND-AQUA.md](PUZZLES-AND-AQUA.md). O player continua sem atualização.
