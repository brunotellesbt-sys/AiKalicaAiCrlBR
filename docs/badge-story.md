# Competição da 18ª insígnia, rivais e capítulo Galactic da 22ª

As duas Ligas reconhecem **18 insígnias e a vitória na competição da Battle
Frontier**. O circuito continua com seus 24 ginásios; vencer a competição
permite desafiar tanto Kanto quanto Hoenn sem esperar as 24 insígnias ou o
desfecho Galactic. Os guardas da Rota 23 e as duas entradas das Ligas usam a
mesma permissão.

Os sprites de caminhada de Eren e Luffy passam à escala dos outros rivais.
O ajuste inclui as versões da campanha e do estádio, com os nove quadros
direcionais completos, sem alterar seus retratos de batalha.

## A competição

O encontro dos seis participantes acontece na praça externa junto à recepção
da Battle Frontier. O grupo reúne o jogador, o rival do sexo oposto de sua
região inicial, os outros dois protagonistas da outra região, Luffy e Eren.
Os participantes entram no estádio já existente para disputar uma competição
própria da campanha. Somente o espaço do estádio é compartilhado com o PWT.

São dois grupos de três, com um confronto entre cada par. Cada participante
disputa duas partidas; o primeiro de cada grupo chega à final. Vitórias são o
primeiro critério. Os desempates consideram o saldo de Pokémon restantes,
depois o total de sobreviventes e, persistindo a igualdade, a ordem sorteada
na inscrição. Os resultados das partidas entre NPCs são simulados e entram
na classificação; as partidas do jogador usam batalhas reais.

Uma derrota isolada na fase de grupos ainda permite disputar a classificação.
Quem não vencer seu grupo, desistir ou perder a final volta ao Centro Pokémon
da Frontier e precisa iniciar outra tentativa. Entre as partidas, HP, PP e
status são curados e os itens equipados são repostos. A equipe mantém sua
experiência e os itens usados da Bag seguem o consumo normal. Não há redução
para o nível 50, prêmio em BP, registro de PWT nem restauração integral de uma
cópia antiga da equipe.

Após vencer, os cinco adversários parabenizam o jogador com falas próprias
na praça externa, fora do prédio. A vitória fica registrada no save. Uma
tentativa interrompida na arena tem recuperação própria e não pode entrar
acidentalmente no fluxo do PWT.

## Rivais de acordo com o personagem e o início

O seletor dos encontros existentes considera o personagem escolhido e a
região inicial, mantendo os quatro protagonistas distintos. Na região onde
começou, o rival local é do sexo oposto. Na outra região, os outros dois
personagens alternam entre os encontros já existentes.

| Início | Jogador | Rival local | Outro rival, mesmo sexo | Outro rival, sexo oposto |
|---|---|---|---|---|
| Hoenn | Red | May | Brendan | Leaf |
| Hoenn | Leaf | Brendan | May | Red |
| Hoenn | Brendan | May | Red | Leaf |
| Hoenn | May | Brendan | Leaf | Red |
| Kanto | Red | Leaf | Brendan | May |
| Kanto | Leaf | Red | May | Brendan |
| Kanto | Brendan | Leaf | Red | May |
| Kanto | May | Red | Leaf | Brendan |

Um início nas Sevii mantém a afinidade com Kanto já usada pela campanha.
Nome, sprite, retrato e fala usam a mesma identidade. Os times, os gatilhos e
as flags dos encontros nativos são preservados. Wally, Blue como líder de
Viridian e os personagens próprios do PWT não entram nessa substituição.

## Galactic na 22ª insígnia

O compartimento do navio abandonado da Rota 108 passa a exigir **22 insígnias
no total**, incluindo as dos ginásios extras. A visibilidade dos grunts segue
a mesma regra. O aviso da 22ª orienta a investigação da Room 6; os encontros
anteriores de Luffy e Eren continuam sendo pré-requisitos narrativos desse
capítulo. Eles já não são uma barreira para as Ligas depois da competição.

## Validação e downloads

A camada 164, `badge-story`, tem um contrato de publicação separado:
[cobertura e limites](design/badge-story/VALIDATION.md). A publicação exige
26 provas atuais ligadas aos hashes das cinco ROMs: auditoria de source e,
por edição, competição, identidade dos rivais, permissões da campanha,
comportamento normal/TESTE e abertura do jogo.

A [revisão das cenas inteiras](design/badge-story/source-scene-review.md)
mostra os dois mapas com os tiles nativos e distingue esses renders das
observações no emulador.

As quatro [edições normais](../roms/README.md) e a
[TESTE separada](../roms/rom-de-teste/LEIA-ME.md) recebem a mesma campanha.
A TESTE mantém encontros aleatórios e abordagens automáticas desativados;
os eventos obrigatórios da campanha e os desafios por conversa permanecem.
O player do Pages recebe a entrega pelo fluxo normal após o merge.

As provas anteriores mantêm os hashes das ROMs em que foram executadas. O ZIP
contém as quatro ROMs normais, as provas atuais, os relatórios históricos e o
catálogo de tiles. As capturas históricas continuam no repositório; dentro do
ZIP, `HISTORICAL-MEDIA.json` registra seus hashes e links para o commit
imutável anterior. O pacote não afirma reproduzir todo o histórico offline,
nem representa uma nova campanha completa jogada.
