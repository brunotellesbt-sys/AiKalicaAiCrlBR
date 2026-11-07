# Canal sul de One Island e revisão das áreas criadas

A revisão 171 liga o canal oeste de Treasure Beach ao mar horizontal ao sul
por `JourneyOneSouthPassage`, um trecho de Surf de 8 × 32 tiles com limites
de pedrinhas inteiras. O GPS acompanha o meridiano já desenhado no mapa-múndi;
a imagem do mapa e todas as posições anteriores são preservadas.

O acabamento corrige quatro cantos de encosta/espuma em Treasure Beach,
quatro rochas incompletas perto dos terminais e 53 células de limite que
precisavam de pedras visíveis. O embarque de Six Island recupera sua água
navegável. As sete águas de embarque e a área inteira dos 12 barcos existentes
são protegidas da substituição por rochas.

Na caverna Horizonte, duas entradas e dois limiares sem destino são fechados
com faces de rocha nativas completas; um falso degrau volta a ser piso de
caverna. A entrada/saída real e os três personagens conservam suas posições.
Os portais fechados ficam em trechos separados da entrada usada pelo jogador;
as provas locais desses objetos devem ser distinguidas do percurso pela
entrada real.

Duas emendas de câmera, em `JourneyWorldSea02` e
`JourneyWorldFill21Right`, passam a consultar o contorno do vizinho direto
adequado. Esse ajuste só desenha a borda: células indefinidas continuam
bloqueadas, com a mesma altura e regra de movimento. O censo bruto ainda
registra 30 projeções contraditórias no grafo de rotas dobrado; isso não é
apresentado como 30 defeitos visíveis corrigidos nem como zero global.

O novo trecho herda a família de encontros de água e pesca do mar vizinho.
A TESTE conserva a supressão global de encontros e abordagem automática dos
treinadores. Ginásios, rivais e progressão dos eventos não são redesenhados
nesta revisão.

As cinco edições foram atualizadas e passaram abertura nativa. A TESTE
passou com e sem a bateria distribuída e mantém encontros e abordagens
automáticas desativados. As cinco ROMs também abriram no mGBA do navegador,
com os mesmos bytes dos downloads.

Passaram 825 testes de Hoenn, 12 das rotas de Surf e 6 da configuração de CI.
As 12 provas atuais estão vinculadas aos hashes finais; a revisão inclui
35 mapas completos antes/depois, o percurso novo de 261 passos, sete
retornos aos cais e save/Continue. O recorte não equivale a quatro campanhas
completas. O GitHub Pages recebe o pacote após o merge em `main`.

- [Erros, reprodução, causas e soluções em TXT](../errors/2026-11-07-generated-area-review.txt)
- [Índice das provas visuais e funcionais](design/generated-area-review/README.md)
- [Provas da revisão 171](../mods/hoenn/generated-area-review-validation/)
- [Manifesto das ROMs públicas](../mods/hoenn/versions/versions.json)
