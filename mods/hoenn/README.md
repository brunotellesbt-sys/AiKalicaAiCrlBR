# Hoenn — mundo integrado e alpha jogável

Versão atual: [como jogar e limites da alpha](PLAYABLE-ALPHA.md), [mapa integrado dentro do jogo](WORLD-MAP.md) e [ROM e manifesto](playable/). Kanto, Hoenn e Sevii usam uma única ROM. Somente Surf, Dive e Waterfall permanecem HMs; Whirlpool foi cancelado. As campanhas completas ainda precisam de validação integral.

## Inventário inicial e histórico do porte

O texto abaixo registra o levantamento inicial; consulte os documentos acima para a candidata jogável atual.

[Mundo conectado e estados regionais](INTEGRATION.md): conexões físicas Surf
de Cinnabar/Rota 114 e do mar atrás de Ever Grande/Sevii numa base experimental;
**não substitui a ROM publicada nem conclui
a integração da história**.

A decisão é usar **uma única ROM**, com a mesma equipe e navegação por Surf.
O navio Vermilion–Slateport exigirá um ticket; o caminho por mar será independente
desse ticket. As ilhas hoje acessíveis por barco também devem permitir Surf.

**A integração completa de Hoenn ainda está pendente.** A candidata nativa
e suas validações parciais estão em [INTEGRATION.md](INTEGRATION.md).
O arquivo enviado foi identificado como
Emerald USA/Europe `BPEE`, SHA-256
`a9dec84dfe7f62ab2220bafaef7479da0929d066ece16a6885f6226db19085af`.
[source-inventory.json](source-inventory.json) registra os 518 mapas, 34 grupos,
2.941 eventos de objetos, 542 entradas de treinadores, 1.313 warps, 375 triggers
e 720 eventos de fundo da fonte pública fixada em
[`pret/pokeemerald@731ad5b`](https://github.com/pret/pokeemerald/tree/731ad5bfd6e6f265508d0efcca0ba42f9dcf5881).
Eventos de objetos incluem pessoas, Pokémon, obstáculos e itens; não são todos NPCs humanos.

O inventário não é um pacote de mapas jogáveis. Copiar os bytes da ROM Emerald
para LeafGreen não preserva endereços de scripts, funções e estados do jogo.
É necessário adaptar layouts/tilesets, NPCs, scripts, treinadores e as funções
especiais de Emerald, usando IDs e estados independentes da história de Kanto.

Para preservar o jogo completo, o porte precisa incluir concursos, Pokéblocks,
PokéNav, bases secretas e os sete sistemas de Battle Frontier. A base atual
não oferece esses sistemas completos. Dive e Whirlpool também não têm ações
de campo funcionais nela; os dois precisam ser implementados.

Cut, Rock Smash, Strength e Flash devem deixar de bloquear a progressão,
incluindo os puzzles que dependem deles. Surf, Dive, Waterfall e Whirlpool
continuarão exigindo o movimento correspondente. Os oito ginásios, os eventos
de Aqua/Magma, a Liga e o pós-jogo precisam ser validados como uma segunda
história, sem sobrescrever as insígnias, flags e variáveis de Kanto.

Reproduza o inventário a partir do ZIP enviado:

```sh
python3 tools/hoenn/audit.py --archive '/caminho/Pokemon - Emerald Version (USA, Europe).zip'
```

O auditor verifica o hash da ROM e lê apenas os dados de mapas da fonte fixada.
Documentos incluídos no ZIP não são tratados como instruções.

## Atlas visual da jornada

[Veja a prévia do mapa-múndi](validation/world-atlas.png), com cartografia real de
Kanto, das ilhas Sevii e do PokéNav de Emerald. `web/world-map.html` oferece
seleção de 38 lugares, consulta dos acessos, controles de teclado e opções para
mostrar/ocultar rotas e Hoenn. O player tem um link para esse atlas.

As nove conexões entre os dez portos seguem exatamente a cadeia de mapas da
ROM de Surf. As linhas são esquemáticas: a disposição dos painéis não determina
distâncias ou a geografia dos mapas marítimos jogáveis. A travessia Surf
Rota 21 ↔ Rota 127 e o barco Vermilion ↔ Slateport aparecem explicitamente como
**planejados na ROM publicada**. Os 17 lugares de Hoenn, incluindo a Rota 127,
também são marcados como não jogáveis nessa versão.

Esta é uma consulta externa no navegador, **não a implementação do PokéNav
dentro da ROM**. Não acompanha o save nem teleporta o jogador. O menu regional
original da ROM permanece inalterado. A cartografia não substitui o porte de
mapas, NPCs e eventos descrito acima.

Para recriar os cinco painéis, use o checkout preparado da versão atual. O
gerador usa Pillow (validado com 12.3.0) para decodificar os tiles e seus mapas:

```sh
python3 tools/hoenn/world_atlas.py --source .local/all-regions-src
python3 -m unittest discover -s tools/hoenn -v
python3 tools/sea_routes/serve.py
# Abra http://127.0.0.1:8765/world-map.html
```

O gerador lê os assets nativos de LeafGreen e os arquivos de cartografia de
Emerald do commit fixado, sem carregar textos anexados. `web/world-map.json`
registra hashes dos arquivos de entrada e das imagens produzidas, o hash da
ROM atual e o estado de cada lugar/travessia. Nenhum byte da ROM é alterado.

Passaram cinco testes offline de integridade e sete verificações no Chromium,
incluindo seleção, teclado, visibilidade, rotas pendentes e layout móvel.
[Relatório do navegador](validation/atlas-browser.json).
