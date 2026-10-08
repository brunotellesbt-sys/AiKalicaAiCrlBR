# Mundo conectado — candidata experimental, não é a versão final

## Surf, Dive e Waterfall no início; antigos HMs terrestres como TMs

A mãe de Pallet e a mãe da casa do jogador em Littleroot agora oferecem o
mesmo pacote de **Surf, Dive e Waterfall**, antes de qualquer insígnia. O
script compartilhado pode ser reutilizado nas futuras famílias das outras
cidades; a seleção de cidade/casa ainda precisa ser migrada para esta ROM
nativa. Os diálogos e os eventos seguintes das mães continuam.

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

## Histórias independentes e ordem livre

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
```

Na pasta de fonte, compile com os caminhos do compilador ARM, binutils,
libpng e pkg-config do ambiente. `make modern -j4` é o alvo validado.
Após editar mapas binários, force sua recompilação com `make modern -W data/maps.s -j4`.

```sh
python3 tools/hoenn/validate_crossing.py \
  --source .local/hoenn-multiregion-src --library .local/mgba-bridge.so \
  --worldsea --westsea --region-state --east-coast --gym-scaling --campaign-gates --free-access --road-access --team-stories --story-access --story-completion --water-hms
python3 tools/hoenn/verify_worldsea.py --source .local/hoenn-multiregion-src
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
3. Migrar cidades iniciais, famílias/Oak, rival do sexo oposto, catálogo/sprites,
   Habilidades Ocultas/Battle Bond, Megas e encontros adaptativos.
4. Validar as conexões Sevii durante uma campanha completa, implementar o
   ticket Vermilion–Slateport, ligar a entrega dos três HMs às futuras
   famílias das cidades iniciais e auditar os demais eventos de puzzles.
5. Validar Aqua/Magma, concursos, bases secretas, Frontier, viagens,
   salvamento e campanhas completas, antes de trocar a ROM no player.
