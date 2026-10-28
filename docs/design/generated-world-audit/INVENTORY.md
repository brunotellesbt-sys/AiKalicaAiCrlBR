# Escopo da revisão do mundo gerado

O [inventário](inventory.json) compara os hashes finais das 164 camadas com
os arquivos adquiridos do commit `e05c82865d38a6638173fd30b2c830d1250aa50d`
de `eonlynx/pokecrossroads`. Arquivos que uma camada alterou e outra restaurou
ao original não contam como alterações finais. Os 6.243 arquivos espaciais
originais usados para comparar mapas, layouts e tilesets foram conferidos
contra os hashes da aquisição.

Na ROM-base `3111ff0e2f5f1caa94b808c8fecf62f7b313d6b241014f416de31eff80105771`,
existem 2.809 arquivos finais alterados e 667 mapas com alterações diretas.
Desses mapas, 399 foram criados e 414 possuem blockdata alterado; 166 têm
somente scripts ou eventos alterados. As categorias são uma organização de
revisão, não uma identificação oficial de cada local no jogo.

| Categoria principal | Mapas |
|---|---:|
| Rotas marítimas | 277 |
| Rotas terrestres | 70 |
| Cavernas | 106 |
| Subaquáticos | 5 |
| Portos | 36 |
| Cidades e vilas | 31 |
| Ginásios novos ou com eventos alterados | 14 |
| Estádios | 2 |
| Outros interiores | 125 |
| Interior de evento | 1 |

O inventário inclui alterações da definição do layout, mesmo sem mudança
no arquivo de mapa local. Por isso `TwoIsland_CapeBrink_Frlg` aparece: seus
bancos gráficos mudaram. Cada linha informa dimensões, bancos, arquivos,
camadas, retângulo das células alteradas, conexões e coordenadas de warps.
O responsável registrado para o arquivo global de layouts é o da última
gravação desse arquivo, não uma atribuição independente de cada propriedade.

Outros 234 mapas são consumidores indiretos de bancos ou scripts compartilhados
alterados. Essa lista é conservadora: um banco alterado não demonstra que o
mapa utiliza os metatiles modificados. Ela serve para examinar dependências,
sem confundir alterações globais com novos defeitos de terreno.

Este inventário **não aprova acabamento, movimento, colisões ou animações**.
Esses resultados precisam de revisão visual e provas próprias na ROM final.

Reprodução, a partir da raiz:

```sh
python3 tools/hoenn/audit_generated_world_inventory.py \
  --source .local/badge-story-src \
  --upstream .local/generated-world-original-inputs \
  --output docs/design/generated-world-audit/inventory.json
```

Em uma máquina sem o cache original, acrescente `--fetch-upstream`. O download
usa o repositório e o commit fixados em `.source-acquired.json`, preservando
somente os arquivos espaciais e rejeitando qualquer hash diferente. Para uma
camada candidata ainda não publicada, use `--append-layer nome-da-camada`.
