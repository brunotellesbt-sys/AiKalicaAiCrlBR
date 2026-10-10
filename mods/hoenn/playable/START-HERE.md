# Pokémon Journey — World Alpha 1

Esta é a primeira versão jogável do mundo integrado **Kanto + Hoenn + Sevii**, com o estaleiro Lavender Port e as animações de barco. O jogo está em **inglês**.

## Como jogar

1. Baixe `Pokemon-Journey-World-Alpha-1.gba` na pasta `mods/hoenn/playable` do PR #67. Use a opção **Download raw file** do GitHub.
2. Abra a ROM no **mGBA** atualizado, ou no player do projeto no navegador.
3. **Comece um Novo Jogo.** Não importe um save das versões antigas de LeafGreen ou de outra ROM.
4. O título começa em Hoenn. Para começar em Kanto, pressione **Select na tela de título**, antes de entrar no menu. No navegador, Select é **Shift**. A escolha da cidade aparece antes da chegada de caminhão ou barco.
5. Converse com todos os familiares para receber **Surf, Dive e Waterfall** e com o professor para obter o inicial e a Pokédex. Pallet e Littleroot conservam os respectivos episódios iniciais originais.

A configuração do player está preparada para GitHub Pages, mas a ativação do site foi recusada pela API do GitHub (403) nesta sessão. O envio de assets para Releases também foi recusado; não há uma Release publicada. A ROM está disponível diretamente no repositório pelo PR #67.

No navegador: **setas** movem, **X** confirma (A), **Z** volta (B), **Enter** abre Start, **Shift** é Select. No celular, use os controles na tela. Ao definir o relógio de Hoenn, confirme com **Yes**.

Use **Save no menu do próprio jogo**. Exporte também o arquivo de save pelo menu do emulador. Saves do navegador ficam associados a esta versão; apagar os dados do site pode apagá-los. Save states são atalhos do emulador e não substituem esse backup.

## Incluído nesta alpha

- 31 opções de cidade inicial, família, professor, iniciais das duas regiões e National Dex.
- Mar aberto entre Fuchsia, a costa das Rotas 14/13 e Lavender Port, com ponte a pé ao norte do cais.
- Mundo conectado por Surf, incluindo o mar atrás de Ever Grande, as Sevii e a costa oeste de Hoenn; Waterfall permite subir ao rio da Rota 114.
- Mapa integrado no menu **Start → MAP**, com posição real do jogador, mar uniforme e faixas retas de Surf; contorno de terra completado a oeste de Kanto e ao norte de Hoenn.
- Fly nesse mesmo mapa, incluindo Lavender Port e as sete cidades de Sevii após visita; cavernas novas são apenas marcadores, sem Fly.
- Lavender Port e a rede de 18 portos, sem oferecer o porto atual; todas as viagens da rede têm animação.
- Insígnias separadas e ginásios em ordem livre com escalonamento. As duas Ligas exigem as **16 insígnias**.
- Missões regionais obrigatórias e ligação Silph–Giovanni–Archie, com as travas nos ginásios combinadas anteriormente.
- Uma Mach Bike compartilhada entre regiões; passagens terrestres antigas de HM adaptadas. Apenas Surf, Dive e Waterfall permanecem HMs.
- Catálogo ampliado, tipo Fairy, Hidden Abilities e Ash-Greninja por Battle Bond após um nocaute.
- Encontros distribuídos por família e estágios conforme a média do avanço regional; níveis relativos à média da equipe. Lendários/míticos ficam em locais especiais e exigem 16 insígnias.
- PWT Singles com seis Pokémon na Battle Frontier. Mega Evolution está implementada; a distribuição de Mega Stones permanece desativada conforme solicitado. Dynamax, Gigantamax e Z-Moves permanecem desativados.

A localização dos Pokémon está em `mods/hoenn/POKEMON-LOCATIONS.md` e nos documentos de habitats da pasta `mods/hoenn`.

## O que está validado e o que falta

A abertura das duas regiões passou desde a tela inicial, por controles normais, até o inicial e o primeiro combate, sem conceder insígnias ou aumentar atributos. Há verificações nativas das viagens, acessos, presentes e sistemas, além de testes do player. Os relatórios desta versão ficam em `mods/hoenn/playable-validation`.

**As duas campanhas completas, da abertura até os dois Hall of Fame, ainda não foram concluídas por controles normais na validação.** Balanceamento, eventos posteriores e acabamento podem precisar de correções. Esta é uma alpha para jogar e encontrar esses problemas; não é anunciada como a versão final.

Se encontrar um problema, guarde um save anterior ao evento e informe: cidade/mapa, último evento feito, insígnias de cada região e como reproduzir. Uma captura da tela ajuda.

## Integridade e reprodução

O pacote inclui `release.json` e `SHA256SUMS`. A ROM tem 32 MiB; confirme seu SHA-256 antes de usar. As 58 camadas de integração e seus hashes constam do manifesto. O pacote inclui o mapa integrado no menu MAP.

Para compilar e exportar a partir da fonte fixada, com a toolchain ARM já configurada:

```sh
python3 tools/hoenn/acquire_multiregion.py --source <nova-pasta>
python3 tools/hoenn/package_playable.py --source <nova-pasta> --build --output mods/hoenn/playable --archive <pacote.zip>
```

O exportador verifica os arquivos finais das camadas. Uma fonte preparada pode ser reutilizada; uma cadeia com camadas ausentes no meio ou hashes divergentes é recusada. Os assets e executáveis de desenvolvimento permanecem fora do pacote jogável.
