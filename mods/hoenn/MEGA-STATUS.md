# Mega Evoluções: auditoria da candidata

Há **97 formas Mega habilitadas**, todas com ligação de transformação e
referências de frente, costas e paletas presentes na ROM compilada.

Mega Garchomp Z tinha somente o ícone na origem. A camada `mega-art` acrescenta
as quatro imagens/paletas de batalha de uma revisão fixada de
[rh-hideout/pokeemerald-expansion](https://github.com/rh-hideout/pokeemerald-expansion/tree/6057b187f946094d614e9c34bc12731ea6a5b7bb/graphics/pokemon/garchomp/mega_z),
com hashes e créditos em [assets/mega-garchomp-z](assets/mega-garchomp-z/README.md).
Os atributos e a mecânica já existentes da forma são preservados.

Os relatórios `mega-validation` identificam a nova candidata pelo SHA-256
`b83768fd15b61e30905de4996e8f67cc7f8edaffe65c6904dc2de7dee857f283`.
`base-catalog.json` preserva o diagnóstico anterior; `reproduction.json`
comprova replay determinístico e idempotente a partir da candidata de habilidades.
Os resultados antigos de mapas e habilidades mantêm seus próprios hashes.

## Verificações executadas

- Cinco batalhas reais com acionamento por Start: Charizard X/Y, Rayquaza,
  Greninja e Garchomp Z. Transformação, imagem no menu após a animação e
  retorno à espécie original ao terminar foram observados.
- Duas batalhas negativas: sem Mega Ring e com pedra incompatível.
- Troca e desmaio de uma Mega: tentar transformar um segundo Pokémon
  continua bloqueado na mesma batalha.
- Ash-Greninja mantém a forma ao sair e voltar. Após uma batalha com desmaio,
  retorna à espécie original, preservando o slot oculto.
- O descompressor ARM reproduziu os pixels de **3.323 imagens de batalha**
  de **1.571 espécies/formas**, incluindo variantes femininas e todas as Megas.
  Foram conferidos os limites dos buffers. Isso não certifica todas as animações.
- As **3.154 paletas normais, shiny e variantes femininas** foram carregadas
  pela rotina ARM e comparadas à compilação. Todos os índices de cores dos
  sprites cabem nas respectivas paletas; as cores adjacentes foram preservadas.
- Decisões nativas de missões: **3.840 casos**, cobrindo todos os 256 conjuntos
  de insígnias em 15 situações, mais 36 verificações de permissão de chefes.

Mega Stones e Mega Ring continuam sem nova distribuição nos eventos. Os itens
foram adicionados somente às equipes dos testes. Batalhas duplas, efeitos de
habilidades específicas e campanhas completas permanecem pendentes.

## Inventário de formas e requisitos

| Espécie | Forma | Requisito nativo | Referências de sprites/paletas |
|---|---|---|---|
| SPECIES_VENUSAUR | SPECIES_VENUSAUR_MEGA | ITEM_VENUSAURITE | Presentes; nem todas renderizadas |
| SPECIES_CHARIZARD | SPECIES_CHARIZARD_MEGA_X | ITEM_CHARIZARDITE_X | Presentes; nem todas renderizadas |
| SPECIES_CHARIZARD | SPECIES_CHARIZARD_MEGA_Y | ITEM_CHARIZARDITE_Y | Presentes; nem todas renderizadas |
| SPECIES_BLASTOISE | SPECIES_BLASTOISE_MEGA | ITEM_BLASTOISINITE | Presentes; nem todas renderizadas |
| SPECIES_BEEDRILL | SPECIES_BEEDRILL_MEGA | ITEM_BEEDRILLITE | Presentes; nem todas renderizadas |
| SPECIES_PIDGEOT | SPECIES_PIDGEOT_MEGA | ITEM_PIDGEOTITE | Presentes; nem todas renderizadas |
| SPECIES_ALAKAZAM | SPECIES_ALAKAZAM_MEGA | ITEM_ALAKAZITE | Presentes; nem todas renderizadas |
| SPECIES_SLOWBRO | SPECIES_SLOWBRO_MEGA | ITEM_SLOWBRONITE | Presentes; nem todas renderizadas |
| SPECIES_GENGAR | SPECIES_GENGAR_MEGA | ITEM_GENGARITE | Presentes; nem todas renderizadas |
| SPECIES_KANGASKHAN | SPECIES_KANGASKHAN_MEGA | ITEM_KANGASKHANITE | Presentes; nem todas renderizadas |
| SPECIES_PINSIR | SPECIES_PINSIR_MEGA | ITEM_PINSIRITE | Presentes; nem todas renderizadas |
| SPECIES_GYARADOS | SPECIES_GYARADOS_MEGA | ITEM_GYARADOSITE | Presentes; nem todas renderizadas |
| SPECIES_AERODACTYL | SPECIES_AERODACTYL_MEGA | ITEM_AERODACTYLITE | Presentes; nem todas renderizadas |
| SPECIES_MEWTWO | SPECIES_MEWTWO_MEGA_X | ITEM_MEWTWONITE_X | Presentes; nem todas renderizadas |
| SPECIES_MEWTWO | SPECIES_MEWTWO_MEGA_Y | ITEM_MEWTWONITE_Y | Presentes; nem todas renderizadas |
| SPECIES_AMPHAROS | SPECIES_AMPHAROS_MEGA | ITEM_AMPHAROSITE | Presentes; nem todas renderizadas |
| SPECIES_STEELIX | SPECIES_STEELIX_MEGA | ITEM_STEELIXITE | Presentes; nem todas renderizadas |
| SPECIES_SCIZOR | SPECIES_SCIZOR_MEGA | ITEM_SCIZORITE | Presentes; nem todas renderizadas |
| SPECIES_HERACROSS | SPECIES_HERACROSS_MEGA | ITEM_HERACRONITE | Presentes; nem todas renderizadas |
| SPECIES_HOUNDOOM | SPECIES_HOUNDOOM_MEGA | ITEM_HOUNDOOMINITE | Presentes; nem todas renderizadas |
| SPECIES_TYRANITAR | SPECIES_TYRANITAR_MEGA | ITEM_TYRANITARITE | Presentes; nem todas renderizadas |
| SPECIES_SCEPTILE | SPECIES_SCEPTILE_MEGA | ITEM_SCEPTILITE | Presentes; nem todas renderizadas |
| SPECIES_BLAZIKEN | SPECIES_BLAZIKEN_MEGA | ITEM_BLAZIKENITE | Presentes; nem todas renderizadas |
| SPECIES_SWAMPERT | SPECIES_SWAMPERT_MEGA | ITEM_SWAMPERTITE | Presentes; nem todas renderizadas |
| SPECIES_GARDEVOIR | SPECIES_GARDEVOIR_MEGA | ITEM_GARDEVOIRITE | Presentes; nem todas renderizadas |
| SPECIES_SABLEYE | SPECIES_SABLEYE_MEGA | ITEM_SABLENITE | Presentes; nem todas renderizadas |
| SPECIES_MAWILE | SPECIES_MAWILE_MEGA | ITEM_MAWILITE | Presentes; nem todas renderizadas |
| SPECIES_AGGRON | SPECIES_AGGRON_MEGA | ITEM_AGGRONITE | Presentes; nem todas renderizadas |
| SPECIES_MEDICHAM | SPECIES_MEDICHAM_MEGA | ITEM_MEDICHAMITE | Presentes; nem todas renderizadas |
| SPECIES_MANECTRIC | SPECIES_MANECTRIC_MEGA | ITEM_MANECTITE | Presentes; nem todas renderizadas |
| SPECIES_SHARPEDO | SPECIES_SHARPEDO_MEGA | ITEM_SHARPEDONITE | Presentes; nem todas renderizadas |
| SPECIES_CAMERUPT | SPECIES_CAMERUPT_MEGA | ITEM_CAMERUPTITE | Presentes; nem todas renderizadas |
| SPECIES_ALTARIA | SPECIES_ALTARIA_MEGA | ITEM_ALTARIANITE | Presentes; nem todas renderizadas |
| SPECIES_BANETTE | SPECIES_BANETTE_MEGA | ITEM_BANETTITE | Presentes; nem todas renderizadas |
| SPECIES_ABSOL | SPECIES_ABSOL_MEGA | ITEM_ABSOLITE | Presentes; nem todas renderizadas |
| SPECIES_GLALIE | SPECIES_GLALIE_MEGA | ITEM_GLALITITE | Presentes; nem todas renderizadas |
| SPECIES_SALAMENCE | SPECIES_SALAMENCE_MEGA | ITEM_SALAMENCITE | Presentes; nem todas renderizadas |
| SPECIES_METAGROSS | SPECIES_METAGROSS_MEGA | ITEM_METAGROSSITE | Presentes; nem todas renderizadas |
| SPECIES_LATIAS | SPECIES_LATIAS_MEGA | ITEM_LATIASITE | Presentes; nem todas renderizadas |
| SPECIES_LATIOS | SPECIES_LATIOS_MEGA | ITEM_LATIOSITE | Presentes; nem todas renderizadas |
| SPECIES_LOPUNNY | SPECIES_LOPUNNY_MEGA | ITEM_LOPUNNITE | Presentes; nem todas renderizadas |
| SPECIES_GARCHOMP | SPECIES_GARCHOMP_MEGA | ITEM_GARCHOMPITE | Presentes; nem todas renderizadas |
| SPECIES_LUCARIO | SPECIES_LUCARIO_MEGA | ITEM_LUCARIONITE | Presentes; nem todas renderizadas |
| SPECIES_ABOMASNOW | SPECIES_ABOMASNOW_MEGA | ITEM_ABOMASITE | Presentes; nem todas renderizadas |
| SPECIES_GALLADE | SPECIES_GALLADE_MEGA | ITEM_GALLADITE | Presentes; nem todas renderizadas |
| SPECIES_AUDINO | SPECIES_AUDINO_MEGA | ITEM_AUDINITE | Presentes; nem todas renderizadas |
| SPECIES_DIANCIE | SPECIES_DIANCIE_MEGA | ITEM_DIANCITE | Presentes; nem todas renderizadas |
| SPECIES_RAYQUAZA | SPECIES_RAYQUAZA_MEGA | move:620 | Presentes; nem todas renderizadas |
| SPECIES_CLEFABLE | SPECIES_CLEFABLE_MEGA | ITEM_CLEFABLITE | Presentes; nem todas renderizadas |
| SPECIES_VICTREEBEL | SPECIES_VICTREEBEL_MEGA | ITEM_VICTREEBELITE | Presentes; nem todas renderizadas |
| SPECIES_STARMIE | SPECIES_STARMIE_MEGA | ITEM_STARMINITE | Presentes; nem todas renderizadas |
| SPECIES_DRAGONITE | SPECIES_DRAGONITE_MEGA | ITEM_DRAGONINITE | Presentes; nem todas renderizadas |
| SPECIES_MEGANIUM | SPECIES_MEGANIUM_MEGA | ITEM_MEGANIUMITE | Presentes; nem todas renderizadas |
| SPECIES_FERALIGATR | SPECIES_FERALIGATR_MEGA | ITEM_FERALIGITE | Presentes; nem todas renderizadas |
| SPECIES_SKARMORY | SPECIES_SKARMORY_MEGA | ITEM_SKARMORITE | Presentes; nem todas renderizadas |
| SPECIES_FROSLASS | SPECIES_FROSLASS_MEGA | ITEM_FROSLASSITE | Presentes; nem todas renderizadas |
| SPECIES_EMBOAR | SPECIES_EMBOAR_MEGA | ITEM_EMBOARITE | Presentes; nem todas renderizadas |
| SPECIES_EXCADRILL | SPECIES_EXCADRILL_MEGA | ITEM_EXCADRITE | Presentes; nem todas renderizadas |
| SPECIES_SCOLIPEDE | SPECIES_SCOLIPEDE_MEGA | ITEM_SCOLIPITE | Presentes; nem todas renderizadas |
| SPECIES_SCRAFTY | SPECIES_SCRAFTY_MEGA | ITEM_SCRAFTINITE | Presentes; nem todas renderizadas |
| SPECIES_EELEKTROSS | SPECIES_EELEKTROSS_MEGA | ITEM_EELEKTROSSITE | Presentes; nem todas renderizadas |
| SPECIES_CHANDELURE | SPECIES_CHANDELURE_MEGA | ITEM_CHANDELURITE | Presentes; nem todas renderizadas |
| SPECIES_CHESNAUGHT | SPECIES_CHESNAUGHT_MEGA | ITEM_CHESNAUGHTITE | Presentes; nem todas renderizadas |
| SPECIES_DELPHOX | SPECIES_DELPHOX_MEGA | ITEM_DELPHOXITE | Presentes; nem todas renderizadas |
| SPECIES_GRENINJA | SPECIES_GRENINJA_MEGA | ITEM_GRENINJITE | Presentes; nem todas renderizadas |
| SPECIES_PYROAR | SPECIES_PYROAR_MEGA | ITEM_PYROARITE | Presentes; nem todas renderizadas |
| SPECIES_MALAMAR | SPECIES_MALAMAR_MEGA | ITEM_MALAMARITE | Presentes; nem todas renderizadas |
| SPECIES_DRAGALGE | SPECIES_DRAGALGE_MEGA | ITEM_DRAGALGITE | Presentes; nem todas renderizadas |
| SPECIES_HAWLUCHA | SPECIES_HAWLUCHA_MEGA | ITEM_HAWLUCHANITE | Presentes; nem todas renderizadas |
| SPECIES_FLOETTE_ETERNAL | SPECIES_FLOETTE_MEGA | ITEM_FLOETTITE | Presentes; nem todas renderizadas |
| SPECIES_BARBARACLE | SPECIES_BARBARACLE_MEGA | ITEM_BARBARACITE | Presentes; nem todas renderizadas |
| SPECIES_ZYGARDE_COMPLETE | SPECIES_ZYGARDE_MEGA | ITEM_ZYGARDITE | Presentes; nem todas renderizadas |
| SPECIES_DRAMPA | SPECIES_DRAMPA_MEGA | ITEM_DRAMPANITE | Presentes; nem todas renderizadas |
| SPECIES_FALINKS | SPECIES_FALINKS_MEGA | ITEM_FALINKSITE | Presentes; nem todas renderizadas |
| SPECIES_HEATRAN | SPECIES_HEATRAN_MEGA | ITEM_HEATRANITE | Presentes; nem todas renderizadas |
| SPECIES_DARKRAI | SPECIES_DARKRAI_MEGA | ITEM_DARKRANITE | Presentes; nem todas renderizadas |
| SPECIES_ZERAORA | SPECIES_ZERAORA_MEGA | ITEM_ZERAORITE | Presentes; nem todas renderizadas |
| SPECIES_RAICHU | SPECIES_RAICHU_MEGA_X | ITEM_RAICHUNITE_X | Presentes; nem todas renderizadas |
| SPECIES_RAICHU | SPECIES_RAICHU_MEGA_Y | ITEM_RAICHUNITE_Y | Presentes; nem todas renderizadas |
| SPECIES_CHIMECHO | SPECIES_CHIMECHO_MEGA | ITEM_CHIMECHITE | Presentes; nem todas renderizadas |
| SPECIES_ABSOL | SPECIES_ABSOL_MEGA_Z | ITEM_ABSOLITE_Z | Presentes; nem todas renderizadas |
| SPECIES_STARAPTOR | SPECIES_STARAPTOR_MEGA | ITEM_STARAPTITE | Presentes; nem todas renderizadas |
| SPECIES_GARCHOMP | SPECIES_GARCHOMP_MEGA_Z | ITEM_GARCHOMPITE_Z | Presentes; nem todas renderizadas |
| SPECIES_LUCARIO | SPECIES_LUCARIO_MEGA_Z | ITEM_LUCARIONITE_Z | Presentes; nem todas renderizadas |
| SPECIES_GOLURK | SPECIES_GOLURK_MEGA | ITEM_GOLURKITE | Presentes; nem todas renderizadas |
| SPECIES_MEOWSTIC_M | SPECIES_MEOWSTIC_M_MEGA | ITEM_MEOWSTICITE | Presentes; nem todas renderizadas |
| SPECIES_MEOWSTIC_F | SPECIES_MEOWSTIC_F_MEGA | ITEM_MEOWSTICITE | Presentes; nem todas renderizadas |
| SPECIES_CRABOMINABLE | SPECIES_CRABOMINABLE_MEGA | ITEM_CRABOMINITE | Presentes; nem todas renderizadas |
| SPECIES_GOLISOPOD | SPECIES_GOLISOPOD_MEGA | ITEM_GOLISOPITE | Presentes; nem todas renderizadas |
| SPECIES_MAGEARNA | SPECIES_MAGEARNA_MEGA | ITEM_MAGEARNITE | Presentes; nem todas renderizadas |
| SPECIES_MAGEARNA_ORIGINAL | SPECIES_MAGEARNA_ORIGINAL_MEGA | ITEM_MAGEARNITE | Presentes; nem todas renderizadas |
| SPECIES_SCOVILLAIN | SPECIES_SCOVILLAIN_MEGA | ITEM_SCOVILLAINITE | Presentes; nem todas renderizadas |
| SPECIES_BAXCALIBUR | SPECIES_BAXCALIBUR_MEGA | ITEM_BAXCALIBRITE | Presentes; nem todas renderizadas |
| SPECIES_TATSUGIRI_CURLY | SPECIES_TATSUGIRI_CURLY_MEGA | ITEM_TATSUGIRINITE | Presentes; nem todas renderizadas |
| SPECIES_TATSUGIRI_DROOPY | SPECIES_TATSUGIRI_DROOPY_MEGA | ITEM_TATSUGIRINITE | Presentes; nem todas renderizadas |
| SPECIES_TATSUGIRI_STRETCHY | SPECIES_TATSUGIRI_STRETCHY_MEGA | ITEM_TATSUGIRINITE | Presentes; nem todas renderizadas |
| SPECIES_GLIMMORA | SPECIES_GLIMMORA_MEGA | ITEM_GLIMMORANITE | Presentes; nem todas renderizadas |
