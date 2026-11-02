# Pallet: borda úmida e acesso sul

O quinto vídeo percorre a borda norte da baía, em `(15..22,17)`, e o corredor
de grama a leste. A reprodução nativa na ROM `bcd8da4c…` mostrou um caso
gráfico diferente da água de altura zero de Treasure Beach: os oito blocos
particulares `302/303` têm comportamento de chão comum e altura 3, mas
desenham grama na metade superior e uma base de encosta com água na metade
inferior. A colisão aberta deixava os pés sobre essa água visível.

O reparo fecha apenas a colisão desses oito blocos. Mantém todos os gráficos,
alturas, comportamentos, árvores, telhado, eventos e pontes. A faixa completa
de grama ao norte e o corredor inteiro de grama em `x23` continuam abertos.
O inventário dos 303 mapas externos FRLG encontrou exatamente esses oito
blocos de chão exposto com a combinação de água e base nativa de encosta.

As 72 células aquáticas transitáveis de Pallet já tinham altura 1. A borda
real de água a leste bloqueia a caminhada sem Surf; o vídeo não demonstra
que essa água seja transitável a pé. A captura nativa correspondente fica
separada da reprodução da borda mista.

O sexto vídeo mostra a entrada pela grama no acesso sul. A ROM acima já usa
o bloco `F305`, de nível múltiplo 15: a travessia por controles preserva o
pedestre no nível 3 e permite Surf no nível 1 abaixo da ponte. O validador
antigo parava numa asserção obsoleta que ainda exigia altura zero, depois
de completar a primeira porta e a viagem de barco. A revisão atual exige 15
sem alterar o validador histórico.

A prova final de Pallet verifica os oito blocos fechados e tenta entrar pelas
nove fronteiras antes acessíveis. A aproximação norte de `(20,17)` já fica
atrás da placa em `(20,16)`; seu bloco é verificado diretamente. A prova
também percorre o corredor completo de grama e faz o caminho
`(18,26) → (18,25) → (18,24) → (18,25) → (18,26)` pela ponte sul sem uma nova
colocação sobre a ponte. As imagens de diagnóstico desta pasta são do
baseline; as provas da recuperação precisam dos SHA da nova ROM e do ELF.


Validação executada na ROM final
`f7af65b4856e6697d5d972f48f8699c7c6b7d4b277ea19cfa3949926265d1b89`,
ELF `3f8ba485b37d17f58f7c7a5a64b1a8dd28492a9ea612afdead2487ceef3d1f9e`:
os oito blocos e as nove aproximações bloqueadas passaram, assim como o
corredor leste, a ida/volta da ponte sul, as portas, a viagem de barco e a
ligação de Surf com a Rota 21. As 24 capturas e seus hashes constam em
`native-final-review.json`; as duas folhas foram inspecionadas. O mapa
inteiro final e sua dependência de arte estão em `final-source/`.

O corte do chapéu no acesso sul é corrigido separadamente pela prioridade
de desenho do pedestre. Os doze tiles de grama completos `(11..22,26)`
continuam com altura física 3; somente a prioridade de exibição muda.
A prova `pier-visibility/` compara pixels de cabeça, corpo e pés em cada um
deles nos dois sentidos e preserva Surf abaixo da ponte de nível múltiplo.
