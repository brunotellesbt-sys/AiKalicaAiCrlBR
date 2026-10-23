# Downloads Ubuntu da CI

Os jobs `sea-routes` e `pages` usam Ubuntu 24.04. Antes de instalar o Chromium,
`configure_ubuntu_apt.py` troca o espelho Ubuntu da Azure e a lista de espelhos
do runner pelo arquivo oficial `https://archive.ubuntu.com/ubuntu`.
As suites, componentes, chaves de assinatura e os demais repositórios são
preservados. O APT recebe timeout de 30 segundos e duas novas tentativas por
download; verificação de assinaturas e TLS permanece habilitada.

Isso corrige o bloqueio observado em `fonts-freefont-ttf`, que consumiu o
limite de dez minutos do job durante `playwright install --with-deps chromium`.
A instalação completa do Playwright, o limite do job e todas as validações
continuam em vigor. As ROMs não precisam ser recompiladas para este ajuste.

Na raiz do repositório, execute os testes sem alterar o APT da máquina:

```bash
python3 -m unittest discover -s tools/ci -v
```

Os testes usam uma árvore temporária com fontes APT de exemplo, conferem a
preservação dos repositórios e das chaves, rejeitam outro sistema operacional
e verificam a execução repetida. O parâmetro `--root` é destinado a essas
árvores de teste. A execução normal é feita com `sudo` somente nos runners
Ubuntu 24.04 das workflows.
