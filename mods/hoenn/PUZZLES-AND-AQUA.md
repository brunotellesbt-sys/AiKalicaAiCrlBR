# Passagens terrestres e episódios obrigatórios de Aqua

Esta revisão avança a candidata nativa, sem atualizar a ROM do player.
As alterações seguem a regra de que apenas Surf, Dive e Waterfall continuam
como HMs e de que as missões fecham ginásios ainda não vencidos.

## Passagens dos Regis

| Local | Exigência anterior | Funcionamento atual |
|---|---|---|
| Desert Ruins | Rock Smash no ponto do puzzle | Ler a inscrição central ou lateral abre a passagem |
| Ancient Tomb | Flash no centro da sala | Ler a inscrição central ou lateral abre a passagem |
| Sealed Chamber, sala externa | Dig diante da inscrição | Ler a inscrição central ou lateral abre a sala interna |

A abertura usa os seis metatiles originais da porta e suas flags originais.
Não adiciona insígnias, itens ou flags de conclusão de equipes. É possível
atravessar sem Pokémon com esses golpes. Salvar e continuar conserva as portas
abertas, inclusive após sair e voltar à sala.

O acesso por Dive à Sealed Chamber, o enigma de Wailord primeiro e Relicanth
por último na sala interna e o percurso de Regice continuam preservados.
As capturas especiais continuam exigindo **oito insígnias de cada região**.
Abrir uma passagem não libera os lendários nem substitui o enigma que abre os
acessos externos dos Regis. Os santuários já existentes continuam como outros
locais de captura; suas posições não mudaram.

## Shelly e Matt obrigatórios

| Insígnias de Hoenn | Episódio pendente | Ginásios que esperam |
|---|---|---|
| 4 | Shelly no segundo andar do Instituto Meteorológico, Rota 119 | A partir do 5º |
| 6 | Matt no B2 do esconderijo Aqua em Lilycove | A partir do 7º |

As duas missões aceitam conclusão antecipada. O episódio Rocket de Mauville
continua na etapa de quatro insígnias: o guia aponta primeiro a base Rocket
se ela estiver pendente e depois o Instituto. Após cinco insígnias continua
a missão de Maxie no Magma Hideout. Nenhuma dessas missões conta insígnias de
Kanto nem altera a escala de níveis dos ginásios.

O NPC na porta informa que o líder está ajudando a combater **Team Aqua**,
indica a rota, o prédio e o andar. Para Matt, também orienta visitar Capitão
Stern no porto de Slateport se a entrada do esconderijo ainda estiver guardada.
Os guardas da missão original e a cena do roubo do submarino permanecem.
As rotas mantêm seus acessos, e ginásios já vencidos podem ser revisitados.

Para concluir cada episódio, o motor exige a vitória nativa e o desfecho da
cena: Shelly vencida com o Instituto salvo; Matt vencido com a fuga do submarino.
O início da invasão ao Centro Espacial e a permissão para a batalha com Archie
também exigem os dois episódios. A vitória no Centro Espacial e Giovanni na
Silph continuam necessários. Castform e o evento original do submarino foram
preservados.

## Candidatas e validação

- Base de embarque: `92c95316b5019ac31cfde8e3cc4476895e61f33714b18ec27478b702cc54a335`.
- Camada `story-puzzles`, quatro arquivos: `fbf2b61b6e1693ecff166f2a02c6a3c7006f6f710443fe71fd9c40c41aec07f0`.
- Camada `aqua-episodes`, dois arquivos: **`0e4626b06423c27889a08588fdfd2f9d294df20fdb4064273c75af1da8b7c285`**.

Os dois overlays verificam os hashes de entrada, podem ser reproduzidos a
partir da camada anterior e conferem seus arquivos ao serem executados novamente.
Os relatórios de `story-puzzles-validation` e `aqua-episodes-validation`
identificam cada ROM. Na base, as três portas não abriam ao ler e as duas missões
Aqua podiam ser puladas, inclusive para liberar Archie.

