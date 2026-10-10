# Pokémon Journey — World Alpha 1

Esta é a primeira versão jogável do mundo integrado **Kanto + Hoenn + Sevii**, com o estaleiro Lavender Port e as animações de barco. O jogo está em **inglês**.

## Como jogar

1. Baixe `Pokemon-Journey-World-Alpha-1.gba` na pasta `mods/hoenn/playable`. Use a opção **Download raw file** do GitHub.
2. Abra a ROM no **mGBA** atualizado, ou no player do projeto no navegador.
3. **Comece um Novo Jogo.** Não importe um save das versões antigas de LeafGreen ou de outra ROM.
4. Depois de escolher **New Game**, confirme seu personagem. Antes da chegada, aparece um menu com **HOENN, KANTO e SEVII ISLANDS**. Escolha a região e depois a cidade/ilha. Não é necessário apertar Select no título. Há 15 cidades de Hoenn, nove de Kanto e sete ilhas de Sevii.
5. Converse com todos os familiares para receber **Surf, Dive e Waterfall** e com o professor para obter o inicial e a Pokédex. Pallet e Littleroot conservam os respectivos episódios iniciais originais.

O player está publicado em https://brunotellesbt-sys.github.io/AiKalicaAiCrlBR/ por GitHub Actions. Ele usa o núcleo mGBA incluído no projeto, controles para teclado/celular e armazenamento de saves no navegador. O deploy publica a mesma ROM cujo hash é validado pelo player. Não há uma Release separada com assets.

No navegador: **setas** movem, **X** confirma (A), **Z** volta (B), **Enter** abre Start, **Shift** é Select. No celular, use os controles na tela. Ao definir o relógio de Hoenn, confirme com **Yes**.

Use **Save no menu do próprio jogo**. Exporte também o arquivo de save pelo menu do emulador. Saves do navegador ficam associados a esta versão; apagar os dados do site pode apagá-los. Save states são atalhos do emulador e não substituem esse backup.

## Incluído nesta alpha

- Menu explícito de três regiões e 31 opções de cidade inicial, família, professor, iniciais das duas regiões e National Dex.
- Treinadores fora dos ginásios seguem a média de nível da equipe, de cinco abaixo a dois acima, entre 1 e 100. Os ginásios preservam a escala pela ordem das insígnias da região e usam [times adaptados ao tamanho da equipe](ADAPTIVE-GYM-TEAMS.md), priorizando os Pokémon principais. Tate e Liza sempre lutam em dupla.
- Cercas aquáticas antigas abertas nas rotas costeiras, incluindo os setores antes isolados das Rotas 124/125; as pedras completas nas bordas sem conexão permanecem.
- Mar aberto entre Fuchsia, a costa das Rotas 14/13 e Lavender Port, com ponte a pé ao norte do cais.
- Mundo conectado por Surf, incluindo o mar atrás de Ever Grande, as Sevii e a costa oeste de Hoenn; Waterfall permite subir ao rio da Rota 114.
- Mapa integrado no menu **Start → MAP**, com posição real do jogador, mar uniforme e faixas retas de Surf; contorno de terra completado a oeste de Kanto e ao norte de Hoenn.
- Fly nesse mesmo mapa, incluindo Lavender Port e as sete cidades de Sevii após visita; cavernas novas são apenas marcadores, sem Fly.
- Lavender Port e a rede de 18 portos, sem oferecer o porto atual; todas as viagens da rede têm animação.
- Insígnias separadas e ginásios em ordem livre com escalonamento. As duas Ligas exigem as **16 insígnias**.
- Missões regionais obrigatórias e ligação Silph–Giovanni–Archie, com as travas nos ginásios combinadas anteriormente.
- Uma Mach Bike compartilhada entre regiões; passagens terrestres antigas de HM adaptadas. Apenas Surf, Dive e Waterfall permanecem HMs.
- Catálogo ampliado, tipo Fairy, Hidden Abilities e Ash-Greninja por Battle Bond após um nocaute. Golpes e learnsets revisados pela referência de Scarlet/Violet com as DLCs; [detalhes](BATTLE-DATABASE.md).
- Encontros distribuídos por família e estágios conforme a média do avanço regional; níveis relativos à média da equipe. Lendários/míticos ficam em locais especiais e exigem 16 insígnias.
- PWT Singles com seis Pokémon na Battle Frontier. Mega Evolution está implementada; a distribuição de Mega Stones permanece desativada conforme solicitado. Dynamax, Gigantamax e Z-Moves permanecem desativados.

A localização dos Pokémon está em `mods/hoenn/POKEMON-LOCATIONS.md` e nos documentos de habitats da pasta `mods/hoenn`.

## O que está validado e o que falta

A abertura das duas regiões passou desde a tela inicial, por controles normais, até o inicial e o primeiro combate, sem conceder insígnias ou aumentar atributos. Há verificações nativas das viagens, acessos, presentes e sistemas, além de testes do player. Os relatórios desta versão ficam em `mods/hoenn/playable-validation`.

As sequências das duas Ligas passaram pelos cinco adversários, Hall of Fame, créditos e Continue com save nativo. Esses testes usam equipes de nível 100, insígnias e cura entre batalhas como fixtures, sem alterar os adversários. A matriz dos líderes cobre 768 combinações de ordem e tamanho de equipe, além de 128 casos com ovos e 3.808 conjuntos de golpes. O aprendizado nativo foi exercitado para os 1.025 Pokémon base em cinco níveis, incluindo golpes de evolução e doze relações de tipo Fada.

**As duas campanhas completas, da abertura até os dois Hall of Fame, ainda não foram concluídas por controles normais na validação.** Balanceamento, eventos posteriores e acabamento podem precisar de correções. Esta é uma alpha para jogar e encontrar esses problemas; não é anunciada como a versão final.

Se encontrar um problema, guarde um save anterior ao evento e informe: cidade/mapa, último evento feito, insígnias de cada região e como reproduzir. Uma captura da tela ajuda.

## Integridade e reprodução

O pacote inclui `release.json` e `SHA256SUMS`. A ROM tem 32 MiB; confirme seu SHA-256 antes de usar. As 63 camadas de integração e seus hashes constam do manifesto. O pacote inclui o mapa integrado no menu MAP.

Para compilar e exportar a partir da fonte fixada, com a toolchain ARM já configurada:

```sh
python3 tools/hoenn/acquire_multiregion.py --source <nova-pasta>
python3 tools/hoenn/package_playable.py --source <nova-pasta> --build --output mods/hoenn/playable --archive <pacote.zip>
```

O exportador verifica os arquivos finais das camadas. Uma fonte preparada pode ser reutilizada; uma cadeia com camadas ausentes no meio ou hashes divergentes é recusada. Os assets e executáveis de desenvolvimento permanecem fora do pacote jogável.

As três novas ilhas e seus ramais estão incluídos nesta ROM: [Emerald Cay, Sunlit Isle e Tidewood Isle](REMOTE-ISLANDS.md). A grama das duas maiores contém oito famílias por ilha. A referência completa da Pokédex foi regenerada em `POKEMON-LOCATIONS.md` e `pokemon-locations.csv`.
