# Erros de CI — entregar à próxima IA

Registro de 15/11/2026 UTC. Pedido do usuário: guardar os erros nesta pasta
para corrigir com a próxima IA. Este commit SOMENTE documenta; nenhuma
correção, compilação, reexecução de testes ou alteração de pacote foi feita.

## Origem e log completo

- Commit analisado:29b1dca1c0fc4eaea3b7ffe202e39de4c1f1b904.
- [Actions43761665375](https://github.com/brunotellesbt-sys/AiKalicaAiCrlBR/actions/runs/43761665375),
  job132957596992, workflow Validate Surf routes.
- Horários enviados:21:06:47,21:07:21 e21:07:23 UTC.
- [Log completo das etapas, com testes e tracebacks](LOG-CI-2026-11-15.txt).
  Obtido da Actions correspondente; inclui as três etapas enviadas e a
  verificação da alpha histórica. Não é nova execução nem validação aprovada.
- SHA-256 do arquivo de log:
  49755bf3322bbc84f74809c24cb8e7dd76f6a779ed6fe7b969dc314dc87007bf

Começar pelo [guia técnico](README.md). Os três erros abaixo têm duas causas
diferentes: release ainda não validada e documentação do ZIP desatualizada.
Não confundir qualquer um deles com um novo defeito funcional demonstrado da ROM.

## 1. Suíte de testes — 8FAIL e1ERROR

Comandos:

    python3 -m unittest discover -s tools/sea_routes -v
    python3 -m unittest discover -s tools/hoenn -v

Resultado enviado:

    Ran 12 tests in 1.303s
    OK
    Ran 1094 tests in 32.533s
    FAILED (failures=8, errors=1, skipped=34)
    Process completed with exit code 1.

Sete falhas chegam a tools/hoenn/verify_versions.py,linha32:

    if require_seal:assert info['validated'] is True,'Unvalidated release'
    AssertionError: Unvalidated release

Casos: test_campaign_coastal_update, test_continuous_ocean,
test_ever_grande_market, test_sevii_harbors, test_sevii_surf_connections,
test_surf_review e test_three_harbor_terminals.

A oitava falha é test_sootopolis_harbor,linha28:

    self.assertTrue(self.manifest['validated'])
    AssertionError: False is not true

O únicoERROR é setUpClass de test_extra_gyms.ExtraGyms,linha11,
também chamando verify() e recebendo Unvalidated release.

Causa conhecida: manifesto da candidata172 mantém validated=false porque a
rede e suas provas finais ainda não estão concluídas. Os9bloqueios exigem
aprovação atual; não autorizam atribuir validated=true só para a CI ficar verde.
Os12KeyError de integração anteriores não reaparecem neste log.

Aviso adicional, não a causa do exit1:
prepare_special_encounter_workshop.py:394, SyntaxWarning: invalid escape
sequence '\l'. Se for corrigido depois, preservar exatamente o texto/scripts
gerados; não misturar essa limpeza com uma aprovação fictícia da release.

## 2. Checkpoint — documento dentro do ZIP está antigo

Comando e traceback enviados:

    2026-11-15T21:07:21.8694827Z
    python3 tools/hoenn/verify_atlas_surf_checkpoint.py --if-candidate
    File ".../verify_atlas_surf_checkpoint.py", line 218, in <module>
        result = verify(args.root, if_candidate=args.if_candidate)
    File ".../verify_atlas_surf_checkpoint.py", line 208, in verify
        verify_archive(root, directory, info, summary)
    File ".../verify_atlas_surf_checkpoint.py", line 173, in verify_archive
        assert digest(bundle.read(name)) == digest(path.read_bytes()), ('Stale archive entry', name)
    AssertionError: ('Stale archive entry', 'docs/CONTINUIDADE-TECNICA-IA.md')
    Process completed with exit code 1.

Causa confirmada: o commit29b1dca foi EXCLUSIVAMENTE documental por pedido
expresso do usuário. Atualizou o guia no Git e criou Aqui, sem alterar o ZIP.
O ZIP conserva os textos do checkpoint1bf71ed, e o verificador exige igualdade
com os textos do HEAD. Essa consequência foi registrada no guia anterior.
Neste run o checkpoint FALHOU; não repetir que a integridade completa do pacote
atual passou só porque havia passado antes da atualização documental.

Correção para a próxima etapa autorizada de pacote:

1. Preservar ROMs/save/freeze/hashes e conferir que não houve troca dos bytes.
2. Sincronizar a documentação do pacote com o Git, incluindo a pasta Aqui.
   Conferir a lista efetivamente empacotada; a pasta não entra automaticamente
   apenas porque foi criada no repositório.
3. Reempacotar o ZIP pelo fluxo existente e atualizar seu hash/tamanho externo
   em candidate-ROM-checkpoint.json. O arquivo não pode conter o hash de si
   mesmo dentro do próprio ZIP.
4. Reexecutar verify_atlas_surf_checkpoint.py e conferir todos os documentos,
   relatórios e hashes. Não desativar a comparação de conteúdo, rebaixar sua
   exigência nem adulterar o guia para esconder o erro.

Esse reparo do ZIP não valida geografia, gameplay ou release final. Não precisa
mudar a ROM apenas para sincronizar documentação. NÃO foi realizado neste lote.

## 3. Gate final — Unvalidated release

Comando e traceback enviados:

    2026-11-15T21:07:23.7965145Z
    python3 tools/hoenn/verify_versions.py
    File ".../verify_versions.py", line 290, in <module>
        verify(p.parse_args().directory)
    File ".../verify_versions.py", line 32, in verify
        if require_seal:assert info['validated'] is True,'Unvalidated release'
    AssertionError: Unvalidated release
    Process completed with exit code 1.

É a mesma causa do item1, em uma etapa separada. Restaurar o ZIP não elimina
esse bloqueio. Para resolver corretamente, concluir a rede física e produzir
as provas atuais antes de finalizar contratos e manifesto.

Pendências concretas estão em README.md:17SCCs de água gerada, Ocaso/rotas
ocultas aindaWIP, ThreeIsland ligando a componente errada, demais lacunas
nativas, auditorias de bancos/retirement/ecologia/DEX, migração dos saves,
percursos por controles e provas das cinco edições. Boot e Birth aprovados
não substituem esse conjunto. Não reutilizar evidência de outra ROM como atual.

## Procedimento e limites desta documentação

A próxima IA deve inspecionar HEAD/branch/PR e os arquivos reais antes de agir.
Manter as quatro arrays do atlas, eventos, NPCs, objetos inteiros e saves.
Não forçar flags, hashes ou contratos; não pular testes nem liberar Pages
com as provas atuais incompletas. Corrigir causas e validar, conforme README.

Este registro preserva a evidência recebida. Não declara os erros corrigidos.
O pedido atual é guardar para a próxima IA, mantendo código/ROMs/save/ZIP/
manifestos/workflows intocados. A documentação dentro do ZIP continua antiga
até uma futura atualização autorizada do pacote.
