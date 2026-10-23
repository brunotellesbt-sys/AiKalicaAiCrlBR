# Instruções persistentes do projeto

Para qualquer alteração de cidades, portos, ginásios, interiores, terreno, praias ou rotas de Surf, leia e aplique [.agents/skills/gba-map-review/SKILL.md](.agents/skills/gba-map-review/SKILL.md).

O usuário exige revisão visual do mapa inteiro, objetos completos e validação de colisões, acessos e conexões na ROM. A preferência anterior por gerar uma proposta inspirada em GBA foi dispensada explicitamente pelo usuário nesta revisão: não gere novas propostas sem um novo pedido. Não apresente imagem gerada como captura do jogo. Não altere o mapa-múndi sem autorização explícita.

Para diagnóstico preciso sem repetir o histórico, consulte primeiro a seção RESUMO de [docs/AJUSTES-GBA.txt](docs/AJUSTES-GBA.txt) e apenas as seções relevantes. Use `tools/hoenn/inspect_map_tile.py` para obter bloco, altura, colisão, camadas e gráficos reais. Os exemplos reutilizáveis ficam em [assets/tiles/](assets/tiles/), com mapa doador e banco explícitos; nunca trate IDs como universais nem copie somente parte de um objeto.
