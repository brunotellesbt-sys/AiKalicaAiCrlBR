# Animação de água e praia

O censo percorre os 901 mapas do inventário, usando os bancos realmente
referenciados por cada layout e cada metatile. A leitura de um callback `NULL`
no banco secundário não demonstra falta de animação: o banco primário e a
rotina de oceano contínuo também atualizam os gráficos.

`audit_generated_shore_animation.py` separa esse censo de uma verificação nativa:
uma câmera por combinação elegível de bancos, mais as sete áreas costeiras
das Sevii. O teste observa 192 quadros de mGBA, exige todos os quadros nativos
dos canais de água e espuma e compara seus bytes na VRAM com os arquivos
indexados compilados. Também associa pixels visíveis de água aos gráficos e
paletas reais do hardware; mudanças de NPC ou do jogador não bastam para
aprovar a animação. Nenhum relógio de animação, callback, paleta ou VRAM é
escrito durante a observação.

As posições iniciais, modo Surf/a pé e episódios de chegada já concluídos
são fixtures declaradas. Four Island inicia uma cena do rival num save novo:
o teste fixa esse episódio como concluído antes da câmera, sem alterar o jogo.
Navel Rock e dois portos originais têm pisos no nível 0; são posições nativas
válidas e não devem ser excluídas só por não usarem o nível 3.

Uma combinação de bancos dos interiores originais do Battle Palace é
explicitamente excluída da amostragem nativa por seus scripts de controle da
instalação. A análise dos arquivos continua incluindo esses mapas; seu canal
primário General é exercitado nos outros bancos. O relatório registra essa
limitação e não afirma ter observado todas as câmeras de todos os mapas.

Em Five Island, os blocos `(8,12) = 0x1121` e `(9,13) = 0x1123` coincidem com
o upstream fixado. Os detalhes estáticos da areia desse conjunto não são uma
nova falha: a água sob eles percorre a animação nativa. Capturas estáticas do
source não servem para concluir que a praia parou.

Reprodução na ROM final, sem compilar enquanto o teste estiver em execução:

```sh
python3 tools/hoenn/audit_generated_shore_animation.py \
  --source .local/generated-world-audit-src \
  --library .local/mgba-review.so \
  --output mods/hoenn/generated-world-audit-validation/common/animation
```

`shore-census.json` contém apenas cobertura estática. `shore-native-banks.json`
contém os resultados nativos, SHA da ROM, imagens, quadros de água/espuma,
limitações e hash do censo usado. Os três testes em
`test_generated_shore_animation.py` rejeitam pixels de outros gráficos ou de
camadas cobertas, mesmo quando existe uma referência à água na VRAM.
