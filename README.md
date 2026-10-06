# AiKalicaAiCrlBR

Ambiente para trabalhar com uma cópia local de **Pokémon LeafGreen USA v1.1**.
Os pacotes, versões, fontes de download, licenças e resultados dos testes estão em
[tools/README.md](tools/README.md).

Prepare o kit para Windows x64 com Python 3.10+:

```sh
python tools/install_portable.py
```

Ou construa o ambiente Wine/QEMU/.NET para Linux com Docker:

```sh
python3 tools/cloud/build.py
python3 tools/cloud/run.py hma --rom 'Pokemon - Leaf Green Version (U) (V1.1).gba'
```

HexManiacAdvance, AdvanceMap e XSE iniciam na nuvem numa sessão gráfica compartilhada.
Os três lançadores também foram testados em Windows. As cópias de trabalho e os arquivos
gerados ficam em `.local/`, fora do Git. Consulte os comandos e as evidências em `tools/README.md`.

A versão [sem obstáculos terrestres de HM](mods/no-hm-walls/README.md) inclui ROM pronta,
patch BPS e gerador reproduzível. **Surf e Waterfall permanecem necessários.**

A versão [com escolha da cidade inicial](mods/choose-starting-city/README.md) permite
escolher entre 16 cidades e ilhas, cada uma com uma casa fixa, receber presentes
da família e começar com Oak visitando sua sala. Os barcos ligam Kanto às sete ilhas
Sevii desde o início.
Inclui a remoção dos obstáculos terrestres e libera Surf/Waterfall sem insígnias.

Esta versão também abre as estradas, entrega Poké Flute após a primeira insígnia
e adapta os níveis dos ginásios à ordem escolhida. Blue assume Viridian; Giovanni
permanece na Team Rocket. A Liga exige as oito insígnias.

Os encontros selvagens agora acompanham a média da equipe (−5 a +2 níveis),
as insígnias e a cidade inicial, combinando os habitats de LeafGreen e FireRed.
