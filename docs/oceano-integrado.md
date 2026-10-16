# Oceano integrado e ligações do mapa

![Mapa atual, sem nomes sobre as rotas](images/navigation/world-map-current.png)

As seis marcações amarelas viraram ligações azuis no mapa normal e no zoom. São cinco passagens novas; Seven Island–Tanoby já tinha uma conexão real e foi reaproveitada. Os nomes ficam na seleção do MAP e no [índice de rotas](rotas-maritimas.md).

| Marcação | Passagem real de Surf |
| --- | --- |
| Lavender → One Island | LAVENDER-ONE SEA |
| Acesso oeste de Two Island | ONE-TWO PASSAGE |
| Saída sul do canal Two–Three | TWO-THREE SEA MOUTH |
| Sul de Sootopolis | SOOTOPOLIS SOUTH CHANNEL, entre as rotas 126 e 130, fora da cratera |
| Seven Island → Tanoby | Acesso existente pelo mar de Seven Island |
| Mar sudoeste → Tanoby | SOUTHWEST SEVII PASSAGE |

As 65 rotas marítimas auditadas têm limites de pedra nas bordas sem conexão. As entradas ligadas a outra rota ficam abertas, com passagem de água ao redor das ilhas. Nove trechos antes vazios receberam ilhas de areia de formatos variados e um treinador próprio por ilha; as praias existentes foram preservadas. Duas áreas adicionais de junção mantêm a travessia Kanto–Sevii ligada ao restante do oceano. A entrada norte da Rota 124 foi alargada, sem o zigue-zague entre pedras.

Hoenn e Kanto/Sevii compartilham os pixels, a paleta, os endereços gráficos e a fase de animação do oceano. A troca de tileset refaz a vista costeira e aplica a iluminação atual, evitando rochas desenhadas sobre a água e o corte de cor durante a travessia. Os cantos externos dos portos das ilhas também usam pedras visíveis, substituindo o fundo preto.

[Vídeo contínuo: Mossdeep → One Island por Surf](videos/mossdeep-one-island-surf.mp4). A gravação usa a edição Gen 1–9 Normal, com movimento pelo controle, ativação nativa de Surf e desembarque na ilha. A posição inicial, a equipe e o progresso são fixtures de teste.

Os 15 acessos a cavernas (14 santuários e Seafoam) têm ramais azuis até os seus ícones no mapa e no zoom. Os acessos submarinos continuam usando Dive. A soleira da caverna Dimensões foi aberta: o corredor da entrada e dos portais Paradox estava isolado da sala interna. As regras dos encontros lendários foram preservadas.

Esta entrega parte do PR #90 já mesclado. Mossdeep, a ponte suspensa e as praias de Dewford mantêm a arte aprovada, comparada pixel a pixel; as portas e os trajetos dos portos são novamente testados nas quatro edições.

As evidências desta atualização ficam em `mods/hoenn/continuous-ocean-validation/`: reprodução independente das três camadas sobre o PR #90, preservação dos eventos existentes, conectividade por colisões compiladas, travessias e cursor do MAP, travessias de ida e volta em todas as conexões aquáticas utilizáveis, entrada e retorno nas 15 cavernas, nove batalhas reais e persistência dos flags após salvar. Inclui viagens às sete ilhas e comparação das cores em todas as 13 emendas Hoenn/FRLG nas quatro edições. As evidências anteriores dos terminais continuam associadas às ROMs históricas; esta atualização não refaz a campanha inteira.

Resultado final: 227 ligações de Surf atravessadas nos dois sentidos (454 travessias), limites externos auditados em 65 trechos, 15 entradas de caverna com ida e volta e abertura do MAP, nove batalhas com persistência ao salvar. As quatro edições passaram por Surf às sete ilhas, 26 travessias das emendas Hoenn/FRLG por edição, viagem Mossdeep–One Island e testes dos dois terminais do PR #90. O player iniciou as quatro ROMs com seus hashes atuais.
