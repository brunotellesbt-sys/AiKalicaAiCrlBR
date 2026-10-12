# Integração em desenvolvimento

Este PR guarda o progresso das 86 camadas de integração. **Não é a entrega final das quatro versões.** A ROM publicada em `playable/` continua sendo a alpha validada de 64 camadas; seus relatórios e verificação de integridade permanecem separados dos resultados da integração nova.

## Implementado na fonte candidata

- Mapa integrado na Pokédex e ampliação de 2× por pixels, também no mapa do menu e dos Centros Pokémon.
- Perfis competitivos para adversários importantes, regras Normal/Hard e limite de gerações.
- Portos menores de Mossdeep e Pacifidlog, ajustes de chegada e escolha/confirmacão da cidade inicial.
- Rivais Eren e Luffy, sprites, equipes, batalhas em parceria e capítulo Galactic no navio, com bloqueio das Ligas até concluir o capítulo.
- Cavernas para Paradoxos e sprites de encontros especiais.
- Requisitos de evolução por nível para treinadores. Evoluções por pedra/item exigem nível 30, 35 ou 40 conforme os atributos da evolução, sem alterar as pedras do jogador.
- Correção do retorno de Mega Floette à forma Eternal Flower após a batalha.

## Evidências e limites

Os relatórios em `integration-validation/` registram o SHA-256 da ROM efetivamente testada. Eles foram produzidos em etapas diferentes e **não constituem uma validação conjunta da ROM final**.

- Limites de evolução por item: seleção nativa testada imediatamente abaixo e no nível mínimo, incluindo métodos alternativos e cadeia ancestral.
- Crossover: equipes nativas em três médias de nível, golpes legais, EVs/IVs, contadores independentes e Mold Breaker restrito à batalha específica de Eren.
- Galactic: batalhas reais dos 19 grunts e sequência final, incluindo as duas batalhas em parceria. O teste prepara progresso anterior e fortalece a equipe do jogador; não comprova o balanceamento de uma campanha completa.
- Megas: transformação e retorno nativos de 91 Megas, em 92 casos incluindo as duas origens de Zygarde. Não são 91 batalhas completas jogadas por controles.
- Atributos: auditoria contra uma referência versionada de Pokémon Showdown, incluindo as Megas.
- Mapa: abertura e retorno da Pokédex e ampliação de pixels no emulador.

## Pendências antes da entrega final

- Regenerar e validar habitats e locais da Pokédex nas quatro versões, incluindo a separação aquática/terrestre.
- Completar a distribuição de itens de evolução, Mega Stones e seus índices.
- Concluir o estojo das 16 insígnias e o DOCX das equipes por ordem dos ginásios.
- Auditar presença única dos personagens e todos os caminhos obrigatórios da história; corrigir posições e visibilidade restantes no capítulo final.
- Validar métodos especiais de evolução e as duas campanhas completas na fonte final.
- Reproduzir toda a cadeia em fonte limpa, exportar quatro ROMs, gerar evidências com o mesmo hash e integrar a seleção no GitHub Pages.

## Compilação da candidata

Com a toolchain ARM configurada, use `python3 tools/hoenn/build_integration_candidate.py --source CAMINHO_DA_FONTE --jobs 4`. O comando prepara as camadas e confere os hashes da fonte, sem sobrescrever a alpha publicada. A reprodução completa em fonte limpa ainda está pendente.

Para testar a abertura nova, use `validate_campaign_playthrough_candidate.py`; `validate_campaign_playthrough.py` conserva o executor correspondente às evidências da alpha publicada.
