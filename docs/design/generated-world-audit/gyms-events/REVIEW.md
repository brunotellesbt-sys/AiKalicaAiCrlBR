# Ginásios, cidades e eventos gerados

Esta revisão parte do source congelado de PR101, camada 164, ROM
`3111ff0e2f5f1caa94b808c8fecf62f7b313d6b241014f416de31eff80105771`.
As imagens `*-source.png` são renderizações dos tiles e eventos do source,
**não capturas do emulador**. O inventário e os hashes estão em `maps.json`.
As provas nativas da versão final ficam no relatório de publicação da camada
seguinte; os resultados desta base são diagnóstico antes das correções.

## Revisão visual

Foram inspecionados os 24 mapas inteiros listados em `maps.json`: os oito
ginásios extras; Lavender, Lilycove, Ever Grande, Fallarbor, Slateport,
Three Island, Six Island e Pallet; laboratório de Oak; duas casas de Ever
Grande; arena PWT; lado externo da Battle Frontier; sala Galactic; oficina
de Lavender e primeiro andar da Pokémon Tower.

- As oito salas têm percursos e dimensões diferentes; os móveis e estátuas
  foram vistos inteiros, com entrada, guia e passagem até o líder livres.
- Nos ginásios, não foi identificado objeto cortado na revisão dos mapas
  completos. A análise do grafo também exige quatro treinadores, quatro
  orientações distintas, aproximação livre de três tiles e quatro linhas
  de visão que cortam separadamente todo trajeto até o líder.
- A floresta abaixo do ginásio de Three Island contém três copas removidas.
  Esse achado está na correção de objetos marinhos/Sevii desta mesma auditoria;
  a aprovação das salas internas não aprova a floresta externa.
- Em Six Island os exemplares isolados foram vistos como árvores completas
  de 2 × 3 tiles. Não se confundiu a linha intermediária de floresta com um
  tronco de árvore isolada.
- O render genérico da Galactic não resolve os gráficos de espécies e
  mostra marcadores de substituição. A inspeção usou
  `galactic-prison-source/team-galactic-final-room.png`, composto com os
  sprites indexados reais e a camada frontal transparente das jaulas.
  Os marcadores genéricos não foram tratados como defeitos do jogo.
- Casas, laboratório, oficina, Pokémon Tower, estádio e área externa foram
  inspecionados também fora do pequeno recorte de entrada. Os móveis,
  fachadas, caminhos e suas portas não apresentam novos cortes confirmados
  nessa revisão.

## Verificações repetíveis

`audit_generated_gym_geometry.py` faz análise estática, e o JSON deixa essa
limitação explícita. Os três controles negativos em `negative-controls.json`
rejeitam treinador olhando para parede, tile sólido na linha de visão e
guia bloqueando a entrada.

`validate_generated_gym_walk.py` usa o controlador nativo dos ginásios para
entrar pela cidade, conversar com o guia, atravessar os quatro alcances,
vencer os treinadores separadamente, desafiar o líder e sair pela porta.
As estatísticas do jogador são aceleradas e as viagens/quest anterior são
fixtures; resultados e aproximações de batalha são produzidos pelo jogo.
Ele exclui as antigas assertivas de Liga com 24 insígnias, pois a permissão
atual de 18/22 é verificada por `validate_badge_story_gates.py`.

`validate_generated_ever_grande.py` percorre as duas casas desde o Centro,
recebe Full Restore e Max Revive uma única vez, conversa novamente, sai pelas
portas e caminha até a barraca de Mega Stones para abrir e fechar a loja.

`validate_pwt_access.py` percorre recepção, balcão, cancelamento da seleção e
saída. A espera antiga por uma pergunta sim/não foi corrigida: a recepcionista
atual abre uma lista dinâmica de gerações e depois a seleção de Pokémon.
O teste agora para na seleção real sem continuar pressionando A sobre ela.
Essa correção é no validador, sem alterar o evento do jogo.

`validate_badge_qualifier.py` valida separadamente o evento da 18ª insígnia,
encontro externo, estádio, derrotas, nova tentativa, vitória, celebração,
save e recuperação de uma arena interrompida. A sequência não é confundida
com inscrição no PWT.

Cada comando recebe `--source`, `--library` e `--output`. Uma prova só vale
para o SHA gravado no seu relatório; não substitua esse hash pelo da ROM
seguinte nem use a aprovação estática como prova de caminhada nativa.
