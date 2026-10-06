# Ferramentas para LeafGreen

| Ferramenta | Versão | Finalidade | Origem |
| --- | --- | --- | --- |
| HexManiacAdvance | 0.5.6.1, pacote debug do autor | Textos, dados, mapas e scripts | Release oficial |
| mGBA | 0.10.5 | Emulador | Release oficial |
| Floating IPS | v198 | Patches IPS/BPS | Release oficial |
| .NET Runtime + Windows Desktop Runtime x64 | 6.0.36 | Executar o editor WPF | Pacotes Microsoft |
| Wine, amd64 WoW64 | 11.0 | Executar aplicativos Windows no Linux | Build comunitário Kron4ek |
| AdvanceMap | 1.95 | Mapas e eventos | Arquivo comunitário |
| XSE | 1.1.1 | Scripts de eventos | Arquivo comunitário com fontes |
| Visual Basic 6 SP6 | KB290887 | Dependência do XSE | Redistribuível Microsoft arquivado |

Nenhuma história ou evento foi alterado. A ROM de referência é **LeafGreen USA v1.1**, código
`BPGE`, revisão `1`. Trabalhe em uma cópia. A abertura da ROM no HexManiacAdvance foi
validada; não significa que todos os recursos de edição ou a compatibilidade de saves foram testados.

## Kit local para Windows x64

Com Python 3.10 ou superior, na raiz do repositório:

```sh
python tools/install_portable.py
```

Isso verifica os hashes e extrai os pacotes em `.local/windows-portable/`.
O .NET fica nessa pasta; não há instalação global. O XSE recebe `msvbvm60.dll` ao lado do
executável, extraído do redistribuível verificado. Atalhos antigos para ROMs de terceiros são ignorados.
Executar novamente preserva a instalação existente e suas configurações.

No Windows, confira os runtimes e abra os lançadores:

```bat
.local\windows-portable\dotnet\dotnet.exe --list-runtimes
.local\windows-portable\HexManiacAdvance.cmd
.local\windows-portable\AdvanceMap.cmd
.local\windows-portable\XSE.cmd
```

Os ZIPs e a extração desse kit foram testados no Linux; os lançadores `.cmd` precisam de
validação no Windows. O mGBA e o Floating IPS continuam em suas pastas: extraia o `.7z`
do mGBA ou o ZIP do Flips e abra seus executáveis.

## HexManiacAdvance na nuvem Linux

Requisitos: Linux x86_64, Python 3.10+, Docker disponível e acesso aos registros e pacotes Debian.
Na raiz do repositório:

```sh
python3 tools/cloud/build.py
python3 tools/cloud/run.py runtimes
python3 tools/cloud/run.py hma --rom 'Pokemon - Leaf Green Version (U) (V1.1).gba'
```

O build usa a imagem Debian fixada por digest, pacotes APT assinados e os arquivos locais
verificados por SHA-256. Usa o proxy e o conjunto de certificados confiáveis do host, sem
salvar valores de credenciais. O Dockerfile mantém a instalação numa camada para reduzir
consumo de disco com o driver VFS da nuvem.

`run.py` copia a ROM para `.local/rom-tools/hma/working.gba`, preservando qualquer cópia já
existente. O editor só recebe essa pasta de trabalho. Seu prefixo Wine e suas configurações
ficam no volume Docker `leafgreen-hma-state`; o processo roda sem rede, sem privilégios
adicionais e com limites de memória/CPU. Os processos precisam ser iniciados novamente
em tarefas futuras; não presuma que imagens ou volumes Docker sobrevivam à publicação.

A interface roda em Xvfb, sem uma prévia web. Para inspecionar uma sessão:

```sh
docker logs leafgreen-hma
docker exec -e DISPLAY=:99 leafgreen-hma xdotool search --onlyvisible --name 'Hex Maniac Advance' getwindowname
docker exec -e DISPLAY=:99 leafgreen-hma import -window root /home/editor/editor.png
docker cp leafgreen-hma:/home/editor/editor.png /tmp/editor.png
```

Salve as edições no editor antes de encerrar o contêiner. Para iniciar outra sessão após
encerrá-lo, remova apenas o contêiner `leafgreen-hma` e rode o comando novamente; a pasta
`working.gba` e o volume de configurações são preservados.

### Fontes do WPF

O editor usa famílias de fontes normalmente presentes no Windows. `Fonts/` fornece aliases
locais derivados de **Carlito e Liberation**, sob SIL OFL 1.1, para as famílias esperadas pelo WPF.
Esses arquivos não são fontes da Microsoft. As alterações se limitam aos nomes das fontes;
os glifos são preservados. Os avisos, licenças e `Fonts/create_aliases.py` acompanham os arquivos.
O registro de fontes acontece apenas no prefixo Wine do contêiner, sem alterar as fontes do host.

### AdvanceMap e XSE no Linux

Os pacotes estão incluídos e preparados no kit. `run.py advancemap` e `run.py xse` também
estão disponíveis, mas **suas interfaces não iniciaram nesta nuvem durante a validação**.
São executáveis Windows de 32 bits; a combinação deste host com Wine/WoW64 falhou na
inicialização. Os pacotes e a dependência VB6 foram conferidos; não declare sua execução
Linux pronta sem uma nova validação. Use os lançadores Windows para testar esses programas.

## Origem, hashes e licenças

Na pasta `tools`:

```sh
sha256sum -c SHA256SUMS
```

Os manifestos registram URLs e commits fixos. O .NET foi comparado com os SHA-512 da
Microsoft; Wine e HexManiacAdvance, com os SHA-256 publicados nas releases; o VB6 arquivado,
com o SHA-256 da receita Winetricks 20200412. ZIPs foram verificados por CRC e o mGBA por 7-Zip.
Os hashes dos demais arquivos são calculados localmente, não assinaturas de seus autores.

AdvanceMap e XSE são cópias de arquivos comunitários, não releases oficiais autenticadas.
O executável AdvanceMap foi comparado byte a byte com uma segunda cópia independente.
O XSE foi obtido de um commit fixo; tamanho e identificação Git dos arquivos foram conferidos.
Seu executável informa versão 1.01.0001 (1.1.1), compatível com a versão no projeto fonte.
Os créditos originais de LU-HO Poké e HackMew foram preservados. Não atribuímos uma licença
open source a esses dois programas nem garantimos que os arquivos sejam os mais recentes.

As pastas preservam os avisos originais e fontes disponíveis: MIT para HexManiacAdvance,
MPL-2.0 para mGBA, GPL-3.0-or-later para Flips, LGPL-2.1-or-later para Wine, MIT/avisos de
terceiros nos pacotes .NET e os avisos do redistribuível VB6. Essas licenças não se estendem às ROMs.
Consulte os manifestos por pasta para as URLs exatas e os arquivos `LICENSE`, `COPYING` e `NOTICE`.

## Evidência de validação

- .NETCore.App e WindowsDesktop.App 6.0.36 reconhecidos pelo `dotnet.exe` sob Wine.
- Interface do HexManiacAdvance renderizada; cópia da ROM aberta e tabela Pokémon consultada:
  Bulbasaur com HP 45, ataque 49 e sprite correto. Original e cópia mantiveram o SHA-256 inicial.
  Captura: [hexmaniac-leafgreen.png](cloud/hexmaniac-leafgreen.png).
- Extração do kit Windows repetida sem sobrescrever a instalação existente.
- Execução das interfaces AdvanceMap/XSE nesta nuvem: falhou; execução em Windows: não testada.
