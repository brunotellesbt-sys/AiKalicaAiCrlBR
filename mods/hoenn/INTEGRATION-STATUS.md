# Atualização costeira e níveis dinâmicos

Atualização posterior: as quatro edições incluem o [porto de Sootopolis](../../docs/porto-sootopolis.md),
com ponte prolongada e ligada à terra, terminal, capitão interno da rede geral e submarino 64×64.
Os testes novos de caminhada, portas e viagens passaram em cada edição e também no layout
da crise. A camada 141 reproduziu seus 21 arquivos. Os resultados costeiros abaixo pertencem
à publicação anterior, preservada com seus hashes; não foram repetidos integralmente nesta revisão.

As quatro ROMs atuais incluem as casas de Pallet/Fuchsia/Sevii, pontes e embarcações revisadas, navios maiores de Hoenn, os portos compactos, a sala de Rotom com visual de Lavender, bordas completas de areia, níveis dinâmicos e entradas de Eren/Luffy fora da câmera, com orientação estável e diálogos maiores. O mapa marítimo inclui os corredores originais de Surf e as conexões novas, desenhados em segmentos ortogonais; Seafoam e as 14 cavernas novas usam acessos reais. O zoom detalhado de 448×224 funciona no menu e na AREA, com locais especiais corrigidos. A Diglett’s Cave tem dois combates opcionais Galactic e um grunt de levantamento. As evidências novas ficam em `coastal-update-validation/`: 140 camadas, 1.483 arquivos reproduzidos, 21 portos, 343 mapas auditados estruturalmente e 57 costas geradas. Foram observados dois pontos válidos de entrada dos rivais em cada uma das 12 rotas. A campanha inteira não foi jogada do começo aos créditos nesta entrega.

O atlas agora une os mares contínuos sem desenhar divisões entre arquivos como rotas, usa grandes áreas retangulares e oculta o protótipo desconectado. O GPS compilado cobre 408.618 tiles, com deslocamento máximo de dois pixels entre vizinhos e igualdade nas bordas compartilhadas. Há pontos próprios para 145 andares de cavernas originais. Oito viagens por controles atravessam os 56 mares gerados ativos e os corredores nativos solicitados, totalizando 7.468 tiles e 152 transições. A equipe de nível 100, Rare Candies e repels são recursos do teste. Veja [navegação, imagens e pendências finais](../../docs/navegacao-e-pendencias-finais.md).

Resultados de PWT e mecânicas das seções abaixo são históricos do PR #79. Seus bytes e hashes originais foram preservados em `validation-baselines/pr79/`; nenhum torneio foi repetido nesta atualização. Consulte [imagens e detalhes](../../docs/atualizacao-costeira.md).

---

Registro histórico do PR #79, de 14/10/2026: build de 116 camadas, PWT e encontros especiais. As seções abaixo descrevem essa validação anterior e seus limites. Veja [balanceamento](../../docs/pwt-balanceamento.md) e [encontros especiais](../../docs/encontros-especiais-e-formas.md).

# Estado da integração

A entrega contém quatro ROMs GBA: Gen 1–4 Normal/Hard e Gen 1–9 Normal/Hard. Todas usam a mesma integração de Kanto, Hoenn, Sevii e do capítulo Galactic. As diferenças binárias permitidas são somente o registro de geração/IVs, o título e seu checksum. O manifesto verifica os hashes das ROMs e dos relatórios nativos.

## Implementado nesta entrega

- Ecologia por família e por geração, sem duplicação entre locais; filtros aquáticos, probabilidades de raridade e AREA da Pokédex integrada.
- Missões obrigatórias separadas por região e requisito de 16 insígnias mais capítulo Galactic para ambas as Ligas.
- Doze encontros obrigatórios de Eren/Luffy, contadores independentes e três celas de energia na prisão Galactic. As grades abrem no desfecho; Dialga, Palkia e Giratina só ficam disponíveis nas cavernas depois da missão.
- Presença de Steven conforme sua etapa e retirada de Giovanni da Silph após sua derrota, antes de aparecer como aliado em Hoenn.
- Escolha independente de Red, Leaf, Brendan ou May; confirmação da cidade e retorno à região. Cartão com oito insígnias de cada região em páginas alternadas por L/R/Select.
- Fornecedores de Mega Stones e itens de evolução, tutores de condições regionais e Dragon Ascent, e alternativas por nível para métodos especiais.
- Builds competitivas para oponentes importantes. Normal usa IVs aleatórios; Hard usa 31. Ambas usam EVs com orçamento 510, nature, habilidade e golpes legais conforme o nível.
- Bag com espaço para todos os tipos atuais de item, menus com índices de 16 bits, pilhas de até 999 e TMs reutilizáveis. Exige save novo.
- Somente Surf, Dive, Waterfall e Fly são HMs; os obstáculos terrestres foram removidos e os túneis são iluminados.
- Seleção das quatro edições no player estático de GitHub Pages, com verificação do download e saves separados pelo nome da edição.
- Índices em `docs/` e DOCX das 768 equipes geradas para os 16 líderes, ordens e quatro edições.

