# Encontros aquáticos e acabamento costeiro

Esta revisão parte do PR 102, camada 165 (`af1a430`). O mapa-múndi é preservado.
As alterações da camada `coastal-ecology` são aplicadas em um snapshot separado;
a ROM e os registros da revisão anterior continuam imutáveis.

## Problemas e comportamento esperado

- Há travessias com água navegável sem cabeçalho nativo de encontros ou sem
  família aquática disponível em uma das gerações. Os dois requisitos precisam
  existir para o encontro funcionar; preencher apenas a tabela não basta.
- A água rápida reutilizada pelas costas abertas de Sevii não acionava a
  verificação de encontros. O comportamento deve ser habilitado somente nas
  costas integradas, preservando as barreiras de água rápida de outros mapas.
- Os cinco novos fundos subaquáticos usam piso comum. Esses pisos precisam
  acionar encontros aquáticos somente nos cinco mapas previstos. Quatro rotas
  subaquáticas existentes também precisam do gatilho nos tiles de água sem
  possibilidade de emergir; seu piso comum original continua preservado.
- Trinta árvores isoladas de Pallet usavam duas peças de floresta sobreposta.
  A troca pelo conjunto isolado de Viridian conserva altura, colisão e acessos.
- No vídeo de 28/10, o personagem sai da lateral do píer de One Island para
  a água a pé. A reprodução na ROM anterior identificou água com altura zero
  em `(21,6)` de Treasure Beach, acessível pelo tablado em `(20,6)`.
  A água deve bloquear o pedestre e permitir o embarque nativo com Surf.
  O retorno do Surf para o tablado também precisa continuar funcionando.
- A reprodução com a bateria antiga mostrou que Continue restaurava o modo
  pedestre salvo na água. Uma recuperação restrita a Treasure Beach executa a
  transição nativa para Surf após restaurar o objeto, preservando posição e save.
- Dezesseis pares de rochas perderam suas bases em nove mapas; duas variantes
  de peças superiores tinham escapado do detector anterior. As peças órfãs
  recebem uma frente inteira de encosta, sem alterar suas propriedades físicas.
  O cabo de Kindle Road recebe 26 ajustes nos três mapas que compartilham a borda.
- Oito tiles mistos de grama/água na baía de Pallet permitiam pisar sobre a
  parte azul do desenho. Eles passam a bloquear a caminhada; o corredor de
  grama, o acesso leste e a rampa sul continuam abertos.
- As aproximações secas de Pallet e Cinnabar escondiam parte da cabeça atrás
  das tábuas ao norte. A correção trata somente a prioridade visual, mantendo
  a passagem inferior de Surf e a altura física do pedestre.
- As costas marinhas de Kanto e Sevii recebem bancos privados coerentes com
  a paleta do mar conectado. São 498 palavras inferiores de água em onze
  tabelas e 43 mapas-alvo; objetos, callbacks e água doce permanecem preservados.
  Os dois vídeos de Mossdeep mostram fases da animação original de Emerald:
  a comparação no mesmo quadro não identificou diferença de paleta na ligação.

O [registro em TXT](../errors/2026-10-28-videos-surf-tiles.txt) identifica os
nove vídeos, reprodução, causas, soluções e verificações para evitar regressões.

## Organização dos encontros

As famílias mantêm um único identificador de habitat. Um habitat pode abranger
mapas conectados, sem cadastrar a mesma família em outro identificador.
Os doadores consideram conexão física e ambiente: rio, costa, oceano ou fundo
subaquático. As tabelas atuais, incluindo mudanças posteriores de eventos e
cavernas, são a referência; não são substituídas por uma versão antiga da fauna.

As tabelas terrestres, Rock Smash e encontros ocultos são preservadas.
Instalações com regras próprias, interiores e protótipos aposentados são
registrados separadamente no censo; isso não remove seus encontros existentes.
A ROM TESTE continua sem encontros aleatórios e sem abordagem automática de
treinadores, inclusive nas áreas que passam a ter fauna nas ROMs normais.

## Verificação reproduzível

1. Executar o reparo em memória e comparar a lista de arquivos alterados.
2. Revisar mapas nativos inteiros, peças completas e vizinhos das emendas.
3. Preparar e compilar somente o snapshot novo; congelar ROM, ELF e cinco edições.
4. Ler cabeçalhos, famílias, fases e comportamentos diretamente da ROM compilada.
5. Acionar encontros reais com passos no emulador nas duas faixas de geração;
   verificar a supressão na TESTE. Uma chamada direta que cria um Pokémon não
   prova que o jogador consegue encontrá-lo ao caminhar ou surfar.
6. Percorrer os píeres pelos controles, incluindo laterais, ponta, retorno do
   mar e conexões. Fixtures iniciais devem ser declaradas; não reposicionar o
   personagem durante o percurso para contornar um bloqueio.
7. Fazer boot real das cinco edições, com e sem o save distribuído na TESTE,
   e conferir o player do navegador antes de publicar os arquivos.

Os relatórios em `mods/hoenn/coastal-ecology-validation/` devem registrar o SHA
da ROM efetivamente testada. Renders de source são revisão visual; não são
capturas do emulador nem certificação de movimento. O publicador permanece
bloqueado enquanto faltarem as provas obrigatórias da versão final.

## Resultados da ROM final

ROM-base `f7af65b4856e6697d5d972f48f8699c7c6b7d4b277ea19cfa3949926265d1b89`,
ELF `3f8ba485b37d17f58f7c7a5a64b1a8dd28492a9ea612afdead2487ceef3d1f9e`.
A preparação independente confere 32.244 inputs e os 38 arquivos alterados;
23 binários de mapas e metatiles correspondem aos bytes da ROM compilada.

- As sete ilhas passaram nas 107 fronteiras expostas de píer/água: tentativa
  de sair a pé, prompt nativo de Surf, partida e retorno ao tablado. A bateria
  antiga de Treasure Beach passou em boot real, Continue e retorno por controles.
- Pallet passou nas oito margens mistas bloqueadas e nove aproximações, com
  acesso pela grama, rampa, ponte e cais. Pallet e Cinnabar passaram nas
  32 observações direcionais das 16 células secas e nos dois caminhos inferiores
  de Surf; a comparação usa pixels reais do avatar, incluindo cabeça e pés.
- O censo de objetos verificou 415 mapas de superfície, 613 rochas completas
  e 27 variantes nativas, sem padrões órfãos de rocha ou pinheiros não nativos.
  Os renders inteiros e os percursos das encostas são revisões complementares.
- O censo aquático verifica 434 mapas: 379 requerem encontros e 55 têm exceção
  explícita. Não há lacunas de cabeçalho, pool ou gatilho nos quatro períodos.
  As ROMs normais produziram dez batalhas reais; a TESTE percorreu 1.100 passos
  e 1.000 consultas nativas sem produzir encontros.
- As cinco edições passaram em abertura nativa e revisão de comportamento;
  a TESTE também passou em Continue usando exatamente o novo save distribuído.

As provas atuais identificam seus arquivos e capturas por hash. A campanha,
ginásios e cavernas anteriores são preservados por comparação com a camada
165; seus testes anteriores permanecem identificados como históricos. Esta
entrega não representa uma campanha completa jogada novamente no My Boy.

Na conferência de entrega, passaram 596 testes Hoenn, 12 testes de Surf e
seis testes de CI. As cinco edições abriram no mGBA do navegador, com bytes
conferidos contra o manifesto e saves separados. O player estático do Pages
foi preparado com as cinco ROMs atuais e o registro `errors/`. A publicação
do site depende do merge; o preparo local não altera o site público.
