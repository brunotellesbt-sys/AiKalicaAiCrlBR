Reforma na fonte, posterior à ROM C8; ainda sem compilação/prova nativa.

66.669 células de enchimento de recife viram água Surf real, além de linhas
bloqueadas junto aos percursos. Nenhuma célula anteriormente passável muda.
Núcleos de objetos nativos completos preservados;39faces nativas/Dive ainda
têm revisão própria pendente. Água decorativa excluída dos resgates de saves.

A primeira checagem apenas por SCC não bastava: Emerge abria3538células fora
do percurso. O auditor agora percorre caminhos dirigidos, incluindo esses
atalhos. A tabela C de áreas decorativas bloqueia Dive/Emerge nelas, sem
inventar colisão em água. Seu conteúdo, ABI e lookup são conferidos. Resultado
final da fonte:1SCC jogável,0células decorativas alcançáveis, obrigações antigas
de34costas,18cavernas,5Dive e7portos continuam passando. Não é prova da ROM.

96nadadores novos ficam em96mapas ordinários, todos na água alcançável,
com corredor de3x6, quatro orientações e distância mínima entre treinadores.
IDs existentes preservados; flags novas compiladas contra todas as macros
antigas, incluindo aliases, dentro do save existente. Regras normais/Hard,
geração e TESTE não são alteradas. Faltam batalhas/abordagem/SAVE nativos.

Sete estátuas restantes substituídas pelos sprites nativos próprios; flags,
scripts, IDs e posições intactos. O PNG é prévia de assets da fonte, não
captura do jogo. Versão4 mantém a migração3 e atualiza templates só nos
mapas alterados;96posições de novos nadadores têm resgate lateral de um tile
para saves anteriores. É aplicado uma só vez; capturas/história preservadas.

O preparador prepare_atlas_surf_redesign.py reproduz tudo da171 imutável
e snapshotC8 autenticado, em diretório privado novo. Não publicar nem chamar
o pedido inteiro concluído: faltam exteriores grandes/diversos, entradas e
câmaras próprias para105lendários, auditoria global das rochas e demais gates.

Suíte completa:339casos;337PASS, dois erros por fixtures históricos ausentes
no sparsecheckout. Três arquivos rastreados restaurados byte a byte doHEAD;
reexecução dos5testes desse móduloPASS. Logs da falha e correção preservados.
