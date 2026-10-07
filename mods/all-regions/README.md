# LeafGreen Journey — todas as regiões

A ROM atual é **[LeafGreen-Journey-AllRegions.gba](LeafGreen-Journey-AllRegions.gba)**.
O [patch BPS](LeafGreen-Journey-AllRegions.bps) usa a ROM original de LeafGreen USA
revisão 1 da raiz do repositório. Comece um jogo novo nesta ROM e use um nome de
save próprio; saves da versão original não são compatíveis com o motor ampliado.

| Catálogo | Total |
| --- | ---: |
| Espécies-base, Bulbasaur a Pecharunt | 1.025 |
| Formas adicionais | 457 |
| Registros jogáveis | 1.482 |
| Mega Evoluções | 48 |
| Mega Stones correspondentes | 47 |

Rayquaza usa Dragon Ascent. Mega Diancie e Diancite completam as Megas clássicas;
as Megas de Pokémon Legends: Z-A não estão incluídas.

**Dynamax, Gigantamax e Z-Moves estão desativados**, para jogador e adversários.
As seis formas Gigantamax da versão anterior foram retiradas deste catálogo.
Eternamax também não foi importado. Os novos arquivos não importam sistemas de
batalha dos jogos doadores. A única transformação selecionável no menu de golpes
é Mega Evolução; Terastalização e Ultra Burst também não são ativáveis.
As formas naturais/de habilidade, como Aegislash, Wishiwashi, Palafin e Terapagos,
usam as regras da expansão, com referências limitadas às formas presentes.

**Os novos Pokémon continuam fora da grama, água, pesca, capturas e presentes.**
Mega Ring e Mega Stones continuam sem distribuição. Encontros, níveis dinâmicos,
casas iniciais, família, professor, Surf/Waterfall, ferries, ginásios e Liga
mantêm as regras da jornada anterior.

## Origem dos dados

Os quatro arquivos enviados foram identificados por SHA-256 e auditados por
suas tabelas reais. X/Y e Scarlet/Violet reutilizam IDs de espécies antigas;
os registros foram remapeados para IDs próprios, preservando os Pokémon antigos.
Sun Sky e Sword/Shield possuem tabelas ampliadas. Personagens de outros universos,
formas não oficiais, placeholders e os slots Gigantamax não foram adicionados.

A preferência entre duplicatas é Unova já importado, Sword/Shield, Sun Sky,
Scarlet/Violet e X/Y. Há 853 registros preservados de Unova, 348 de Sword/Shield,
80 de Scarlet/Violet e 201 complementados pela expansão aberta. Sun Sky e X/Y
foram auditados, mas suas espécies válidas já possuem dados nas fontes preferidas.

Para as novas importações, os **seis atributos básicos, sprites de frente/costas
e paletas normais** vêm das ROMs enviadas. Tipagens, habilidades, golpes,
evoluções, ícones, cries e paletas shiny usam os equivalentes canônicos da expansão;
isso evita herdar as habilidades e regras dos Pokémon substituídos pelos hacks.
Os atributos modificados dos hacks são preservados e identificados no catálogo.
O primeiro quadro dos sprites importados é exibido; os outros quadros ficam no pacote.

Os arquivos enviados **não contêm 47 espécies-base** de Hisui/Paldea. Elas foram
completadas com dados e sprites da mesma expansão pública já utilizada no projeto,
fixada no commit `7606f57650627704c9aad965a031fd3a454590e2` de
[kerrymilan/roguemon-expansion](https://github.com/kerrymilan/roguemon-expansion/tree/7606f57650627704c9aad965a031fd3a454590e2).
O complemento inclui mais 154 formas alternativas e cosméticas, mantendo as referências do motor válidas.

[donor-inventory.json](donor-inventory.json) registra os arquivos, hashes, slots,
nomes e a lista exata de lacunas nos uploads. [catalog.json](catalog.json) informa
a origem de cada registro; `native_graphics` identifica os complementos da expansão.
Nenhuma espécie-base de número 1 a 1025 ficou ausente da ROM resultante.
O sprite de Terapagos do arquivo Scarlet corresponde à forma Terastal; ele foi
associado a essa forma, enquanto a forma normal usa o sprite da expansão.

## Reconstrução e validação

Leia [tools/regions](../../tools/regions/README.md). O inventário também contém
os endereços de origem para conferir os dados diretamente nos arquivos enviados.
O ZIP extraído é determinístico e não copia código de máquina dos jogos doadores.

[manifest.json](manifest.json) registra os hashes da ROM/BPS e dos overlays.
[validation/results.json](validation/results.json) vincula os testes funcionais
no mGBA ao hash da ROM. As capturas mostram os iniciais das regiões posteriores,
Mega Diancie, Terapagos e os complementos. Há testes de integridade para todas
as espécies e referências de evoluções/formas, além das regras anteriores da jornada.

A versão final passou por **2.202 verificações no mGBA e 33 testes automatizados**.
