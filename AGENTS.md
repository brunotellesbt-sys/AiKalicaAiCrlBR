Retomada mais recente: [docs/RETOMADA-2026-11-17.md](docs/RETOMADA-2026-11-17.md).
PR112 foi merged pelo autor emmain9dff8c3. Branch atual de trabalho:
fix/cave-chambers-release-validation-2026-11-17. Gates finais e cavernas em trabalho.

# Instruções persistentes do projeto

Antes de editar mapas conectados, aplique também [Aqui/SKILL-DIVISAS-E-CAMERAS.md](Aqui/SKILL-DIVISAS-E-CAMERAS.md): layout declarado/ativo, faixa do vizinho, bancos, diagonais e cache `mapView` precisam concordar antes e depois da travessia.

Antes de qualquer tarefa, leia [docs/CONTINUIDADE-TECNICA-IA.md](docs/CONTINUIDADE-TECNICA-IA.md)
e o JSON histórico lá vinculado. Após cada lote coerente, atualize esse guia e
`errors/ESTADO-DA-TAREFA.txt` com o pedido literal mais recente, o último pedido
concluído, o pedido ainda incompleto, arquivos, provas/hashes, limitações e
próximo passo. Faça checkpoint e push verificado antes de operações longas.
O usuário pediu explicitamente PR normal, sem rascunho, nesta continuidade;
descreva as pendências sem confundir abertura do PR com validação/publicação
das ROMs. Preserve o ambiente antigo e as preparações parciais.

Para qualquer alteração de cidades, portos, ginásios, interiores, terreno, praias ou rotas de Surf, leia e aplique [.agents/skills/gba-map-review/SKILL.md](.agents/skills/gba-map-review/SKILL.md).

Consulte também [errors/README.md](errors/README.md) e o registro de erros relevante antes de editar; atualize-o com reprodução, causa, solução e provas da ROM final para evitar regressões já documentadas.

O usuário exige revisão visual do mapa inteiro, objetos completos e validação de colisões, acessos e conexões na ROM. A preferência anterior por gerar uma proposta inspirada em GBA foi dispensada explicitamente pelo usuário nesta revisão: não gere novas propostas sem um novo pedido. Não apresente imagem gerada como captura do jogo. Não altere o mapa-múndi sem autorização explícita.

Para diagnóstico preciso sem repetir o histórico, consulte primeiro a seção RESUMO de [docs/AJUSTES-GBA.txt](docs/AJUSTES-GBA.txt) e apenas as seções relevantes. Use `tools/hoenn/inspect_map_tile.py` para obter bloco, altura, colisão, camadas e gráficos reais. Os exemplos reutilizáveis ficam em [assets/tiles/](assets/tiles/), com mapa doador e banco explícitos; nunca trate IDs como universais nem copie somente parte de um objeto.
