# Revisão dos mapas criados

Esta camada parte do merge do PR 101 (`48d328c`) e conserva os pixels do
mapa-múndi, a campanha e a ABI dos saves. O inventário compara os arquivos
atuais com o upstream fixado na aquisição: 667 mapas receberam alterações
diretas, 414 têm terreno alterado e 234 são consumidores indiretos de bancos
ou scripts compartilhados. Inventário, inspeção visual e teste na ROM são
resultados distintos.

## Correções

- 228 objetos de rocha incompletos nas costas: restauração de 227 rochas
  nativas de 2 × 2 dentro das células já bloqueadas; uma metade isolada na
  Rota 126 virou pedra pequena inteira, conservando a água livre abaixo.
- Três copas abaixo do ginásio de Three Island: floresta terminada com
  árvores completas e acesso livre à porta do ginásio.
- Sete quartos de portos antigos: saída redirecionada ao desembarque atual
  da mesma ilha, mantendo os IDs dos mapas para saves antigos.
- Bases Rocket: cantos isolados de móveis substituídos por mesas nativas
  completas, mantendo acesso aos NPCs e portas.
- Cavernas Paradox: remoção da fileira de topos de escada usada como piso;
  duas escadas completas em posições acessíveis, com os mesmos IDs de warp.
- Cinco mapas subaquáticos: parede repetida usada como piso substituída por
  chão nativo; entradas de cavernas e limites fechados com peças completas.

São 40 arquivos de recursos: 32 terrenos e oito definições de mapa. Os
atributos do piso subaquático, alturas, eventos e conexões preservados são
conferidos pelo gerador. As mudanças de colisão para completar o relevo e os
móveis são verificadas por caminhos na ROM.

## Como reproduzir

Use a skill `.agents/skills/gba-map-review/SKILL.md` e o roteiro curto em
`docs/AJUSTES-GBA.txt`. Os doadores e bancos de tiles permanecem em
`assets/tiles/`; IDs pertencem ao banco indicado, não são universais.

```sh
python3 tools/hoenn/prepare_generated_world_audit.py \
  --source .local/generated-world-audit-src --clone-from .local/badge-story-src
python3 tools/hoenn/validate_generated_world_source.py \
  --source .local/generated-world-audit-src --baseline .local/badge-story-src \
  --output /tmp/generated-source.json --preflight
```

Compile a candidata isolada antes de congelar as cinco edições com
`freeze_generated_world_audit.py`. Nunca compile enquanto um validador lê
essa fonte, ELF ou ROM. Cada relatório final contém o SHA da ROM executada;
as provas anteriores continuam identificadas como históricas.

Os validadores específicos percorrem os ginásios, quartos, cavernas,
mergulhos, praias e píeres com controles. `run_generated_surface_navigation.py`
divide as emendas entre processos independentes e exige cobertura completa
para unir os resultados. Colocação inicial, progresso e equipes de teste são
fixtures declaradas; o percurso não escreve coordenadas do personagem.

`audit_generated_shore_animation.py` separa o censo de referências gráficas
das fases observadas na VRAM e dos pixels realmente desenhados na câmera.
Callbacks e relógios de animação não são escritos. O banco compartilhado do
interior do Battle Palace fica explicitamente fora da amostragem nativa
de praias; os outros bancos aplicáveis e as sete costas Sevii são amostrados.

## Evidências

O inventário e os mapas inteiros ficam em `docs/design/generated-world-audit/`.
As imagens de source são rotuladas; não representam capturas do emulador.
Os renders finais vinculam mapa, layout, blockdata, bancos e imagens por hash,
evitando aceitar um PNG antigo como retrato da versão atual.

As provas nativas atuais ficam em
`mods/hoenn/generated-world-audit-validation/`. `proof-plan.json` seleciona os
relatórios completos; `publish_generated_world_audit.py --preflight` verifica
seus contratos antes de atualizar as ROMs, TESTE/save, ZIP e player.

As verificações de portas, deslocamento, animação e batalhas são recortes
reproduzíveis. Elas não representam uma campanha inteira jogada do início
ao fim nem uma certificação automática de toda escolha estética.

## Resultado da versão final

ROM-base: `b04918724939a54bbe3321d274953a9311ab8c7b4eebc3cbeb844ffcd3604386`.
O plano final vincula 26 relatórios completos aos bytes executados.

- 990 travessias nativas: 854 com Surf e 136 a pé, em 470 emendas.
- 55 ligações marítimas extensas percorridas nos dois sentidos, com bancos,
  cor do oceano, estado de Surf e posição no mapa conferidos.
- 26 cavernas, 97 aproximações a NPCs, sete saves antigos retomados e cinco
  mergulhos completos; mais 15 acessos marítimos e o percurso de Navel Rock.
- Oito ginásios: 32 treinadores e oito líderes nas normais; 32 abordagens
  automáticas suprimidas na TESTE, com desafios manuais preservados.
- Água e espuma verificadas nos bancos aplicáveis e nas sete costas Sevii;
  animação de Dewford conferida separadamente em oito fases e seis emendas.
- Cinco ROMs com boot nativo e boot no player; TESTE também com o save
  distribuído. Stage do GitHub Pages validado localmente.
- 489 testes Hoenn, 12 de rotas marítimas e seis de CI aprovados.

O ZIP contém as quatro normais e as provas nativas atuais. A TESTE fica na
pasta separada; o índice de imagens de source mantém os hashes e links do
commit visual imutável para os renders de referência fora do ZIP.
