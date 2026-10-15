# Porto de Sootopolis: validação das quatro edições

[Imagens e implementação](../../../docs/porto-sootopolis.md).

Cada relatório identifica o SHA-256 da ROM executada no mGBA:

- [Gen 1–4 Normal](Gen1-4-Normal/sootopolis-harbor.json)
- [Gen 1–4 Hard](Gen1-4-Hard/sootopolis-harbor.json)
- [Gen 1–9 Normal](Gen1-9-Normal/sootopolis-harbor.json)
- [Gen 1–9 Hard](Gen1-9-Hard/sootopolis-harbor.json)
- [Fonte comum, antes do cabeçalho de edição](validation/sootopolis-harbor.json)
- [Reprodução independente e idempotência](validation/reproduction.json)

São testados ponte sem Surf, portas, colisão do submarino 64×64, viagem de ida e
volta pela rede mundial, grama na cabeceira, ausência da fileira inferior e acesso
no mapa da crise. Os arquivos `special-encounters.json` de cada edição também
registram testes novos da oficina, captura, formas e habitats. Posição inicial e história
são fixtures; as caminhadas, conversas e viagens usam o controle. A campanha
inteira não foi repetida.
