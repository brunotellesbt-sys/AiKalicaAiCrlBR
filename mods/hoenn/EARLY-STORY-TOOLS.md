# Itens antecipados e encontros fixos da história

A mãe entrega **Silph Scope, Devon Scope e Wailmer Pail desde o começo**, sem
insígnias, na residência escolhida em Kanto ou Hoenn. A Poké Flute continua
como recompensa do **primeiro ginásio de qualquer região**, conforme a regra
anterior. Surf, Dive e Waterfall mantêm sua distribuição entre os familiares.

Ter os itens não conclui missões: Giovanni continua no esconderijo Rocket,
Steven mantém sua cena na Rota 120 e a funcionária da floricultura mantém
sua explicação. Esses personagens reconhecem o item já recebido, inclusive
se estiver no PC, e não entregam outra cópia. Se o jogador não tiver o item,
o doador original ainda pode entregá-lo. A Poké Flute original de Mr. Fuji
mantém a verificação já existente do prêmio do primeiro ginásio.

Com a mochila cheia, a mãe guarda os itens restantes. Uma entrega parcial
pode ser retomada sem repetir os itens recebidos. Não há novos campos no save;
a posse na mochila ou no PC determina quais ferramentas ainda faltam.

## Locais e exceções da história

A regra de uma família por habitat vale para **encontros aleatórios**.
Encontros fixos ligados à história podem existir em outros locais e permanecem
com suas condições e desfechos originais. Não foram removidos nem deslocados.

| Encontro | Local fixo mantido | Item para ativar o encontro |
|---|---|---|
| Snorlax | Rotas 12 e 16 de Kanto | Poké Flute: primeiro ginásio, em qualquer região |
| Kecleon | Rotas 119 e 120, incluindo a cena de Steven | Devon Scope: mãe, desde o início |
| Sudowoodo | Battle Frontier, área externa leste | Wailmer Pail: mãe, desde o início; acesso à Frontier mantém suas regras |
| Fantasma de Marowak | Pokémon Tower, 6º andar | Silph Scope: mãe, desde o início; continua não capturável |
| Hypno do resgate de Lostelle | Berry Forest | Nenhum item específico; episódio original de Lostelle |
| Voltorb/Electrode disfarçados de itens | Power Plant, New Mauville e esconderijo Aqua | Nenhum item para iniciar a batalha ao interagir; acessos e episódios próprios dos locais permanecem |

As trocas já concluídas continuam: Drowzee/Hypno nos encontros aleatórios de
Berry Forest, Skorupi/Drapion em Mt. Pyre; Cubone/Marowak na Pokémon Tower e
Nidoran♀/Nidorina/Nidoqueen em Diglett’s Cave. Não houve outra redistribuição.
[Documento por rota](POKEMON-LOCATIONS.md), [planilha](pokemon-locations.csv)
e [lendários/míticos](SPECIAL-LOCATIONS.md).

Os 105 Pokémon especiais dos santuários ainda exigem oito insígnias de cada
região, sem exigir vitória nas Ligas. Antecipar os itens não altera essa regra.

## Candidata e reprodução

Camada `early-story-tools`, após `tower-habitats`, sobre a mesma fonte fixada
`e05c82865d38a6638173fd30b2c830d1250aa50d`. Candidata compilada:
`ba38f2ff2d305dd6636aea2e78b05e0297c4fa6d92f0506a941cf2fd68a6c3ae`.

A preparação verifica hashes de entrada, altera sete arquivos e preserva
explicitamente scripts de encontros, recompensa do primeiro ginásio, pools
de selvagens, áreas da Pokédex e regras de nível. O Silph Scope do esconderijo
só desaparece depois de o item ser recebido ou reconhecido; a flag de ocultação
é gravada nesse momento, permitindo revisitar sem outro objeto.

Partindo do checkout da candidata anterior descrita em [TOWER-HABITATS.md](TOWER-HABITATS.md):

