# Pokémon Tower: família de Marowak e nível do fantasma

Cubone, Marowak e Marowak de Alola passam de Diglett’s Cave para os cinco
andares de encontros da Pokémon Tower. Nidoran♀, Nidorina e Nidoqueen fazem
a troca inversa. A torre mantém quatro famílias; a caverna mantém cinco.
As demais 442 famílias conservam seus locais, incluindo Drowzee/Hypno em
Berry Forest e Skorupi/Drapion em Mt. Pyre.

A candidata é `cccad98c4ecb02105da420913043ee854355f875a14591a6fc144f4dd8f75d0a`.
A camada `tower-habitats` vem após `lostelle-habitats`. Altera quatro arquivos:
slots de encontros, pools adaptativos, áreas da Pokédex e a reconstrução do
fantasma em `src/battle_setup.c`. Scripts, coordenadas, escadas, textos e
regras de história da torre permanecem iguais.

## Correção de nível

O evento já criava Marowak respeitando a média da equipe −5/+2. Com o Silph
Scope, `StartMarowakBattle` recriava o Pokémon para definir sexo/natureza,
mas usava novamente o nível fixo 30. A versão anterior reproduziu o erro:
equipe de nível 5, faixa esperada 1–7, Marowak de nível 30.

A reconstrução agora reutiliza o nível do Pokémon que o script criou. Mantém
Marowak, sexo feminino, natureza Serious e o valor de IVs codificado pelo
original. Não aplica a rotação de estágios evolutivos ao fantasma da história.
A impossibilidade de capturá-lo permanece no código; tentativas de captura
não foram exercitadas nesta validação.

## Distribuição

| Habitat | Família transferida | Chance de família em encontro terrestre |
|---|---|---|
| Pokémon Tower | Cubone / Marowak / Marowak de Alola | 49% |
| Diglett’s Cave | Nidoran♀ / Nidorina / Nidoqueen | 21% |

Nos encontros aleatórios, os estágios continuam pela média das insígnias:
Cubone no início, Cubone e as duas formas de Marowak no meio, as duas formas
no final; Nidoran♀ no início, Nidoran♀/Nidorina no meio, Nidorina/Nidoqueen
no final. Pesos e slots foram recalculados mantendo a ordem de raridade.
Água, pesca e todos os demais habitats conservam seus pools.

Os locais atualizados estão no [guia](POKEMON-LOCATIONS.md) e na
[planilha](pokemon-locations.csv). O gerador usa as camadas em ordem para
preservar as duas trocas de famílias nas próximas gerações do documento.

## Verificação

- Construção ARM, reaplicação determinística e idempotência dos quatro arquivos.
- Regressão nativa dos 135 habitats, níveis, média regional, famílias aquáticas,
  chances de pesca e primeira Pokédex Nacional.
- 508 casos de mapa/família na função utilizada pela Pokédex, verificando seis
  espécies nos 254 mapas de encontros; 18 casos evolutivos nos seis mapas afetados.
- Evento original por coordenada: fuga sem Silph Scope deixa a cena pendente;
  quatro vitórias com o item concluem a cena. Equipes de níveis 5, 40, 100 e
  uma equipe mista 7/21/44 mantêm o fantasma na faixa correta.
- Salvamento e Continue após a vitória mantêm Silph Scope e conclusão;
  caminhada entra no sétimo andar pela escada original voltada para a esquerda.
- Auditoria de inglês permanece válida.

Relatórios em [tower-habitat-validation](tower-habitat-validation).
A falha esperada da candidata anterior está separada em `baseline-regression.json`;
as evidências da nova candidata estão em `tower-ghost.json`, `tower-habitats.json`
e `wild.json`.

## Inventário dos demais eventos fixos

O novo `audit_story_encounters.py` percorre referências entre scripts locais
e compartilhados. Inclui explicitamente o callback de Sudowoodo acionado pelo
Wailmer Pail em `item_use.c`, que não é referenciado pelo script de conversa.

Foram encontradas 130 associações de mapa/script/espécie e 13 casos
fora do habitat aleatório: Voltorb/Electrode em Aqua Hideout, New Mauville e
Power Plant; Snorlax nas Rotas 12 e 16; Kecleon nas Rotas 119 e 120; Sudowoodo
na Frontier. Hypno e Marowak não aparecem mais nessa lista de divergências.

Isso é um inventário estático: condições/flags não foram avaliadas, há 360
raízes de eventos não resolvidas e não se garantiu cobertura de saltos dinâmicos,
macros ou espécies escolhidas pelo motor. Os eventos restantes continuam como
no original nesta revisão. A preferência sobre exceções para os eventos que
repetem famílias está pendente; não se afirma exclusividade global de todos
os encontros fixos.

## Reprodução e limites

```sh
cp -a .local/hoenn-lostelle-habitats-src .local/hoenn-tower-habitats-src
python3 tools/hoenn/prepare_tower_habitats.py --source .local/hoenn-tower-habitats-src
PATH="$PWD/.local/arm-gcc/usr/bin:$PWD/.local/arm-binutils/usr/bin:$PATH" make -C .local/hoenn-tower-habitats-src -j4
python3 tools/hoenn/verify_abilities.py --source .local/hoenn-lostelle-habitats-src --candidate .local/hoenn-tower-habitats-src --output mods/hoenn/tower-habitat-validation/preparation --layer tower-habitats
python3 tools/hoenn/validate_wild.py --source .local/hoenn-tower-habitats-src --library .local/mgba-bridge.so --output mods/hoenn/tower-habitat-validation
python3 tools/hoenn/validate_tower_habitats.py --source .local/hoenn-tower-habitats-src --library .local/mgba-bridge.so --output mods/hoenn/tower-habitat-validation
python3 tools/hoenn/validate_tower_ghost.py --source .local/hoenn-tower-habitats-src --library .local/mgba-bridge.so --output mods/hoenn/tower-habitat-validation
python3 tools/hoenn/audit_story_encounters.py --source .local/hoenn-tower-habitats-src --output mods/hoenn/tower-habitat-validation/fixed-encounters.json
python3 tools/hoenn/document_habitats.py --source .local/hoenn-tower-habitats-src --output mods/hoenn
python3 -m unittest discover -s tools/hoenn -v
```

Posição, equipe, inventário e flags dos três treinadores comuns da torre são
fixtures. HP, ataque, velocidade, PP e limpeza de condições/confusão da equipe
foram ajustados em RAM para isolar o evento; vitórias, fuga, cena e escada são
nativas. A cópia do Pokémon inimigo é lida enquanto a batalha está ativa e
decodificada depois do retorno, pois o motor limpa a equipe inimiga ao sair.
Não há validação de dificuldade, campanha completa, captura na grama ou revisão
visual da tela de áreas da Pokédex. O player continua com sua versão anterior;
a candidata exige novo jogo e não há conversão de saves.