- PWT com torneios por geração, Copa global, líderes compartilhados separados, 162 retratos e conjuntos de caminhada, arena própria e builds temporárias com restauração integral da equipe.

## Escopo desta atualização

Esta atualização valida o PWT e os problemas de Disable, Encore, Torment e PP solicitados em seguida. O manifesto declara `validation_scope: pwt-update`; `validated` confirma esse escopo e a integridade das quatro ROMs, sem declarar uma validação completa das campanhas. Os relatórios adicionais concluídos antes dessa mudança de escopo permanecem identificados pela ROM testada. Uma tentativa de replay da Liga de Hoenn terminou em derrota da equipe de teste contra Phoebe e não foi usada como aprovação; ela não foi repetida após o pedido de limitar a validação ao PWT.

## O que as evidências comprovam

Os relatórios atuais em `versions/evidence/` identificam o alvo exato para PWT e regressões de golpes. Os relatórios históricos, mantidos nos diretórios de cada módulo e identificados por sua ROM, usam mGBA e incluem equipes dos ginásios, limites de geração, habitats aquáticos, interfaces de início/mapa/Pokédex/cartão, transporte, missões, capítulo Galactic, Ligas, Mega/reversão, atributos e save/Continue. A reprodução compara os arquivos finais das 109 camadas com uma árvore limpa proveniente dos 30.038 arquivos verificados do upstream.

As batalhas de missão usam deslocamento/progresso anterior preparados e, em alguns testes, atributos do jogador aumentados na memória do emulador. Os adversários, resultados e flags de vitória são nativos. Esses aumentos não alteram a ROM nem seus base stats. As equipes dos ginásios no DOCX são extrações do gerador nativo, sem esses aumentos.

A auditoria de habilidades e itens verifica registros, slots e referências válidas. Os testes específicos de Hidden Abilities, herança e Battle Bond exercitam efeitos reais. Isso não equivale a testar individualmente todas as interações possíveis das 318 habilidades e dos 870 itens.

Além dos alvos e requisitos de evolução, foram executadas pelos menus reais as animações de Pikachu → Raichu/Raichu de Alola, Kadabra → Alakazam, Onix → Steelix, Pawmo → Pawmot e Gimmighoul → Gholdengo. Esses cenários verificam consumo da pedra ou Rare Candy, consumo do Metal Coat carregado, nível resultante e preservação no save. Uma única TM Thunderbolt foi ensinada a dois Pokémon sem consumo, e os golpes foram preservados após salvar/recarregar. Os Pokémon, itens e local iniciais desses cenários são preparados; o uso pelo menu e as animações não são simulados.

Os trechos iniciais de Kanto e Hoenn também foram percorridos desde New Game somente com controles, sem escrever na RAM, forçar resultados ou aumentar atributos. Em Kanto, o tutorial do rival permite vitória ou derrota, como no original; o teste exige sua conclusão e a saída normal do laboratório. Em Hoenn, o resgate de Birch termina com uma vitória real. Esses relatórios cobrem a abertura, não a campanha completa.

## Limites restantes

A suíte de [interações de batalha](../../docs/interacoes-de-batalha.md) aprovou 684 cenários por edição (2.736 verificações). Ela corrigiu a previsão da IA para Spikes/Toxic Spikes com Heavy-Duty Boots ativas e conferiu o efeito de Magic Room/Klutz. Os casos incluem Trick Room, imunidades, dano, itens, terrenos, PP e efeitos em duplas. A cobertura não é exaustiva; animações e consumo dos itens não são reproduzidos nessa suíte.

Não foi feita uma campanha humana contínua desde New Game até os créditos nas quatro edições. As Ligas foram vencidas e os saves retomados com progresso anterior preparado. As missões e as interfaces possuem verificações próprias, mas isso não comprova todas as combinações de ordem, diálogos e balanceamento em uma campanha completa. Relate a edição, o local e um save ao encontrar um problema.

Saves antigos não são compatíveis com a Bag ampliada. A ROM mantém o formato histórico de metadados Game Freak; seu campo de um byte para o tamanho do bolso de itens é limitado a 255 para ferramentas externas. O motor e a Bag usam a capacidade real de 620; um editor externo deve conhecer este formato de save.

A alpha anterior de 64 camadas permanece preservada em `playable/`, com suas próprias evidências. Seus relatórios não são apresentados como testes das novas ROMs.

O PWT atual passou por inspeção das 446 equipes elegíveis nas quatro edições, instanciação das 162 identidades na arena e oito torneios Gen 1–4 completos (57 batalhas) e torneios completos nas gerações 6 e 9. Foram aprovados 65 cenários de histórico, restrições e PP, mais cinco de Encore; a auditoria de atributos atual conferiu as 91 Megas da referência, incluindo Mega Dimension. A apresentação é adaptada à GBA. A auditoria de todos os times canônicos de personagens modernos ainda está pendente; veja o documento do PWT.
