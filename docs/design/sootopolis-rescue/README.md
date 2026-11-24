# Revisão do resgate obrigatório de Sootopolis

## Terreno e acessos

O terminal, a ponte, as portas e os dois layouts de Sootopolis conservam seus blocos e suas posições. O capitão na coordenada (8, 11) continua oferecendo o ferry normal. Depois de Rayquaza, a conversa também permite embarcar para o resgate.

O mapa da missão usa dois bancos de areia copiados inteiros de JourneyWorldSea01. O desembarque fica em (7, 19), no banco sul. Os moradores esperam em (17, 7) e (18, 7), no banco norte. Manaphy está na água entre os bancos. A área usa os bancos gráficos do doador e sua borda marítima. A viagem e o retorno ligam a área ao porto.

[Mapa inteiro da área de resgate](resgate-mapa.png)

## Progressão e validação

A missão usa a variável de save 0x40E5. O estado 1 inicia a busca, o 2 registra o contato com os moradores, o 3 aguarda o desembarque e o 4 registra a conclusão. O bloqueio do último ginásio usa o seletor regional e é conferido também na conversa com o líder para saves criados dentro do ginásio antes da atualização.

O emulador percorreu a entrada pelo porto, a viagem de barco, a ida e volta por Surf, o save durante a escolta, o Continue, a confirmação pelo capitão e a abertura da porta do ginásio. A matriz também verificou as oito escolhas de último ginásio, o atendimento de saves com oito insígnias e a ordem de Galactic antes ou depois do resgate. O início de cada teste prepara as insígnias, os eventos anteriores e a posição de partida.

[Captura do encontro com os moradores](../../../mods/hoenn/sootopolis-rescue/Pokemon-Journey-Gen1-4-Hard/reach-castaways.png) · [Captura de Lugia e da embarcação](../../../mods/hoenn/sootopolis-rescue/Pokemon-Journey-Gen1-4-Hard/lugia-shields-the-raft.png) · [Manifesto das cinco ROMs](../../../mods/hoenn/sootopolis-rescue/validation.json)
