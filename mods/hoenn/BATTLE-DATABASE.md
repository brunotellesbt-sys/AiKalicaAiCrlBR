# Golpes e learnsets de Scarlet/Violet

A referência escolhida é Scarlet/Violet com as DLCs. Espécies ausentes usam o último conjunto de golpes por nível disponível na base de referência. A revisão cobre os 1.025 Pokémon da National Dex, além das formas reconhecidas pela referência. Formas transformadas, de fantasia e Totem que compartilham a tabela da espécie base continuam usando essa tabela; golpes exclusivos de evento não são convertidos em aprendizado por nível.

A fonte é [Pokémon Showdown, revisão 942cda7](https://github.com/smogon/pokemon-showdown/tree/942cda71d14bf0618bd57991708a2e2734b6daba/data). Os hashes Git dos arquivos `learnsets.ts`, `pokedex.ts` e `moves.ts` estão no JSON de referência. O importador confere os blobs antes de decodificá-los; a referência normalizada tem SHA-256 `4558fa7b1b41d2f259506ea855e63341bbe2ee83f5748f7fd4609e5ab83a8b75`.

Foram atualizadas 100 tabelas nativas de aprendizado. A configuração agora fixa geração 9 para os learnsets e atributos dos golpes, evitando que uma atualização futura de `GEN_LATEST` mude a referência silenciosamente. Os PP corrigidos são:

| Golpe | PP anterior | PP atual |
|---|---:|---:|
| Mat Block | 15 | 10 |
| Psychic Fangs | 15 | 10 |
| Victory Dance | 20 | 10 |
| Bitter Malice | 15 | 10 |
| Lunar Blessing | 10 | 5 |
| Take Heart | 10 | 15 |

A auditoria lê os dados **compilados na ROM**, usando os offsets produzidos pela mesma toolchain ARM. Ela compara tipos, categoria, poder, precisão, PP, prioridade e pares nível/golpe. Na ROM nova, 1.395 espécies/formas e 847 golpes correspondem à referência, sem diferenças nos campos auditados. São 89 espécies/formas do tipo Fada nessa comparação. Sliggoo e Goodra de Hisui também passam a exibir Aço/Dragão na ordem oficial; a combinação de tipos já era a mesma.

Os golpes de dano fixo, poder variável e KO direto usam sentinelas ou coeficientes internos do motor. Esses números não são substituídos por zero: a referência registra separadamente o poder oficial e sua representação interna. Os efeitos completos de todos os golpes não são certificados apenas por essa comparação de atributos.

As escolhas específicas deste projeto permanecem: **Cut é Grama**, **Strength é Pedra**, e **Battle Bond usa a transformação clássica após um KO**. Surf, Dive e Waterfall continuam sendo os únicos HMs. Mega Evolução permanece; Dynamax, Gigantamax e Z-Moves não são ativados.

[Learnsets dos 1.025 Pokémon por nível, em CSV](level-up-learnsets.csv). Nível 0 indica golpe de evolução. O documento de localização continua em [POKEMON-LOCATIONS.md](POKEMON-LOCATIONS.md).

A ROM resultante é `031e77443df329f04eeb923b50efc1d695a15deefa6d22c2dbe5c474f7995cd7`. As evidências nativas desta versão ficam em `playable-validation`; testes de estado, equipe e viagem usam fixtures descritas nos relatórios. Uma sequência de Liga com essas fixtures não equivale a completar toda a campanha desde um Novo Jogo.

A revisão também corrigiu o habitat de Five Island: uma área de oito tiles de grama torna acessíveis Magnemite/Magneton/Magnezone, Blitzle/Zebstrika, Heatmor e Sizzlipede/Centiskorch. A auditoria dos habitats ativos agora encontra os 920 Pokémon base não especiais. Lendários e míticos permanecem nos locais próprios, com exigência de 16 insígnias.
