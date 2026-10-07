# Construção e auditoria do catálogo Unova

Execute os comandos na raiz do repositório. Use o checkout existente da tarefa;
não crie um Git worktree sem pedido explícito. Os checkouts abaixo são caches de
dependências e código-base em `.local/`, separados dos arquivos do projeto.

Requisitos: Linux x64, Python 3.10+, Git, Make, GCC/G++ para as ferramentas nativas,
`libpng-dev`, `pkg-config`, `dpkg-deb` e binutils ARM. Em Debian/Ubuntu, os pacotes
nativos são `build-essential libpng-dev pkg-config binutils-arm-none-eabi`.
O GCC ARM e newlib têm versões e hashes fixados no instalador:

```sh
python3 tools/unova/bootstrap.py
git clone https://github.com/kerrymilan/roguemon-expansion.git .local/expanded-firered
git -C .local/expanded-firered checkout 7606f57650627704c9aad965a031fd3a454590e2
python3 tools/unova/build.py --source .local/expanded-firered --nm /usr/bin/arm-none-eabi-nm
```

O clone deve estar limpo antes da primeira aplicação do overlay. O preparador
recusa alterações existentes. Para revisar uma nova versão do overlay, use um
novo diretório de cache limpo e o mesmo commit; preserve edições do checkout
anterior. Para recompilar a mesma versão já preparada, repita `build.py`.
`--toolchain`, `--nm` e `--jobs` permitem selecionar os caminhos e paralelismo.
Na nuvem desta tarefa, binutils estão em `.local/arm-binutils/usr/bin`; o comando
sem `--nm` usa esse caminho. Quando libpng/pkg-config estiverem instalados em
`.local/native`, use:

```sh
export PKG_CONFIG_LIBDIR="$PWD/.local/native/usr/lib/x86_64-linux-gnu/pkgconfig"
export PKG_CONFIG_SYSROOT_DIR="$PWD/.local/native"
export LD_LIBRARY_PATH="$PWD/.local/native/usr/lib/x86_64-linux-gnu"
python3 tools/unova/build.py --source .local/expanded-firered
```

O build configura LeafGreen, revisão 1, aplica os overlays da jornada, importa
`mods/unova-catalog/donor-assets.zip`, compila o motor e remove os obstáculos
terrestres pelas tabelas do ELF produzido. Ele exporta a ROM de 32 MiB, o BPS
contra o original e referências de depuração. Os IDs de gráficos dos objetos
agora têm 16 bits; o modificador de HMs trata essa diferença explicitamente.

## Reextrair os dados enviados

O build usa o pacote extraído e verificado que já está no repositório. Para
recriá-lo, aplique `mods/unova-catalog/donor/unova_emerald_2_0_3.bps` à base correta
de Emerald com `bps.apply(patch_bytes, source_bytes)`. A rotina implementa as quatro
operações BPS e verifica os três CRCs. A base é Emerald USA, SHA-1
`f3ae088181bf583e55daf962a92bb46f4f1d07b7`; ela foi reconstruída de
`pret/pokeemerald` no commit `731ad5bfd6e6f265508d0efcca0ba42f9dcf5881`, usando
agbcc e o alvo `compare`.

```sh
python3 tools/unova/extract.py \
  --rom .local/unova/unova-emerald.gba \
  --source .local/expanded-firered \
  --output mods/unova-catalog/donor-assets.zip
```

O extrator exige o SHA-256 exato da ROM doadora. Ele remapeia espécies pelo número
da Pokédex e pelas listas de formas, habilidades e golpes pelos nomes; IDs de
Emerald e LeafGreen não são intercambiáveis. Campos inválidos ou nomes não
reconhecidos interrompem a extração. O ZIP é determinístico, contém o inventário
e os gráficos comprimidos, e não inclui código de máquina da ROM doadora.

## Verificar

```sh
python3 -m unittest discover -s tools/unova -v
python3 -m unittest discover -s tools/journey -v
python3 -m unittest discover -s tools/rom_hacks -v
```

Para repetir os testes funcionais, instale `libmgba-dev` ou use o mGBA já
compilado no cache desta nuvem:

```sh
gcc -shared -fPIC -O2 tools/rom_hacks/mgba_bridge.c -o /tmp/mgba-bridge.so -lmgba
python3 tools/unova/validate_emulator.py --library /tmp/mgba-bridge.so
```

Na instalação local desta tarefa:

```sh
LD_LIBRARY_PATH="$PWD/.local/mgba-build" \
  python3 tools/unova/validate_emulator.py --library .local/mgba-bridge.so
```

O teste usa offsets reais exportados pelo compilador, inicia pelo menu do jogo,
percorre casas e travessias, cria os 859 registros, testa Fada, gera as 392
combinações de treinador/ordem de ginásio e exercita as 47 Megas com reversão.
Ao final, aciona Mega Evolução pelo menu de golpes numa batalha real.
As chamadas de funções e itens injetados existem apenas na memória do emulador;
a ROM distribuída permanece intacta. Um teste interrompido não deixa um relatório
antigo de sucesso no lugar do novo.
