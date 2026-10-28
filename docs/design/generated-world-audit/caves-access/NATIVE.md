# Passagens nativas da versão corrigida

ROM verificada: `b04918724939a54bbe3321d274953a9311ab8c7b4eebc3cbeb844ffcd3604386`.
Os relatórios finais ficam em
`mods/hoenn/generated-world-audit-validation/common/caves/generated-cave-routes.json`
e `common/coastal-caves/coastal-cave-access.json` no mesmo diretório de validação.

- 26 cavernas criadas: entrada, 97 aproximações aos NPCs e retorno pelos controles.
- Sete alojamentos antigos: salvar, continuar e sair para o desembarque atual.
- Cinco pontos de mergulho: Surf, prompt de Dive, entrada e saída da caverna,
  prompt de retorno à superfície e posição original preservada.
- Navel Rock: caverna, exterior e píer seco; saída com Surf e desembarque de volta.
- Verificação complementar das 14 ilhas de santuários e de Seafoam: partir do
  mar, alcançar a caverna e retornar, incluindo os cinco acessos por mergulho.

As duas provas incluem 63 capturas nativas com seus hashes. Posição inicial,
equipe, modo inicial e treinadores Rocket já derrotados são fixtures declaradas.
As rotas seguintes usam os controles; batalhas e capturas lendárias não são o
objeto destas provas. A campanha Galactic possui validação separada.

A primeira tentativa do controlador escolhia `(3,2)` atrás da porta de retorno
da base Rocket. O jogo chega corretamente em `(3,4)`: o metatile da escada é uma
porta não animada. O controlador passou a escolher o lado interno da porta,
confirmou o caso isolado e repetiu as 26 cavernas. Essa correção é do teste;
nenhum byte da ROM ou do ELF congelados mudou durante a execução.
