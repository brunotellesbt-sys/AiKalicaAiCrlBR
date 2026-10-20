# Dewford, pontes das Sevii e acessos das cavernas

A camada 161 corrige as travessias e o acabamento costeiro sobre o circuito de 24 insígnias. O mapa-múndi e os oito ginásios continuam preservados pela auditoria do código de origem. As quatro edições normais e a TESTE recebem a mesma geografia.

Em Dewford/Rota 107, a lateral da ponte bloqueia a saída de pedestres para o oceano; as duas escadas mudam corretamente entre a altura da areia e a do tabuleiro. O personagem fica visível sobre a ponte, e o Surf continua passando por baixo da ponte alta. A costa sul conserva as dimensões originais, com a floresta continuando na borda nativa e o canto de praia completo. A câmera carrega também os tiles diagonais do terminal, evitando o retângulo de água ou pedras sobre o telhado. Os dois atendentes de Dewford permanecem acessíveis.

[Mapas inteiros de Dewford e vizinhos](design/dewford-coast/review.json) · [Vista conjunta do porto, ponte e costa](design/dewford-coast/Dewford-port-bridge-and-south-coast.png). Essas imagens são renderizações dos tiles nativos; as capturas de emulador ficam nos relatórios de cada edição.

Nas sete Sevii, a ponte de madeira foi prolongada sobre o espaço onde ficavam as coberturas antigas. As sete pontas terminam com madeira contínua, sem a antiga faixa metálica. A chegada ao terminal acontece no fim desse tabuleiro; o retorno volta ao mesmo ponto. Na Ilha 1, a extensão atravessa a ligação já existente com Treasure Beach. O Surf fica fora dos píeres baixos, onde as tábuas ocultavam parte do personagem, e usa a água livre ao redor. Essa regra é específica dos píeres baixos; a ponte alta de Dewford conserva suas duas camadas.

A [revisão das sete pontes](design/sevii-bridges/README.md) inclui mapas completos antes e depois. A [verificação nativa adicional](../mods/hoenn/dewford-coast-validation/map-finishing/map-finishing.json) confere entradas dos terminais, salvamento no píer, o Centro de Six Island e as margens de Two Island e One Island.

Os nove acessos de santuários em `JourneyWorldSea00`–`08` receberam a montanha nativa inteira. A porta de cada caverna mantém sua posição e seu destino. A [revisão das montanhas](design/cavernas-costeiras.md) apresenta os mapas completos antes e depois, identificados como renderizações dos tiles de origem.

## Verificação da entrega

O [manifesto das ROMs](../mods/hoenn/versions/versions.json) exige 27 relatórios vinculados aos hashes finais: auditoria de origem, todas as conexões externas de Surf e cinco conjuntos de cinco provas nativas. Em cada edição, são verificados Dewford/Rota 107, as sete pontes e píeres, duas entradas e saídas de cada uma das nove cavernas, as regras de encontros/treinadores e a abertura do jogo desde o início.

Os relatórios ficam em [dewford-coast-validation](../mods/hoenn/dewford-coast-validation/). Os deslocamentos usam os controles do emulador. Os testes de campo preparam somente posição inicial, equipe e progresso; não reposicionam o personagem nem escrevem sua altura durante a viagem. O teste de inicialização não escreve memória do jogo e, na TESTE, carrega explicitamente o mesmo arquivo de bateria `.sav` distribuído na pasta de teste antes de escolher Continue.

A tela azul enviada não foi reproduzida nesta validação com mGBA. A TESTE foi aberta desde o início, com e sem o save incluído; os relatórios registram esses casos, sem atribuir uma causa não confirmada. Isso não comprova uma correção específica no My Boy. [Abertura sem save](../mods/hoenn/dewford-coast-validation/TESTE/fresh-main-menu.png) · [Continue com o save distribuído](../mods/hoenn/dewford-coast-validation/TESTE/battery-continued-to-field.png).

O [vídeo de Dewford](videos/dewford-coast-corrected.mp4) percorre terminal, ponte, os dois atendentes e a cidade em uma viagem contínua por controles. A revisão do mapa inteiro e as capturas nativas complementam os testes de colisão; um teste de passagem não substitui a observação do acabamento.

As provas antigas de ginásios, campanha e recursos anteriores conservam seus próprios hashes na cadeia histórica. A auditoria da camada atual confirma os arquivos preservados; não apresenta essas gravações antigas como testes das ROMs novas. Os capítulos de história após a 18ª e a 22ª insígnias continuam aguardando o conteúdo que o autor informou que detalhará.

As [quatro ROMs normais](../roms/README.md) e a [TESTE](../roms/rom-de-teste/LEIA-ME.md) são atualizadas juntas. A TESTE mantém encontros selvagens e abordagens automáticas desativados; conversar com treinadores continua permitindo batalhas. O player é validado com as cinco edições e preparado para publicação; o GitHub Pages recebe a atualização após o merge em `main`.

## Reproduzir a validação

Depois de compilar o código de origem da camada 161 e congelar os arquivos usados pelos leitores nativos:

```bash
python3 tools/hoenn/validate_dewford_coast_source.py --source .local/dewford-coast-src --baseline .local/sootopolis-src --output mods/hoenn/dewford-coast-validation/source.json
python3 tools/hoenn/validate_dewford_coast.py --source .local/dewford-coast-editions/Gen1-9-Normal --library .local/mgba-review.so --output mods/hoenn/dewford-coast-validation/Gen1-9-Normal --video
python3 tools/hoenn/validate_coastal_pier_safety.py --source .local/dewford-coast-editions/Gen1-9-Normal --library .local/mgba-review.so --output mods/hoenn/dewford-coast-validation/Gen1-9-Normal
python3 tools/hoenn/validate_coastal_cave_finishing.py --source .local/dewford-coast-editions/Gen1-9-Normal --library .local/mgba-review.so --output mods/hoenn/dewford-coast-validation/Gen1-9-Normal
gcc -shared -fPIC -O2 tools/rom_hacks/mgba_bridge.c -o /tmp/mgba-coldboot.so -lmgba
python3 tools/hoenn/validate_cold_boot.py --source .local/dewford-coast-editions/TESTE --library /tmp/mgba-coldboot.so --output mods/hoenn/dewford-coast-validation/TESTE --battery roms/rom-de-teste/Pokemon-Journey-TESTE.sav
```

Os demais validadores de campo e inicialização devem ser executados sobre os cinco arquivos de edição. A publicação só aceita os relatórios completos e correspondentes aos hashes das ROMs distribuídas:

```bash
python3 tools/hoenn/publish_dewford_coast.py --source .local/dewford-coast-src
python3 tools/hoenn/run_versions_browser.py
python3 tools/hoenn/stage_pages.py --output /tmp/player-site
```
