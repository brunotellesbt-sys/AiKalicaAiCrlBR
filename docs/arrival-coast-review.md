# Chegadas, florestas e costas — revisão 167

Esta revisão corrige os casos das cinco fotos e dos dois vídeos diferentes de
02/11. O arquivo `Screenrecorder-20261102-145837.mp4` foi enviado duas vezes;
as cópias têm o mesmo SHA-256. A revisão 166 continua preservada como histórico:
seus testes não cobriam todas essas situações e não certificavam o acabamento
de todo o mundo.

## Correções

| Local e reprodução | Causa e solução |
| --- | --- |
| One Island: retângulos no mar junto às rochas | Havia água animada também na camada superior, ainda com outra paleta. Foram corrigidas as 30 referências aquáticas superiores, preservando gráficos, animação e os pixels de areia/rocha. |
| One Island/Treasure Beach: fragmentos de rocha junto ao terminal | Três células eram partes de objetos cujo restante havia sido apagado pelo porto. Foram removidos os fragmentos completos; a rocha que realmente continua entre os dois mapas foi preservada inteira. |
| One Island: montanha cortada no acesso oeste de Surf | A conexão nova expôs a antiga borda interior da montanha. Foram fechadas 49 células com faces e cantos nativos. Uma rocha nativa inteira fecha a ponta norte do corredor, alinhada ao recife da rota vizinha, sem alterar o acesso oeste de ida e volta. |
| Chegada à cidade inicial: mãe/jogador no oceano | Dez pares de coordenadas continuavam apontando aos portos aposentados ou à água. Foram reposicionados nas sete Sevii, Dewford, Mossdeep e Pacifidlog. Os demais destinos e os eventos de viagem foram preservados. |
| Cinnabar: sair do terminal, ficar sob as tábuas e andar no mar | A porta de altura zero desembocava diretamente na ponte de nível múltiplo. A saída agora fornece a altura de terra. Saves antigos recebem recuperação restrita ao estado inválido; a passagem inferior de Surf continua funcionando. |
| Fuchsia e rotas 14/15: bases da floresta apagadas pela rota marítima | Foram concluídos os conjuntos de árvores e as margens em seis mapas, com 232 células alteradas. Os bancos carregados de ambos os lados das conexões usam as variantes marinhas corretas. As ruas, arbustos, cercas, ilhotas e portaria original foram preservados. |

O mapa-múndi, dimensões e conexões físicas não foram redesenhados. As tabelas
de encontros, história, ginásios e regras de batalha não mudam nesta camada.
O Chinchou do segundo vídeo, isoladamente, não identifica um defeito: encontros
continuam ativos nas edições normais. A TESTE continua sendo verificada
separadamente, sem encontros aleatórios nem abordagem automática de treinador.

## Evidências e limites

ROM base compilada: `9ade93b456c32bc41868642dabb287e0297cba8ebbeda97aa478bd6b11c678f5`.
ELF: `b441e07a811665f170114eba582e26165081a34d0077a7df6d2f1c46500c7b8e`.
Os cinco arquivos distribuídos possuem hashes próprios, pois os cabeçalhos e
regras de edição são diferentes; esses hashes ficam no manifesto final.

- A prova de fonte recompõe a camada sobre a versão 166, confere todos os
  arquivos herdados e vincula os blocos, a tabela de chegada e as rotinas
  corrigidas aos bytes compilados.
- A prova de chegada deve percorrer os 30 inícios personalizados desde o boot,
  seleção da cidade, viagem, fala da mãe e entrada no quarto, somente pelos
  controles. Littleroot usa a cena original e fica explicitamente limitada ao
  censo compilado dos 31 destinos nesta prova.
- A prova costeira reúne três percursos nativos independentes: One Island,
  floresta de Fuchsia/rotas 14–15 e terminal de Cinnabar. Compara também os
  pixels visíveis, bancos e fases de água realmente carregados.
- As cinco edições precisam de abertura real e teste das regras da TESTE.
  O save distribuído é o mesmo que precisa passar pelo Continue nativo.

As colocações iniciais, equipe e progresso dos testes de geometria são fixtures
de inspeção declaradas; depois da partida, o percurso usa os controles. As provas
de boot e chegada não escrevem callbacks, coordenadas ou memória do jogo.
Isto não representa uma campanha completa jogada nem uma nova certificação de
todos os mapas da camada 165.

Os relatórios atuais ficam em
[`mods/hoenn/arrival-coast-review-validation/`](../mods/hoenn/arrival-coast-review-validation/).
O manifesto distribuído exige as 13 provas atuais e mantém as provas anteriores
como históricas. As imagens de fonte de
[`design/arrival-coast-review/`](design/arrival-coast-review/) são identificadas
como renders, separadas das capturas nativas de emulador.

## Registros para os próximos ajustes

- [Fotos: causas, correções e prevenção em TXT](../errors/2026-11-02-fotos-chegada-e-costas.txt)
- [Vídeo de Cinnabar: porta, ponte e saves antigos](../errors/2026-11-02-video-cinnabar.txt)
- [Vídeo de Fuchsia: floresta, margem e bancos gráficos](../errors/2026-11-02-video-floresta-fuchsia.txt)
- [Guia prático](AJUSTES-GBA.txt) e [catálogo de tiles com banco/doador](../assets/tiles/README.md)
