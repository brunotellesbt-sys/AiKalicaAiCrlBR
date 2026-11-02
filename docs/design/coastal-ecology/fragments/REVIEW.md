# Fragmentos de rocha nas bases das encostas

O terceiro vídeo mostra One Island e Treasure Beach. O pequeno fragmento branco
sob a grama em One Island corresponde ao objeto nativo de 2 × 2 em `(6,16)`;
há outro em `(15,16)`. A comparação com o upstream verificado mostra a família
`108 / 109 / 118 / 119`. A antiga abertura para Surf removeu somente a fileira
inferior `118 / 119`, deixando os dois quartos superiores combinados com a
base da encosta. Os gráficos 420/421 desse motivo representam a parte superior
da rocha; a inclusão em um canal de animação não os transforma em espuma.

A mesma assinatura exata aparecia em 16 objetos de nove mapas. O reparo troca
somente os 32 metatiles superiores `108 / 109` pela base reta nativa `123`,
preservando todos os bits de altura/colisão e a fileira inferior de mar já
aberta. A base reta usa o exemplar de One Island `(8,16)`. Os dois objetos
nativos completos em Green Path `(37,17)` e `(39,17)` permanecem inteiros.

`cliff-fragment-repair.json` registra os mapas, coordenadas, palavras e hashes
de cada arquivo. `cliff-rock-fragments-comparison-source.png` compara os
recortes de todos os 16 locais antes/depois desta troca gráfica isolada.
Essas imagens são renderizações de source; não são capturas do emulador.

As nove imagens inteiras em `before/` vêm do snapshot imutável da camada 165.
Seu `source-provenance.json` contém a dependência completa de gráficos,
paletas, atores, mapas, layouts e renderizador. As duas folhas foram revistas
junto aos recortes: as bases continuam ligadas aos cantos, cercas e massas de
encosta, sem cortar o relevo nem ocupar a ponte ou corredores de Surf.

O censo de objetos agora também usa `108 / 109` como âncoras. Ele identifica os
16 fragmentos na camada 165; antes, sua busca apenas pela família comum
`110 / 111 / 118 / 119` não enxergava uma rocha depois de apagar seus dois
quartos inferiores. Os testes distinguem um fragmento de uma variante nativa
completa e recusam alterar eventos ou uma fileira inferior inesperada.

`validate_coastal_fragments.py` exige a ROM final compilada e verifica os
blocos e bancos carregados em cada local, conserva as duas variantes completas
e percorre o mar nos dois sentidos por controles. As posições iniciais são
fixtures declaradas; em Route 17, a posição maior que 127 usa um WarpEvent
nativo de 16 bits restaurado antes do movimento. As capturas e o relatório
resultantes são vinculados aos SHA da ROM e do ELF efetivamente executados.

A mesma prova agregada percorre o cabo sul de Kindle Road, incluindo a
continuação real da montanha em One Island e a antiga face que descia até
Treasure Beach. Verifica os 26 blocos carregados nas três áreas, testa as
duas barreiras externas, atravessa as duas conexões por controles e surfa
sobre as seis células inteiras da base antiga já removida. A revisão desse
objeto usa o contexto dos três mapas, pois apenas fechar Kindle Road
deixaria um fragmento da antiga encosta no mapa da praia.

Validação final executada: ROM
`f7af65b4856e6697d5d972f48f8699c7c6b7d4b277ea19cfa3949926265d1b89`,
ELF `3f8ba485b37d17f58f7c7a5a64b1a8dd28492a9ea612afdead2487ceef3d1f9e`.
As 38 capturas atuais e os 60 passos de Surf passaram, incluindo as duas
barreiras do cabo e a volta pelas duas conexões. O verificador estrito de
publicação também aceitou o relatório `coastal-fragments.json`.
`native-review.json` vincula o relatório e as quatro folhas de capturas nativas;
`after/` contém as nove imagens inteiras do source final com nova proveniência.
Esta prova cobre os objetos e movimentos descritos; a uniformidade da água
tem sua própria comparação nativa de pixels e fases.

A revisão final também inclui `kindle/`: os três mapas inteiros e o contexto
unido de One Island/Kindle Road/Treasure Beach antes/depois, com hashes das
imagens em `source-review.json`. `native-final-review.json` referencia somente
as 38 capturas da ROM final, não as capturas diagnósticas anteriores.
