# Portos integrados de Sevii, Surf e acabamento costeiro

Os sete terminais ficam agora no fim das pontes das próprias ilhas. A porta
leva diretamente ao interior existente e o capitão mantém a rede de viagens.
Os antigos terminais separados foram removidos; seus mapas continuam como
mar, com as mesmas conexões externas. O mapa-múndi não foi redesenhado.

É possível sair da ponte usando Surf e desembarcar de volta no mesmo tablado.
O personagem usa a transição nativa para caminhada no nível da ponte e aparece
inteiro acima da madeira. Caminhar para a água sem usar Surf continua bloqueado.
As pontas permanecem de madeira, sem a faixa metálica.

Six Island teve as 14 árvores incompletas recompostas com as três fileiras
nativas. A cidade tem 18 árvores inteiras, sem galhos soltos entre o Centro
Pokémon e o ginásio nem entre o ginásio e o porto. A margem norte e os cantos
da encosta foram fechados. Centro, ginásio, casas, NPCs e conexões permanecem.
[Cidade inteira e vizinhos](design/sevii-integrated/six-landscape/README.md).

O mar usa o mesmo padrão nas emendas afetadas, preservando os comportamentos
de água, os contornos de praia, os objetos e as paletas nativas. Em Dewford,
a praia junto ao pé da ponte deixou de cobrir o corpo do personagem.
Os dois atendentes e a ponte alta com passagem de Surf por baixo permanecem.

[Sete mapas completos antes/depois](design/sevii-integrated/README.md) ·
[Relatórios e capturas nativas](../mods/hoenn/sevii-integrated-validation/).
As imagens dos mapas completos são renderizações dos tiles de origem;
as capturas dos percursos são identificadas separadamente nos relatórios.

## Validação

A camada 162 exige 42 relatórios vinculados aos hashes das ROMs: auditoria
independente do código e 428 ligações externas de Surf (856 travessias), mais oito
verificações em cada uma das quatro edições normais e na TESTE.

Os percursos verificam os sete terminais, portas, capitães, viagens e retorno
do Surf ao mesmo píer; salvamento e Continue em terra e no mar; os 720 tiles
carregados de Six, as 18 árvores e seus acessos; as 26 emendas afetadas e seus
bancos gráficos; Dewford/Rota 107 e as nove entradas de cavernas. A visibilidade
do personagem é conferida nos pixels reais da captura, além das flags do jogo.

As posições iniciais, equipe e progresso são preparações explícitas dos testes.
Os deslocamentos usam os controles do emulador, sem corrigir coordenadas ou
altura durante a viagem. As provas antigas conservam seus hashes históricos.
Os interiores dos oito ginásios, a campanha e o mapa-múndi foram preservados;
esta entrega não representa uma nova campanha completa jogada.

A TESTE acompanha os mesmos mapas e correções, mantendo encontros aleatórios
e abordagens automáticas desativados. A abertura é verificada com e sem o save
distribuído. A tela azul relatada no My Boy não foi reproduzida no mGBA; sua
causa específica continua sem confirmação. Os testes no navegador usam o
player com as cinco edições. O GitHub Pages recebe os arquivos após o merge.

## Reproduzir

Prepare a camada com `prepare_sevii_integrated_piers.py`, compile com
`build_integration_candidate.py` e congele ROM, ELF e código antes dos leitores
nativos. O compilador e binutils ficam nas pastas locais do ambiente:

```bash
PATH="$PWD/.local/arm-gcc/usr/bin:$PWD/.local/arm-binutils/usr/bin:$PATH" \
  python3 tools/hoenn/build_integration_candidate.py --source .local/sevii-integrated-src --jobs 4
```

Os validadores de cada edição são `validate_integrated_piers.py`,
`validate_six_landscape.py`, `validate_integrated_ocean_seams.py`,
`validate_dewford_coast.py`, `validate_integrated_dewford_view.py`,
`validate_coastal_cave_finishing.py`, `validate_review_mode.py` e
`validate_cold_boot.py`. Este último precisa de um bridge com a API
`load_save` para carregar explicitamente o arquivo de bateria.

Depois das provas correspondentes aos arquivos finais:

```bash
python3 tools/hoenn/publish_sevii_integrated_piers.py --source .local/sevii-integrated-src
python3 tools/hoenn/run_versions_browser.py
python3 tools/hoenn/stage_pages.py --output /tmp/player-site
```
