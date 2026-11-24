# Resgate obrigatório de Sootopolis

Depois da cena de Rayquaza, fale com o capitão dentro do porto de Sootopolis. Ele leva você até o ponto de resgate. Encontre Manaphy por Surf, alcance os moradores no banco de areia e volte ao capitão com a jangada. A sequência termina com a confirmação do desembarque no porto.

O resgate libera o último ginásio de Hoenn em qualquer ordem de insígnias. Em saves com as oito insígnias da região já obtidas, o capitão oferece a missão quando o jogador volta ao porto. Luffy reconhece a despedida do navio caso Galactic tenha acontecido primeiro. O serviço de ferry continua disponível pelo capitão.

A investigação posterior do Governo Mundial e o epílogo de Shaymin estão registrados no roteiro. [História de Luffy](../../../docs/IDEIAS-HISTORIAS-LENDARIOS.md#3-luffy-kyogre-lugia-e-manaphy--o-mar-que-engole-os-caminhos)

## ROMs

Aplique o patch da mesma edição à ROM do catálogo completo do PWT. O player usa os mesmos patches para gerar Play e Download. [ROM-base do PWT](../pwt-complete-rosters/README.md)

| Edição | Patch |
| --- | --- |
| Gen 1–4 Normal | [BPS](Pokemon-Journey-Gen1-4-Normal-rescue.bps) |
| Gen 1–4 Hard | [BPS](Pokemon-Journey-Gen1-4-Hard-rescue.bps) |
| Gen 1–9 Normal | [BPS](Pokemon-Journey-Gen1-9-Normal-rescue.bps) |
| Gen 1–9 Hard | [BPS](Pokemon-Journey-Gen1-9-Hard-rescue.bps) |
| TESTE | [BPS](Pokemon-Journey-TESTE-rescue.bps) |

## Reprodução

A camada `sootopolis-rescue` parte de uma cópia privada da fonte com `pwt-complete-rosters`. Aplique `prepare_sootopolis_rescue.py`, compile e gere as edições com `package_versions.py` e `package_review_rom.py`. O comando `python3 tools/hoenn/verify_sootopolis_rescue.py` reconstrói as cinco ROMs e confere as provas do emulador. [Manifesto](validation.json)
