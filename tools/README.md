# Ferramentas para LeafGreen

Pacotes oficiais para **Windows 64 bits**. A ROM não foi modificada; edite uma cópia.

| Ferramenta | Versão | Uso | Licença |
| --- | --- | --- | --- |
| HexManiacAdvance | 0.5.6.1 | Textos, dados, mapas e scripts | MIT |
| mGBA | 0.10.5 | Testar o jogo em um emulador | MPL-2.0 |
| Floating IPS / Flips | v198 | Criar e aplicar patches IPS/BPS | GPL-3.0-or-later |

## Uso

- Extraia o ZIP em `HexManiacAdvance/` e execute `HexManiacAdvance.exe`.
  O pacote oficial é identificado como `debug` e exige **.NET Desktop Runtime 6 para Windows x64**.
- Extraia o arquivo `.7z` em `mGBA/` com um extrator compatível e abra o emulador para testar a ROM.
- Extraia o ZIP em `FloatingIPS/` e execute `flips.exe` para gerar um patch entre a ROM original e a editada.

A ROM recebida é **LeafGreen USA v1.1**, código `BPGE`, revisão `1`.
Confirme que o editor reconhece essa revisão antes de editar. Não reutilize offsets de
outra versão. Os executáveis Windows não foram executados na nuvem Linux e sua
compatibilidade de edição com essa ROM ainda precisa de validação no editor.

## Origem, integridade e licenças

`manifest.json` registra as URLs oficiais, versões, tamanhos e hashes. Na pasta `tools`, execute:

```sh
sha256sum -c SHA256SUMS
```

Os ZIPs e o 7z foram verificados por sua integridade interna. O SHA-256 do HexManiacAdvance
foi comparado com o publicado na release; os demais hashes são calculados localmente,
não assinaturas dos autores. Os downloads usaram HTTPS com verificação de certificado.

Cada pasta contém a licença e o ZIP do código-fonte da mesma tag. Os pacotes originais
foram preservados com seus avisos de terceiros. Não é necessário extrair o código-fonte
para usar os executáveis. As licenças das ferramentas não se estendem às ROMs.

## Pendências: AdvanceMap e XSE

Não estão incluídos. As conexões a `ampage.no-ip.info` e `www.pokecommunity.com` foram
bloqueadas pelo proxy (HTTP 403). Não foi possível verificar os pacotes oficiais e suas
condições de redistribuição. Não foram usados espelhos desconhecidos. Sua inclusão requer
pacotes de origem verificável e suas licenças. HexManiacAdvance reúne funções de mapas e
scripts, mas os fluxos específicos de AdvanceMap e XSE não foram testados.

## Releases oficiais

- https://github.com/haven1433/HexManiacAdvance/releases/tag/v0.5.6.1
- https://github.com/mgba-emu/mgba/releases/tag/0.10.5
- https://github.com/Sir-Walrus/Flips/releases/tag/v198
