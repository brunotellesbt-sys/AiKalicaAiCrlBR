# Protótipo Rota 127 ↔ Rota 21 — não é a versão final

A passagem aprovada usa a borda leste da Rota 127, ao sul de Mossdeep,
e a borda oeste da Rota 21 Sul, ao norte de Cinnabar. Uma rota marítima
intermediária conecta os mapas fisicamente, sem teleportar o jogador.
A Rota 128 e a ligação com Ever Grande permanecem intactas.

## Base experimental

O protótipo usa [`eonlynx/pokecrossroads`](https://github.com/eonlynx/pokecrossroads/tree/e05c82865d38a6638173fd30b2c830d1250aa50d),
commit `e05c82865d38a6638173fd30b2c830d1250aa50d`, com 518 mapas de
Emerald e 421 mapas de FRLG antes da nova passagem. Essa base já contém
os sistemas nativos de Emerald; a presença dos mapas não demonstra que
as duas campanhas completas funcionam juntas.

**A ROM publicada, o player e seus saves não foram substituídos.** As
modificações anteriores de LeafGreen ainda não foram migradas para esse
motor. Saves antigos não têm compatibilidade validada: a proposta é
preservar a versão atual separadamente e exigir um novo jogo na futura versão.

Os oito flags de insígnias são compartilhados entre as regiões no upstream.
Antes de qualquer lançamento, é necessário separar os estados regionais,
migrar a jornada personalizada, validar as campanhas e adaptar os ginásios
de Hoenn para ordem livre e níveis escaláveis, conforme solicitado.

## O que foi implementado e testado

- Canal marítimo sem interseção com eventos; NPCs, warps e triggers das
  duas rotas preservados por hash.
- Conexões de mapa nos dois sentidos, mantendo Surf durante a passagem.
- Conversão dos metatiles na prévia e no trecho de câmera salvo entre
  os formatos Emerald/FRLG; recarga de tilesets, paletas e animações.
- Redesenho da tela após a troca de formato, corrigindo as texturas
  incorretas na entrada de Kanto.
- Compilação nativa e quatro travessias físicas em mGBA aprovadas:
  Hoenn → passagem → Kanto → passagem → Hoenn.
- Preparação reproduzida em arquivos originais do commit fixado, com
  comparação byte a byte dos 14 arquivos resultantes e idempotência.

[Preparação](integration-validation/preparation.json),
[teste de travessia](integration-validation/crossing.json) e
[captura da chegada em Kanto](integration-validation/Route21_South_Frlg-arrival.png).

O teste injeta uma equipe e ativa Surf **somente na memória do emulador**
para isolar as conexões. Não comprova entrega dos HMs, dispensa de insígnias,
ferry/ticket, campanhas, pós-jogo, compatibilidade de saves ou as regras
personalizadas. Nenhuma dessas funcionalidades deve ser anunciada como pronta.

## Reproduzir

Reserve pelo menos 400 MB livres e use o toolchain ARM moderno preparado
no ambiente. A aquisição exige uma pasta nova; não sobrescreve um checkout.

```sh
python3 tools/hoenn/acquire_multiregion.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_crossing.py --source .local/hoenn-multiregion-src
```

Na pasta de fonte, compile com os caminhos do compilador ARM, binutils,
libpng e pkg-config do ambiente. `make modern -j4` é o alvo validado.
Após editar mapas binários, force sua recompilação com `make modern -W data/maps.s -j4`.

```sh
python3 tools/hoenn/validate_crossing.py \
  --source .local/hoenn-multiregion-src --library .local/mgba-bridge.so
```

O validador depende do ELF correspondente à ROM, de `arm-none-eabi-nm`
em `.local/arm-binutils/usr/bin` e da ponte mGBA preparada pelos testes
anteriores. Ele é específico ao ABI desta base fixada.

## Trabalho obrigatório antes do lançamento

1. Confirmar a migração com novo save, preservando a versão anterior.
2. Separar 16 insígnias e flags/variáveis das histórias regionais; validar
   ginásios livres, níveis adaptativos e bloqueio correto de cada Liga.
3. Migrar cidades iniciais, famílias/Oak, rival, Blue, catálogo/sprites,
   Habilidades Ocultas/Battle Bond, Megas e encontros adaptativos.
4. Migrar as conexões Sevii, implementar o ticket Vermilion–Slateport,
   liberar Surf/Waterfall desde o início e adaptar todos os puzzles que
   exigem outros HMs, preservando Dive e Whirlpool.
5. Validar Aqua/Magma, concursos, bases secretas, Frontier, viagens,
   salvamento e campanhas completas, antes de trocar a ROM no player.
