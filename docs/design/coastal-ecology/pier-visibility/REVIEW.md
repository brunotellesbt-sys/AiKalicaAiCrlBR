# Pallet e Cinnabar: personagem inteiro nos acessos secos

Os vídeos de Pallet e Cinnabar mostravam o chapéu sendo coberto pela ponte,
mesmo quando o estado de caminhada e a altura física estavam corretos.
O personagem ocupa pixels acima do tile onde estão seus pés: corrigir apenas
a prioridade sobre a ponte não bastava para o passo seguinte, ao sul dela.

A correção mantém o pedestre acima da camada das tábuas em dois acessos
inteiros: os quatro tiles secos de Cinnabar `(9..10,16..17)` e os doze tiles
de grama de Pallet `(11..22,26)`. Só muda a prioridade usada no desenho.
Altura física, colisão, coordenadas, estado de Surf e gráficos do mapa
permanecem iguais. A regra exige personagem do jogador, caminhada e nível 3;
quem surfa continua no nível 1 e na camada inferior da ponte alta.

`validate_coastal_pier_visibility.py` percorreu os 16 tiles nos dois sentidos,
os seis tiles da ponte alta de Cinnabar nos dois sentidos e a ponte de Pallet.
Em cada posição seca comparou o quadro real do personagem em VRAM/OAM com
os pixels efetivamente exibidos, separando cabeça, corpo e pés. Também
executou as duas travessias de Surf sob as pontes e os dois desembarques de
volta às plataformas com a transição nativa, por controles. As primeiras
colocações, equipe, progresso e supressão de encontros são fixtures explícitas.
Nenhuma coordenada, altura ou modo é escrito durante os percursos.

ROM: `f7af65b4856e6697d5d972f48f8699c7c6b7d4b277ea19cfa3949926265d1b89`.
ELF: `3f8ba485b37d17f58f7c7a5a64b1a8dd28492a9ea612afdead2487ceef3d1f9e`.
Os 32 registros de aproximação seca passaram, sem falha de pixels. As 75
capturas reais estão vinculadas em `native-final-review.json`, junto das sete
folhas inspecionadas. O jogador parcialmente encoberto ao surfar debaixo da
ponte alta é a camada nativa intencional desse percurso; os passos sobre a
madeira e os acessos secos mostram o personagem inteiro.