Nas candidatas, houve leitura e travessia física das três portas, salvamento,
Continue e nova travessia. Esse teste passou também na ROM final e confirmou
que oito insígnias de apenas uma região não liberam capturas. Regirock e
Registeel recusaram os confrontos antes das 16 insígnias.

Shelly e Matt foram abordados pelo botão A e vencidos em batalhas nativas.
Castform foi entregue, o submarino partiu e os ginásios fecharam/abriram conforme
as missões. Houve Continue após as etapas, conservação das insígnias e da
pendência de Kanto. A matriz ARM passou **5.120 decisões** de missões com todos
os 256 conjuntos de insígnias por cenário e **44 permissões** de história,
incluindo recusas de Archie e da invasão ao Centro Espacial sem os episódios.

As viagens, insígnias iniciais e missões anteriores são fixtures. O teste de
batalhas aumenta atributos em RAM; as conclusões posteriores da Silph e do
Centro Espacial também são fixtures para conferir a ligação. Isso não comprova
balanceamento, o percurso integral do roubo em Slateport nem duas campanhas
completas. O layout dos saves não mudou; a candidata continua exigindo novo jogo.

## Reprodução

As árvores abaixo devem ser cópias da candidata anterior já compilada, com a
fonte fixada em `e05c82865d38a6638173fd30b2c830d1250aa50d`. O ambiente usa GCC ARM,
Binutils ARM e a ponte mGBA existentes em `.local`.

```sh
python3 tools/hoenn/prepare_story_puzzles.py --source .local/hoenn-puzzles-src
PATH="$PWD/.local/arm-gcc/usr/bin:$PWD/.local/arm-binutils/usr/bin:$PATH" make -C .local/hoenn-puzzles-src -j4
python3 tools/hoenn/verify_abilities.py --layer story-puzzles --source .local/hoenn-frontier-travel-src --candidate .local/hoenn-puzzles-src --output mods/hoenn/story-puzzles-validation
python3 tools/hoenn/validate_story_puzzles.py --source .local/hoenn-frontier-travel-src --library .local/mgba-bridge.so --output mods/hoenn/story-puzzles-validation/baseline
python3 tools/hoenn/validate_story_puzzles.py --source .local/hoenn-puzzles-src --library .local/mgba-bridge.so --output mods/hoenn/story-puzzles-validation/native
python3 tools/hoenn/prepare_aqua_episodes.py --source .local/hoenn-aqua-episodes-src
PATH="$PWD/.local/arm-gcc/usr/bin:$PWD/.local/arm-binutils/usr/bin:$PATH" make -C .local/hoenn-aqua-episodes-src -j4
python3 tools/hoenn/verify_abilities.py --layer aqua-episodes --source .local/hoenn-puzzles-src --candidate .local/hoenn-aqua-episodes-src --output mods/hoenn/aqua-episodes-validation
python3 tools/hoenn/validate_aqua_episodes.py --source .local/hoenn-puzzles-src --library .local/mgba-bridge.so --output mods/hoenn/aqua-episodes-validation/baseline
python3 tools/hoenn/validate_aqua_episodes.py --source .local/hoenn-aqua-episodes-src --library .local/mgba-bridge.so --output mods/hoenn/aqua-episodes-validation/native
python3 tools/hoenn/validate_campaign_matrix.py --source .local/hoenn-aqua-episodes-src --library .local/mgba-bridge.so --output mods/hoenn/aqua-episodes-validation/matrix
python3 tools/hoenn/validate_story_puzzles.py --source .local/hoenn-aqua-episodes-src --library .local/mgba-bridge.so --output mods/hoenn/aqua-episodes-validation/puzzles
```

Sequência completa das histórias em [INTEGRATED-STORY.md](INTEGRATED-STORY.md);
prioridades restantes em [REMAINING-WORK.md](REMAINING-WORK.md).
