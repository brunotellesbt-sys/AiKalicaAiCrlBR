# Validação do terminal de Pallet

`layout.json` registra os hashes de entrada/saída da camada, os tiles preservados,
as posições original e nova do barco, o casco do navio e a geometria atualizada do atlas.

`validation/` contém o teste nativo da ROM comum e a reprodução independente.
Cada pasta `Gen1-*-*` contém o teste físico da respectiva ROM publicada. Os
relatórios registram o SHA-256 do arquivo realmente executado. Caminhadas,
portas, conversas, viagens e transições de Surf usam o controle no mGBA.
O preparo inicial da equipe, da história e da posição é uma fixture.

As imagens em `docs/images/pallet-harbor` são renderizações dos tiles e sprites
usados na compilação; as imagens deste diretório são capturas do emulador.
