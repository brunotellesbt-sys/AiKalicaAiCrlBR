# LeafGreen: obstáculos terrestres removidos, Surf e Waterfall preservados

Abra **LeafGreen-No-HM-Walls.gba** no mGBA. A ROM original na raiz e seu ZIP continuam intactos.
A modificação é específica para **LeafGreen USA v1.1 / BPGE**.

- Removidos fisicamente dos eventos dos 425 mapas: **55 árvores de Cut, 97 pedras de Rock Smash e 58 blocos de Strength**.
- Victory Road: quatro barreiras do quebra-cabeça substituídas por piso transitável; os estados dos interruptores ficam resolvidos.
- Seafoam: as duas correntezas dependentes de blocos ficam resolvidas, incluindo os eventos de queda e a passagem próxima às escadas. Articuno e seu evento continuam presentes.
- Rock Tunnel: os dois andares ficam iluminados sem Flash.
- **Surf e Waterfall continuam necessários e funcionam como no original.** Água, cachoeiras, atributos dos tiles e encontros aquáticos foram preservados. Seafoam mantém as alterações de água que o próprio jogo usa ao resolver o quebra-cabeça.

Fly continua funcionando normalmente. NPCs que exigem progresso na história ou insígnias continuam existindo; a mudança não pretende pular esses eventos. Placas com dicas dos antigos quebra-cabeças continuam com seus textos originais.

## Gerar novamente ou aplicar o patch

Requer apenas Python 3.10+; nenhum editor Windows é necessário:

```sh
python3 tools/rom_hacks/remove_hm_walls.py 'Pokemon - Leaf Green Version (U) (V1.1).gba'
python3 -m unittest discover -s tools/rom_hacks -v
```

Alternativamente, abra **LeafGreen-No-HM-Walls.bps** no Floating IPS e selecione a ROM original. O patch verifica a ROM de origem. O gerador recusa outra revisão ou uma ROM previamente editada.

Os endereços em `reference.json` vêm do projeto [pret/pokefirered](https://github.com/pret/pokefirered/tree/037335f4c725d7c9aecdac87066f2002b4bd7e14), compilado com `make compare_leafgreen_rev1`. Essa compilação foi comparada byte a byte com a ROM enviada e produziu exatamente o mesmo arquivo. O gerador edita eventos, oito células de mapa e dez scripts nos seus endereços originais, preservando os IDs locais dos demais objetos. Não altera a capacidade da ROM nem o cabeçalho.

`manifest.json` registra os hashes, as contagens, os mapas afetados e os bytes modificados em cada script. O SHA-256 da origem é `2f978f635b9593f6ca26ec42481c53a6b39f6cddd894ad5c062c1419fac58825`.

## Validação

Os seis testes verificam todos os mapas, a preservação dos demais NPCs/eventos e dos atributos de água, os dois mapas de Flash, o evento de Articuno, a reprodução exata da ROM pelo BPS e a rejeição de arquivos incorretos.

Também foram executados testes no núcleo **mGBA 0.10.5**, com uma partida nova sem Pokémon, insígnias ou HMs: passagem por uma antiga árvore, uma pedra quebrável e um bloco, passagem pela barreira de Victory Road, bloqueio ao tentar entrar na água a pé e carregamento dos dois mapas de Seafoam com correnteza resolvida. Capturas e resultados estão em `validation/`.

Esses testes usam saltos de mapa apenas na memória do emulador para chegar aos pontos de verificação; esses comandos não fazem parte da ROM distribuída. Não equivalem a uma campanha completa. Prefira iniciar um jogo novo; antes de experimentar um save existente, faça uma cópia. A compatibilidade com saves antigos e a campanha inteira não foram validadas.

Para repetir os testes de emulação, compile a fonte do mGBA já incluída em `tools/mGBA/` como biblioteca compartilhada, sem interfaces Qt/SDL, e compile a ponte com os headers da mesma configuração:

```sh
gcc -shared -fPIC -I.local/mgba-build/include -I.local/mgba-source/mgba-0.10.5/include \
  tools/rom_hacks/mgba_bridge.c -L.local/mgba-build \
  -Wl,-rpath,"$PWD/.local/mgba-build" -lmgba -o .local/mgba-bridge.so
python3 tools/rom_hacks/validate_emulator.py --library .local/mgba-bridge.so \
  --screenshots .local/hm-validation
```