```sh
cp -a .local/hoenn-tower-habitats-src .local/hoenn-early-story-tools-src
python3 tools/hoenn/prepare_early_story_tools.py --source .local/hoenn-early-story-tools-src
PATH="$PWD/.local/arm-gcc/usr/bin:$PWD/.local/arm-binutils/usr/bin:$PATH" \
  make -C .local/hoenn-early-story-tools-src -j4
python3 tools/hoenn/verify_abilities.py --source .local/hoenn-tower-habitats-src \
  --candidate .local/hoenn-early-story-tools-src --layer early-story-tools \
  --output /tmp/early-story-tools/preparation
python3 tools/hoenn/audit_english_text.py --baseline .local/hoenn-sky-access-src \
  --candidate .local/hoenn-early-story-tools-src --output /tmp/early-story-tools/english-audit.json
python3 tools/hoenn/validate_early_story_tools.py --source .local/hoenn-early-story-tools-src \
  --library .local/mgba-bridge.so --city 1 --output /tmp/early-story-tools/kanto
python3 tools/hoenn/validate_early_story_tools.py --source .local/hoenn-early-story-tools-src \
  --library .local/mgba-bridge.so --city 17 --output /tmp/early-story-tools/hoenn
python3 tools/hoenn/validate_family.py --source .local/hoenn-early-story-tools-src \
  --library .local/mgba-bridge.so --city 1 --output /tmp/early-story-tools/kanto-family
python3 tools/hoenn/validate_family.py --source .local/hoenn-early-story-tools-src \
  --library .local/mgba-bridge.so --city 17 --output /tmp/early-story-tools/hoenn-family
python3 tools/hoenn/validate_crossing.py --source .local/hoenn-early-story-tools-src \
  --library .local/mgba-bridge.so --story-access --westsea --output /tmp/early-story-tools/first-badge
python3 tools/hoenn/document_habitats.py --source .local/hoenn-early-story-tools-src --output /tmp/early-story-tools/locations
python3 -m unittest discover -s tools/hoenn -v
python3 -m unittest discover -s tools/sea_routes -v
```

## Evidências e limites

Os relatórios ficam em [early-story-tools-validation](early-story-tools-validation).
Passaram escolha de cidade e conversa por botão com a mãe em Viridian e Oldale;
chamadas ARM da entrega nas 31 casas; restrição à mãe, zero insígnias, revisita,
mochila cheia, retomada de entrega parcial, armazenamento no PC e salvar/carregar.
Nos dois inícios, os três donos originais finalizaram suas continuações com
item na mochila, no PC e ausente: 18 casos. A cura e os eventos de família
foram novamente exercitados nas duas cidades pelo validador de família.
O Silph Scope deixado no esconderijo também passou por mochila cheia e nova
tentativa: a flag de ocultação só é gravada depois de a entrega funcionar.

A recompensa da Poké Flute passou nos 16 ginásios, sem prêmio antes de uma
insígnia, com revisita, mochila cheia e reconhecimento por Fuji. Passaram
também 18 transições Surf no oeste. A auditoria preserva as 97 traduções,
mede dez linhas adicionadas e não encontra marcadores portugueses nas fontes
manifestadas. Todos os novos diálogos estão em inglês.

As viagens, estados das cenas, chamadas de entrega das 31 casas e capacidade
da mochila são fixtures. As continuações dos donos não significam que seus
confrontos originais foram jogados neste teste; as vitórias de ginásio foram
simuladas para verificar a recompensa. Salvar/carregar usa a API nativa,
sem repetir a navegação do menu de título nesta etapa. A auditoria de inglês
reverte apenas as edições aprovadas antes de comparar a tradução, e verifica
os hashes atuais: não declara que o novo código de eventos é uma mudança só
de texto.

O inventário estático anterior resolve 130 associações de mapa/script/espécie,
com 13 ocorrências fora do habitat aleatório. Esses encontros fixos foram
preservados como exceções; ainda há callbacks e condições não cobertos.
Não houve duas campanhas completas nem validação de balanceamento. A candidata
não foi publicada no player. [Trabalho restante](REMAINING-WORK.md).
