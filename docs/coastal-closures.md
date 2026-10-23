# Encostas completas, praias animadas e rotas costeiras

Six Island recebe a lateral oeste inteira, o canto superior recuado e o pé da
montanha junto ao porto, incluindo sua continuação em Water Path. Seis árvores
inteiras deram espaço à encosta; as outras doze conservam copa, corpo e base.
Prédios, portas, NPCs, pontes e conexões permanecem.

Em Dewford e nas rotas 106 e 107, a areia seca do terminal fica no mesmo nível
da borda de praia. Isso elimina as diferenças invisíveis que prendiam o
jogador. A ponte alta conserva pedestre no nível 4 e Surf no nível 1, com
transições nas duas escadas. A ponta direita da escada usa a peça nativa inteira.
Os dois vendedores continuam acessíveis.

A praia privada usa os oito quadros nativos de água e espuma, incluindo os
cantos e a água visível sob a ponte. A atualização conserva a mesma fase dos
gráficos. Ao carregar novamente o banco secundário, uma atualização única após
o DMA repõe a fase corrente; a cópia do banco não pode recolocar o desenho
estático por cima da animação. O código atua apenas no banco privado de Dewford.

Os sete antigos portos separados, que já tinham sido substituídos por mar,
passam a se chamar **ONE ISLAND COAST** até **SEVEN ISLAND COAST**. Os nomes
aparecem no banner e na interface do mapa. A projeção corrige as voltas
artificiais do marcador no interior desses trechos: 1.013 posições mudam em
sete grades, preservando todas as 25 fronteiras compartilhadas e as outras
grades. As curvas menores que acompanham a geometria esquemática são
documentadas nas comparações. Nenhuma rota física adicional foi necessária.
Os gráficos, a paleta, o desenho e os pontos do mapa-múndi permanecem iguais.

## Consulta e reutilização

- [Guia prático em TXT](AJUSTES-GBA.txt): diagnóstico, exemplos de tiles,
  acabamento, animações, testes e prompts completos.
- [Pasta local de tiles](../assets/tiles/README.md): 33 exemplos nomeados,
  344 quadros e os gráficos e paletas nativos. Emerald e FRLG ficam separados.
- [Comparações da projeção](design/coastal-closures/route-projection/README.md):
  antes/depois sobre o atlas preservado, identificados como renderizações de source.
- [Contrato da validação](design/coastal-closures/VALIDATION.md): provas nativas,
  hashes, cobertura e limitações.

Consulta curta sem carregar tabelas inteiras no contexto:

```bash
python3 tools/hoenn/catalog_common_tiles.py --find "frlg praia reta"
python3 tools/hoenn/catalog_common_tiles.py --verify assets/tiles
python3 tools/hoenn/inspect_map_tile.py --source SOURCE --map Route107 --x 2 --y 5 --radius 1 --output /tmp/tile-dewford
```

O exportador e o inspetor leem os dados reais; os PNGs de source não são
capturas do emulador. Copiar uma imagem achatada para outro slot não transfere
seu comportamento, sua paleta nem sua animação.

## Validação e distribuição

A camada 163 exige auditoria independente dos 24 arquivos alterados e 31
relatórios ligados aos hashes finais. Em cada edição são conferidos Six,
Dewford, as animações, conexões e posição do marcador, o modo de exploração
e a abertura do jogo. Os componentes incluem os sete portos integrados e as
26 emendas de água. Posições iniciais e progresso dos testes são fixtures
declaradas; os percursos usam os controles do emulador.

O executor `run_coastal_validation.py` agrupa as verificações sobre edições
congeladas, limita os processos paralelos, registra logs e verifica que ROM e
ELF não mudaram. Nunca compile enquanto esses leitores estiverem executando.

```bash
python3 tools/hoenn/run_coastal_validation.py --frozen FROZEN.json --output mods/hoenn/coastal-closures-validation --jobs 2 --video --assemble
```

As quatro ROMs normais e a TESTE recebem os mesmos mapas. A TESTE mantém
encontros aleatórios e abordagens automáticas de treinadores desativados;
interações manuais continuam disponíveis. Seu save é testado no Continue.
Ela permanece em `roms/rom-de-teste/`, separada do ZIP das quatro edições.
O player do Pages recebe os arquivos após o merge.

As 42 provas da camada 162 e as anteriores mantêm seus hashes históricos.
Esta entrega não representa uma nova campanha completa jogada. A tela azul
relatada anteriormente no My Boy não teve sua causa específica reproduzida
no mGBA; as verificações de boot registram apenas o comportamento observado.
