# Validação em 6 de outubro de 2026

A imagem produzida por `python3 tools/cloud/build.py` foi executada nesta nuvem Linux x86_64.
As três ferramentas rodaram simultaneamente na sessão offline `leafgreen-desktop`,
sem privilégios adicionais, com Xvfb e prefixos separados para os programas de 32 e 64 bits.

| Verificação | Resultado |
| --- | --- |
| Runtime Windows via Wine 11 | Microsoft.NETCore.App e Microsoft.WindowsDesktop.App 6.0.36 |
| HexManiacAdvance 0.5.6.1 | ROM aberta; Bulbasaur, HP 45, ataque 49 e sprite renderizados |
| AdvanceMap 1.95 via Wine 10/QEMU i386 | ROM reconhecida como BPG, idioma E, versão 1.1; mapa CELADON DEPT (0.0) e tileset renderizados |
| XSE 1.1.1 via Wine 10/QEMU i386 | ROM selecionada pela interface; script compilado com saída correta |
| Reexecução do lançador HMA | Sessão existente reutilizada; nenhum segundo editor criado |
| Kit Windows portátil | Reexecução preserva instalação existente |
| Arquivos de ferramentas | Todos os 26 hashes em `tools/SHA256SUMS` conferidos |

Versões Debian observadas: Wine `10.0~repack-6`; QEMU `10.0.13+ds-0+deb13u1`.
Wine 11 e os pacotes dos editores continuam intactos e verificados pelos hashes existentes.

O teste XSE inseriu na cópia de trabalho:

```text
#org 0x800000
lock
release
end
```

O compilador escreveu exatamente `6A 6C 02` no offset `0x800000`. O restante da ROM
foi comparado byte a byte com o original. Após a verificação, somente essa cópia de teste
foi restaurada. A ROM original nunca foi disponibilizada ao contêiner: apenas as cópias
na pasta de trabalho são montadas.

Capturas da execução atual:

- [HexManiacAdvance](hexmaniac-leafgreen.png)
- [AdvanceMap com mapa e tileset](advancemap-leafgreen.png)
- [XSE com o resultado do compilador](xse-compiled.png)

O SHA-256 original e das três cópias de trabalho ao final da validação:
`2f978f635b9593f6ca26ec42481c53a6b39f6cddd894ad5c062c1419fac58825`.
O ZIP original também permanece sem alterações no Git.

## Windows nativo

O [GitHub Actions em Windows 2022](https://github.com/brunotellesbt-sys/AiKalicaAiCrlBR/actions/runs/37445549073)
executou `tools/windows/validate.ps1` e passou. O teste chamou os três `.cmd` distribuídos,
conferiu os dois runtimes locais, exigiu janelas reais visíveis e responsivas, capturou
as interfaces e verificou o encerramento dos lançadores com código zero.
As capturas e os resultados JSON ficam no artefato `windows-tools-validation`.

Isso valida instalação e execução dos lançadores em Windows; o teste funcional de compilação
XSE e leitura do mapa foi realizado na nuvem Linux. Todas as funções de edição, histórias
modificadas, saves e funcionamento de uma ROM alterada no emulador ainda precisam de testes
específicos conforme as mudanças feitas no jogo.

## Correções aplicadas

- Wine/WoW64 sozinho não executou nem seu `cmd.exe` de 32 bits neste host.
- O carregador Linux de 32 bits exigiu QEMU. Emular somente o carregador causou conflito
  com os endereços fixos dos executáveis; incluir `wine-preloader.static` resolveu a abertura.
- Fontes ausentes provocavam o erro VB6 380 do XSE. Os aliases OFL resolveram esse erro.
- Uma sessão compartilhada evita duplicar a imagem por editor no Docker VFS.
- A trava na inicialização impede que comandos consecutivos reiniciem o mesmo prefixo Wine
  enquanto outro comando está preparando fontes e registro.

Os logs ainda podem conter avisos de Bluetooth/RPC e sinais de serviços auxiliares do Wine
sob QEMU. Esses avisos não impediram as operações verificadas acima; um erro do próprio editor
ou uma falha de operação deve ser investigado, mesmo que o processo continue aberto.
