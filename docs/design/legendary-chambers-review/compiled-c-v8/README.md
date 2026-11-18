Este checkpoint preserva o progresso solicitado em 18/11/2026. A ROM privada C
inclui os 105 interiores, nove exteriores maiores, migração 8 e a correção das
localizações AREA da Pokédex. As cinco ROMs públicas permanecem na versão 7.
A validação final continua pendente; este diretório não é um selo de lançamento.

Identidades da compilação examinada:

- ROM: `d296428c98f989a815e24d9def5a51bfd284c50f1ca9831547cb42fb7ce8c0ce`.
- ELF: `48051289a43f05e3ebc30d891a3de68e46140d44015189a1ea15766b00211214`.
- Marker: `91a5f6809e36d29d9063b436f5b84de7db1967ea3aaf277515ecfcfc2a0b3cda`.

`compiled-freeze.json.gz` registra 34.396 entradas e 2.604 saídas preparadas.
`prepared-source-delta.tar.gz` guarda todas essas saídas e o marker, com hashes
conferidos contra a fonte congelada. A fonte completa, ROM, ELF e predecessores
continuam preservados no ambiente. O delta deve ser aplicado somente sobre o
predecessor autenticado, sem sobrescrever fontes antigas ou reconstruções parciais.

Provas atuais da C, com fixtures iniciais declarados e controles reais:

- 105 entradas, corpos das espécies e retornos; 210 PNG e 48.600 pixels de sprites.
- Nove montanhas completas: 729 células, 189 PNG, câmeras antes/depois e colisões.
- 103 fragmentos originais e seis adicionais: 54 casos, 210 PNG e 48 bloqueios.
- 96 vitórias de treinadores de Surf, flags privadas e quatro baterias com Continue.
- 34 ligações entre costas nativas, adaptadores e rotas externas, com ida/volta.
- Cinco viagens Dive/santuário/Emerge e duas divisas da Rota 131.
- 18 baterias antigas: SAVE real na V7, Continue na C, novo SAVE e segundo Continue.
- Articuno: recusa com 15 insígnias, captura real com 16, remoção do ator,
  consumo da Master Ball, SAVE e Continue com os bytes da equipe preservados.
  Giratina e Pecharunt ainda não foram executados neste lote. Não são 105 capturas.

Os verificadores independentes das câmaras, exteriores e rochas foram novamente
executados sobre estas cópias. Seus resultados estão em
`independent-native-verification.json`. Os componentes comprimidos preservam
integralmente o JSON; `proof-gzip-index.json` registra os hashes originais.
`SHA256SUMS` autentica todos os arquivos deste diretório.

`compiled-source/atlas-surf-final-source.json.gz` registra o replay independente
das 2.604 saídas, 2.046 mapas compilados, 3.118 warps, 401 atores afetados e 2.473
linhas AREA, além dos segmentos ELF/ROM e arte do atlas preservada. A auditoria
de ecologia conserva 190/383 famílias para os dois limites de geração. As 978
referências AREA efetivas foram realocadas para gatilhos atuais da espécie e do
limite exatos; 261 precisaram trocar de proprietário. As 72 linhas antigas que
não produziam encontros foram removidas explicitamente. Não houve mudança nos
conteúdos dos encontros. Esta auditoria de fonte não substitui encontros nativos.

Pendências para concluir a entrega:

1. Concluir capturas representativas restantes e agregar/verificar todas as provas.
2. Atualizar o percurso dos sete portos para as chegadas atuais do Atlas. O
   validador histórico falhou no planejamento com coordenadas antigas, antes
   de mover o jogador; isso ainda não demonstra defeito na ROM. A tentativa
   especulativa de alterar o filtro de pontes foi retirada.
3. Repetir capitão de Pacifidlog e ThreeIsland na C; suas provas B são históricas.
4. Exportar as cinco edições C e validar regras, limites, modo TESTE, encontros,
   batalhas manuais e baterias/cold boots de cada edição.
5. Finalizar contrato/publicador estrito da camada 172, leitores históricos,
   validação no navegador e todos os checks obrigatórios.

Os oito FAIL e um ERROR de selo do lançamento não foram contornados. Os logs
do checkpoint estão em `checks/`; o resultado da suíte deve ser lido nesses
logs, sem transformar os testes focados em aprovação global. Nenhum merge foi feito.

Retomada no ambiente preservado:

```bash
python3 tools/hoenn/validate_legendary_captures_native.py \
  --source .local/final-atlas-src --library .local/mgba-bridge-ci.so \
  --output .local/final-atlas-review/capture-487 --national 487
```

Repetir para `--national 1025`. Para o problema dos portos, comparar
`.journey-atlas-surf-layout[ports][arrivals]` com as coordenadas históricas de
`.journey-sevii-integrated-piers`. Não recompilar a fonte C enquanto houver
validadores lendo essa ROM/ELF. As provas A/B e V7 não podem ser relabeladas como C.
