# Provas da revisão 171

Os renders de fonte mostram os mapas inteiros antes/depois, com NPCs e
identificação explícita: não são capturas do emulador. Para o novo canal,
o painel anterior informa que o mapa ainda não existia; não inventa um
render histórico.

Os relatórios nativos registram movimentos pelos controles, BG/VRAM/OAM,
pixels, animação e baterias de save. Posições iniciais e condições de teste
são declaradas como fixtures. Nenhuma captura antiga certifica a nova ROM.

Os diretórios abaixo recebem os resultados finais vinculados ao SHA-256
da ROM e do ELF. A existência deste índice não substitui a conclusão dos
relatórios nem o selo do manifesto publicado.

- [Fonte, mapas completos e comparação compilada](../../../mods/hoenn/generated-area-review-validation/common/source/)
- [Câmeras das duas emendas e controles preservados](../../../mods/hoenn/generated-area-review-validation/common/native/coast/)
- [Objetos completos da caverna, percurso real e saves](../../../mods/hoenn/generated-area-review-validation/common/native/caves/)
- [Sete embarques, rochas e limites dos portos](../../../mods/hoenn/generated-area-review-validation/common/native/ports/)
- [Canal vertical, mar horizontal, animação e Continue](../../../mods/hoenn/generated-area-review-validation/common/native/south/)
- [Regressão costeira das correções anteriores, reexecutada](../../../mods/hoenn/generated-area-review-validation/common/native/coast-regression/)
- [Abertura e regras das cinco edições](../../../mods/hoenn/generated-area-review-validation/editions/)

O recorte não equivale a quatro campanhas completas. Censos de fonte não
demonstram, sozinhos, que o jogador percorreu todas as cavernas, ginásios
e eventos. O relatório de fonte separa as verificações geométricas dos
percursos realmente executados na ROM.

Verificações concluídas: 12 provas atuais, cinco aberturas nativas e cinco
aberturas no navegador; 825 testes de Hoenn, 12 de Surf e 6 de CI aprovados.
A ROM nativa tem SHA-256
`52156af727381fb5b47dacf83f8f57696e05dae05c4971368310b98515eba935`;
as edições exportadas têm identidades próprias registradas no manifesto.
