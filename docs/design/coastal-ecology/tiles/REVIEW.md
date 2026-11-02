# Revisão visual da ecologia costeira

Base imutável: ROM `b04918724939a54bbe3321d274953a9311ab8c7b4eebc3cbeb844ffcd3604386`
da camada 165. As imagens desta pasta são renders de source, não capturas de
movimento no emulador. Os hashes dos insumos e dos PNGs foram conferidos antes
da inspeção.

Foram vistos os **21 mapas inteiros** de `source-review/`, nas quatro pranchas:
Dewford e Rotas 106/107, a ilha do terminal, as sete cidades Sevii e suas
franjas próximas, Lavender, Lilycove, Fallarbor e Rota 114. A inspeção abrangeu
árvores, fachadas, encostas, margens de praia, pontes e entradas. Não foi
confirmado outro corte nesses 21 mapas. A aparência de água de um render
estático não certifica as fases nativas de animação.

O censo complementar em `complete-object-census.json` lê as **415 superfícies**
com os bancos de rocha considerados. Encontrou 613 rochas completas de 2 × 2,
27 variantes com a arte original preservada e nenhum novo padrão de rocha
incompleto. As 11 ocorrências na borda de Battle Frontier conservam os blocos
visíveis, o border e as conexões originais; não foram tratadas como novas
rochas quebradas.

O exame das 367 copas FRLG distingue árvores isoladas de floresta sobreposta.
As peças da árvore na emenda Green Path/Water Path de Six Island compõem uma
árvore completa entre os dois mapas; a base da Rota 2 continua em Viridian.
As três copas na borda sul da Rota 11 usam a continuação de floresta original,
com border e conexões intactos. Nenhum desses casos foi apagado.

## Correção confirmada em Pallet

Um exame adicional encontrou **30 árvores** desenhadas com peças de floresta
sobreposta em posições de árvores isoladas. Os metatiles `0x01C` e `0x024`
produziam um fragmento de folhagem/sombra à esquerda, sem uma árvore vizinha
que o completasse. O padrão completo não aparece entre os exemplos nativos
do upstream; a diferença é visível na comparação ampliada.

`coastal_ecology_tiles.py` reconstrói cada objeto de **2 × 3** com o doador
nativo de Viridian `(12,23)`, usando o mesmo banco `gTileset_General_Frlg`:

```
00E 00F
01E 01F
026 027
```

São 60 IDs gráficos alterados em um único `map.bin`. Todos os bits de altura
e colisão permanecem idênticos em todas as células. Nenhum evento, NPC, warp,
conexão, dimensão de mapa ou pixel do mapa-múndi muda. Os três testes de
regressão conferem os objetos inteiros, células fora da área, banco doador e
recusa de sobreposição a eventos.

O mapa inteiro antes, o mapa inteiro previsto depois, o mapa inteiro doador e
a comparação ampliada foram vistos. `pallet-native-tree-repair.json` registra
os hashes e as 30 posições. O mapa previsto depois usa exatamente as palavras
emitidas pelo helper; a confirmação na ROM compilada pertence à validação
final da camada 166. Os atores dos renders são estáticos, sem simular as flags
de visibilidade do jogo.

Reprodução do censo a partir da raiz:

```sh
python3 tools/hoenn/audit_coastal_complete_objects.py \
  --source .local/generated-world-audit-src \
  --upstream .local/generated-world-original-inputs \
  --output /tmp/coastal-complete-objects.json
python3 -m unittest discover -s tools/hoenn -p test_coastal_ecology_tiles.py
```

O reconhecimento de um padrão nativo não aprova automaticamente toda escolha
estética, e o censo não cobre todos os tipos de montanha, móvel ou construção.
Ele complementa as imagens inteiras e as provas nativas de acesso.
