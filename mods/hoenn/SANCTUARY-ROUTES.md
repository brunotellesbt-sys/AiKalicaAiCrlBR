# Percursos dos 14 santuários e dos 105 altares

Esta etapa percorre os nove santuários de ilha e os cinco submersos na
candidata `3b3e16d6`, sem alterar a ROM nem atualizar o player. A distribuição
e as coordenadas continuam em [SPECIAL-LOCATIONS.md](SPECIAL-LOCATIONS.md)
e [POKEMON-LOCATIONS.md](POKEMON-LOCATIONS.md).

Cada roteiro começa numa posição do mar perto do acesso. Depois dessa
colocação inicial, desembarque, entrada na caverna, caminhada até cada altar,
saída e retorno ao ponto inicial usam os controles no motor mGBA. Nos cinco
locais submersos, Dive e subida são ativados pelas confirmações normais de
A/B; não há entrada direta de efeitos de campo ou scripts de altar.

Os testes antigos usavam colocações internas para partes do roteiro. O novo
percurso chega à área livre da caverna pelo corredor original. O alvo interno
`14,18` usado anteriormente fica numa parede; a referência de chegada agora
é o chão em `14,17`. Nenhum tile da candidata foi modificado para o teste.

## Resultados

Passaram **1.422 mudanças de posição**, 28 transições por portas/escadas,
os cinco mergulhos e as cinco subidas à superfície. As transições de Dive
são conferidas separadamente das 28 transições de caminhada.

| Santuário | Acesso | Altares verificados | Mudanças de posição |
|---|---|---:|---:|
| Tempestades | Surf | 8 | 111 |
| Aurora | Surf | 8 | 111 |
| Vulcao | Surf | 8 | 111 |
| Titans | Surf | 9 | 117 |
| Floresta | Surf | 8 | 111 |
| Eclipse | Surf | 8 | 111 |
| Dragoes | Surf | 9 | 117 |
| Estrelas | Surf | 7 | 111 |
| Cristais | Surf | 6 | 97 |
| Mares | Surf + Dive | 5 | 69 |
| Origens | Surf + Dive | 8 | 89 |
| Profundezas | Surf + Dive | 7 | 89 |
| Dimensoes | Surf + Dive | 7 | 89 |
| Abismo | Surf + Dive | 7 | 89 |

As **105 interações reais** recusaram o encontro com zero insígnias. Uma
sentinela no resultado do script verifica que o NPC executou sua permissão;
o teste não aceita um resultado antigo como prova de conversa. Nenhuma
batalha começou, nenhuma captura foi registrada e nenhum altar foi concluído.

Passaram **33 Saves/Continues**: 14 nas câmaras, 14 de volta à superfície
e cinco no retorno submerso. Mapas, posições, modos de deslocamento e zero
insígnias nas duas regiões foram preservados. A permissão de captura
continuou fechada.

O planejador lê agora os dois formatos de atributos de metatiles usados
pela candidata: FRLG nas ilhas e Emerald nas cavernas e mares de Hoenn.
O percurso de Sky Pillar foi repetido como regressão do formato Emerald,
incluindo retorno, recusa de despertar antecipado e três Continues.

- [Roteiros, altares e saves](sanctuary-routes-validation/native/sanctuary-routes.json).
- [Continue na câmara de Tempestades](sanctuary-routes-validation/native/Tempestades-chamber-after-continue.png).
- [Continue no retorno submerso de Mares](sanctuary-routes-validation/native/Mares-underwater-return-after-continue.png).
- [Continue na superfície de Abismo](sanctuary-routes-validation/native/Abismo-surface-return-after-continue.png).
- [Regressão de Sky Pillar](sanctuary-routes-validation/sky-pillar/sky-pillar-access.json).

## Reprodução e limites

ROM: `3b3e16d60b50a9be8105eaa8a62bb91ea7923f7748d0bfbd68be64a264fe544d`.
Fonte fixada em `e05c82865d38a6638173fd30b2c830d1250aa50d`.
Preparar a árvore compilada e a ponte mGBA conforme
[SKY-PILLAR-ACCESS.md](SKY-PILLAR-ACCESS.md). Então:

```sh
python3 tools/hoenn/validate_sanctuary_routes.py --source .local/hoenn-sky-access-src --library .local/mgba-bridge.so --output mods/hoenn/sanctuary-routes-validation/native
python3 tools/hoenn/validate_sky_pillar_access.py --source .local/hoenn-sky-access-src --library .local/mgba-bridge.so --output mods/hoenn/sanctuary-routes-validation/sky-pillar
python3 -m unittest discover -s tools/hoenn -v
python3 -m unittest discover -s tools/sea_routes -v
```

Equipe com Surf/Dive, insígnias iniciais e as 14 posições de chegada no mar
são fixtures. Encontros selvagens são desativados. Esta etapa verifica as
aproximações locais, os interiores e retornos; não percorre a viagem inteira
entre regiões para chegar a cada mar. Também não testa batalhas e capturas
dos 105 especiais ou dificuldade. As campanhas completas continuam pendentes.
