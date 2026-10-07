# LeafGreen Journey + catálogo Unova

Use **[LeafGreen-Journey-Unova.gba](LeafGreen-Journey-Unova.gba)** para jogar esta versão.
O [patch BPS](LeafGreen-Journey-Unova.bps) deve ser aplicado à ROM original
`Pokemon - Leaf Green Version (U) (V1.1).gba` da raiz do repositório.

**Comece um jogo novo.** O motor ampliado muda o formato dos dados salvos e os IDs
de itens; saves da ROM original e das versões anteriores desta jornada não são
compatíveis. As versões anteriores continuam nas respectivas pastas.

## Conteúdo importado

| Conteúdo | Quantidade |
| --- | ---: |
| Espécies-base, de Bulbasaur a Genesect | 649 |
| Formas adicionais | 210 |
| Registros jogáveis no total | 859 |
| Formas Mega completas | 47 |
| Mega Stones utilizadas por essas formas | 46 |

Rayquaza usa Dragon Ascent para a Mega Evolução. As formas adicionais também
incluem variantes regionais, Unown, formas alternativas, Primais e Gigantamax
presentes no arquivo enviado. A inclusão dessas formas no catálogo não libera
os respectivos itens nem outras mecânicas durante a jornada.

Os seis atributos básicos, rendimentos de experiência/EVs, habilidades, crescimento,
gênero e listas de golpes disponíveis foram extraídos do arquivo enviado. Os
sprites de frente e costas e suas paletas normais também vêm desse arquivo.
O motor utiliza o primeiro quadro dos sprites importados para a exibição; os
demais quadros permanecem no pacote de dados. Ícones, paletas shiny, sons,
compatibilidade com TMs e regras de evolução são os equivalentes da expansão.
Há 32 registros sem lista de golpes no arquivo; eles usam a lista compatível da
expansão, identificada em `native_learnset_fallbacks` no inventário.

O tipo **Fada** funciona nas batalhas, com imunidade a Dragão e a tabela correta
de vantagens e resistências. Foram corrigidas 22 espécies-base e Mega Gardevoir/
Mega Mawile que ainda tinham tipagem antiga. As formas que já eram Fada mantêm
sua tipagem, inclusive as variantes regionais correspondentes.

As Mega Evoluções usam Mega Ring, a pedra correspondente e o botão **START** no
menu de golpes. Há uma Mega Evolução por treinador em cada batalha e a forma
normal é restaurada ao terminar. **Mega Ring e Mega Stones não são entregues nesta
versão.** Os testes injetam esses itens apenas na sessão temporária do emulador.

**Os novos Pokémon não foram colocados em grama, água, pesca, eventos de captura
ou presentes.** As listas de encontros continuam sendo as da jornada anterior,
com níveis pela média da equipe, fases por insígnias e exclusivos de FireRed.

## O que falta no arquivo enviado

Estão presentes as **649 de 649 espécies-base das gerações 1 a 5**. O arquivo não
contém as espécies-base de número **650 em diante**, embora contenha algumas formas
regionais e especiais posteriores de espécies mais antigas. **Mega Diancie** também
não está presente. A lista `missing_base_species` compara o catálogo com a expansão
utilizada, até o número 1025; ela não representa Pokémon importados nesta ROM.

Consulte [catalog.json](catalog.json) para os registros e as lacunas;
[donor-patch.json](donor-patch.json) contém a identificação do BPS e da ROM doadora.
O [BPS original enviado](donor/unova_emerald_2_0_3.bps) exige Emerald USA de 16 MiB
com CRC32 `1f1c08fb`. Ele foi aplicado a uma base reconstruída pelo código público
de `pret/pokeemerald`, com validação dos CRCs de origem, patch e resultado.

## Jornada preservada

- As 16 cidades/casas iniciais, família, presentes, inicial e visita do professor.
- Surf e Waterfall presentes, utilizáveis sem insígnias ao ensinar os golpes.
- Árvores, pedras e demais barreiras terrestres removidas; Snorlax permanece.
- Poké Flute após o primeiro ginásio, independentemente da identidade do líder.
- Ginásios em qualquer ordem, com 49 treinadores escalados pela ordem das insígnias.
- Blue no ginásio de Viridian e rival com aparência do personagem do sexo oposto.
- Giovanni permanece nos confrontos do Team Rocket; Liga exige oito insígnias.
- Travessias antecipadas entre as ilhas e Kanto.

## Código e validação

A base original de LeafGreen não suporta essas espécies, habilidades e formas.
Esta ROM usa a expansão aberta
[kerrymilan/roguemon-expansion](https://github.com/kerrymilan/roguemon-expansion/tree/7606f57650627704c9aad965a031fd3a454590e2),
fixada no commit `7606f57650627704c9aad965a031fd3a454590e2`, com os overlays desta
jornada e um catálogo restrito ao conteúdo importado. Os menus de depuração estão
desativados. As ferramentas de edição devem respeitar as tabelas desta expansão;
os offsets da ROM original não se aplicam a esta versão.

As instruções de reconstrução estão em [tools/unova](../../tools/unova/README.md).
[manifest.json](manifest.json) registra hashes, fonte, casas, encontros e alterações
de mapas. [validation/results.json](validation/results.json) registra os testes
no mGBA vinculados ao SHA-256 da ROM. As capturas na mesma pasta mostram a jornada,
os HMs, sprites importados e a Mega Evolução na interface de batalha.
