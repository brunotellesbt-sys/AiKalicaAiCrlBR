# Hoenn — inventário e porte pendente

A decisão é usar **uma única ROM**, com a mesma equipe e navegação por Surf.
O navio Vermilion–Slateport exigirá um ticket; o caminho por mar será independente
desse ticket. As ilhas hoje acessíveis por barco também devem permitir Surf.

**Hoenn ainda não foi integrado.** O arquivo enviado foi identificado como
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
