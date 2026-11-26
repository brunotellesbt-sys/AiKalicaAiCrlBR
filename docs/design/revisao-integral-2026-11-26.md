# Revisão de Pokémon Journey

## Oito batalhas antes do navio

O autor definiu quatro batalhas de estrada para Eren e quatro para Luffy. O total usa as insígnias obtidas nos três circuitos, independentemente da cidade de nascimento. A competição da Frontier e as batalhas do navio têm seus próprios requisitos. [Locais e marcos](../historia-e-missoes.md#eren-e-luffy)

| Personagem | Insígnias | Evolução das equipes e da história |
| --- | --- | --- |
| Eren | 1, 5, 13, 20 | Larvitar e Gible acompanham a busca por Mikasa e Armin. Na Rota 112 ele decide esperar o parceiro que ficou para trás. A vista do mar na Rota 17 o faz lembrar de Armin. No oeste da Rota 123, Steelix dá peso à pergunta sobre quem vive do outro lado de uma muralha. As equipes têm 2, 3, 5 e 6 membros. |
| Luffy | 2, 7, 11, 15 | Na Rota 106 ele procura o bando pela praia com Solrock e Lotad. Na Rota 13, Lombre o ajuda a achar água. A cozinha vazia do navio da Rota 108 o faz sentir falta do bando. No Caminho Aquático da Ilha 6, Poliwrath mostra como socorrer alguém na correnteza. As equipes têm 2, 3, 5 e 6 membros. |

A Rota 123 tem duas aproximações distintas. O encontro fica no lado oeste acessível pela Rota 118. Pela Rota 108 o jogador sobe ao convés usando a escada existente. Esses locais usam os mapas e os treinadores nativos. Os dois personagens têm sequências independentes. Uma viagem tardia pode concentrar encontros já liberados.

O jogo preserva os bits das vitórias antigas, inclusive as das rotas aposentadas. Ao contar três vitórias do mesmo personagem, indica sua quarta batalha. Ao contar quatro, aceita a etapa para o navio. O teste em C percorre 16.384 máscaras e os totais de zero a 24 insígnias. A matriz de emulação usa batalhas reais com equipe do jogador reforçada e deslocamento inicial preparado. Ela mede progressão e níveis. O balanceamento com equipes de campanha exige partidas independentes.

## Dependências da campanha

| Etapa | Condição e consequência | Verificação aplicável |
| --- | --- | --- |
| Crise climática em Hoenn | Após a sétima insígnia regional, o Space Center, a Seafloor Cavern e Rayquaza podem ficar próximos. O desfecho de Rayquaza abre o resgate de Sootopolis. | Exercitar a porta do oitavo ginásio nos diferentes percursos regionais. |
| Resgate de Luffy | O jogador sinaliza para Lugia. Articuno estabiliza a jangada, Zapdos ilumina a passagem e Moltres atende os sobreviventes. O desembarque encerra o resgate. | Conferir a jangada, a cura, o retorno de Surf e o Continue durante a escolta. |
| Desejo de Jirachi e Titan Cave | Com o resgate concluído, Eren encontra Jirachi. Regirock, Regice e Registeel representam as muralhas. Regigigas está ligado ao juramento do Fundador. Groudon traz o tremor e a questão do uso da força. | Testar a recusa e a ordem dos selos. Somente Gen 1–9 e TESTE encenam as memórias de Regieleki e Regidrago. |
| Frontier e Galactic | A competição abre com 18 insígnias. A entrada do capítulo final exige 22, vitória na competição, os dois capítulos e as batalhas dos viajantes. Ao fim do navio, Eren e Luffy se despedem. | Conferir os motivos de recusa individualmente e a exceção para um final já iniciado em save antigo. |
| Estojo | O Trainer Card possui três páginas de oito. L percorre no sentido inverso, R e Select avançam. O circuito extra usa oito flags próprias. | Reabrir as páginas com combinações de insígnias nos três circuitos, salvar, reiniciar e comparar. |

A Rota 119 após o Weather Institute e o 7º andar da Silph têm batalhas de rival. Os novos locais ficam fora desses gatilhos. A ordem livre de ginásios impede associar uma quantidade total de insígnias a um líder específico. [Decisões narrativas](../IDEIAS-HISTORIAS-LENDARIOS.md)

## Plano de execução e evidência necessária

| Ordem | Trabalho nas camadas produzidas para Journey | Critério para fechar |
| --- | --- | --- |
| 1 | Reproduzir o estado publicado, testar a sequência dos oito e isolar erros do equipamento de teste. | ROM, ELF e marker identificados, cinco patches reconstituídos, vitórias, testes históricos, navegador e preparação do Pages aprovados. |
| 2 | Conferir PWT, adversários e Megas disponíveis nas duas caps. Revisar entrada, batalha, desistência, restauração da equipe, itens, PP e ausência de participantes de Legends Z-A. | Resultados por edição e por requisito, com batalhas reais e retorno ao campo. |
| 3 | Rever textos e estados da campanha por cidade inicial e ordem regional. Verificar quem pode saber de cada fato, inclusive depois da despedida. | Matriz de pré-requisitos, tentativas prematuras, interrupção, retomada e término de cada missão. Texto compilado medido com a fonte utilizada e cenas vistas no emulador. |
| 4 | Revisar todos os mapas alterados pelas camadas do projeto, seus vizinhos, os ginásios extras e os locais de encontro. Conferir bancos, animação, metatiles, colisão, altura e eventos de cada estado condicional. | Inventário por mapa e estado, imagens antes/durante/depois da divisa e no retorno, identificação da compilação e das coordenadas. Comparar com o Atlas e suas áreas de captura. |
| 5 | Fazer percursos integrados das missões, nova partida, save, reinicialização e Continue nas cinco edições. Revisar os arcos lendários propostos com o autor. | Evidências da ROM correspondente, jornadas completas e publicação somente após os checks obrigatórios. |

O escopo de edição começa nos arquivos tocados por cada camada e nos seus consumidores. Os mapas e recursos originais servem de referência. A captura de uma batalha ou o teste de integridade de um arquivo histórico, isoladamente, não encerra uma revisão de mundo ou de campanha.

A primeira execução completa da suíte local de Hoenn revelou um erro de infraestrutura na cópia de 147 MiB de evidências históricas. O teste da camada 162 fixava o destino em `/tmp` mesmo com outro volume temporário configurado. O mesmo teste passou ao honrar `TMPDIR` e continuar copiando e verificando o conjunto original. A ROM de referência e o histórico das falhas do CI estão nos registros de continuidade. [Guia técnico](../CONTINUIDADE-TECNICA-IA.md)
