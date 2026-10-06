# Escolher a cidade inicial em LeafGreen

Abra **LeafGreen-Choose-Starting-City.gba** no mGBA e inicie uma **partida nova**, com um save separado das outras versões. A ROM e o ZIP originais foram preservados. Esta versão também contém a remoção dos obstáculos terrestres de HM do PR anterior.

## Como funciona

No começo do jogo, escolha entre **16 locais**: Pallet, Viridian, Pewter, Cerulean, Vermilion, Lavender, Celadon, Fuchsia, Saffron e as **sete ilhas Sevii**, incluindo as ilhas normalmente liberadas no pós-game. Cada local tem **uma única casa fixa**. Você escolhe somente a cidade ou ilha; a casa é sempre a mesma.

A lista está em [homes.json](../../tools/journey/homes.json). As residências necessárias à história foram excluídas: Mr. Fuji, Warden, a senhora do Tea, a casa roubada de Cerulean, a família do rival, Copycat, Lorelei e a família de Lostelle. Nenhum prédio inteiro vira residência da família. Conversas, serviços e itens opcionais dos antigos moradores da casa escolhida podem ser substituídos, incluindo Move Maniac, Sticker Man e a sala opcional do Trainer House da Ilha 7.

**Os barcos entre Vermilion e as sete ilhas funcionam desde o início**, em ambos os sentidos. Fale com o marinheiro do porto; use “Other” para acessar a segunda página de destinos. A regra de transporte é independente das missões de Bill, Celio e Lostelle, das insígnias e da Liga: não marca essas missões como concluídas nem concede passes de eventos. O S.S. Anne mantém a exigência do S.S. Ticket e seus eventos originais.

Somente a residência escolhida recebe um interior com quarto, escada, sala e mesa. O quarto usa o desenho do quarto original; a sala usa o desenho da casa original de Pallet. Os moradores humanos daquela casa são convertidos em família: uma mulher adulta é preferida para o papel de mãe; os demais viram pai, irmã ou irmão conforme o perfil do personagem. Os sprites passam a representar os papéis familiares. Animais e objetos não contam como familiares. As outras casas continuam com seus moradores e eventos originais.

- A mãe entrega **HM03 Surf**; outro familiar entrega **HM07 Waterfall**.
- Se só houver a mãe, ela entrega **os dois HMs**.
- Um terceiro familiar entrega **três Potions**.
- Os presentes são entregues uma única vez. Se a bolsa estiver cheia, o que falta fica disponível para a próxima conversa.
- Depois dos presentes, a mãe usa os mesmos scripts de diálogo e cura da mãe original. Esses diálogos originais permanecem em inglês.

**Surf e Waterfall podem ser usados sem insígnias**, tanto por interação no mapa quanto pelo menu Pokémon. Ainda é preciso ensinar o movimento a um Pokémon compatível. A água e as cachoeiras continuam com seu comportamento normal; não podem ser atravessadas a pé.

Em cidades diferentes de Pallet, você nasce no quarto. Ao descer a escada, Oak está na sala e há uma maleta sobre a mesa. **Fale com Oak**: ele diz que é amigo dos seus pais e veio visitar a família, oferece **Bulbasaur, Charmander ou Squirtle no nível 5**, entrega a **Pokédex** e cinco Poké Balls e volta ao laboratório em Pallet. O evento não se repete. A porta impede sair sem receber o primeiro Pokémon. O começo da história fica no estado correspondente à entrega da Pokédex, evitando repetir a sequência do inicial, a batalha inicial no laboratório e a encomenda de Viridian. As escolhas do rival permanecem coerentes com seu inicial.

Em **Pallet**, a casa elegível é a casa original, e o encontro com Oak e a entrega do inicial/Pokédex continuam no laboratório, como no jogo original. A mãe também dá os dois HMs. Cinnabar e Indigo não aparecem no menu porque não têm residência elegível.

## Arquivos e reprodução

- `LeafGreen-Choose-Starting-City.gba`: ROM pronta.
- `LeafGreen-Choose-Starting-City.bps`: patch para a **ROM original USA v1.1**, não para a ROM do PR anterior. Aplique com Floating IPS.
- `manifest.json`: hashes, casas, exclusões, arquivos de implementação e alterações terrestres de HM.
- `debug-reference.json`: endereços e IDs para reproduzir os testes da ROM construída.
- `validation/`: capturas e resultados dos testes no mGBA.

A implementação está em [tools/journey](../../tools/journey). Usa a revisão `037335f4c725d7c9aecdac87066f2002b4bd7e14` de [pret/pokefirered](https://github.com/pret/pokefirered/tree/037335f4c725d7c9aecdac87066f2002b4bd7e14), cuja compilação original foi comparada byte a byte com a ROM fornecida. O compilador agbcc usado foi `da598c1d918402c42c0c0d7128ba14567f3175e9`.

Para reconstruir, prepare um checkout **separado e limpo** desse commit, instale agbcc nele seguindo a documentação de pret, e disponibilize ARM binutils, make, compiladores C/C++ e libpng. O overlay recusa outro commit ou mudanças existentes em arquivos rastreados. Então execute:

```sh
python3 tools/journey/build.py --source .local/journey-src --nm arm-none-eabi-nm
python3 -m unittest discover -s tools/rom_hacks -v
python3 -m unittest discover -s tools/journey -v
```

O processo aplica o overlay, compila `leafgreen_rev1`, identifica os endereços pelo ELF dessa compilação e aplica a remoção dos obstáculos terrestres. Finalmente gera a ROM combinada e o BPS contra a ROM original. Não depende de Wine ou de editores Windows.

Para testar no núcleo mGBA, use a ponte e as instruções de compilação em [no-hm-walls/README.md](../no-hm-walls/README.md), depois execute:

```sh
python3 tools/journey/validate_emulator.py --library .local/mgba-bridge.so
```

Os testes usam comandos temporários na memória do emulador para chegar a outras casas e cenários; esses comandos não fazem parte da ROM entregue. Passaram **72 verificações no mGBA**, cobrindo escolha pelo menu real, escada, visita de Oak, três iniciais, Pokédex, cura, presentes, todas as casas, casa fixa por cidade, saídas das casas e viagens antecipadas entre Kanto e as sete ilhas e uso real de Surf/Waterfall sem insígnias. Os seis testes de integridade/BPS desta versão e os seis da modificação terrestre também passaram. A campanha inteira ainda não foi jogada até o final; saves de outras versões não são suportados.
