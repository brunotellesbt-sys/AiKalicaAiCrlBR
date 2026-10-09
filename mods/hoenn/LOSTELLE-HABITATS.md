# Família de Hypno reservada para Berry Forest

Drowzee/Hypno passa de Mt. Pyre para Berry Forest, o mesmo habitat do Hypno
fixo no resgate de Lostelle. Skorupi/Drapion faz a troca inversa, ocupando
os seis andares, exterior e cume de Mt. Pyre. Berry Forest mantém cinco
famílias; Mt. Pyre, quatro. As outras 442 famílias conservam seus locais.

A candidata é `0f1df90862f23c168e73a811588e21a6787f042e1808b0830796b52403a12afc`.
A camada `lostelle-habitats` vem depois de `route131-sea-access` e altera
apenas os slots de encontros, pools adaptativos e tabela de áreas da Pokédex.
Os scripts do resgate, a normalização de nível, as fases evolutivas e a lógica
da tela de áreas permanecem iguais. Os marcadores anteriores ficam preservados.

## Encontros e Pokédex

| Habitat | Família transferida | Chance terrestre da família |
|---|---|---|
| Berry Forest | Drowzee / Hypno | 29% |
| Mt. Pyre | Skorupi / Drapion | 29% |

Essa chance vale quando ocorre um encontro terrestre; o estágio depende da
média das insígnias regionais. No início aparece Drowzee ou Skorupi; no meio,
a espécie básica ou sua evolução; no final, Hypno ou Drapion. O Hypno fixo do
resgate continua sendo Hypno, independentemente dessa fase. Sua batalha usa
a faixa da média da equipe −5/+2, limitada a 1–100.

Os pesos foram redistribuídos dentro dos dois habitats, preservando a ordem
de raridade. Encontros de Surf/pesca e todos os demais habitats permanecem
iguais. Continuam 920 espécies-base comuns em 444 famílias e 135 habitats;
lendários, míticos e Ultra Beasts não entram nos encontros aleatórios.

O documento [POKEMON-LOCATIONS.md](POKEMON-LOCATIONS.md) e a
[planilha](pokemon-locations.csv) foram regenerados da nova camada. O gerador
reconhece a camada para não restaurar os locais antigos na próxima execução.
Os slots atualizados estão em
[lostelle-habitat-validation/preparation/preparation.json](lostelle-habitat-validation/preparation/preparation.json).

## Evidências e reprodução

- Construção ARM concluída, reaplicação determinística e idempotência dos três arquivos.
- Verificação nativa dos 135 habitats, níveis, média regional, espécies aquáticas,
  chances de pesca e Pokédex Nacional entregue com a primeira Pokédex.
- 508 casos de mapa/família na função nativa usada pela Pokédex, verificando
  as quatro espécies nos 254 mapas de encontros: presença somente no habitat correto.
- 27 casos de fase evolutiva: três fases em Berry Forest e nos oito mapas de Mt. Pyre.
- Auditoria de inglês preservada, incluindo 97 textos traduzidos e 160 linhas medidas.
- Resgate e recompensas repetidos na nova candidata: [LOSTELLE-STORY.md](LOSTELLE-STORY.md).

```sh
cp -a .local/hoenn-route131-sea-src .local/hoenn-lostelle-habitats-src
python3 tools/hoenn/prepare_lostelle_habitats.py --source .local/hoenn-lostelle-habitats-src
PATH="$PWD/.local/arm-gcc/usr/bin:$PWD/.local/arm-binutils/usr/bin:$PATH" make -C .local/hoenn-lostelle-habitats-src -j4
python3 tools/hoenn/verify_abilities.py --source .local/hoenn-route131-sea-src --candidate .local/hoenn-lostelle-habitats-src --output mods/hoenn/lostelle-habitat-validation/preparation --layer lostelle-habitats
python3 tools/hoenn/validate_wild.py --source .local/hoenn-lostelle-habitats-src --library .local/mgba-bridge.so --output mods/hoenn/lostelle-habitat-validation
python3 tools/hoenn/validate_lostelle_habitats.py --source .local/hoenn-lostelle-habitats-src --library .local/mgba-bridge.so --output mods/hoenn/lostelle-habitat-validation
python3 tools/hoenn/document_habitats.py --source .local/hoenn-lostelle-habitats-src --output mods/hoenn
python3 -m unittest discover -s tools/hoenn -v
```

Os testes de dados chamam funções ARM diretamente, com posição e insígnias
preparadas como fixtures; não são capturas pela grama nem revisão visual da
tela da Pokédex. O resgate tem validação separada por controles. Ainda faltam
campanhas completas, balanceamento e revisão dos demais encontros fixos da
história contra a regra de localização única. Uma busca estática nos scripts
locais ainda encontrou Voltorb/Electrode, Sudowoodo, Marowak, Kecleon e Snorlax
em eventos fora dos habitats aleatórios; Voltorb/Electrode e Snorlax têm
eventos em mais de um local. Esses eventos não foram alterados nesta revisão
e exigem uma decisão antes de prometer exclusividade global. A busca não cobre
scripts compartilhados ou espécies escolhidas dinamicamente.

A candidata não foi publicada
no player; exige novo jogo e não oferece conversão de saves.
