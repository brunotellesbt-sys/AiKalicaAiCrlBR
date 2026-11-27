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

## Resultados da ROM dos oito encontros

| Verificação | Resultado observado |
| --- | --- |
| Campo e batalha | 40 vitórias no mGBA, oito por edição. Cada encontro foi recusado com uma insígnia a menos. A escada da Rota 108 levou ao terceiro encontro de Luffy no convés. |
| Progresso e save | Cada edição abriu uma bateria da versão Titan Story em (6, 7), preservou o segundo estágio da caverna, salvou pelo menu e voltou ao mesmo ponto após reiniciar. Na Gen 1–9 Normal a bateria salva diante do guarda recuperou as oito vitórias. O jogador entrou na sala da Galactic com os demais requisitos de história preparados. |
| Texto e estojo | 18 falas confrontadas com o texto compilado. A maior linha tem 168 dos 208 pixels disponíveis. Na Gen 1–9 Normal os botões do cartão percorreram Hoenn, Kanto e o circuito extra, com 22 das 24 insígnias. |
| Navegador | As cinco ROMs reconstituídas pelos patches abriram no Chromium. Cada edição executou 362 frames e exportou um estado nativo de 528.472 bytes. O pacote local do Pages passou. |
| Registro do PWT | Em cada edição, 12 casos cobriram recusas por composição de equipe e os prêmios de 10 e 25 BP. O teste dos prêmios prepara o estágio final e verifica o pagamento único e a restauração da equipe. |
| Megas de Legends Z-A | O estoque de Ever Grande inclui 45 pedras. Das 49 formas compiladas, 17 são elegíveis na Gen 1–4 e 49 na Gen 1–9 e na TESTE. Em todas as edições o jogador ativou Mega Raichu Y e a IA de Lt. Surge ativou Mega Raichu X no mesmo combate. |
| Mecânicas de combate | 684 casos em cada edição, entre eles 324 combinações de tipos e 90 verificações de condições de status por tipo. Também foram medidos clima, terreno, ordem dos turnos, habilidades, itens e efeitos com dois Pokémon em campo. Os estados iniciais de combate foram preparados para isolar cada regra. |

Os relatórios comprimidos preservam as observações e a identidade de cada ROM. As imagens dos dois Raichu correspondem aos hashes registrados. [Evidências de mecânicas e inventário](revisao-integral-2026-11-26/) · [Evidências dos encontros, do navio e do estojo](../../mods/hoenn/crossover-badges/)

### Alcance da revisão do mundo

O inventário confrontou 179 camadas e 6.243 arquivos espaciais da fonte original. Dos 2.051 mapas atuais, 1.383 têm alterações diretas e 232 usam bancos gráficos ou scripts compartilhados modificados. Entre os mapas diretamente afetados há 885 rotas marítimas, 211 cavernas, 72 rotas terrestres e 14 ginásios. Cada registro identifica layout, conexões, saídas, bancos e camadas responsáveis. Um mapa entra na fila de inspeção mesmo que a única mudança tenha sido um script. A aprovação visual de uma divisa exige vê-la no emulador em ambos os sentidos e nos estados condicionais aplicáveis. [Inventário completo em JSON comprimido](revisao-integral-2026-11-26/inventario-mapas.json.gz)

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
