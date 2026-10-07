# Catálogo das demais regiões

Execute na raiz do repositório. O pacote `mods/all-regions/donor-assets.zip`
contém os dados extraídos e verificados; não é necessário baixar as ROMs doadoras
para compilar. A base e as dependências são as descritas em
[tools/unova](../unova/README.md).

```sh
python3 tools/unova/bootstrap.py
git clone https://github.com/kerrymilan/roguemon-expansion.git .local/all-regions-src
git -C .local/all-regions-src checkout 7606f57650627704c9aad965a031fd3a454590e2
python3 tools/regions/build.py --source .local/all-regions-src --nm /usr/bin/arm-none-eabi-nm
```

Use uma cópia limpa da base antes da primeira preparação; edições anteriores
são preservadas e recusadas. O preparador guarda o catálogo canônico pré-processado
em `.region-native.c`. Para revisar o pacote extraído, `--reimport` reaplica o
catálogo a partir desse original, sem reutilizar tabelas já importadas.
`--export-only` recalcula os artefatos sem compilar. `--toolchain` e `--nm` permitem selecionar GCC e binutils. Nesta nuvem, binutils
estão em `.local/arm-binutils/usr/bin`, usados por padrão; em Debian/Ubuntu com
`binutils-arm-none-eabi` instalado, use `--nm /usr/bin/arm-none-eabi-nm`.

## Reextração

Disponha as ROMs descompactadas em uma pasta de trabalho, com os nomes e hashes
registrados em `donor-inventory.json`. O extrator exige exatamente esses hashes.
Passe um checkout da base e seu arquivo `.region-native.c`, gerado pelo build:

```sh
python3 tools/regions/merge_catalog.py \
  --source .local/all-regions-src \
  --preprocessed .local/all-regions-src/.region-native.c \
  --donors .local/donors --output mods/all-regions
python3 tools/regions/build.py --source .local/all-regions-src --reimport
```

As tabelas de nomes/stats/sprites vêm dos ponteiros no cabeçalho das ROMs, com
limites de slots fixados para cada arquivo. Nomes truncados e erros de grafia têm
aliases explícitos. Formas duplicadas usam mapeamento explícito; os padrões
Vivillon e a forma Terastal de Terapagos foram conferidos visualmente. Sprites
vazios, tamanhos inválidos e referências LZ77 inválidas são rejeitados. Duplicatas
preservam a fonte preferida, com origem registrada. As 47 lacunas de espécies-base
e as 154 formas complementares usam os dados da expansão fixada no mesmo commit.

O importador mantém as tipagens/habilidades/regras canônicas para novas espécies,
copia os atributos e sprites dos doadores e restringe referências de evoluções e
formas a espécies ativas. Gigantamax/Eternamax ficam fora; o motor bloqueia
Dynamax e Z-Moves, além de não habilitar Terastalização/Ultra Burst.

## Verificação

```sh
python3 -m unittest discover -s tools/regions -v
python3 -m unittest discover -s tools/unova -v
python3 -m unittest discover -s tools/journey -v
python3 -m unittest discover -s tools/rom_hacks -v
```

Com a ponte mGBA já preparada:

```sh
LD_LIBRARY_PATH="$PWD/.local/mgba-build" \
  python3 tools/unova/validate_emulator.py \
    --directory mods/all-regions --rom-name LeafGreen-Journey-AllRegions \
    --output mods/all-regions/validation --library .local/mgba-bridge.so
```

Os testes criam todos os registros, verificam 48 Megas e os bloqueios de mecânicas,
renderizam todos os complementos e repetem as verificações de casas, HMs, ferries,
ginásios, Fada e ativação real de Mega pelo menu. Os itens são injetados apenas na
memória dos testes; nenhuma distribuição é adicionada à ROM.
