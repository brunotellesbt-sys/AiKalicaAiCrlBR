# Rotas físicas segundo o atlas — camada 172

**Em reconstrução. Sem ROM 172 validada ou publicada.**

O ambiente que continha a implementação anterior está indisponível. A base
recuperada é a revisão 171, commit `7ec174b8f7d0c621ec9a60d8b771619e86628889`.
Os scripts, relatórios e candidatos locais da camada 172 não foram recuperados.
O estado verificável e as exigências recebidas estão em
[ESTADO-DA-TAREFA.txt](../errors/ESTADO-DA-TAREFA.txt).

A arte original do mapa-múndi é a referência imutável. A nova rede deve
respeitar direção, distância, conexões e posições físicas, com escala de oito
tiles por pixel e corredores de seis tiles. O marcador do jogador precisa
derivar das coordenadas globais afins; mover só o GPS não corrige geografia.

A entrega exige prova independente da classificação da arte e da rede,
migração versionada de saves, índices de consulta compactos, ecologia com
gatilhos efetivos, revisão dos mapas inteiros e travessias reais na ROM.
Relatórios estáticos ou de candidatos anteriores não substituem essas provas.

O código será preservado em checkpoints remotos. Enquanto houver pendências,
o PR deve permanecer em rascunho e as ROMs públicas continuam na revisão 171.
