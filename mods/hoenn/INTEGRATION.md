# Mundo conectado — candidata experimental, não é a versão final

## Integração marítima atual

[Veja a projeção quadrada](validation/connected-world.png), também disponível
em `web/world-layout.html`. Kanto fica ao norte, Hoenn ao sul e Sevii a leste:
ilhas 1–3 na primeira faixa, 4–5 na segunda e 6–7 na terceira. Birth Island
e Navel Rock permanecem ligadas ao setor leste. Não há teleporte nas novas
conexões oceânicas: o jogador atravessa as bordas dos mapas por Surf.

A ligação de Hoenn com Sevii usa a Rota 131, à direita de Pacifidlog.
As ligações nativas Rota 131–Pacifidlog–Rota 130 e Rota 128–Ever Grande
permanecem intactas. Uma malha de dez setores e seis corredores verticais
substitui, na candidata, a cadeia linear da versão publicada.

A travessia norte foi revisada conforme solicitado: agora sai **ao sul de
Cinnabar**, entra no lago da **Rota 114**, a oeste da região de Lavaridge,
e continua por uma costa nova até a Rota 115 (Rustboro) e Rota 105 (Dewford).
O canal remove os tiles bloqueadores apenas nas faixas registradas. Mantém
a base secreta em (11,27), o Revive escondido em (7,30), NPCs e warps.
A conexão terrestre original da Rota 114 com a Rota 115 também permanece.

**80 transições Surf novas passaram em mGBA**, nos dois sentidos. Isso não
equivale a validar caminhadas completas de todas as cidades até o mar,
as campanhas, entregas de HM ou todos os sistemas de Emerald.
[Teste atual](integration-validation/connected-world.json).

## Estados regionais

O upstream colocava 763 flags de eventos de FRLG em posições já usadas por
Hoenn, inclusive sua faixa de treinadores. A candidata realoca essas flags
para um banco persistente exclusivo e separa as oito insígnias e o estado
de campeão de Kanto. Dados globais, como equipe e Pokédex, permanecem comuns.
O guarda da Liga de Hoenn agora verifica as oito insígnias, não apenas Winona.

Passaram testes de concessão, consulta, limpeza e alternância das insígnias
em ambas as regiões, independência dos campeonatos, não alteração do flag
de treinador coincidente e salvamento/carregamento nativo da flash do
emulador. **Este motor exige um novo save.** Não há conversão de saves antigos.

As 131 saídas dos quatro overlays foram reproduzidas em arquivos originais
do commit fixado. Foram verificadas 84 conexões recíprocas, sem sobreposição
de entradas, e a reaplicação da última camada é idempotente.
[Reprodução](integration-validation/world-reproduction.json).

## Histórico: primeira travessia, agora desconectada

A primeira passagem aprovada usava a borda leste da Rota 127, ao sul de Mossdeep,
e a borda oeste da Rota 21 Sul, ao norte de Cinnabar. Uma rota marítima
intermediária conecta os mapas fisicamente, sem teleportar o jogador.
A Rota 128 e a ligação com Ever Grande permanecem intactas. A camada oeste
desconecta esse protótipo e o substitui pela saída ao sul de Cinnabar.
Os relatórios antigos de quatro travessias são históricos, de outra ROM.

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

Os oito flags de insígnias eram compartilhados entre as regiões no upstream.
A separação implementada acima não conclui a migração: ainda é necessário
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
python3 tools/hoenn/prepare_worldsea.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_westsea.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/prepare_region_state.py --source .local/hoenn-multiregion-src
```

Na pasta de fonte, compile com os caminhos do compilador ARM, binutils,
libpng e pkg-config do ambiente. `make modern -j4` é o alvo validado.
Após editar mapas binários, force sua recompilação com `make modern -W data/maps.s -j4`.

```sh
python3 tools/hoenn/validate_crossing.py \
  --source .local/hoenn-multiregion-src --library .local/mgba-bridge.so \
  --worldsea --westsea --region-state
python3 tools/hoenn/verify_worldsea.py --source .local/hoenn-multiregion-src
python3 tools/hoenn/world_layout.py
node tools/hoenn/validate_world_layout.cjs
```

O validador depende do ELF correspondente à ROM, de `arm-none-eabi-nm`
em `.local/arm-binutils/usr/bin` e da ponte mGBA preparada pelos testes
anteriores. Ele é específico ao ABI desta base fixada.

## Trabalho obrigatório antes do lançamento

1. Preservar a versão anterior; a candidata exige um novo jogo, sem conversão.
2. Completar a auditoria de variáveis e todos os estados das histórias; validar
   ginásios livres, níveis adaptativos e bloqueio correto de cada Liga.
3. Migrar cidades iniciais, famílias/Oak, rival, Blue, catálogo/sprites,
   Habilidades Ocultas/Battle Bond, Megas e encontros adaptativos.
4. Migrar as conexões Sevii, implementar o ticket Vermilion–Slateport,
   liberar Surf/Waterfall desde o início e adaptar todos os puzzles que
   exigem outros HMs, preservando Dive e Whirlpool.
5. Validar Aqua/Magma, concursos, bases secretas, Frontier, viagens,
   salvamento e campanhas completas, antes de trocar a ROM no player.
