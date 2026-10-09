# Missões originais obrigatórias na ordem livre de ginásios

**Regra atual das Ligas:** oito insígnias de Kanto e oito de Hoenn, com mensagem
própria. As missões continuam nos ginásios. A validação histórica abaixo foi
substituída somente nas entradas das Ligas por
[SIXTEEN-BADGE-LEAGUES.md](SIXTEEN-BADGE-LEAGUES.md).

As missões de história devem ser concluídas. A ordem livre dos ginásios e
as rotas abertas não tornam esses episódios opcionais. Esta etapa fecha sete
lacunas de progressão: antes, as travas exigiam chefes e incursões adicionais,
mas não verificavam os episódios originais abaixo.

| Região | Após insígnias da região | Missão exigida antes do próximo ginásio |
|---|---|---|
| Kanto | 1 | Mt. Moon: quatro Rockets, Miguel e escolha de um fóssil |
| Kanto | 2 | Rocket de Cerulean: recuperar o TM roubado; Rocket recrutador da Rota 24: vencer e concluir a cena |
| Kanto | 4 | Pokémon Tower: acalmar Marowak, vencer os três Rockets do 7º andar e resgatar Fuji |
| Hoenn | 1 | Petalburg Woods: derrotar Aqua e concluir o socorro ao pesquisador Devon |
| Hoenn | 1 | Rusturf Tunnel: derrotar Aqua, recuperar as peças Devon e concluir o resgate de Peeko |
| Hoenn | 2 | Entregar a carta Devon a Steven em Granite Cave |
| Hoenn | 2 | Oceanic Museum: vencer os dois Aqua e concluir a entrega das peças a Stern |

Os guias dos ginásios informam a equipe, rota e local do próximo episódio
pendente. As rotas permanecem livres. Ginásios já vencidos continuam abertos
para revisitas. As missões usam suas flags de batalha e seus desfechos originais;
receber um item antecipado não concede uma conclusão.

Os checkpoints anteriores continuam: esconderijo Rocket de Celadon após duas
insígnias; incursões de Kanto após quatro; Silph/Giovanni após seis. Em Hoenn,
Mt. Chimney após duas; base Rocket e Shelly após quatro; esconderijo Magma após
cinco; Matt/submarino após seis; Centro Espacial, aliança Giovanni/Archie e
desfecho da crise após sete. Celadon precede a exigência da Tower quando ambos
estiverem pendentes. [História integrada](INTEGRATED-STORY.md).

## Duas falhas reproduzidas e corrigidas

A candidata anterior permitiu entrar fisicamente na Liga de Kanto com oito
insígnias e sem o resgate de Fuji. O teste usa estados anteriores de fixture;
não simula que uma campanha completa tenha sido jogada. Na candidata desta etapa, as duas Ligas
verificavam todas as pendências dos respectivos checkpoints, além das oito
insígnias da própria região. A flag antiga de entrada na Elite Four não
dispensa essa exigência. Os guardas dessa etapa indicavam a missão pendente; essa mensagem foi corrigida
na etapa das 16 insígnias.

Steven também marcava a carta como entregue mesmo sem `LETTER` na mochila,
porque o roteiro original pressupunha a passagem pela Devon. Esse comportamento
foi reproduzido conversando com o NPC. Agora ele pede a carta quando ela falta;
com a carta, a entrega original a consome e conclui o episódio. Se estiver no
PC, é necessário retirá-la para a entrega.

## Devon e o primeiro ginásio variável

No original, vencer Roxanne iniciava o roubo das peças Devon. Agora, após a
primeira insígnia de Hoenn e a conclusão de Petalburg Woods, uma transição de
cidade com o controle de ginásio prepara a cena original em Rustboro.
Isso não vence o grunt, não entrega as peças nem conclui o resgate.

O script de Roxanne só inicia o estado Devon se ele ainda estiver em zero.
Vencê-la depois não reinicia uma missão em andamento ou concluída. Foram
exercitados os oito primeiros ginásios possíveis e os estados Devon 4 e 7.

## Reprodução e evidências

Camada `mandatory-native-missions`, após `early-story-tools`, na fonte fixada
`e05c82865d38a6638173fd30b2c830d1250aa50d`. ROM candidata compilada:
`127e1f2ae2eab558764d9e2f585c0ba1772e6f32b8d6f660d51a91ad094cfa03`.
Não foi publicada no player.

```sh
cp -a .local/hoenn-early-story-tools-src .local/hoenn-mandatory-native-src
python3 tools/hoenn/prepare_mandatory_native_missions.py --source .local/hoenn-mandatory-native-src
PATH="$PWD/.local/arm-gcc/usr/bin:$PWD/.local/arm-binutils/usr/bin:$PATH" \
  make -C .local/hoenn-mandatory-native-src -j4
python3 tools/hoenn/verify_abilities.py --source .local/hoenn-early-story-tools-src \
  --candidate .local/hoenn-mandatory-native-src --layer mandatory-native-missions \
  --output /tmp/mandatory-missions/preparation
python3 tools/hoenn/validate_mandatory_native_missions.py --source .local/hoenn-early-story-tools-src \
  --library .local/mgba-bridge.so --output /tmp/mandatory-missions/baseline
python3 tools/hoenn/validate_mandatory_native_missions.py --source .local/hoenn-mandatory-native-src \
  --library .local/mgba-bridge.so --output /tmp/mandatory-missions/native
python3 tools/hoenn/validate_campaign_matrix.py --source .local/hoenn-mandatory-native-src \
  --library .local/mgba-bridge.so --output /tmp/mandatory-missions/matrix
python3 tools/hoenn/audit_english_text.py --baseline .local/hoenn-sky-access-src \
  --candidate .local/hoenn-mandatory-native-src --output /tmp/mandatory-missions/english-audit.json
python3 tools/hoenn/audit_campaigns.py --source .local/hoenn-mandatory-native-src \
  --output /tmp/mandatory-missions/campaign-dependencies.json
python3 -m unittest discover -s tools/hoenn -v
python3 -m unittest discover -s tools/sea_routes -v
```

[Relatórios e capturas](mandatory-native-validation): 11.008 decisões ARM de
travas, cobrindo os 256 subconjuntos de insígnias de cada cenário; 44 verificações
das permissões anteriores; sete portas físicas que bloqueiam e reabrem;
sete recusas físicas de Liga com oito insígnias próprias e oito da outra região,
seguidas de salvar/carregar; e 512 combinações de insígnias para as permissões
das Ligas. A conversa com Steven passou sem carta e com carta. A cena posterior
à batalha de Roxanne conservou os estados Devon 4 e 7.

O replay determinístico verifica sete arquivos alterados e preserva os scripts
de batalha dos episódios, os níveis dos ginásios/selvagens e as entregas da
família. Os 38 novos trechos de texto estão em inglês e cabem na fonte normal.
As localizações dos Pokémon permanecem iguais.

Insígnias, vitórias e estados anteriores das missões são fixtures de entrada
nesses testes. Os confrontos originais destes sete episódios não foram jogados
novamente nesta etapa. As portas, diálogos, entrega da carta e consultas às
permissões executam o motor nativo. Ainda falta a auditoria dos demais episódios
e jogar ambas as campanhas completas; isso é trabalho de implementação e
validação restante, não uma autorização para deixar missões opcionais.
