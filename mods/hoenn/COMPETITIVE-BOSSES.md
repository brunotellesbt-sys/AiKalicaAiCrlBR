# Batalhas competitivas e mapa real

Rivais, líderes dos 16 ginásios, Elite Four, campeões, chefes e administradores das equipes vilãs recebem EVs legais totalizando 510 (máximo 252 por atributo), natureza, habilidade compatível, item e quatro golpes de perfil competitivo. Nas versões Hard, os seis IVs são 31; nas versões Normal, os IVs originais são preservados. Treinadores comuns, inclusive os treinadores auxiliares dos ginásios, não recebem esse tratamento competitivo. A quantidade de Pokémon, os níveis por ordem regional e os formatos de batalha continuam sendo os já definidos; Tate e Liza permanecem uma batalha dupla.

Os perfis são uma cópia versionada da base pública `pkmn/smogon`, commit `76409f50659091d187cb36c6c6a3896bc3e45402`. São 611 perfis. OU da geração 9 tem prioridade, seguido por National Dex, OU da geração 8 e análises de singles/LC adequadas à espécie. Nem toda espécie tem uma análise OU. Na falta de perfil, o jogo seleciona um papel físico/especial, velocidade ou resistência a partir dos atributos da espécie, com STAB, cobertura e suporte. Os EVs de LC são convertidos para uma distribuição de campanha. Nas versões Hard, todos os IVs são 31, inclusive quando uma análise recomendaria zero.

TM, tutor e egg moves são permitidos desde níveis baixos quando a espécie pode aprendê-los. Golpes exclusivos de level-up ficam limitados ao nível atual. A seleção não copia golpes incompatíveis de uma evolução final para sua forma básica. Evoluções por nível abaixo do requisito são revertidas quando uma equipe original é reduzida de nível. Os principais Pokémon e as formas definidas para cada ordem de ginásio são preservados.

Para todos os treinadores, evoluções permanentes por pedra ou item carregado exigem um nível mínimo conforme a soma dos atributos base da evolução: abaixo de 500, nível 30; de 500 a 529, nível 35; a partir de 530, nível 40. Métodos alternativos da mesma evolução não contornam esse requisito. A cadeia inteira de pré-evoluções também é conferida, respeitando requisitos por nível maiores. Por exemplo, Ninetales exige nível 35 e Arcanine exige nível 40; abaixo disso, o adversário usa a pré-evolução correspondente. Esta regra não altera o uso de pedras pelo jogador e não se aplica às transformações temporárias de Mega Evolução.

A IA usa os recursos avançados disponíveis nesta versão do motor: avaliação de dano/KO, HP, escolhas e trocas inteligentes, previsão de movimentos/trocas, prevenção de ciclos de PP e conhecimento da equipe adversária. Isso aumenta a dificuldade desde o primeiro ginásio; não é garantia de uma jogada matematicamente ótima a cada turno. A alteração se aplica às batalhas de campanha, não às regras próprias da Battle Frontier/PWT.

Não foram adicionados Z-Moves, Dynamax, Gigantamax ou Terastallization. Mega Stones e Primal Orbs já presentes nas equipes originais compatíveis são preservados; estes perfis não liberam novas pedras para o jogador.

## Mapa e Pokédex

O desenho a oeste de Dewford foi realinhado à conexão existente: canal oeste → Dewford Coast → Dewford Gate → lado oeste da Rota 105. Ao norte, Rustboro Coast se conecta à Rota 115. Nenhum mapa jogável foi redesenhado para essa correção do atlas.

A opção AREA da Pokédex agora mostra Kanto, Hoenn e Sevii no mesmo mapa integrado. Pontos laranja piscantes indicam habitats realmente cadastrados na ROM e os locais dos encontros fixos nos santuários. Cavernas de Sevii usam sua própria sub-região. A existência de um habitat no mapa não dispensa as condições de progresso para encontrar a espécie: estágios evolutivos variam com o avanço, e os lendários/míticos continuam exigindo as 16 insígnias.

As validações nativas inspecionam as equipes geradas, os flags de IA de uma batalha real e os dois tipos de learnsets diretamente dos bytes compilados. A tela AREA é aberta, fechada e reaberta com controles no emulador. Os testes usam estados iniciais preparados; não representam uma pessoa jogando as duas campanhas inteiras do começo ao fim.
