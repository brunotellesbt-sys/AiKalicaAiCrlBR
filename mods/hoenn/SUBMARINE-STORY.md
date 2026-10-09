# Maxie, Stern e o esconderijo Aqua

A candidata `0e4626b06423c27889a08588fdfd2f9d294df20fdb4064273c75af1da8b7c285`
passou pela sequência local de eventos que liga Maxie a Matt. Esta revisão
melhora a validação; não modifica a ROM nem atualiza o player.

## Percurso exercitado

1. Conversar com Maxie no Magma Hideout e vencê-lo ativa a cena de Groudon e
   prepara a entrevista de Stern em Slateport.
2. Conversar com Stern inicia sua entrevista, conduz o personagem ao porto e
   entra no prédio pela passagem original.
3. Caminhar até o gatilho do porto executa o roubo do submarino por Archie.
   A conclusão esconde os dois guardas da entrada do esconderijo Aqua.
4. Entrar pela costa de Lilycove com Surf e percorrer os três andares do
   esconderijo usando suas escadas e teletransportes originais.
5. Conversar com Matt, vencê-lo e concluir a partida do submarino libera a
   pendência de Hoenn. A pendência de Kanto e as insígnias ficam preservadas.
6. Voltar pelo teletransporte de saída e pela escada ao primeiro andar,
   conversar com a água para ativar Surf e sair pela entrada de Lilycove.
   Salvar e continuar já no mar conserva Surf e a conclusão da missão.

No esconderijo foram registrados **138 passos e oito transições**. O percurso
até Matt usou somente comandos direcionais, sem escrever a posição do
personagem, trocar de mapa artificialmente ou iniciar scripts de NPCs.
Na volta foram registrados **49 passos e duas transições**, pelo teletransporte
do B2 e pela escada ao primeiro andar. Surf foi ativado com A e confirmação
normal na margem `(13, 12)`, sem forçar o estado do personagem. O gatilho da
entrada levou o jogador de volta à costa de Lilycove.

Houve **seis batalhas e oito treinadores vencidos**, contando Maxie, Matt,
duas batalhas duplas entre grunts e o grunt encontrado na saída. Os marcadores
nativos dos dois oponentes de cada batalha dupla foram conferidos.

O auxiliar de batalhas agora reconhece o menu de seleção de alvo das batalhas
duplas. Antes, ele cancelava esse menu e impedia o teste de prosseguir. O teste
isolado anterior de Matt também foi corrigido: o personagem agora interage
de uma posição caminhável à direita dele, em vez de ser colocado sobre uma
parede. Shelly e Matt passaram novamente nessa validação corrigida.

O salvamento e o Continue nativos passaram após Maxie, após o roubo e após
Matt e após voltar ao mar de Lilycove. As etapas seguintes conservaram os
estados da entrevista, roubo, derrota de Maxie/Matt e fuga do submarino.
No último Continue, o personagem permaneceu no mesmo mapa em Surf, com as
insígnias originais, Hoenn sem missão pendente nessa etapa e Kanto ainda
aguardando suas incursões.

## Evidências e limites

- [Relatório do percurso](submarine-story-validation/submarine-story.json).
- [Entrevista entrando no porto](submarine-story-validation/stern-interview-enters-harbor.png).
- [Entrada por Surf](submarine-story-validation/surf-enters-aqua-hideout.png).
- [Chegada a Matt](submarine-story-validation/native-hideout-path-reaches-matt.png).
- [Conclusão após a batalha](submarine-story-validation/matt-defeated-after-full-native-route.png).
- [Surf ativado na margem de saída](submarine-story-validation/native-surf-prompt-return.png).
- [Retorno a Lilycove](submarine-story-validation/native-return-to-lilycove-after-matt.png).
- [Continue no mar após retornar](submarine-story-validation/native-lilycove-return-after-continue.png).
- [Shelly/Matt com posições caminháveis](aqua-episodes-validation/native/aqua-episodes.json).

Insígnias iniciais, missões anteriores, deslocamentos entre cidades e a posição
inicial em Surf são fixtures. A equipe usa nível 100 e atributos aumentados em
RAM para acelerar as batalhas, com cura entre os confrontos para restaurar PP.
As vitórias e os eventos descritos acima são
nativos; não foram simulados por marcadores de conclusão. Esse teste não cobre
a viagem inteira entre cidades, todos os grunts,
o balanceamento ou duas campanhas completas.

## Reprodução

Usar a árvore compilada da candidata `aqua-episodes`, com fonte fixada em
`e05c82865d38a6638173fd30b2c830d1250aa50d`, e a ponte mGBA do ambiente:

```sh
python3 tools/hoenn/validate_submarine_story.py --source .local/hoenn-aqua-episodes-src --library .local/mgba-bridge.so --output mods/hoenn/submarine-story-validation
python3 tools/hoenn/validate_aqua_episodes.py --source .local/hoenn-aqua-episodes-src --library .local/mgba-bridge.so --output mods/hoenn/aqua-episodes-validation/native
python3 -m unittest discover -s tools/hoenn -v
```

A preparação dessa árvore está em [PUZZLES-AND-AQUA.md](PUZZLES-AND-AQUA.md).
As prioridades restantes estão em [REMAINING-WORK.md](REMAINING-WORK.md).
