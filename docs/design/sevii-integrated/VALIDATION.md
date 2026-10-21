# Contrato das provas da entrega

A entrega exige 42 relatórios atuais: duas provas comuns (`sevii-integrated-source`
e `all-surf-links`) e oito provas para cada uma das quatro edições e a TESTE:
`integrated-piers`, `ocean-seams`, `six-landscape`, `dewford-coast`,
`dewford-beach-visibility`, `coastal-cave-finishing`, `review-mode` e `cold-boot`.
Cada relatório deve passar e identificar o SHA-256 da ROM correspondente.
Relatórios ausentes, repetidos, desconhecidos, reprovados ou com SHA antigo
impedem a validação da entrega.

`integrated-piers` percorre os sete terminais, suas portas e os capitães;
confirma ida e volta pela rede, embarque e retorno com Surf no mesmo píer,
colisões dos cascos e fachadas, save/Continue no píer e na água, os sete portos
antigos livres e suas 25 conexões preservadas. `ocean-seams` revisa 26 emendas
gráficas de 18 mapas, com 52 cruzamentos e 78 capturas por edição; seu conjunto
é distinto dessas 25 conexões dos portos antigos. `six-landscape` exige as
18 árvores completas, falésias, os 720 metatiles carregados, sete percursos
secos, cinco portas de ida e volta e sete testes de colisão de Six Island.
Esses testes usam posições iniciais e progresso como fixtures; não representam
uma campanha completa.

As provas de visibilidade do píer incluem a projeção do quadro real do jogador,
obtida do OAM, da VRAM e da paleta OBJ. O verificador reconta os pixels do PNG
nativo, incluindo cabeça, corpo e pés. Flags de sprite visível e números
declarados no JSON não substituem os pixels. O publicador copia os PNGs
referenciados junto dos relatórios e preserva seus hashes e bytes.

O defeito anterior de retorno com Surf continua documentado separadamente em
`mods/hoenn/sevii-integrated-validation/baseline/sevii-reboarding/`:
sete retornos bloqueados na ROM
`5e0cecc8d2143334795a752e9bb1f70343671f34a29dbd2af3a78e3bff05ef50`.
O relatório original conserva `passed: false`, `expected_broken_baseline: true`
e seu SHA original; os sete PNGs são fixados individualmente no manifesto.
Ele demonstra a regressão e não conta como uma prova atual aprovada. A prova
anterior da praia de Dewford também conserva seus pixels ocultos e seu SHA.
O histórico de validação permanece associado às versões em que foi executado.

Os testes de rejeição usam esses artefatos reais e um relatório nativo atual:

```sh
python3 tools/hoenn/test_sevii_integrated_release.py \
  --validation mods/hoenn/sevii-integrated-validation/Gen1-9-Normal -v
python3 -m unittest discover -s tools/hoenn -p test_native_beach_visibility.py -v
```

O primeiro comando executou os 16 casos com a prova final de Gen1-4-Normal:
seis casos atuais e dez casos históricos, todos aprovados, sem casos ignorados.
Os dois testes específicos da praia também passaram. Eles verificam que SHA
antigo, retorno bloqueado, jogador ainda surfando,
ausência da projeção OAM, PNG alterado e pés encobertos são rejeitados.

Durante o teste da primeira compilação, o save/Continue de One Island falhou
uma vez; três repetições preservando o mesmo lugar concluíram, sem reparos
de memória. A causa não foi estabelecida. O validador exige 60 quadros
neutros e tarefas de viagem concluídas antes de salvar, mantendo a verificação
de retorno real ao campo. A primeira execução completa também identificou
que a porta de Seven Island na última linha do mapa não era ativada ao cruzar
a conexão a partir do tablado vizinho. Na origem final, o terminal começa em
`(17,13)`, a porta fica em `(20,18)` e o tablado de entrada em `(20,19)`, antes
da conexão. O percurso nativo é exigido novamente nas cinco edições.

A origem final é identificada por
`08fc8a08b95e8e3a923e3342b4f1a31bbaccd1582cbc67ea010021191c43fd6e`.
A auditoria compilada aprovada fixa 108 arquivos autorizados. A prova comum
de Surf percorreu 428 ligações recíprocas, com 856 cruzamentos; esses totais
não substituem os percursos de portas e reembarque dos terminais.

O publicador só sela o manifesto depois do verificador completo aprovar as
ROMs, as 42 provas, os saves, os PNGs e o histórico. Nenhum resultado da
primeira compilação substitui a execução dos testes com os hashes finais.
