# Rotas H, J e K fora do Atlas

A revisão retira os três traçados marcados do mapa-múndi, da visualização em
2× e das passagens de Surf na ROM. O mapa abaixo foi extraído da compilação
com os novos blocos de terreno.

![Atlas após a retirada das rotas H, J e K](mapa-HJK.png)

- **H** fecha a ligação horizontal abaixo de Mossdeep.
- **J** fecha a vertical ao lado de H até o cruzamento superior. A nadadora
  mantém a batalha e o registro de vitória no trecho navegável ao norte.
- **K** fecha a paralela inferior entre Kanto e Sevii. A linha de cima recebe
  todo o tráfego oeste–leste e o entroncamento para o sul continua aberto.
  O banco de areia sem eventos continua visível além do recife.

As bordas bloqueiam o Surf e a água atrás delas conserva a aparência do mar.
Saves antigos nas células retiradas migram ao carregar pela primeira vez. Os
saves feitos a pé no banco de areia migram para a praia acessível mais próxima.
A Pokédex aponta Finneon e Lumineon para um habitat navegável.

## ROM jogável

Cada patch BPS usa como base a edição de mesmo nome do **Atlas 172**.
Aplique o patch à ROM correspondente. Mantenha uma cópia do seu save antigo
e use o mesmo nome de arquivo da nova ROM para carregar esse save no emulador.

| Edição | Patch |
| --- | --- |
| Gen 1–4 Normal | [BPS](Pokemon-Journey-Gen1-4-Normal-atlas172-HJK.bps) |
| Gen 1–4 Hard | [BPS](Pokemon-Journey-Gen1-4-Hard-atlas172-HJK.bps) |
| Gen 1–9 Normal | [BPS](Pokemon-Journey-Gen1-9-Normal-atlas172-HJK.bps) |
| Gen 1–9 Hard | [BPS](Pokemon-Journey-Gen1-9-Hard-atlas172-HJK.bps) |
| TESTE | [BPS](Pokemon-Journey-TESTE-atlas172-HJK.bps) |

Os patches são candidatos de revisão para as cinco edições. Os downloads
principais do Atlas 172 continuam disponíveis para quem já está jogando.

## Reprodução e validação

Em uma cópia privada da fonte compilável do Atlas 172, execute
`tools/hoenn/prepare_atlas_route_pruning.py` com
`--inventory-source` apontando para a fonte histórica 171 e
`--output` para exportar a auditoria de habitats. Compile essa cópia com a
mesma toolchain do Atlas 172.

`validate_atlas_route_pruning_native.py` lê os blocos e a arte da ROM
compilada, percorre as alternativas com controles no mGBA e verifica saves
antigos com dois carregamentos sucessivos. O manifesto vincula os resultados
e os patches à compilação correspondente.

```sh
python3 tools/hoenn/verify_atlas_route_pruning.py
```
