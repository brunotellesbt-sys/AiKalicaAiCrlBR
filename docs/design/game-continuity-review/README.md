# Campanha e câmeras — proveniência

`native-contact-168.png` reúne seis capturas reais da candidata 168: Four,
Two, Three e Six vistas da rota antes da divisa, Shelly presente no Instituto
e o jogador dentro do ginásio após vencer e sair pela Rota 119. Não é uma
imagem gerada nem um render de tiles. A margem da própria tela pode recortar
um prédio; os blocos visíveis foram comparados com o banco canônico do vizinho.

ROM: `cd91b1a3b8b783fe860c6668a7efcc741e847d198f0363b2288e382045e55479`.
ELF: `ab5dbf1fbb10d335adde96a972e352d4a1f3a35158cc1513ee67bd71d6ee5103`.
As imagens individuais, hashes e observações estão nos relatórios em
`mods/hoenn/game-continuity-review-validation/common/{campaign,coasts}`.

`baseline/` preserva diagnósticos da ROM 167 e da primeira candidata parcial.
Na 167, Shelly não era criada; na candidata parcial, a batalha funcionava,
mas o estado 2 reabria o bloqueio. Esses relatórios são diagnósticos e não
provas de aprovação. A falha de estado 2 tem `passed: false` explicitamente.

O reparo costeiro troca apenas os bancos atribuídos a 16 layouts. A comparação
integral de pixels e atributos próprios e das bordas afetadas está no marcador
de preparação e na prova de fonte. Nenhum arquivo de terreno, porta, evento,
conexão, gráfico ou callback de animação foi alterado. As 92 conexões direcionais
têm comparação de fonte; a validação nativa percorre 16 pares de ida e volta,
com 32 transições e 304 capturas. Esses escopos não são equivalentes.

As colocações iniciais e o progresso anterior dos percursos são fixtures
identificadas. A batalha, o presente, as portas, a saída, as conexões e a bateria
usam os mecanismos nativos. O Continue é um boot real sem escrita na memória.
A inspeção não representa uma campanha inteira jogada.
