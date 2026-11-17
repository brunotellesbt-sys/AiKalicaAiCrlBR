Correção das103peças suspeitas do banco nativo General

Pedido: “Resolva essas 103 peças suspeitas”.52grupos em20mapas foram
revisados com mapas inteiros e recortes. A preparação elimina103fragmentos
e conserva462rochas grandes completas. Não altera colisão, altura, eventos,
warps, coordenadas, dimensões, conexões nem os quatro arrays da arte do atlas.

Praias e encostas recebem seus contornos nativos inteiros. Quartos isolados
recebem pedras pequenas nativas inteiras18C e194; a variante194 conserva o
fundo de água rasa naRoute108. Definições, gráficos, paletas, atributos e
animações existentes permanecem intactos. Os oito words dos dois doadores
são autenticados; a prévia pegou um ID de vegetação193 escolhido por engano,
que foi corrigido antes de materializar/compilar qualquer ROM desta correção.

A migração5 descarta uma vez apenas o fundo guardado no save4, preservando
posições, NPCs e flags. Saves0..3 ainda passam pelas migrações anteriores.
Quatro testes de fontePASS, incluindo drift, evento na posição e arte errada.
Auditoria física da fontePASS:1SCC jogável, todas as obrigações antigas
preservadas,0células decorativas alcançáveis. Falta compilar e validar naROM.

Os renders são de fonte. Alguns mapas estão explicitamente terrain-only
porque o renderer não resolve berry trees/variáveis dinâmicas; não são
capturas do emulador nem prova de sprite/colisão nativa. As imagens completas
e relatórios ficam aqui no repositório. O ZIP de quatro ROMs contém resumo
e referência com hashes; não declara replay offline destas imagens.
