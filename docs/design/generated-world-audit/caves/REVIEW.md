# Cavernas e interiores criados

A revisão visual examinou os mapas inteiros das cinco pranchas de cavernas
e das quinze pranchas de interiores: 28 cavernas/subsolos e 87 outros
interiores. O [registro](visual-review.json) identifica cada imagem e seu hash.
São renderizações dos dados de mapa, não capturas do emulador.

Foram corrigidos sete fragmentos de escrivaninha em cada andar da base Rocket,
usando três objetos nativos completos por andar. No santuário Dimensões,
quinze tiles de topo de escada haviam sido usados como piso bloqueado, impedindo
chegar às duas cavernas Paradox. A encosta sul foi restaurada pelo doador
Navel Rock e os dois acessos passaram para escadas completas em chão livre,
conservando os IDs dos warps.

Os sete alojamentos de portos aposentados continuam existindo para saves
antigos. Suas saídas agora apontam para o desembarque válido de cada terminal
atual. Não foram apagados mapas, eventos ou cômodos do save.

O exame estático cobre 118 interiores/subsolos criados, 217 warps e 280 objetos.
Os retornos dos quartos familiares consideram a troca condicional de cabeçalho
feita por `JourneyFamilyHomeHeader`; examinar somente o cabeçalho da casa
original produz falsos destinos inválidos. Este exame não certifica movimento.

`validate_generated_cave_routes.py` testa na ROM selecionada as entradas,
aproximações dos NPCs e retornos de 26 cavernas criadas; sete saves feitos nos
alojamentos antigos; e cinco percursos com os prompts nativos de Dive e retorno
à superfície. A colocação inicial, a equipe e os confrontos Rocket já vencidos
são fixtures declaradas. Os percursos usam controles, sem teletransportes
internos nem escrita de coordenadas do jogador durante a caminhada.

Sprites variáveis não resolvidos pelo renderizador são registrados, não
interpretados como falhas do terreno. Os prisioneiros Galactic têm barreiras
intencionais antes da libertação; a campanha possui verificação própria.
