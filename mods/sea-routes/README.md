# Rotas marítimas — primeira etapa da expansão de regiões

A [ROM](LeafGreen-Journey-SeaRoutes.gba) e o [patch BPS](LeafGreen-Journey-SeaRoutes.bps)
incluem dez mapas marítimos conectados fisicamente. É possível usar Surf para
viajar entre Vermilion, as sete ilhas Sevii, Birth Island e Navel Rock e voltar
pelo mesmo caminho. O caminho principal segue para leste/oeste; o porto de cada
ilha fica ao norte. Os barcos e seus NPCs continuam disponíveis.

Em Vermilion, a saída fica ao sul pela água na parte leste da baía, perto das
colunas 33/34 do mapa. Nos portos das ilhas, use Surf pela lateral esquerda do
píer e siga para sul. Para desembarcar, volte pelo canal e alcance o píer.
Surf é necessário, mas insígnias e tickets não são exigidos para essas rotas.
Surfar não consome ticket. Surf/Waterfall, os ginásios e o catálogo anterior
continuam presentes. Não foram adicionados encontros com espécies novas.

**Hoenn e a segunda história de Emerald ainda não estão nesta ROM.**
Também faltam Dive, Whirlpool e o navio com ticket para Slateport. O inventário
e os requisitos desse porte estão em [mods/hoenn](../hoenn/README.md).
Esta entrega é a base marítima jogável, não a integração completa de Emerald.

Comece um jogo novo e use um save próprio. O patch usa a ROM original LeafGreen
USA v1.1 da raiz. [manifest.json](manifest.json) contém os hashes e a origem do motor;
[routes.json](routes.json) registra as conexões e os arquivos de origem modificados.

Passaram 21 verificações de Surf em mGBA: embarque, transições físicas entre
mapas, ida/volta e ausência de exigência de ticket/insígnias. O navegador foi
validado com Chromium e os pacotes locais EmulatorJS/mGBA 4.2.3; a captura mostra
o jogo respondendo aos controles. Testes adicionais verificam o catálogo,
a água na elevação correta e os NPCs/warps dos portos.

## Compilação

Prepare um checkout com [tools/regions](../../tools/regions/README.md), usando
`--prepare-only`, depois execute:

```sh
python3 tools/sea_routes/build.py --source .local/sea-routes-src
```

Depois da aplicação, esse checkout passa a ser específico desta versão.
O construtor da versão anterior recusa esse diretório para evitar misturar releases.
O build força a remontagem dos dados de mapas porque as dependências do motor
não detectam todas as alterações em arquivos `.bin`.

```sh
python3 -m unittest discover -s tools/sea_routes -v
LD_LIBRARY_PATH="$PWD/.local/mgba-build" python3 tools/sea_routes/validate_emulator.py --library .local/mgba-bridge.so
```

## Navegador e GitHub Pages

`web/` contém o player, os controles de teclado/toque e o emulador com versões
fixadas. As dependências ficam no próprio site; seus hashes, licença e a pequena
alteração que desativa a consulta opcional de atualizações estão em
`web/emulator/provenance.json`. Não é necessário um servidor de aplicação.

O workflow `pages.yml` prepara o site e a ROM e publica no GitHub Pages quando
estas alterações chegam à branch `main`. A ativação automática depende das
permissões de Pages do repositório; se a organização proibir essa configuração,
selecione GitHub Actions em Settings → Pages. A URL ainda depende desse deploy.

Para testar localmente:

```sh
python3 tools/sea_routes/serve.py
# Abra http://127.0.0.1:8765/
```

Os saves ficam no navegador, com opção de exportação pelo menu do emulador.
Uma ROM local também pode ser aberta; isso executa o arquivo selecionado e não
o conecta a outro jogo ou transfere sua equipe.
