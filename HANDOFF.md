# HANDOFF — Continuidade da sessão (SIG-CPL)

> Leia este arquivo primeiro se você é uma IA (ou pessoa) retomando este
> projeto sem o histórico da conversa que o construiu. Ele existe para que
> você não precise redescobrir decisões, armadilhas e estado por conta
> própria. Depois deste arquivo, a ordem de leitura recomendada é:
> 1. `README.md` — arquitetura, módulos implementados, RBAC, decisões tomadas.
> 2. `docs/requisitos_macros.md` — transcrição completa do documento de
>    requisitos original, com status de implementação por requisito (RF-xxx).
> 3. O código em si — está bem comentado nos pontos não óbvios.

## O que é este projeto

SIG-CPL — Sistema Integrado de Gestão de Cadeia Produtiva Local. Um sistema
de gestão para a CPL Autopeças de Atibaia/SP, no âmbito do Programa SP
Produz do Estado de São Paulo. Nasceu de um documento de requisitos macros
(~57 requisitos funcionais) que o usuário forneceu como PDF — a transcrição
completa está em `docs/requisitos_macros.md`, já com status de implementação
marcado requisito a requisito.

**Stack:** FastAPI + SQLAlchemy 2.x + PostgreSQL + Alembic + Jinja2/HTMX +
Bootstrap 5 (via CDN, sem build de JS) + openpyxl (leitura de .xlsx) +
fpdf2 (geração de PDF). 100% Python — sem Node.js no projeto em si (só foi
usado ad-hoc para testes visuais, ver seção de gotchas).

## Estado exato ao final desta sessão

- **Em produção:** https://sigcpl.dedev.cloud (deploy feito nesta sessão —
  ver seção própria abaixo, "Deploy em produção", com todos os detalhes de
  como foi feito e como reimplantar).
- **Local do projeto:** `C:\Users\andlu\sig-cpl`
- **É um repositório git com remoto no GitHub**: https://github.com/andlucace/sig-cpl,
  branch `master`. `/opt/sigcpl` na VPS também é um working directory git
  (não mais cópia de arquivo) tracking `origin/master` — reimplantar agora
  é `git push` local + `ssh ... "cd /opt/sigcpl && ./deploy.sh"` (ver seção
  "Deploy em produção" abaixo, que documenta também uma armadilha real de
  perda temporária do `.env.prod` durante essa conversão — resolvida sem
  downtime, mas vale ler antes de repetir esse tipo de conversão em outro
  projeto). Autenticação via **duas deploy keys separadas** (uma por
  máquina, cada uma em `~/.ssh/sigcpl_github` local e VPS — a da VPS é só
  leitura). `.env`/`.env.prod` estão no `.gitignore`, nunca foram
  commitados de propósito (e o `.env.prod` da VPS foi purgado do histórico
  git depois do incidente mencionado acima).
- **Postgres:** container Docker `sigcpl_db`, porta **5433** (não 5432 —
  a 5432 padrão está ocupada por outro projeto do usuário, `rh_nepen_db`).
  Sobe com `docker compose up -d` na raiz do projeto.
- **Servidor de dev:** por padrão sobe na porta 8000, mas a porta 8000
  costuma estar ocupada por outro projeto do usuário (`rh_nepen_backend`).
  Nesta sessão, rodamos sempre em `--port 8010`. No momento em que esta
  sessão terminou, **o servidor pode ainda estar rodando em
  `http://127.0.0.1:8010`** — confira com `netstat -ano | grep 8010` antes
  de subir outro, e mate o processo antigo antes de reiniciar (o servidor
  não usa `--reload`, então mudanças de código exigem restart manual).
- **Migrações Alembic aplicadas:** 29 revisões, todas no banco atual:
  1. `18541dca0a36` — modelos base (CPL, Entidade, Pessoa, Usuário)
  2. `0ba4d1a10f9d` — módulo Governança
  3. `5dd913b79202` — módulo Planejamento Estratégico
  4. `ac2ebdd62dd4` — módulo Cadastro dinâmico (diagnóstico, campanhas,
     convites, importação de planilha)
  5. `5891c62d1cb7` — módulo Documentos (repositório, versionamento,
     aprovação/assinatura, geração de ata em PDF)
  6. `5bff0df723be` — trilha de auditoria (`registros_auditoria`)
  7. `45d01888a884` — catálogo de indicadores (fonte, responsável,
     histórico de valores)
  8. `03a8cd5342ad` — módulo Maturidade (editais, critérios, avaliações,
     recursos)
  9. `16a954e6a8d8` — remapeamento manual de colunas na importação
     (status do lote, arquivo staged, mapeamento salvo)
  10. `66fb5b2556d0` — amplia `DiagnosticoCadastral` (qualificação,
      sustentabilidade, contatos internacionais, certificações,
      digitalização) + tabela nova `diagnosticos_cadastrais_historico`
      (snapshot de empregos, pra "novos empregos" no RF-046)
  11. `d1b19a7c50fc` — tabela `notificacoes` (RF-049)
  12. `5dfb7c6bf49e` — módulo de Projetos: tabelas `demandas_projeto` e
      `projetos` (RF-031/032 — só a fundação, demanda → projeto →
      portfólio)
  13. `55267d31bbca` — plano de trabalho básico do projeto (RF-033:
      `introducao`, `objeto`, `objetivos`, `justificativa`, `impactos`)
  14. `336459855cb9` — tabela `etapas_projeto` (RF-034 parcial: etapas/
      atividades com cronograma) — precisou de ajuste manual (enum
      `statustarefa` reaproveitado, ver gotcha novo abaixo)
  15. `777ba9fa79ad` — tabelas `metas_projeto`, `indicadores_projeto`,
      `riscos_projeto` + coluna `projetos.impactos_socioambientais`
      (finalização do RF-034) — de novo precisou de ajuste manual
      (`metas_projeto.status` reaproveita `statustarefa`)
  16. `d798be587a1c` — tabelas `equipe_projeto`, `origens_recurso_projeto`
      + colunas `projetos.continuidade`/`escalabilidade` (RF-035,
      fundação) — sem enum reaproveitado desta vez, aplicada sem ajuste
      manual
  17. `c0bdeb29e88f` — tabelas `editais_fomento`, `recursos_submissao_projeto`
      + coluna `projetos.edital_fomento_id` (RF-029/030) — precisou de
      ajuste manual (`recursos_submissao_projeto.status` reaproveita
      `statusrecurso`, criado originalmente pra `RecursoAvaliacao`/RF-027)
  18. `bcae54b40941` — tabela `aquisicoes_projeto` + colunas
      `etapas_projeto.valor_previsto`/`valor_executado` (RF-035,
      finalização — aquisições e cronograma físico-financeiro) —
      precisou de ajuste manual (`aquisicoes_projeto.status` reaproveita
      `statustarefa`)
  19. `94d2ed47a842` — tabelas `cotacoes_aquisicao`, `desembolsos_projeto`
      + colunas `aquisicoes_projeto.etapa_id`/`origem_recurso_id`/
      `contrapartida`/`justificativa_excecao` (RF-036/037/038) —
      precisou de ajuste manual diferente do de sempre: `contrapartida`
      é `Boolean NOT NULL` numa tabela (`aquisicoes_projeto`) que já
      tinha linhas, e o autogenerate não adiciona `server_default`
      sozinho (só olha pra `server_default` do modelo, não pro
      `default=` do Python/ORM) — sem isso o `ALTER TABLE` falharia
      contra as linhas existentes. Corrigido adicionando
      `server_default=sa.text('false')` na coluna
  20. `69235b36be9e` — tabelas `alteracoes_plano_projeto`,
      `entregas_projeto` + colunas `etapas_projeto.marco`/
      `riscos_projeto.evidencia_documento_id` (RF-039/040) — dois
      ajustes manuais de uma vez: enum reaproveitado
      (`alteracoes_plano_projeto.status` reaproveita `statusrecurso`) e
      `Boolean NOT NULL` sem `server_default` de novo
      (`etapas_projeto.marco`, mesmo gotcha exato da migração
      `bcae54b40941`) — ambos pegos antes de aplicar
  21. `48be8b55a24d` — tabela `tokens_recuperacao_senha` + colunas
      `usuarios.mfa_secret`/`usuarios.mfa_backup_codes` (RF-004) — sem
      gotcha nenhum dos dois de sempre (colunas novas todas nullable)
  22. `2f06d7b1b330` — tabela `ofertas_entidade` + coluna
      `diagnosticos_cadastrais.capacidade_produtiva` (RF-010) — sem
      gotcha nenhum dos dois de sempre (enum `tipooferta` criado pela
      primeira vez, não reaproveitado; coluna nova nullable)
  23. `a6b25ad2bdeb` — tabela `itens_habilitacao_juridica` (RF-027) —
      sem gotcha nenhum dos dois de sempre (enum `statusitemhabilitacao`
      criado pela primeira vez, tabela nova). RF-026 não precisou de
      migração — só reaproveitou funções de cálculo já existentes.
  24. `ec51d69e4f77` — tabela `requisitos_habilitacao_edital` (RF-003) —
      sem gotcha nenhum dos dois de sempre (sem enum, tabela nova sem
      coluna `NOT NULL` retroativa)
  25. `4fc9db3f454d` — tabela `registros_falha` (RNF-012) — sem gotcha
      nenhum dos dois de sempre (sem enum, tabela nova sem coluna
      `NOT NULL` retroativa)
  26. `3163d6162f16` — tabelas `eventos`, `recursos_biblioteca`,
      `inscricoes_evento` (RF-050/RF-051) — sem gotcha nenhum dos dois de
      sempre (dois enums novos — `tipoevento`/`statusevento` e
      `tiporecursobiblioteca` — nenhum reaproveitado; tabelas novas sem
      coluna `NOT NULL` retroativa)
  27. `bc65b64e9955` — tabela `matches_inovacao` (RF-052) — sem gotcha
      nenhum dos dois de sempre (enum `statusmatchinovacao` criado pela
      primeira vez, tabela nova sem coluna `NOT NULL` retroativa)
  28. `970f9469baaa` — colunas `entidades.latitude`/`longitude` (RF-011) —
      sem gotcha nenhum dos dois de sempre (colunas `Float` nulas, nenhum
      enum envolvido)
  29. `92eefc2fd38f` — tabela `solicitacoes_adesao` (F01) — **gotcha real
      dos dois de sempre, pego antes de aplicar**: a tabela reaproveita
      os enums `tipoentidade` (`Entidade.tipo`) e `elo` (`EntidadeElo.elo`)
      pros campos `tipo`/`elo_pretendido`, ambos criados em migrações
      anteriores — o arquivo autogerado usava `sa.Enum(...)` puro nos
      dois, que teria tentado `CREATE TYPE` de novo e quebrado com
      `DuplicateObject`. Corrigido trocando os dois por
      `postgresql.ENUM(..., create_type=False)`, mesmo padrão já
      documentado várias vezes nesta lista — `statussolicitacaoadesao`
      (novo, campo `status`) ficou com `sa.Enum` normal, sem ajuste,
      porque esse tipo é criado pela primeira vez nesta migração.
  - (a visão global + paginação da auditoria, feita antes da nº 10,
    **não** precisou de migração — é só query/rota/template novos;
    mesma coisa para RF-041/045/053/017, feitas depois da nº 20)

### Usuários de teste já existentes no banco

Só no banco de **desenvolvimento local** — produção tem só o
`admin@sigcpl.dedev.cloud` criado na sessão de deploy (ver seção "Deploy
em produção"), sem nenhum dado de exemplo.

| E-mail | Senha | Papel (`UsuarioPapel`) |
|---|---|---|
| `admin@atibaia-autopecas.sp.gov.br` | `trocar-senha-123` | `administrador_plataforma` (global) |
| `gestora@cpl-autopecas.example` | `senha-gestora-123` | `entidade_gestora` escopado à CPL Autopeças de Atibaia |
| `conselho@exemplo.com` | `senha-conselho-123` | nenhum papel (útil para testar 403) |
| `conselho-maria@exemplo.com` | `senha-teste-123` | `conselho_comite` escopado à CPL Autopeças; `pessoa_id` = Maria Souza, que é `MembroOrgao` só do "Conselho Gestor" (não da "Comissão de Inovação") — útil para testar `verificar_participacao_orgao` (ela deve conseguir votar/deliberar no Conselho Gestor, mas receber 403 na Comissão de Inovação) |

### Dados de exemplo já no banco

- 2 CPLs: **CPL Autopeças de Atibaia** (`CPL-AUTOPECAS-ATB`) e **CPL Têxtil
  de Americana** (`CPL-TEXTIL-AME`).
- Na CPL Autopeças: 2 órgãos de governança (Conselho Gestor, Comissão de
  Inovação), 1 pessoa (João Pereira), reuniões/deliberações/tarefas de
  teste, e 1 ciclo de Planejamento Estratégico ("2026-2027") com objetivo,
  meta, iniciativa e indicador de exemplo.
- Também na CPL Autopeças: 2 entidades importadas via planilha de teste
  ("Metalurgica Silva Ltda ME", "Autopecas Bragantina"), 1 campanha de
  atualização cadastral ("Atualizacao cadastral 2026") com 1 convite já
  respondido (via o formulário público `/atualizacao/{token}`), e 1 lote de
  importação de exemplo (`entidades_teste.csv`, 3 linhas: 2 criadas, 1 erro
  proposital por falta de razão social — útil para ver o relatório por
  linha funcionando).
- Também: 2 documentos "Ata — Reuniao de Inovacao" (gerados via o botão
  "Gerar ata em PDF" na tela da reunião) e 1 "Comprovante de pagamento
  teste" (confidencial, já aprovado) — úteis para ver o repositório de
  documentos com estados variados (`/painel/documentos`).

## Ordem em que este projeto foi construído (por que importa)

A sequência de decisões afeta o que é seguro mudar sem quebrar coisas:

1. **Esqueleto inicial** — FastAPI + SQLAlchemy + Postgres + Alembic +
   Jinja2/HTMX escolhidos deliberadamente (sem build de frontend). Modelos
   base: `CPL`, `Entidade`, `Pessoa`, `Usuario`. Auth por e-mail/senha (JWT).
2. **Módulo de Governança** (RF-015 a RF-020) — primeiro módulo funcional
   completo (modelo → API → UI). Vira o **padrão a seguir** para os módulos
   seguintes: arquivo de rotas web separado do de API (rotas web consultam o
   banco direto, não reaproveitam os endpoints REST — ver README, é uma
   duplicação deliberada, não um esquecimento).
3. **RBAC** — o modelo `UsuarioPapel` já existia desde o início mas não
   tinha endpoint nem checagem nenhuma. Foi implementado depois, sobre o que
   já existia: `app/core/rbac.py` com grupos de papéis + `verificar_papel()`
   chamada explicitamente em cada endpoint (não é um `Depends` genérico —
   ver comentário no README sobre por que).
4. **Frontend/UI** — Bootstrap 5 + Bootstrap Icons via CDN, layout com
   sidebar, dashboard com KPIs reais. Reescreveu todos os templates que já
   existiam da Governança.
5. **Módulo de Planejamento Estratégico** (RF-021 a RF-023) — construído
   copiando o padrão da Governança (models → schemas → API → migração →
   UI → teste). Reaproveita os grupos de RBAC da Governança e o enum
   `StatusTarefa` (não criou um enum de status duplicado).
6. **Módulo de Cadastro dinâmico** (RF-012 a RF-014) — mesmo padrão de
   novo, com duas peças novas que os módulos anteriores não tinham:
   (a) um `app/services/` para lógica de import não trivial (mapeamento de
   coluna, dedup), separado das rotas; (b) uma rota **pública sem
   autenticação nenhuma** (`app/web/routes_atualizacao_publica.py`,
   `/atualizacao/{token}`) para autopreenchimento por token — a segurança
   é o token ser imprevisível (`secrets.token_urlsafe`) e não o RBAC. Antes
   deste módulo, `EntidadeCPL` (vínculo entidade↔CPL) não tinha endpoint
   algum — foi adicionado aqui como pré-requisito.
7. **Módulo de Documentos** (RF-042/043) — antes de construir, perguntei
   (via `AskUserQuestion`) duas coisas que eram genuinamente decisão do
   usuário: onde armazenar arquivo, e qual escopo de "geração de documento
   padronizado". Resposta do armazenamento: usuário mencionou Hostinger;
   investiguei a conta dele via MCP (só leitura) e achei uma VPS já rodando
   Docker Compose com outro projeto FastAPI+Postgres dele (`rh-nepen`) atrás
   de Traefik — documentei isso como contexto de deploy futuro (seção
   "Infraestrutura de implantação" no README), mas **não implantei nada**:
   perguntei de novo, explicitamente, se era pra fazer o deploy agora ou só
   construir local, e o usuário escolheu só construir local. Resposta do
   escopo de geração: só exportar ata de reunião em PDF (não um "pacote de
   submissão" completo, que depende da Fase 2). Armazenamento ficou em
   disco local (`settings.uploads_dir`), pensado desde já pra funcionar
   igual numa VPS (só monta um volume no mesmo caminho, sem mudar código).
8. **Trilha de auditoria** (RF-056/RNF-003) — último item da Fase 1/MVP.
   Decisão de arquitetura (não perguntei ao usuário, por ser mais técnica
   que de produto): em vez de espalhar uma chamada manual de log em cada
   um dos ~30 endpoints existentes (frágil, fácil esquecer um), a captura
   de CRIACAO/ATUALIZACAO/EXCLUSAO é **automática via listener do
   SQLAlchemy** (`app/services/auditoria.py`, eventos `before_flush` +
   `after_flush` na `Session`) — cobre qualquer modelo mapeado, presente
   ou futuro, sem precisar lembrar de instrumentar nada. Só eventos que
   não são uma escrita de linha (login, download de arquivo) precisam de
   chamada explícita (`registrar_evento()`), feita nos 2 pontos de login
   (API e web) e nos 2 pontos de download de documento (API e web). O
   "quem" e o "IP" chegam ao listener via `contextvars`
   (`app/core/audit_context.py`), populados por um middleware em
   `app/main.py` que decodifica o JWT sem tocar o banco.
9. **Indicadores e relatórios** (RF-044 a RF-048) — fecha a Fase 1/MVP.
   Diferente dos módulos anteriores, não criou tabelas de domínio novas
   além de duas: `IndicadorEstrategico` ganhou `fonte`/`responsavel_id`, e
   `IndicadorValorHistorico` guarda a série histórica (RF-044 exige isso
   explicitamente, e antes só existia `valor_atual`, sem histórico). O
   resto é uma **camada de agregação** (`app/services/indicadores.py`)
   sobre dado que Governança, Planejamento e Cadastro dinâmico já
   coletavam — deliberado, pra não duplicar coleta de dado. Antes de
   implementar, perguntei ao usuário (via `AskUserQuestion`) só a decisão
   que era genuinamente dele: RF-048 pede 6 tipos de relatório
   (executivo/anual/recadastramento/comissão/projeto/impacto) e construir
   todos era demais pro escopo atual — ele escolheu só o "Relatório
   Executivo" em PDF, reaproveitando a mesma infra da ata de reunião
   (por isso `_GeradorAta` em `geracao_documentos.py` virou `_GeradorPDF`,
   generalizado pra servir aos dois documentos, não só à ata). RBAC do
   indicador ganhou a mesma exceção de "responsável pessoal" que
   objetivo/meta/iniciativa já tinham (`_pode_executar`), agora que ele
   também tem `responsavel_id`.
10. **Maturidade e reconhecimento** (RF-024 a RF-028) — primeiro módulo da
    **Fase 2** (o usuário pediu "seguir para a próxima fase" depois de
    confirmar, via `AskUserQuestion`, que "próxima fase" significava Fase
    2 e não algo que ainda faltasse da Fase 1). Maior módulo novo desde
    Governança: `Edital`, `CriterioMaturidade`, `Avaliacao`,
    `AvaliacaoCriterio`, `RecursoAvaliacao`. Duas decisões perguntadas ao
    usuário antes de implementar (`AskUserQuestion`), porque eram
    genuinamente dele: (a) construir o fluxo de recursos/apelação (RF-027)
    já nesta etapa ou deixar pra depois — escolheu construir já; (b)
    confirmar que edital/critérios são configuração **global**
    (compartilhada entre CPLs, gerida só por `ADMINISTRADOR_PLATAFORMA`)
    e não algo que cada CPL cria pra si — confirmou que sim, é o que
    RN-006 já sugeria. Ponto de design mais importante: **RN-016**
    ("decisão de maturidade não pode ser só algorítmica") foi implementada
    como uma separação real de dois passos, não só documentada — concluir
    uma avaliação (`concluir_avaliacao`) só calcula um `nivel_sugerido`;
    nenhum código atualiza `CPL.nivel_maturidade` até uma chamada humana
    explícita e separada (`decidir_nivel`, endpoint próprio, RBAC mais
    restrito que quem avalia). Reaproveitou o gotcha já documentado de
    enum reutilizado entre migrações (`NivelMaturidade`, que já existia
    desde a migração base do `CPL`) — a migração autogerada precisou do
    mesmo ajuste manual (`postgresql.ENUM(..., create_type=False)`) que já
    tinha sido feito outras vezes. Bônus de validação: a trilha de
    auditoria (item 8) capturou as mudanças de `Avaliacao` automaticamente
    sem nenhum código novo — confirma que o listener genérico realmente
    cobre modelos futuros, não só os que existiam quando foi construído.
11. **Fechar limitações do RBAC** — usuário pediu explicitamente "fechar
    itens menores pendentes" em vez de partir para o próximo módulo grande
    (Projetos, RF-029 a RF-041, ficou pra depois). Três coisas, todas já
    documentadas como limitação conhecida havia sessões: (a) escopo de CPL
    para Entidade/Pessoa na leitura (`GET`) — criar continua sem escopo de
    propósito, o registro pode não ter vínculo ainda; (b) escopo por órgão
    específico (`verificar_participacao_orgao`, novo em `app/core/rbac.py`)
    — `MembroOrgao` já existia desde Governança, só não estava ligado ao
    RBAC; (c) página 403 amigável no portal web via
    `@app.exception_handler(StarletteHTTPException)` em `main.py`, que
    intercepta só GET fora de `/api/` e sem header `HX-Request` (API e
    HTMX continuam recebendo JSON — HTMX não troca conteúdo em resposta
    não-2xx mesmo, então devolver a página inteira quebraria o fragmento).
    Testado com um usuário novo (`conselho-maria@exemplo.com`, ver tabela
    de usuários de teste) criado especificamente pra provar o caso que
    antes vazava: `MembroOrgao` de um órgão só, tentando votar no outro.
    **Achado no meio do trabalho, não relacionado ao RBAC**: rodar a suite
    de regressão Playwright revelou que `gerar_pdf_ata()` estava quebrada
    em produção desde a sessão de Indicadores — um `NameError` genuíno
    (`_GeradorAta` não existe mais, virou `_GeradorPDF`, mas uma chamada
    interna não foi atualizada quando o rename aconteceu via
    `replace_all`). Corrigido e reimplantado **imediatamente**, em commit
    separado, antes mesmo de terminar o resto do RBAC — geração de ata é
    uma função usada de verdade, não fazia sentido esperar. Lição: depois
    de qualquer rename com `replace_all`, rode a suite de regressão antes
    de considerar terminado, não só teste o caminho que motivou a mudança.
12. **Tela de criação/edição de CPL** (RF-001) — segundo "item menor" da
    sequência pedida pelo usuário (depois de RBAC). `PATCH /api/cpls/{id}`
    novo (só existia `POST`/`GET`) + `app/web/routes_cpl.py` +
    `/painel/cpls`. Deliberadamente **não** deixa editar
    `nivel_maturidade`/`data_reconhecimento`/`data_validade_reconhecimento`
    pelo form — esses só mudam via `decidir_nivel()` do módulo de
    Maturidade (RN-016), então o schema `CPLUpdate` nem inclui esses
    campos, pra não abrir um atalho by-design. Mesma regra de acesso da
    criação (só `ADMINISTRADOR_PLATAFORMA`) — decisão que já vinha do
    docstring original do `POST /api/cpls`, só estendida ao `PATCH`.
13. **Remapeamento manual de colunas na importação** (RF-013) — terceiro
    "item menor". Antes, `processar_planilha()` fazia tudo num passo só
    (upload → mapeamento automático → processa linhas), e se o cabeçalho
    não batesse com nenhum alias conhecido, o campo ficava em branco sem
    avisar ninguém. Virou um fluxo em 2 passos: `preparar_importacao()`
    salva o arquivo em staging (reaproveita `app/services/armazenamento.py`,
    o mesmo mecanismo do repositório de Documentos) e devolve cabeçalhos +
    sugestão, sem tocar em nenhuma linha; `confirmar_importacao()` só roda
    depois que o usuário conferiu/ajustou o mapeamento na tela
    `/painel/cadastro/importacoes/{id}/mapear`. `ImportacaoLote` ganhou
    `status` (`pendente_mapeamento`/`concluido`), `arquivo_path` (staging)
    e `mapeamento_colunas` (JSONB — o que foi de fato usado, trilha de
    origem do próprio mapeamento). Migração precisou de **dois** ajustes
    manuais no arquivo autogerado: (a) `sa.Enum` sozinho dentro de
    `add_column` não criou o tipo Postgres — precisou de
    `postgresql.ENUM(...).create(op.get_bind(), checkfirst=True)`
    explícito antes (variante nova do gotcha de enum já documentado,
    desta vez num enum **novo**, não reaproveitado — vale conferir sempre,
    não só quando o enum já existe); (b) a coluna `status` é `NOT NULL`
    mas já havia 1 lote de importação antigo no banco, então precisou de
    `server_default='CONCLUIDO'` pra não quebrar o backfill (removido
    logo depois, já que todo INSERT novo passa pelo default do modelo
    Python). Provei que o problema era real com um CSV de teste com
    cabeçalhos que não batem com nenhum alias ("Nome do Fornecedor",
    "Documento Fiscal", "Cidade Base") — sem remapeamento manual, essa
    planilha importaria tudo em branco; com ele, mapeei na mão e os dados
    foram parar nos campos certos (confirmado lendo a `Entidade` criada de
    volta). `processar_planilha()` (1 passo) continua existindo pra quem
    não precisa da conferência manual.
14. **Visão global da auditoria + paginação de verdade** — quarto e último
    "item menor" da lista. Antes, `GET /auditoria/cpls/{id}` e a tela web
    correspondente tinham um limite fixo de 200/registros mais recentes,
    sem `offset` nem contagem total — e eventos com `cpl_id=None` (login,
    criação de `Usuario`/`Pessoa`/`CPL` em si) não apareciam em nenhuma
    tela, só consultáveis direto no banco. Consolidei a lógica de consulta
    num único helper novo, `consultar_registros()` em
    `app/services/auditoria.py` (parâmetros `cpl_id`, `somente_global`,
    `acao`, `entidade_tipo`, `offset`, `limite`; devolve `(registros,
    total)`), usado tanto pela API quanto pela web, tanto na visão por-CPL
    quanto na global — evita duplicar a mesma query em 4 lugares.
    `GET /api/auditoria/cpls/{cpl_id}` ganhou `offset` e o header
    `X-Total-Count`; `GET /api/auditoria/global` é rota nova, restrita a
    `PAPEIS_EDITAL_GESTAO` (= só `ADMINISTRADOR_PLATAFORMA`, já que cruza
    dados de todas as CPLs). No lado web, mesma coisa em
    `/painel/auditoria/cpls/{id}` (query param `pagina`) e
    `/painel/auditoria/global` (nova, linkada a partir do seletor de CPL
    só quando `cpl_ids_visiveis()` devolve `None`, ou seja só pra quem já
    enxerga todas as CPLs). Extraí a tabela de eventos e os controles de
    página anterior/próxima em dois partials Jinja
    (`_tabela_registros.html`, `_paginacao.html`) reaproveitados pelas duas
    telas, em vez de duplicar o HTML. **Armadilha evitada por pouco**: o
    card novo "Visão global" no seletor de CPL quase ganhou a mesma classe
    `list-group-item-action` dos itens de CPL — isso teria feito o
    seletor `.list-group-item-action >> nth=0` do script de regressão
    `auditoria_shot.js` clicar no link errado (visão global em vez da
    primeira CPL). Troquei pra um `<a class="card">` com classes
    distintas antes de rodar a suite completa, exatamente pra não
    repetir o tipo de acoplamento entre UI nova e teste antigo que já
    causou o bug do `_GeradorAta`/`_GeradorPDF` nesta mesma sessão. Não
    precisou de migração — mudança é só de query/rota/template. Nenhuma
    regressão nos scripts Playwright existentes (as falhas observadas ao
    rodar a suite completa — `cpl_edit_shot.js` por sigla duplicada de uma
    rodada anterior não-idempotente, `pdf_shot.js` por `networkidle` nunca
    resolver ao abrir um PDF local via `file://`, `shot.js` por faltar URL
    hardcoded — já eram conhecidas e não têm relação com este módulo;
    confirmado também sem nenhum 500 no log do servidor durante a run).
15. **Ampliação do resumo cadastral e painéis** (RF-046/047) — usuário
    escolheu esta entre 3 opções (a outra era "outros relatórios do
    RF-048" e a terceira "iniciar módulo de Projetos", maior escopo).
    Duas partes:
    (a) **Campos que faltavam no diagnóstico**: qualificação,
    sustentabilidade, contatos internacionais, certificações e
    digitalização ganharam campo em `DiagnosticoCadastral` — mesmo
    padrão booleano+descrição já usado por `realiza_inovacao`/
    `descricao_inovacao` (certificações usa lista separada por vírgula,
    como `ods_relacionados`). Precisou tocar **3 pontos de escrita**, não
    só 1: `PUT /api/cadastro/entidades/{id}/diagnostico` (schema
    `DiagnosticoCadastralUpdate` — bastou adicionar os campos, o endpoint
    já fazia `dados.model_dump().items()` genérico), o formulário público
    de campanha (`app/web/routes_atualizacao_publica.py` +
    `atualizacao_form.html` — precisou de `Form(...)` novo por campo E
    de HTML novo, já que esse formulário não é genérico), e a importação
    de planilha (`_ALIASES_CAMPO`/`_CAMPOS_BOOLEANOS` em
    `app/services/importacao_entidades.py` — como é data-driven, só
    precisou adicionar entradas nos dicionários; `CAMPOS_CONHECIDOS` e a
    tela de remapeamento manual já pegam os campos novos automaticamente,
    sem tocar template). De brinde, notei que `participacao_associativa`/
    `entidades_associativas` já existiam no modelo e já entravam no
    resumo (`percentual_associativismo`) desde a sessão que criou
    Indicadores, mas **nunca tinham sido expostos no formulário
    público** — ou seja, na prática nunca eram preenchidos por uma
    entidade real respondendo à campanha, só via API direta ou
    importação. Corrigido no mesmo formulário, já que eu estava mexendo
    nele mesmo.
    (b) **"Novos empregos" (variação no tempo, RF-046)**: `DiagnosticoCadastral`
    sobrescreve o valor a cada resposta, sem histórico — então criei
    `DiagnosticoCadastralHistorico` (mesmo padrão de
    `IndicadorValorHistorico`: uma tabela `*_historico` que só acumula,
    nunca é sobrescrita) e um helper único, `registrar_snapshot_
    diagnostico()` em `app/services/indicadores.py`, chamado pelos
    mesmos 3 pontos de escrita logo após aplicar os campos novos (com
    `db.flush()` antes, pra garantir que os valores já estão no objeto).
    `resumo_cadastral()` soma, por entidade, a diferença entre o
    snapshot mais antigo dentro dos últimos 12 meses e o mais recente —
    **decisão deliberada**: só conta crescimento (`if diferenca > 0`),
    não é "saldo líquido" da CPL, é "empregos novos criados"; e precisa
    de **pelo menos 2 snapshots por entidade** dentro da janela pra
    contar qualquer coisa — com histórico vazio ou só 1 ponto, o valor é
    honestamente 0, não uma estimativa. Testado de verdade via curl:
    `PUT` com `empregos_diretos=12`, depois de novo com `=20`, e
    `novos_empregos_diretos_12_meses` bateu em `8` — não só testei que o
    campo aparece, testei que a conta dá o número certo.
    **Armadilha evitada por pouco**: `ResumoCadastralRead` em
    `app/schemas/indicadores.py` é um `response_model` do FastAPI — se eu
    tivesse esquecido de adicionar os campos novos nesse schema, a API
    teria **silenciosamente descartado** todo campo novo da resposta
    (FastAPI filtra pelo response_model), enquanto a tela web (que usa o
    dict do service direto, sem passar por schema) teria funcionado
    normal — um bug que só apareceria pra quem consome a API, não pra
    quem usa a UI, exatamente o tipo de inconsistência silenciosa fácil
    de não notar sem testar os dois caminhos. Vale lembrar isso sempre
    que um campo novo entrar em algo que já tem `response_model`.
    Regressão completa rodada de novo (Playwright + verificação de
    log do servidor), incluindo o fluxo de importação (que teve
    `_ALIASES_CAMPO`/`_CAMPOS_BOOLEANOS` mexidos) — sem nenhum 500.
16. **Relatório de recadastramento** (RF-048) — usuário pediu pra "seguir
    conforme recomendado"; entre as opções restantes do RF-048 (anual,
    recadastramento, comissão, projeto, impacto), escolhi recadastramento
    porque é o único que reaproveita dado que já existe **de verdade**
    (nível de maturidade, validade do reconhecimento, avaliações,
    `lacunas()`) sem precisar inventar uma nova janela temporal (anual) ou
    uma nova agregação por-órgão (comissão) — projeto continua bloqueado
    (módulo não existe) e impacto duplicaria o executivo sem uma fonte de
    dado territorial própria. Mesmo par serviço+PDF do executivo:
    `resumo_recadastramento()` (novo, em `app/services/maturidade.py`) +
    `gerar_pdf_relatorio_recadastramento()` (novo, em
    `app/services/geracao_documentos.py`), chamados por 2 rotas novas
    (`POST /api/maturidade/cpls/{id}/relatorio-recadastramento` e o
    equivalente web) que salvam o PDF como `Documento` — cópia quase
    literal do fluxo do executivo (`app/web/routes_indicadores.py`), só
    trocando os dados. Nenhuma migração — não criei tabela nem coluna
    nova, só uma função de agregação sobre dado que o módulo de
    Maturidade (RF-024-028, sessão anterior) já mantinha.
    **Armadilha evitada, não nova mas quase repetida**: ao testar o PDF
    gerado, `doc.get_text()` via PyMuPDF voltou com `�` no lugar de
    acento/travessão — por um instante pareceu o mesmo bug real que já
    apareceu antes neste projeto. Mas dessa vez confirmei rasterizando a
    página como imagem (`page.get_pixmap()`) em vez de confiar na
    extração de texto, e o PDF renderiza os acentos perfeitamente — é uma
    particularidade de como esse `get_text()` lê a tabela de encoding da
    fonte embutida (Arial local, via `_FONTES_REGULAR`), não um bug do
    app. Reforça o padrão já documentado: **nunca confiar em extração de
    texto/repr de PDF gerado por este código — sempre confirmar via
    imagem rasterizada ou renderização real**, mesma lição do gotcha do
    `python -c` com acento.
17. **Notificações automáticas** (RF-049) — entre "fase 2" e "finalizar
    fase 1", usuário deixou a escolha comigo via `AskUserQuestion`;
    recomendei e ele confirmou RF-049 sobre RF-053 (exportação
    XLSX/CSV), RF-055 (portal público) e o módulo de Projetos (Fase
    2/3, maior escopo). Modelo novo `Notificacao`
    (`app/models/notificacao.py`, tabela `notificacoes`) — mesmo padrão
    "log que só acumula" de `RegistroAuditoria`, `lida`/`lida_em` como
    único estado mutável, chave de deduplicação é (usuario_id, tipo,
    entidade_id). Serviço novo, `app/services/notificacoes.py`, com uma
    função por fonte (`_gerar_reunioes_proximas`,
    `_gerar_tarefas_com_prazo`, `_gerar_documentos_com_validade`,
    `_gerar_metas_com_prazo`, `_gerar_recadastramentos_proximos`) e um
    orquestrador (`gerar_notificacoes()`) chamado por
    `GET /api/notificacoes` e `/painel/notificacoes` — **sem
    agendador/worker neste stack** (sem Celery/cron), a varredura roda
    sob demanda a cada acesso à tela/endpoint, decisão deliberada pra
    não introduzir infra nova só pra isso.
    **Resolução de destinatário por fonte** (a parte não-trivial deste
    módulo): reunião avisa os membros ativos do órgão (`MembroOrgao.
    pessoa_id` → `Usuario.pessoa_id`, pulando pessoa sem conta), tarefa e
    meta avisam o `responsavel_id` (mesma indireção pessoa→usuário),
    documento avisa direto quem criou (`Documento.criado_por_id` já é um
    `usuario_id`, sem indireção), e recadastramento de CPL avisa todos
    os `ADMINISTRADOR_PLATAFORMA` (reaproveitando
    `cpls_com_vencimento_proximo()` do módulo de Maturidade).
    **Bug real pego só ao testar de ponta a ponta, não na leitura do
    código**: a primeira versão passava a mesma janela curta (7 dias,
    pensada pra prazo operacional de tarefa/reunião) também pro
    recadastramento de CPL — que já tinha seu próprio padrão de 90 dias
    estabelecido em `cpls_com_vencimento_proximo(dias: int = 90)` desde
    a sessão de Maturidade. Só descobri criando um cenário de teste de
    verdade (CPL com validade em 30 dias, dentro de 90 mas fora de 7) e
    vendo a notificação **não aparecer** quando deveria — corrigido
    desacoplando `_gerar_recadastramentos_proximos()` da `janela_dias`
    do resto, sempre usando os 90 dias já convencionados. **Lição**:
    "reaproveitar uma função que já existe" não é o mesmo que "reaproveitar
    o parâmetro que a chama em outro contexto" — cada fonte de
    notificação pode ter sua própria escala de tempo, testar com dado
    real dentro/fora de cada janela teria pego isso mais cedo se eu
    tivesse pensado nisso antes de escrever o código, não só depois.
    UI: link novo "Notificações" na barra lateral, tela
    `/painel/notificacoes` (lista + marcar uma/todas como lidas). Sem
    badge de não-lidas na barra lateral — nenhuma outra seção tem
    indicador equivalente, e adicionar um exigiria um mecanismo (context
    processor Jinja2) não usado em nenhum outro lugar do projeto;
    recorte de escopo deliberado, documentado no README. RBAC é só posse
    (usuário só vê/marca a própria notificação), não papel — testado
    tentando marcar a notificação de um usuário logado como outro,
    `404` corretamente. Testado de ponta a ponta com fixtures reais
    (reunião, tarefa, documento, meta, CPL) criadas e removidas via
    script Python direto na sessão (não pela API), confirmando que cada
    fonte notifica exatamente quem deveria e ninguém mais.
18. **Relatório anual** (RF-048) — usuário disse "continuar para a
    RF-048" sem especificar qual dos 4 tipos restantes (anual, comissão,
    projeto, impacto); escolhi anual e expliquei a razão em vez de
    perguntar de novo (mesmo padrão do item 16: já tinha perguntado o
    suficiente nesta cadeia de decisões). Razão: é o mais universalmente
    valioso (prestação de contas anual é um artefato real de programas
    públicos) e o mais barato de construir sobre dado que já existe —
    comissão exigiria uma nova função de resumo por-órgão (em vez de
    por-CPL) e projeto continua bloqueado (módulo não existe); impacto
    foi descartado de novo por duplicar o executivo sem fonte de dado
    territorial própria. Diferença central pro executivo: executivo é
    **acumulado desde sempre**; anual é **recortado a
    `[1º jan, 31 dez]` de um ano específico** — `resumo_anual(db,
    cpl_id, ano)`, novo em `app/services/indicadores.py`, reaproveitando
    os mesmos joins de `resumo_governanca`/`resumo_planejamento` mas com
    filtro de data adicionado.
    **Refactor pra evitar duplicar lógica**: "novos empregos" (RF-046,
    resumo cadastral) já calculava a diferença de `empregos_diretos`
    entre dois snapshots de `DiagnosticoCadastralHistorico` dentro de
    uma janela rolante de N dias (`_novos_empregos_diretos`). O
    relatório anual precisa da mesma conta, mas com `[início, fim]`
    explícitos (o ano-calendário), não uma janela relativa a "agora".
    Extraí a lógica pra `_novos_empregos_diretos_periodo(db,
    entidade_ids, inicio, fim)` e reescrevi `_novos_empregos_diretos`
    como uma chamada fina por cima dela (`inicio=agora-dias, fim=agora`)
    — comportamento idêntico pro caso já existente (verificado: nenhum
    teste de regressão do resumo cadastral mudou), e o relatório anual
    ganha a variante nova de graça. "Tarefas/metas concluídas no ano"
    usa `updated_at` como proxy — nem `TarefaGovernanca` nem
    `MetaEstrategica` guardam uma data de conclusão própria; recorte de
    escopo documentado, não um bug.
    **Testado de verdade, não só "não deu erro"**: gerei o relatório
    para 2026 (ano com dado real — 4 reuniões, 2 deliberações, etc.) e
    depois pra 2025 (nenhum dado ainda existia naquele ano) e confirmei
    via PDF rasterizado que os números realmente mudam pra zero — sem
    esse segundo teste, um bug onde o filtro de ano fosse ignorado
    silenciosamente (e o relatório "anual" sempre mostrasse o total
    acumulado) passaria despercebido, já que os números de 2026
    "pareciam certos" sozinhos.
19. **Relatório de comissão e relatório de impacto** (RF-048) — usuário
    disse "seguir com o restante da RF-048", que na sessão anterior eu
    tinha deixado como comissão/projeto/impacto. Reconsiderei "impacto"
    em vez de simplesmente reafirmar a rejeição anterior ("duplicaria o
    executivo") — na prática, o executivo mistura governança +
    planejamento + cadastro + catálogo num só documento, então um
    relatório que **só** mostra o recorte cadastral/socioambiental do
    RF-046/047 (sustentabilidade, ODS, certificações, digitalização,
    inovação) é um artefato genuinamente diferente pra quem só precisa
    disso — não é o mesmo documento com outro título, é uma seleção de
    campos diferente e mais focada. Construí os dois:
    (a) **Comissão** — `resumo_orgao(db, orgao_id)`, novo em
    `app/services/indicadores.py`, ao lado dos outros `resumo_*`
    (mesmo que escopado por órgão, não por CPL — a proximidade
    conceitual com `resumo_governanca` pesou mais que a diferença de
    parâmetro). Serve qualquer `TipoOrgao`, não só comissão temática —
    sem custo técnico adicional pra generalizar, e evita uma
    distinção artificial entre "comissão" e "conselho" que o requisito
    não exige tecnicamente. Detalhe que quase passou batido: tarefas só
    contam se ligadas a uma deliberação **daquele órgão**
    (`TarefaGovernanca.deliberacao_id` → `Deliberacao.reuniao_id` →
    `Reuniao.orgao_id`) — uma tarefa solta da CPL (sem
    `deliberacao_id`) não é atribuível a nenhum órgão específico, então
    fica de fora, corretamente. Rota nova em
    `app/api/routes/governanca.py` (não em `indicadores.py`, já que o
    escopo é órgão, não CPL) — `POST /api/governanca/orgaos/{id}/
    relatorio-comissao`, RBAC `PAPEIS_GESTAO` escopado ao `cpl_id` do
    órgão (não ao órgão em si — não existe RBAC por-órgão granular o
    bastante pra isso hoje, e não era o objetivo desta tarefa).
    (b) **Impacto** — `gerar_pdf_relatorio_impacto()` reaproveita
    `resumo_cadastral()` **sem nenhuma função de agregação nova** — só
    reformata um subconjunto dos mesmos campos que o executivo já usa,
    omitindo governança/planejamento/catálogo. É o relatório mais barato
    de todos os 5 construídos nesta sessão e na anterior.
    **Teste que provou o escopo por-órgão de verdade**: gerei o
    relatório de comissão pro "Conselho Gestor" (que tem só 1 reunião e
    2 deliberações próprias) numa CPL que tem 4 órgãos e 4 reuniões no
    total — confirmei via PDF rasterizado que aparecia só a 1 reunião e
    as 2 deliberações do Conselho Gestor, não as das outras 3 comissões/
    grupos da mesma CPL. Sem esse teste específico, um bug onde o join
    esquecesse o filtro por `orgao_id` (e vazasse dado de outros
    órgãos) passaria despercebido, porque o "resumo" ainda pareceria
    plausível sozinho.
    Com isso, RF-048 fica completo exceto "relatório de projeto"
    (bloqueado, sem módulo de Projetos) — todos os outros 5 tipos
    citados no requisito (executivo, anual, recadastramento, comissão,
    impacto) estão implementados.
20. **Módulo de Projetos — fundação** (RF-031/032) — usuário pediu "fazer
    o módulo de projetos", o maior bloco pendente do sistema (13
    requisitos em 6 sub-áreas: editais, demandas/portfólio, plano de
    trabalho, financeiro, execução, prestação de contas). Diferente das
    outras vezes que decidi sozinho e só expliquei depois, aqui **parei
    e perguntei antes de codificar** — duas decisões que só o usuário
    podia tomar: (a) o sistema já tem um `Edital` (maturidade) e o
    RF-029 fala de outro "edital" (fomento/submissão) — são conceitos
    diferentes ou o mesmo? Usuário confirmou: diferentes. (b) por onde
    começar essa primeira fatia — usuário escolheu "fundação: demanda →
    projeto → portfólio" (RF-031/032) em vez de "editais primeiro" ou
    "plano de trabalho completo".
    **Modelos novos**: `DemandaProjeto` (RF-031) e `Projeto` (RF-032),
    em `app/models/projeto.py`. Decisão de design que vale registrar:
    `DemandaProjeto.origem_id` é uma referência **solta**, sem FK de
    banco — mesmo padrão de `RegistroAuditoria.entidade_id` — porque a
    origem (empresa/comissão/instituição/edital) aponta pra tabelas
    diferentes conforme `origem_tipo`, não dá pra usar uma FK rígida
    única. `Projeto.eixo_sp_produz` é texto livre, não enum — o
    documento de requisitos não define uma lista fechada de eixos do
    programa, e inventar uma lista seria fabricar dado que não está na
    fonte (mesmo cuidado já tomado antes com "gestão de parâmetros" e
    outros campos sem especificação). `EstagioProjeto` foi modelado com
    o ciclo de vida **completo** (demanda → elaboração → submetido →
    aprovado → execução → concluído/rejeitado/cancelado) mesmo só
    usando os estágios iniciais nesta fatia — mesmo truque de
    `StatusAvaliacao`/`TipoNotificacao`: evita migração nova quando
    RF-033 em diante forem construídos.
    **RBAC**: papel `GESTOR_PROJETO` já existia no enum `Papel` (e já
    fazia parte de `PAPEIS_TAREFA_EXECUCAO`) desde muito antes deste
    módulo existir — o documento de requisitos original já previa esse
    perfil. Criei `PAPEIS_PROJETO_LEITURA`/`PAPEIS_PROJETO_GESTAO`
    reaproveitando `PAPEIS_GOVERNANCA_LEITURA`/`PAPEIS_GESTAO` como
    base, só acrescentando `GESTOR_PROJETO` — mesmo padrão de
    `PAPEIS_TAREFA_EXECUCAO`.
    **Dois jeitos de criar projeto**: converter uma demanda
    (`POST /api/projetos/demandas/{id}/converter`) ou criar direto no
    portfólio (`POST /api/projetos/cpls/{id}/projetos`) — a demanda
    convertida não é apagada, só muda de status
    (`CONVERTIDA_EM_PROJETO`) e ganha um vínculo 1:1 com o projeto
    criado; tentar converter de novo dá 400, testado.
    **Rota do relatório de comissão fica em `governanca.py`, não em
    `indicadores.py`** (precedente do item 19) — mesma lógica se
    aplicaria aqui se houvesse relatório de projeto, mas não há ainda.
    Testado de ponta a ponta via Playwright: registrar demanda → ver
    detalhe → converter em projeto → editar estágio no portfólio →
    voltar à lista e confirmar que a demanda convertida some de
    "pendentes" mas o projeto aparece no portfólio. RBAC testado
    (Conselho/Comitê lê mas recebe 403 ao tentar criar demanda). Zero
    500 reais na regressão completa — a única linha de "Traceback" no
    log era um `_ProactorBasePipeTransport` do asyncio no Windows
    (conexão fechada abruptamente após um download que já tinha
    respondido 200), não um erro da aplicação; confirmado checando que
    não há nenhuma linha `"HTTP/1.1" 500` de verdade no log.
    Escopo explicitamente fora desta fatia (documentado no README, não
    esquecido): edital de fomento com cronograma/recursos (RF-029/030),
    plano de trabalho detalhado — objeto/etapas/cronograma/equipe
    (RF-033 a RF-035), orçamento/cotações/desembolsos (RF-036 a
    RF-038), execução física/financeira/riscos (RF-039/040) e
    prestação de contas (RF-041). "Relatório de projeto" (RF-048) segue
    bloqueado até esses existirem.
21. **Plano de trabalho básico do projeto** (RF-033) — usuário disse
    "vamos seguir com a sequência natural do projeto". Diferente do
    item 20 (onde parei pra perguntar antes de começar o módulo
    inteiro), aqui decidi sozinho e só expliquei depois — mesmo padrão
    usado pra escolher entre anual/comissão/impacto no RF-048: é uma
    decisão de sequenciamento *dentro* de um módulo já aprovado, não
    "qual módulo grande começar", que é o tipo de decisão que
    realmente exige perguntar antes. Escolhi RF-033 (informações
    básicas: introdução, objeto, objetivos, justificativa, impactos)
    como a camada mais fundamental que ainda faltava dentro de "plano
    de trabalho" — RF-034 (etapas/cronograma/metas/indicadores/riscos)
    e RF-035 (equipe/aquisições/recursos) naturalmente se apoiam em ter
    primeiro o texto básico do plano, não o contrário.
    **Decisão de modelagem**: os 5 campos novos foram pra dentro da
    própria tabela `projetos`, não uma entidade `PlanoDeTrabalho`
    separada — é uma relação 1:1 real (todo projeto tem no máximo um
    plano de trabalho), então uma tabela à parte só adicionaria um
    join sem nenhum ganho (nenhuma dessas informações é
    multi-valorada ou tem ciclo de vida próprio, diferente de
    etapas/atividades do RF-034, que aí sim vão precisar de tabelas
    próprias quando forem construídas).
    **UI**: form separado do form de portfólio na mesma página
    (`/painel/projetos/{id}/plano-de-trabalho`, distinto de
    `/painel/projetos/{id}`) — evita que salvar uma mudança rápida de
    estágio dispare validação/re-render de 5 campos de texto longo, e
    vice-versa; os dois forms na mesma página não interferem um no
    outro (testado explicitamente: preencher plano de trabalho não
    reseta os campos de portfólio salvos por outro form, e vice-versa).
    Na API é o mesmo `PATCH /api/projetos/{id}` de sempre — só o schema
    `ProjetoUpdate` ganhou os campos novos, sem rota nova.
    Nenhuma migração de dado exigiu tratamento especial — todos os 5
    campos são `Text` nullable, sem `server_default` necessário (só
    populado quando editado, mesmo padrão dos vários outros campos
    opcionais adicionados a tabelas já existentes nesta sessão).
22. **Etapas e cronograma do projeto** (RF-034, parcial) — usuário disse
    "seguir para implementar a RF-034". RF-034 pede etapas, atividades,
    cronograma, metas quanti/qualitativas, resultados, indicadores,
    riscos e impactos socioambientais — grande demais pra uma fatia só
    (o mesmo raciocínio já aplicado a RF-032/033/RF-048/RF-045). Decidi
    sozinho e expliquei depois (mesmo padrão dos itens 19/21 — decisão
    de sequenciamento dentro de um módulo já aprovado): construí só
    "etapas/atividades/cronograma", a camada estrutural que todo o
    resto (metas, resultados, indicadores) precisaria referenciar de
    qualquer forma. Deixei riscos de fora deliberadamente mesmo sendo
    citado no RF-034 — o RF-040 (Execução) pede risco com muito mais
    detalhe (probabilidade, impacto, evidência de mitigação), e criar
    um modelo simplificado agora só pra depois trocar por um mais
    completo pareceu pior que não ter nada ainda.
    Modelo novo `EtapaProjeto` — "etapa" e "atividade" tratadas como o
    mesmo nível (sem hierarquia de dois níveis), mesma simplificação já
    usada em `TarefaGovernanca`. `ordem` é auto-incrementada no
    servidor (conta quantas etapas já existem pro projeto e usa esse
    número) — decisão deliberada de não expor um campo de ordem manual
    no formulário, mais uma fonte de erro de usuário do que valor.
    **Gotcha que já era conhecido e aconteceu de novo, mesmo assim**:
    rodei `alembic upgrade head` sem revisar o autogenerate primeiro
    (confiança excessiva depois de várias migrações seguidas darem
    certo sem ajuste manual) e caiu exatamente no gotcha já documentado
    — `sa.Enum('PENDENTE', ...)` dentro de `create_table` tentando
    `CREATE TYPE statustarefa`, que já existe desde o módulo de
    Governança. Erro real do Postgres
    (`DuplicateObject: type "statustarefa" already exists`), rollback
    limpo (DDL transacional — `alembic current` continuou na revisão
    anterior, tabela não ficou pela metade), corrigido trocando pra
    `postgresql.ENUM(..., create_type=False)` e reaplicado com sucesso.
    **Reforça a lição, de novo**: **sempre** revisar o arquivo de
    migração autogerado antes de rodar `upgrade head`, procurando por
    `sa.Enum(...)` — não só quando "parece" que pode ser um enum
    reaproveitado, porque mesmo sabendo do gotcha eu ainda deixei passar
    dessa vez. Considerar até grepar `sa.Enum(` no diff da migração como
    parte do fluxo padrão antes de aplicar, em vez de confiar na memória.
23. **Finalização do RF-034** (metas, indicadores, riscos, impactos
    socioambientais) — usuário disse "seguir com a finalização da
    RF-034", revertendo a decisão do item 22 de deixar riscos de fora.
    Motivo da reversão: riscos ficou pedido explicitamente de novo pelo
    usuário, então construí um modelo (`RiscoProjeto`:
    descrição/probabilidade/impacto/resposta/responsável/status) já
    projetado para ser estendido pelo RF-040 (Execução) em vez de
    duplicado quando esse módulo for construído — ver docstring do
    modelo. Também adicionados `MetaProjeto` (quanti/qualitativa, com
    `valor_alvo`/`valor_alcancado` — só o valor mais recente, sem série
    histórica) e `IndicadorProjeto` (mais simples que
    `IndicadorEstrategico` do RF-044, também sem série histórica própria
    por enquanto). `impactos_socioambientais` virou um campo a mais em
    `projetos` (mesmo padrão 1:1 do RF-033), com um label próprio no
    form de plano de trabalho — é conceitualmente distinto do campo
    "Impactos esperados" do RF-033 (esse é sobre resultados/efeitos
    gerais do projeto; o novo é especificamente sobre impacto
    socioambiental).
    **Gotcha do enum reaproveitado aconteceu de novo, pela 3ª vez**:
    `MetaProjeto.status` reaproveita `StatusTarefa`, e o autogenerate
    gerou `sa.Enum(...)` de novo — desta vez pego *antes* de aplicar
    (segui a própria lição do item 22 e grepei `sa.Enum(` no arquivo
    gerado antes de rodar `upgrade head`), corrigido pra
    `postgresql.ENUM(..., create_type=False)` sem precisar de rollback.
    Migração `777ba9fa79ad`.
    Testado via curl (criar/listar/atualizar os 3 recursos novos, tanto
    pelas rotas web quanto pela API JSON) e via Playwright (screenshot
    com as 3 novas seções preenchidas — ver
    `projeto_rf034_final_shot.js` no diretório de scratch de screenshots,
    padrão do item 4 de "Armadilhas já resolvidas"), sem erros de
    console nem 500 reais no log do servidor local.
24. **RF-035, fundação** (continuidade, escalabilidade, equipe, origem
    dos recursos) — usuário disse "seguir com a implementação dos
    próximos requisitos recomendados", uma continuação genérica sem
    apontar um requisito específico. Decidi sozinho, sem perguntar: o
    RF-035 era o próximo item explicitamente listado como "falta" logo
    após a finalização do RF-034 (mesmo raciocínio de sequenciamento já
    usado nos itens 19/21/22 — dentro de um módulo já aprovado, decisão
    de "o que vem a seguir" não exige pausa). RF-035 pede "continuidade,
    escalabilidade, equipe, aquisições, origem dos recursos e cronograma
    físico-financeiro" — de novo grande demais pra uma fatia só (mesmo
    padrão do RF-034). Escopo desta fatia: **continuidade/
    escalabilidade** (campos `Text` a mais em `Projeto`, mesmo padrão
    narrativo do RF-033/034, adicionados ao mesmo form de plano de
    trabalho), **equipe** (`EquipeProjeto` — pessoa, função texto livre,
    vigência — mirror exato de `MembroOrgao` do RF-016, não reaproveitei
    `PessoaVinculo` porque aquele é sobre papel de acesso/RBAC numa
    entidade ou CPL, um conceito diferente de "função exercida neste
    projeto específico") e **origem dos recursos**
    (`OrigemRecursoProjeto` — fonte texto livre, valor, contrapartida
    booleana). **Aquisições e cronograma físico-financeiro ficaram de
    fora deliberadamente**: aquisições se sobrepõe ao RF-037 (cotações/
    pesquisa de preço), e cronograma físico-financeiro é essencialmente
    etapas (já existem, RF-034) cruzadas com valores financeiros por
    etapa, que só faz sentido depois que RF-036 (itens de despesa)
    existir — mesmo raciocínio já usado para riscos no item 22 (não
    duplicar um modelo simplificado que logo será substituído).
    **Primeiro campo monetário do sistema**: `OrigemRecursoProjeto.valor`
    usa `Numeric(14, 2)`/`Decimal` de verdade, diferente do padrão
    `String` usado em `valor_alvo` de `MetaProjeto` (que aceita metas
    não-numéricas como "30 empresas") — aqui é sempre dinheiro.
    Migração `d798be587a1c`, sem enum nenhum envolvido (`funcao` e
    `fonte` são texto livre, mesmo raciocínio de `eixo_sp_produz`), então
    sem o gotcha de sempre — mas segui o hábito de grepar `sa.Enum(`
    antes de aplicar de qualquer forma, como reforçado no item 23.
    Testado via curl (criar/listar/atualizar/encerrar, web e API JSON) e
    via Playwright (`projeto_rf035_shot.js`, mesmo diretório de scratch),
    sem erros de console nem 500 reais no log.
25. **RF-029/030: edital de fomento, submissão e recursos** — usuário
    disse "seguir a sequência natural (RF-029/030)", apontando
    explicitamente os dois requisitos juntos desta vez (diferente dos
    itens 22/24, onde a fatia foi decidida por mim). Ao contrário de
    RF-034/035 (que listam vários conceitos distintos num único
    requisito, forçando um corte), RF-030 já é intrinsecamente uma coisa
    só — "recursos, contrarrazões, diligências, respostas e decisões" é
    o mesmo fluxo de ida-e-volta de um processo de submissão — então
    RF-029 e RF-030 foram construídos juntos nesta fatia, sem deixar
    nada deliberadamente de fora dentro desses dois requisitos.
    **Modelo `EditalFomento`** (RF-029) — título, descrição, requisitos,
    documentos exigidos (texto livre — documento não define um
    checklist estruturado, e criar um checklist estruturado exigiria
    mudar `Documento.cpl_id`, hoje `NOT NULL`, pra aceitar documento sem
    CPL, mudança maior do que esta fatia pedia), datas de
    abertura/encerramento (o encerramento é o "marco de submissão" do
    requisito) e responsável. Global, não escopado a uma CPL — mesmo
    padrão do `Edital` de maturidade (`app/models/maturidade.py`), que é
    um conceito PROPOSITALMENTE diferente (critérios de avaliação de
    maturidade, não financiamento) apesar do nome igual em português —
    distinção já validada com o usuário antes de começar o módulo de
    Projetos (ver item 20). RBAC de gestão reaproveita
    `PAPEIS_EDITAL_GESTAO` (só `ADMINISTRADOR_PLATAFORMA`), mesmo grupo
    do edital de maturidade — mesma autoridade, mesmo motivo (é
    configuração compartilhada do programa, não algo que uma CPL
    gerencia); leitura é `PAPEIS_PROJETO_LEITURA`.
    **Vínculo projeto↔edital** — `Projeto.edital_fomento_id`, setado só
    via a ação explícita `POST /{id}/submeter`, que também move
    `estagio` pra `SUBMETIDO` na mesma transação (não editável pelo
    PATCH genérico de portfólio, pra manter a submissão como um evento
    deliberado, não um efeito colateral de editar outro campo).
    **Modelo `RecursoSubmissaoProjeto`** (RF-030) — `tipo`
    (`TipoRecursoSubmissao`: recurso/contrarrazão/diligência, enum
    novo), protocolo e prazo (controle explícito pedido pelo
    requisito), descrição, e decisão (reaproveita `StatusRecurso` —
    pendente/deferido/indeferido — o mesmo enum de `RecursoAvaliacao`,
    RF-027, mesmo conceito de ciclo de vida). Diferente de
    `RecursoAvaliacao` (que é 1:1 com a avaliação, no máximo um
    recurso), aqui é uma lista sem limite — o processo real vai e volta
    (diligência → resposta → nova diligência ou decisão), então múltiplos
    registros por projeto são esperados, não um erro. Decisão é
    `PAPEIS_EDITAL_GESTAO` (autoridade diferente de quem gere o
    projeto), mesmo raciocínio do `decidir_recurso` de RF-027.
    **Bug pego e corrigido antes do deploy, não durante**: as rotas
    `GET /editais-fomento` e `GET /editais-fomento/{id}` foram
    registradas originalmente *depois* de `GET /{projeto_id}` no
    roteador da API — como o FastAPI/Starlette casa rotas na ordem de
    registro, `GET /api/projetos/editais-fomento` caía primeiro em
    `GET /{projeto_id}`, tentando interpretar `"editais-fomento"` como
    UUID e devolvendo 422. Pego no teste via curl (não no Playwright,
    que só testa fluxos via UI/web, onde esse path específico não é
    usado do mesmo jeito) — corrigido movendo o bloco inteiro de rotas
    de edital de fomento pra antes da seção "Projetos / portfólio" no
    arquivo. **Lição nova pra registrar**: sempre que um sub-recurso
    global (sem prefixo de path variável antes dele, tipo
    `/editais-fomento` vs. `/{projeto_id}/algo`) for adicionado a um
    router que já tem uma rota `GET /{id}` genérica, ele **precisa** ser
    registrado antes dessa rota genérica — testar com curl direto na
    API (não só via UI) pra pegar esse tipo de colisão de rota, porque a
    UI web nunca bate nesse endpoint específico do jeito que expõe o bug.
    Migração `c0bdeb29e88f`, com o gotcha de enum reaproveitado de
    sempre (`statusrecurso`) — pego antes de aplicar, virou hábito.
    Testado via curl (criar edital, submeter projeto, criar
    recurso/contrarrazão/diligência, decidir, tudo via web e API JSON) e
    via Playwright (`projeto_rf029_030_shot.js`), sem erros de console
    nem 500 reais no log.
26. **RF-035, finalização** (aquisições e cronograma físico-financeiro)
    — usuário disse "implementar o restante da RF-035", desta vez
    pedindo explicitamente a parte que eu tinha decidido adiar nos itens
    22/24 (raciocínio anterior: aquisições se sobrepõe ao RF-037,
    cronograma físico-financeiro depende do RF-036 existir). Como o
    pedido agora é explícito, construí uma versão do RF-035 completo
    sem esperar RF-036/037 existirem — mesmo padrão já usado em
    `RiscoProjeto` (modelo simplificado agora, desenhado pra ser
    estendido depois, não duplicado).
    **Cronograma físico-financeiro**: não é uma entidade nova — são só
    dois campos a mais (`valor_previsto`, `valor_executado`,
    `Numeric(14,2)`) em `EtapaProjeto`. Cronograma físico-financeiro é
    fundamentalmente "etapa (já tem datas/status = lado físico) +
    dinheiro por etapa (lado financeiro)", então juntar na mesma linha
    fez mais sentido que criar uma tabela separada — mesma lógica já
    usada pra `impactos_socioambientais`/continuidade/escalabilidade
    virarem colunas a mais em vez de entidades novas.
    **Aquisições**: `AquisicaoProjeto` — item, descrição, categoria e
    quantidade (texto livre, mesmo raciocínio de `eixo_sp_produz`:
    quantidade pode vir com unidade não padronizada — "50 unidades",
    "200 kg" — e categoria não tem lista fechada no documento), valor
    estimado (`Numeric`, dinheiro de verdade), data prevista,
    responsável e status (`StatusTarefa`, reaproveitado). Desenhado pra
    ser estendido por uma `CotacaoAquisicao` ligada a `aquisicao_id`
    quando o RF-037 (pesquisas de preço, cotações de múltiplos
    fornecedores, validação de quantidade mínima) for construído — não
    duplicar.
    Migração `bcae54b40941`, com o gotcha de enum reaproveitado de
    sempre (`statustarefa` em `aquisicoes_projeto.status`) — pego antes
    de aplicar via grep, sem rollback.
    Testado via curl (criar/atualizar aquisições e etapas com valores
    financeiros, web e API JSON, conferindo os totais somados nas
    tabelas) e via Playwright (`projeto_rf035_final_shot.js`), sem erros
    de console nem 500 reais no log. Com esta fatia, **o RF-035 está
    100% implementado** — não fica mais nenhum campo do requisito
    pendente, só o resto do módulo de Projetos (RF-036 a RF-041).
27. **RF-036/037/038: financeiro do projeto** (itens de despesa,
    cotações, desembolsos) — usuário disse "seguir para as RFs 036-038",
    os três nomeados juntos, então construí os três nesta mesma fatia
    (mesmo padrão do item 25/RF-029-030 — quando o pedido já vem
    agrupado, não recorto sozinho).
    **RF-036 não é uma tabela nova**: "cadastrar itens de despesa,
    quantidades, valores, categorias, fontes, contrapartida e
    vinculação a etapas" é o `AquisicaoProjeto` do RF-035 visto pelo
    ângulo financeiro — por isso a extensão foi adicionar
    `etapa_id`/`origem_recurso_id`/`contrapartida` na mesma tabela, não
    criar um `ItemDespesaProjeto` duplicado.
    **RF-037** — `CotacaoAquisicao` (fornecedor, valor, anexo opcional
    via Documentos, `selecionada`), exatamente a extensão já anunciada
    na docstring de `AquisicaoProjeto` desde o item 24. "Validar
    quantidade mínima de fornecedores" virou uma regra de negócio de
    verdade, não só descritiva: `POST /cotacoes/{id}/selecionar` conta
    quantas cotações a aquisição tem e, se for menos que
    `MINIMO_COTACOES` (constante `= 3`, **não fixado no documento de
    requisitos** — é prática comum de pesquisa de mercado no setor
    público brasileiro, decisão minha, documentada no código), exige
    `justificativa_excecao` (senão 400) — testado nos dois sentidos
    (bloqueia com 2 cotações sem justificativa, libera com 3+ sem
    exigir nada). A seleção desmarca qualquer cotação selecionada
    anterior da mesma aquisição (só uma vencedora por vez).
    **RF-038** — `DesembolsoProjeto` (data, valor, aquisição e origem de
    recursos ligadas, bem adquirido, comprovante via Documentos,
    `conciliado`). **"Saldos" não é armazenado** — é `OrigemRecursoProjeto.valor`
    menos a soma dos desembolsos ligados àquela origem, calculado a
    cada carregamento da tela (`saldos_por_origem` no web route), pra
    nunca ficar dessincronizado do que realmente foi gasto. "Conciliação
    por projeto" também não é uma entidade — é a leitura agregada da
    tabela de desembolsos com o toggle `conciliado` por linha.
    **Padrão de UI evitando JS**: a princípio desenhei o form de "nova
    cotação" fazendo o usuário escolher a aquisição por um `<select>` e
    submetendo pra uma URL com `{aquisicao_id}` no path — isso exigiria
    JS pra montar a URL dinamicamente antes do submit, que não é um
    padrão usado em nenhum outro lugar deste projeto (só forms HTML
    puros). Corrigido antes de testar: a rota web virou
    `POST /{projeto_id}/cotacoes` com `aquisicao_id` como campo de form
    normal (igual ao padrão de `responsavel_id` em outros forms), não
    path param — a API manteve `/aquisicoes/{id}/cotacoes` (REST de
    verdade, sem o mesmo problema pra um cliente HTTP). **Se precisar de
    novo de um form que "cria X pra um Y escolhido num select", sempre
    usar `Y_id` como campo de form, nunca um path param dinâmico
    montado por JS.**
    Migração `94d2ed47a842` — gotcha novo, ver "Armadilhas já
    resolvidas" (coluna `Boolean NOT NULL` nova numa tabela já populada
    precisa de `server_default` explícito, autogenerate não resolve
    sozinho a partir do `default=` do Python).
    Testado via curl (criar aquisição vinculada a etapa/origem, criar
    cotações, validar a regra de mínimo com e sem justificativa,
    registrar desembolso, conferir saldo calculado, conciliar — web e
    API JSON) e via Playwright (`projeto_rf036_038_shot.js`, incluindo o
    form de cotação sem JS de fato funcionando pelo navegador), sem
    erros de console nem 500 reais no log.
28. **RF-039/040: execução do projeto** (entregas, marcos, alterações
    de plano, aprovações; riscos com evidência de mitigação) — usuário
    disse "prosseguir para as RFs 039/040", os dois nomeados juntos,
    então construí os dois nesta fatia (mesmo padrão dos itens 25/27).
    **RF-040 foi a extensão mais barata de toda a sessão**: "gerenciar
    riscos com probabilidade, impacto, resposta, responsável e
    evidência de mitigação" já tinha 4 dos 5 campos prontos desde o
    RF-034 — só faltava `evidencia_documento_id` em `RiscoProjeto`,
    exatamente como a docstring original do modelo já previa (ligar ao
    repositório de Documentos, mesmo padrão de
    `AvaliacaoCriterio.evidencia_documento_id`).
    **RF-039** ("acompanhar execução física e financeira, entregas,
    marcos, alterações de plano e aprovações") — a parte física/
    financeira já estava coberta desde o RF-035/038 (`EtapaProjeto`
    status/valores, `DesembolsoProjeto`); o que faltava eram três
    conceitos novos:
    - **Marcos**: de novo não é entidade nova — `marco: Boolean` a mais
      em `EtapaProjeto` (mesmo padrão de não duplicar já usado pro
      cronograma físico-financeiro e pra `AquisicaoProjeto`/RF-036).
    - **Entregas**: `EntregaProjeto` — título, etapa opcional, datas
      prevista/entrega, documento opcional e aprovação
      (`aprovado`/`aprovado_por_id`/`data_aprovacao`), **mesmo padrão
      de aprovação que `Documento` já usa** (não um workflow de
      aprovação genérico à parte). `data_entrega` preenchida ou não já
      sinaliza se foi entregue; `aprovado` é uma decisão independente
      sobre o que foi entregue.
    - **Alterações de plano**: `AlteracaoPlanoProjeto` — `tipo` (texto
      livre), descrição/justificativa, solicitação e decisão,
      reaproveitando `StatusRecurso` e o mesmo formato de campos
      (`parecer_decisao`/`decidido_por_id`/`data_decisao`) já usado em
      `RecursoSubmissaoProjeto` (RF-030). **Diferença de autoridade
      importante**: decisão aqui é `PAPEIS_GESTAO` (entidade gestora/
      administrador — governança interna do projeto), não
      `PAPEIS_EDITAL_GESTAO` como em `RecursoSubmissaoProjeto` (que
      contesta uma decisão do órgão externo do edital) — são
      autoridades diferentes por natureza, mesmo os dois reaproveitando
      `StatusRecurso`. Aprovação de entrega usa a mesma autoridade
      (`PAPEIS_GESTAO`) pelo mesmo raciocínio.
    **Bug de UI pego antes de testar**: a primeira versão do form de
    "decidir alteração" e "aprovar entrega" estava condicionada a
    `e_administrador` (só `ADMINISTRADOR_PLATAFORMA`), copiado por
    hábito do padrão de `RecursoSubmissaoProjeto`. Mas a autorização de
    verdade no backend é `PAPEIS_GESTAO`, que também inclui
    `ENTIDADE_GESTORA`/`DIRIGENTE_ENTIDADE_GESTORA` — um usuário desses
    papéis teria permissão real (backend aceitaria) mas nunca veria o
    form (`e_administrador` é `False` pra eles). Corrigido criando
    `_pode_gestao(db, usuario, cpl_id)` em `routes_projeto.py` (checa
    `PAPEIS_GESTAO` de verdade, não só admin) e usando esse flag em vez
    de `e_administrador` nos dois forms. **Lição**: ao decidir qual
    flag de contexto usar pra esconder/mostrar um form no template,
    conferir contra qual grupo de papéis a rota realmente valida no
    backend — não reaproveitar `e_administrador`/outro flag existente
    só porque "parece" a mesma coisa.
    Migração `69235b36be9e`, com os dois gotchas de sempre juntos numa
    mesma migração pela primeira vez (enum reaproveitado + `Boolean NOT
    NULL` sem `server_default`) — ambos pegos antes de aplicar.
    Testado via curl (etapa marco, entrega → registrar → aprovar,
    alteração de plano → decidir, `evidencia_documento_id` em risco via
    API — web e API JSON) e via Playwright
    (`projeto_rf039_040_shot.js`), sem erros de console nem 500 reais
    no log. Com esta fatia, **RF-029 a RF-040 do módulo de Projetos
    estão completos** — só falta RF-041 (relatório de
    execução/financeiro/dossiê de evidências) pra fechar o módulo
    inteiro.
29. **RF-041: relatório de execução, relatório financeiro e dossiê de
    evidências do projeto** — usuário disse "seguir para implementação
    da RF-041". Repeti o padrão de geração de relatório já usado 5
    vezes no RF-048 (resumo agregado em `app/services/*.py` → função
    de formatação em `app/services/geracao_documentos.py` → rota que
    busca a entidade, chama `verificar_papel`, gera o PDF, salva via
    `salvar_arquivo` e cria um `Documento`), mas escopado a um único
    `Projeto` em vez de uma CPL inteira — mesmo raciocínio de
    `resumo_orgao`/relatório de comissão (RF-048), que já tinha
    resolvido "escopar a uma sub-entidade" antes. **Nenhuma migração
    nesta fatia** — as três funções novas (`resumo_execucao_projeto`,
    `resumo_financeiro_projeto`, `dossie_evidencias_projeto`, em
    `app/services/projeto.py`, arquivo novo — o módulo de Projetos
    nunca tinha tido lógica fora das rotas até agora) só leem entidades
    que já existem, sem criar nenhuma tabela/coluna:
    - **Relatório de execução**: cronograma (etapas concluídas/marcos),
      metas, indicadores, entregas, riscos (por `StatusRisco`) e
      alterações de plano pendentes.
    - **Relatório financeiro**: origens de recursos com saldo
      calculado (mesmo cálculo — nunca armazenado — já usado na tela
      de detalhe), aquisições e desembolsos/conciliação.
    - **Dossiê de evidências**: agrega os quatro pontos onde o módulo
      já linka Documentos (`CotacaoAquisicao.documento_id`,
      `DesembolsoProjeto.documento_comprovante_id`,
      `RiscoProjeto.evidencia_documento_id`,
      `EntregaProjeto.documento_id`), filtrando cada um por FK não-nula
      — não introduz nenhum vínculo novo, só lê o que as fatias
      RF-036/037/038/040/039 já ligaram.
    Rotas `POST /api/projetos/{id}/relatorio-execucao`,
    `/relatorio-financeiro`, `/relatorio-dossie-evidencias` (API e
    web, ambas com `PAPEIS_GESTAO` — mesma convenção de **todo**
    relatório do sistema, não `PAPEIS_PROJETO_GESTAO`, que é a
    autoridade do dia a dia do projeto, não a de emitir prestação de
    contas), botões em `/painel/projetos/{id}` dentro de um novo card
    "Relatórios (RF-041)", visível só a quem `_pode_gestao` (mesmo
    helper do item 28). Web routes redirecionam pro repositório de
    documentos da CPL (`/painel/documentos/cpls/{id}`), mesmo padrão
    dos outros 5 relatórios — não pra tela do projeto, pra manter
    "todo relatório gerado aparece no mesmo lugar" como convenção única.
    Testado via curl (gerar os 3, conferir que aparecem no repositório
    de documentos), rasterização com PyMuPDF pra validar o conteúdo
    visualmente (inclusive o caminho "com evidência" do dossiê, testado
    de propósito — subi um documento via API e linkei a um desembolso
    via PATCH antes de regerar, pra não validar só o caminho vazio) e
    Playwright (`projeto_rf041_shot.js`, mais um rerun de
    `projeto_rf036_038_shot.js`/`projeto_rf039_040_shot.js`/
    `documentos_shot.js`/`projetos_shot.js`/`rbac_403_shot.js`), sem
    erros de console nem 500 reais no log (só o 403 esperado do teste
    de RBAC). **Com esta fatia, o módulo de Projetos inteiro (RF-029 a
    RF-041) está completo**, e RF-048 também — "relatório de projeto"
    era o único dos 6 tipos que faltava, e o requisito não descreve um
    formato próprio pra ele além do que RF-041 já pede, então não há
    um 7º tipo a construir.
30. **RF-053 (exportação XLSX/CSV) e RF-045 (painel agregado de
    projetos)** — usuário pediu pra "implementar a RF-053 e RF-045",
    depois de eu ter respondido, numa pergunta anterior sobre o que
    ainda falta em todas as fases, que esses dois eram os candidatos
    mais baratos/de maior valor pra fazer em seguida.
    - **RF-053**: a API REST/JSON já era completa e a importação (RF-013)
      já existia; faltava só a **exportação** XLSX/CSV. Escopo escolhido:
      entidades + diagnóstico cadastral de uma CPL — o dado mais "de
      planilha" do sistema, e o par natural da importação. Desenhado pra
      ser **simétrico à importação**: `exportar_entidades()` em
      `app/services/importacao_entidades.py` usa `CAMPOS_CONHECIDOS` (a
      mesma lista de nomes canônicos de campo que a importação já
      reconhece) como cabeçalho — como `mapear_colunas()` já inclui o
      nome canônico de cada campo no próprio conjunto de aliases (`{campo}
      | aliases_norm`), um arquivo exportado por aqui é reconhecido
      100% automaticamente se reimportado, sem precisar de nenhum
      código novo dos dois lados. Testado de propósito: exportei,
      reimportei via `POST /api/cadastro/cpls/{id}/importacoes` e
      conferi que as 35 colunas mapeavam sozinhas (`mapeamento_sugerido`
      cobria os 35 cabeçalhos, nenhum "não mapeado"). CSV sai com BOM
      (`utf-8-sig`) — sem isso o Excel abre acentuação corrompida em
      duplo-clique direto no arquivo; `ler_planilha()` já tentava
      `utf-8-sig` primeiro do lado da *leitura* por causa exatamente
      disso, então a escrita seguiu o mesmo padrão. `GET /api/cadastro/cpls/
      {id}/exportar-entidades?formato=xlsx|csv`, RBAC
      `PAPEIS_GOVERNANCA_LEITURA` (mesma exigência de qualquer leitura
      do módulo), botões em `/painel/cadastro/cpls/{id}`. Escopo
      deliberadamente restrito a entidades — outras listagens (projetos,
      documentos, auditoria) não ganharam exportação nesta fatia.
    - **RF-045**: só faltava "painel de projetos" (o resto do RF-045 já
      existia). Nova função `resumo_projetos_cpl()` em
      `app/services/projeto.py`, mesmo padrão de `resumo_governanca`/
      `resumo_planejamento` (dict pronto pro template, sem
      `response_model` de API próprio — não há requisito pedindo essa
      agregação via API, só o painel). **Distinção importante**: isso
      não duplica os relatórios do RF-041 — aqueles são por um projeto
      só; este agrega **todos os projetos de uma CPL** (contagem por
      estágio/prioridade via `Counter`, financeiro somado de todas as
      origens de recurso/desembolsos, execução agregada de etapas/
      marcos/entregas/metas/riscos). Sem entidade nova, sem migração —
      só leitura agregada do que já existe. Virou um 5º card no topo do
      dashboard (`row-cols-md-5`, era `-4`) e um novo card "Projetos
      (RF-045)" na coluna direita de `/painel/indicadores/cpls/{id}`,
      com link pra `/painel/projetos/cpls/{id}` (portfólio individual).
      **Só maturidade segue sem painel** no RF-045 — não priorizado.
    Nenhuma migração em nenhum dos dois. Testado via curl (export
    xlsx/csv + round-trip de reimportação, RBAC 400/401 do endpoint de
    exportação) e Playwright (`rf045_053_shot.js`, mais rerun de
    `projeto_rf041_shot.js`/`documentos_shot.js`/`indicadores_shot.js`/
    `cadastro.js`), sem erros de console nem 500 reais no log.
31. **Painel de maturidade (resto do RF-045)** — usuário pediu pra
    "finalizar as pendências da RF-045 e do painel de maturidade" logo
    depois do item 30. **A peça mais barata desta sessão inteira**: não
    escrevi nenhuma função de agregação nova — `resumo_recadastramento()`
    (`app/services/maturidade.py`) já existia desde o RF-048 (usada só
    pra gerar o PDF de recadastramento) e já continha exatamente o que
    um "painel de maturidade" precisa (nível vigente, validade do
    reconhecimento com dias-para-vencer, histórico de avaliações,
    lacunas da avaliação vigente). Só precisei chamar essa função a mais
    uma vez, no dashboard (`app/web/routes_indicadores.py`, contexto
    `maturidade`), e criar o card no template — mesmo padrão de reúso
    já visto em `resumo_cadastral()` (dashboard + relatório de impacto)
    e agora repetido pela terceira vez. Adicionei também um 6º KPI no
    topo do dashboard (`row-cols-md-6`, era `-5`) com o nível de
    maturidade atual (texto, não número — `kpi-valor small` porque o
    valor é uma string como "cpl consolidada", não um dígito). Card
    "Maturidade (RF-045)" reaproveita o mesmo alerta de vencimento já
    formatado no PDF de recadastramento (vencido → `alert-danger`,
    vencendo em breve → `alert-warning`), com link pra
    `/painel/maturidade/cpls/{id}` (avaliações completas). Testado o
    caminho vazio também (CPL sem nenhuma avaliação/reconhecimento
    ainda — "não reconhecida"/"Sem reconhecimento formal registrado
    ainda", sem erro). **Com isso, RF-045 está completo**: os cinco
    painéis do requisito (governança, planejamento/cadastro, projetos,
    finanças, maturidade) existem no mesmo dashboard consolidado por
    CPL — nenhuma migração, testado via curl + Playwright, sem 500
    reais no log.
32. **RF-017: anexos de arquivo em reuniões** — usuário pediu "vamos
    implementar a RF-017", a única peça que faltava no módulo de
    Governança (a lista era a resposta da minha sugestão anterior de
    backlog). **Zero entidade nova, zero migração** — `Documento.reuniao_id`
    (`app/models/documento.py`) já existia desde sempre, usado só pela
    geração automática de ata em PDF (`gerar_ata_pdf`, RF-043); só
    faltava deixar o usuário anexar um arquivo *qualquer* (não só a ata
    gerada) a uma reunião. Mudanças:
    - `POST /api/documentos/cpls/{cpl_id}` (`enviar_documento`, já
      existia) ganhou um campo `reuniao_id: uuid.UUID | None = Form(None)`
      opcional — se vier preenchido, valida que `reuniao.orgao.cpl_id ==
      cpl_id` (400 se não bater, 404 se a reunião não existir).
    - `GET /api/documentos/reunioes/{reuniao_id}` (rota nova) — lista os
      anexos de uma reunião, mesmo filtro de confidencialidade
      (`PAPEIS_IMPEDIMENTO_LEITURA` pra ver documento confidencial) já
      usado em `listar_documentos` (por CPL). **Cuidado de ordenação de
      rota**: registrada antes de `GET /{documento_id}` no arquivo — não
      que colidisse (contagem de segmentos de path diferente, `/reunioes/
      {id}` tem 2 segmentos vs. `/{documento_id}` tem 1, então Starlette
      nunca teria confundido as duas), mas segui o hábito de sempre
      checar isso explicitamente depois da lição do item 13 de
      "Armadilhas já resolvidas".
    - Web: rota nova `POST /painel/documentos/reunioes/{id}/anexos` (não
      reaproveitei a genérica `POST /painel/documentos/cpls/{cpl_id}`)
      porque essa redireciona pra lista geral de documentos da CPL, e eu
      queria voltar pro detalhe da reunião — mesmo raciocínio já usado
      pra `ata-pdf` no mesmo arquivo (que também tem sua própria rota
      `/reunioes/{id}/ata-pdf` em vez da genérica).
    - Template `reuniao_detail.html`: card "Anexos" (lista com badge de
      categoria/confidencialidade + botão baixar, mesmo estilo de
      `cpl_documentos.html`) e card "Novo anexo" (form plano de upload,
      sem JS, mesmo padrão de `cpl_documentos.html`).
    **Achado no meio do trabalho, não relacionado ao RF-017**: RF-019
    ("alertas automáticos" de tarefa) estava marcado `⚠️ Parcial` em
    `docs/requisitos_macros.md` desde antes, mas isso já tinha sido
    coberto pelo motor de notificações do RF-049
    (`_gerar_tarefas_com_prazo()` em `app/services/notificacoes.py`) —
    documentação desatualizada, não uma lacuna real. Corrigido pra
    `✅ Implementado` na mesma sessão, já que eu tinha sinalizado isso
    numa resposta anterior sobre o que restava no backlog.
    Testado via curl (upload com `reuniao_id` válido, `reuniao_id` de
    UUID inexistente → 404, listagem por reunião) e Playwright
    (`rf017_shot.js` — upload real de arquivo via UI, mais rerun de
    `reuniao_ata_shot.js`/`documentos_shot.js`), sem erros de console
    nem 500 reais no log. **Com isso, RF-015 a RF-020 (Governança) estão
    completos.**
33. **RF-004: recuperação de senha e MFA** — usuário pediu "implementar
    a RF-004". **Única fatia desta sessão com decisão de escopo real
    tomada via `AskUserQuestion` antes de codar** (as outras foram
    "óbvias" o suficiente pra decidir sozinho): (a) canal de recuperação
    de senha — e-mail transacional de verdade vs. reset assistido por
    administrador vs. só MFA por enquanto — usuário escolheu e-mail de
    verdade; (b) provedor — SMTP genérico vs. API de provedor específico
    (Resend) vs. decidir depois — usuário escolheu SMTP genérico. Isso
    importa porque o sistema **nunca teve nenhum canal de e-mail** antes
    desta fatia (todas as notificações do RF-049 são só dentro do
    sistema) — não dava pra simplesmente inferir a resposta certa, e as
    duas perguntas tinham consequência real (infra nova, segredos novos
    em produção).
    - **Modelo**: `TokenRecuperacaoSenha` (`app/models/usuario.py`) —
      token de uso único (`secrets.token_urlsafe(32)`), `expira_em`,
      `usado_em`. `Usuario` ganhou `mfa_secret` (TOTP em base32) e
      `mfa_backup_codes` (JSONB, lista de hashes bcrypt — nunca texto
      puro). Migração `48be8b55a24d`, sem gotcha nenhum dos dois de
      sempre — colunas novas todas nullable (sem `server_default`
      necessário), sem enum nenhum envolvido.
    - **Dependências novas**: `pyotp` (TOTP) e `qrcode[pil]` (QR code —
      Pillow já vinha transitivamente de `fpdf2`, mas declarei explícito
      mesmo assim, pra não depender de uma transitiva).
    - **`app/services/email.py`**: SMTP genérico via `smtplib` puro —
      nenhum provedor específico embutido, tudo via `SMTP_*` em
      `app/core/config.py`. `SMTP_HOST` ausente levanta `RuntimeError`
      (vira 500 na rota) em vez de fingir que enviou — sinal de
      configuração faltando, não um bug.
    - **`app/services/recuperacao_senha.py`**: `solicitar_recuperacao_senha`
      é **silenciosa** se o e-mail não existir (nunca revela) — a rota
      sempre devolve a mesma mensagem genérica, exista a conta ou não
      (proteção padrão contra enumeração). `redefinir_senha` idem: não
      diferencia "token não existe" de "expirado" de "já usado" na
      resposta — só `False`.
    - **`app/services/mfa.py`**: ativação em **dois passos**, mesmo
      raciocínio do remapeamento de importação (RF-013) — nunca ativar
      direto. `iniciar_ativacao_mfa` já salva o segredo em
      `usuario.mfa_secret`, mas só `confirmar_ativacao_mfa` (código
      válido gerado a partir dele) liga `mfa_enabled`. Sem essa etapa,
      um segredo mal escaneado no autenticador trancaria o próprio
      usuário pra fora — a mesma cautela de "nunca aplicar de primeira
      sem confirmação humana" que já apareceu em RN-016 (decisão de
      nível de maturidade) e no remapeamento de planilha.
    - **Bug de segurança pego antes de testar, não depois**: o token do
      passo intermediário do login com MFA (senha ok, código ainda não
      verificado) é um JWT válido com `sub` = id do usuário — se
      `get_current_user` só checasse `sub`, esse token *pendente*
      seria aceito como sessão completa, **anulando o MFA inteiro** (um
      atacante que interceptasse só esse cookie já teria acesso total,
      sem nunca precisar do segundo fator). Corrigido de duas formas
      redundantes: (1) cookie **separado** (`sigcpl_mfa_pending`, nunca
      `sigcpl_access_token`) — `get_current_user` só lê o cookie de
      sessão de verdade; (2) `get_current_user` também rejeita
      explicitamente qualquer token com a claim `mfa_pending: true`,
      mesmo que reenviado manualmente como Bearer. Duas camadas porque
      a primeira sozinha dependeria de nenhuma rota nunca ler o cookie
      errado por engano — a segunda torna isso estruturalmente
      impossível independente de onde o token apareça.
    - **Login em duas velocidades**: web é 2 passos (POST /login com
      senha → cookie pendente de 5 min → GET/POST /login/mfa com o
      código → cookie de sessão real), porque um humano precisa de uma
      tela pra digitar o código depois de ver que a senha bateu. API é
      **1 passo só** (`mfa_code` opcional no mesmo `POST /api/auth/login`,
      ao lado do `OAuth2PasswordRequestForm`) porque um cliente de API
      já sabe gerar o código na hora — não faz sentido forçar uma
      segunda chamada só por uniformidade com o fluxo web.
    - **Redação de auditoria**: `mfa_secret`, `mfa_backup_codes` e —
      mais importante — **qualquer campo chamado `token`** (não só
      `TokenRecuperacaoSenha.token`) entraram em `_CAMPOS_REDIGIDOS`
      (`app/services/auditoria.py`). Descobri nesse processo que
      `CampanhaConvite.token` (RF-012, sessão bem anterior) **nunca
      tinha sido redigido** — o listener automático de auditoria
      (`before_flush`) captura qualquer modelo com `id`, então esse
      token de autopreenchimento público vinha sendo gravado em texto
      puro na trilha desde que o módulo de Cadastro dinâmico existe.
      Corrigido de graça (redigir por nome de campo, não por modelo,
      resolve os dois de uma vez) — não fui atrás de expurgar o
      histórico já gravado no banco, só parei de gravar novo.
    - **Testado sem depender de um provedor de e-mail real**: subi um
      servidor SMTP de debug local (`aiosmtpd`, instalado só na venv de
      dev — não é dependência do projeto) que só imprime o e-mail
      recebido, apontei `SMTP_HOST=127.0.0.1`/`SMTP_PORT=1025` pro app
      local, e validei o fluxo inteiro ponta a ponta: pedir recuperação
      → capturar o link real do "e-mail" → abrir a página → redefinir →
      confirmar que a senha antiga para de funcionar e a nova funciona
      → confirmar que reusar o mesmo token falha. MFA testado gerando
      códigos TOTP de verdade via `pyotp.TOTP(segredo).now()` num
      script auxiliar (mesmo segredo que o backend gerou), cobrindo
      login sem código (falha), com código TOTP certo (passa), com
      código de backup (passa e consome — reuso falha depois),
      cookie pendente sozinho não abre `/painel` (redireciona pro
      login), e o card de auditoria confirmando a redação. Playwright
      (`rf004_shot.js`) cobriu a UI: `/esqueci-senha`, `/painel/perfil`
      sem MFA, tela de QR code, confirmação, tela de códigos de backup
      (uma vez só), e desativação — sem erros de console. Regressão:
      `login_and_shot.js`/`documentos_shot.js`/`projeto_rf041_shot.js`/
      `rbac_403_shot.js` sem 500 reais no log.
    **Pendência real de deploy** (não de código): as variáveis `SMTP_*`
    em produção (`.env.prod`) ainda estão vazias — a rota
    `/esqueci-senha` vai 500 em produção até alguém preencher
    credenciais de um provedor SMTP de verdade lá. Documentado também no
    README e não escondido — é uma decisão consciente de "a
    funcionalidade está pronta e testada, falta só a chave de
    produção", não um bug.
34. **RF-010: produtos, serviços, tecnologias, canais digitais e
    capacidade produtiva** — usuário pediu "implementar a RF-010",
    escolhida entre os candidatos que eu tinha sugerido numa avaliação
    de backlog anterior. Certificações e diferenciais competitivos já
    existiam desde o RF-012/046 (`DiagnosticoCadastral`); faltava o
    resto.
    - **`OfertaEntidade`** (`app/models/entidade.py`) — produto, serviço
      ou tecnologia (`TipoOferta`), tabela nova e repetível (uma
      entidade pode ofertar vários) — não escopada por CPL como
      `EntidadeElo`, porque o que uma entidade produz é característica
      dela, não algo que muda conforme a CPL. `ativo` em vez de exclusão
      (mesmo padrão de `EquipeProjeto`/`EntidadeElo`).
    - **`Entidade.canais_digitais`** — descoberta no meio do trabalho:
      esse campo JSONB **já existia no modelo desde o RF-006/008**
      (bem antes desta sessão), mas era completamente órfão — sem
      schema Pydantic, sem rota, sem UI, `grep` confirmou zero uso em
      qualquer lugar do código além da própria declaração da coluna.
      Ganhou `PATCH /api/entidades/{id}/canais-digitais` e formulário
      com um conjunto fixo de canais conhecidos (site/Instagram/
      Facebook/LinkedIn/WhatsApp) em vez de chave livre — primeira vez
      que o projeto precisou editar um campo JSONB via form sem JS, e a
      solução foi a mesma lógica de sempre: um `<input>` por chave
      conhecida, não "adicionar campo dinamicamente".
    - **`DiagnosticoCadastral.capacidade_produtiva`** — campo novo,
      texto livre (capacidade varia demais entre tipos de negócio pra
      caber num campo numérico único). Adicionado aos 3 pontos de
      escrita de sempre: formulário público de campanha
      (`atualizacao_form.html`), `_ALIASES_CAMPO` da importação
      (`app/services/importacao_entidades.py`) e schema da API. Como
      `CAMPOS_CONHECIDOS`/`_CAMPOS_DIAGNOSTICO` (RF-053) são derivados
      de `_ALIASES_CAMPO` por `set` subtraction, não hardcoded, o campo
      **apareceu automaticamente na exportação de entidades sem
      nenhuma linha de código a mais ali** — testado explicitamente
      (exportei, conferi que `capacidade_produtiva` estava na 36ª
      coluna do CSV com o valor certo).
    - **Nova tela** `/painel/cadastro/entidades/{id}` — não existia
      NENHUMA tela de detalhe de entidade antes desta fatia (só a lista
      por CPL em `cpl_cadastro.html`, sem drill-down). Reúne ofertas +
      canais digitais (editáveis ali, RBAC `PAPEIS_GESTAO`) e um resumo
      read-only do diagnóstico — deliberadamente **não** um form de
      edição do diagnóstico inteiro: esse continua só editável via
      campanha/planilha/API, mesmo padrão já estabelecido há várias
      sessões (não uma decisão nova). Link adicionado na lista de
      "Entidades vinculadas" de `cpl_cadastro.html`.
    - **RBAC**: reaproveitei a mesma lógica de visibilidade de
      `obter_entidade` (entidade vinculada a uma CPL visível ao
      usuário) fatorada num helper `_get_entidade_visivel_or_404`
      (API) / `_entidade_visivel_ou_none` (web) — não inventei um
      esquema novo de escopo.
    Migração `2f06d7b1b330` — sem gotcha nenhum dos dois de sempre
    (tabela nova com enum `tipooferta` criado pela primeira vez, sem
    reaproveitamento; coluna nova nullable). Testado via curl (criar
    oferta, listar, desativar, atualizar canais digitais, 401 sem auth)
    — achei e contornei uma armadilha de acentuação do git-bash ao
    passar `-d` com "ê"/"ã" direto na linha de comando (mesma família do
    item 11 de "Armadilhas já resolvidas", mas do lado do `curl -d`
    agora, não do `python -c`; contornado escrevendo o JSON num arquivo
    com `python -c "print(json.dumps(...))"` e usando
    `--data-binary @arquivo` em vez de `-d` direto) — e testei o
    formulário público de verdade (busquei um convite real via API,
    submeti `capacidade_produtiva` por ele, conferi que apareceu na
    tela de detalhe da entidade). Playwright (`rf010_shot.js` — navegar
    da lista de entidades da CPL até o detalhe, adicionar uma oferta via
    UI, desativar via UI) mais rerun de `cadastro.js`/`documentos_shot.js`/
    `rbac_403_shot.js`, sem erros de console nem 500 reais no log.
35. **RF-026: simular cenários** e **RF-027: habilitação jurídica** —
    usuário pediu "implementar a RF-26/27", os dois últimos itens
    parciais do módulo de Maturidade, escolhidos entre os candidatos que
    eu tinha sugerido numa avaliação de backlog anterior.
    - **RF-026 (simular cenários)**: a peça mais barata desta sessão —
      **nenhuma função de cálculo nova**. `calcular_pontuacao()`,
      `sugerir_nivel()` e `lacunas()` (todas em
      `app/services/maturidade.py`) já eram puras desde que foram
      escritas pra `concluir_avaliacao()` — só leem `avaliacao.notas`,
      nunca escrevem no banco. A única coisa que faltava era **chamar
      essas mesmas funções enquanto a avaliação ainda está em
      andamento** (hoje só eram chamadas dentro de
      `concluir_avaliacao`, que persiste o resultado e muda o status pra
      `CONCLUIDA`) e mostrar isso numa tela. `simular_avaliacao()` é só
      essas 3 chamadas com o resultado empacotado num dict — 15 linhas.
      "Ver o efeito de mudar uma nota antes de salvar" já era suportado
      de graça: `PUT .../notas` (RF-025) sempre foi chamável múltiplas
      vezes antes de concluir (upsert por critério); só faltava a tela
      mostrar o resultado hipotético a cada recarregamento. Card
      "Simulação" aparece em `avaliacao_detail.html` só enquanto
      `status == em_andamento` — a partir da conclusão real, os campos
      oficiais de `Avaliacao` (`pontuacao_calculada`/`nivel_sugerido`)
      tomam o lugar do card, sem duplicar informação.
      `GET /api/maturidade/avaliacoes/{id}/simulacao`.
    - **RF-027 (habilitação jurídica)**: `ItemHabilitacaoJuridica`
      (`app/models/maturidade.py`) — checklist por CPL+edital, `descricao`
      livre (mesmo raciocínio de `eixo_sp_produz`: sem lista fechada de
      documentos exigidos no requisito), `documento_id` reaproveitando
      Documentos (RF-042), ciclo `pendente → entregue → aprovado/
      rejeitado` (`StatusItemHabilitacao`, enum novo). **Autoridade
      dividida em dois papéis, cuidadosamente**: criar item/anexar
      comprovante é `PAPEIS_GESTAO` (a CPL reunindo a própria
      documentação), analisar (aprovar/rejeitar) é `PAPEIS_EDITAL_GESTAO`
      — mesma autoridade de `RecursoAvaliacao`/`decidir_recurso`, porque
      é o órgão externo do edital validando a regularidade jurídica da
      CPL, não uma decisão interna dela (mesma distinção já usada pra
      `AlteracaoPlanoProjeto` vs. `RecursoSubmissaoProjeto` no módulo de
      Projetos). Pra gating da UI, reaproveitei o flag `e_administrador`
      já existente em `routes_maturidade.py` pro botão de "analisar" —
      conferi antes que ele reflete exatamente `PAPEIS_EDITAL_GESTAO`
      (`cpl_ids_visiveis(db, usuario) is None`, verdadeiro só pra
      `ADMINISTRADOR_PLATAFORMA`, o único papel em
      `PAPEIS_EDITAL_GESTAO`) — mesma lição do item 16 de "Armadilhas já
      resolvidas" (nunca reaproveitar um flag de UI sem conferir contra
      o `PAPEIS_*` exato que o backend valida), desta vez confirmando que
      o flag existente já estava certo, em vez de achar um bug novo.
      Nova seção "Habilitação jurídica" em `cpl_avaliacoes.html`
      (`/painel/maturidade/cpls/{id}`), com upload de comprovante (form
      separado, só aparece pra itens ainda sem `documento_id`) e forms de
      análise (só pra `e_administrador`, só pra itens `entregue`/
      `pendente`).
    Migração `a6b25ad2bdeb` — sem gotcha nenhum dos dois de sempre (enum
    `statusitemhabilitacao` criado pela primeira vez, tabela nova sem
    coluna `NOT NULL` retroativa). Testado via curl: simulação vazia (0
    notas), simulação após lançar uma nota abaixo da nota de corte
    (lacuna detectada), simulação depois de **mudar a mesma nota** pra
    acima da corte (lacuna some, nível sugerido muda de
    `aglomerado_produtivo` pra `cpl_madura` — prova real de "ver o efeito
    de mudar uma nota"), e confirmado que `Avaliacao.pontuacao_calculada`
    continua `None` até `concluir` ser chamado de verdade (a simulação
    nunca vaza pro real). RF-027 testado via curl (criar item, upload de
    comprovante, analisar) e Playwright (`rf026_027_shot.js` — navegar
    até a avaliação em andamento pra ver a simulação, depois criar um
    item de habilitação, anexar comprovante e aprovar, tudo via UI real)
    mais rerun de `maturidade_shot.js`/`maturidade_shot2.js`/
    `rbac_403_shot.js`/`documentos_shot.js`, sem erros de console nem 500
    reais no log. **Com isso, RF-024 a RF-028 (módulo de Maturidade)
    estão completos** — só a limitação deliberada de validade/versão de
    evidência (RF-025, depende do versionamento que `Documento` já tem)
    permanece.
36. **RF-014: máscaras de qualidade de dados + validade temporal** e
    **RF-003: requisitos de habilitação parametrizáveis por edital** —
    usuário pediu "fazer as implementações pendentes do RF-14 e RF-03",
    as duas pendências que sobraram de uma avaliação de backlog
    anterior (RF-003 tinha a premissa desatualizada de "depende do
    módulo de Maturidade", que já existia desde o item 10).
    - **RF-014 (máscaras)**: `app/services/validadores.py`, novo —
      `cnpj_valido`/`cpf_valido` com dígito verificador oficial (mod-11,
      não só contagem de dígitos) e `uf_valida` contra a lista fechada
      das 27 UFs. Aplicado nos três pontos de escrita já estabelecidos
      pra dado cadastral, pra nunca ficar divergente entre eles: criação
      de entidade via API (`_validar_mascaras` em
      `app/api/routes/entidades.py`, 400 se inválido), importação de
      planilha (`app/services/importacao_entidades.py` — linha vai pra
      `ImportacaoLinha(status=ERRO)` em vez de derrubar o import
      inteiro, mesmo padrão de erro-por-linha já usado ali) e
      formulário público de campanha (`routes_atualizacao_publica.py` —
      só valida UF, único campo de máscara exposto nesse formulário;
      re-renderiza com erro em vez de 400 cru, porque é usuário externo
      sem acesso a JSON). Nenhum campo é obrigatório em si (entidade
      estrangeira pode não ter CNPJ/CPF brasileiro) — ausência não é
      erro, valor presente e mal formado é.
      **Validade temporal**: `diagnostico_desatualizado()` em
      `app/services/indicadores.py`, função pura sem campo novo no
      banco — compara `DiagnosticoCadastral.updated_at` contra
      `VALIDADE_DIAGNOSTICO_DIAS = 365` (mesma janela de um ano já usada
      em `_novos_empregos_diretos`, o requisito não fixa um número).
      Só sinaliza (badge "desatualizado" em `entidade_detail.html` +
      contagem em `cpl_dashboard.html`), não invalida nem esconde nada
      — a última resposta continua valendo até alguém atualizar de
      novo.
    - **RF-003 (requisitos parametrizáveis)**: `RequisitoHabilitacaoEdital`
      (`app/models/maturidade.py`) — template por edital, mesmo padrão
      template-vs-instância já usado em `CriterioMaturidade` (template)
      vs. `AvaliacaoCriterio` (instância): aqui é
      `RequisitoHabilitacaoEdital` (template, `PAPEIS_EDITAL_GESTAO`) vs.
      `ItemHabilitacaoJuridica` (instância por CPL, já existia desde o
      RF-027, item 35). Fecha a peça que faltava de "parametrizar...
      documentos... sem alteração de código" — editais/critérios/
      pesos/prazos já eram configuráveis via UI desde o RF-024 (item
      10), só faltava o board de "quais documentos este edital exige"
      também ser dado e não código. Endpoint novo
      `POST /api/maturidade/cpls/{id}/habilitacao/usar-requisitos-edital`
      (e equivalente web) instancia o checklist da CPL a partir do
      template — **idempotente**: só cria item pra requisito cujo
      `descricao` a CPL ainda não tem, pra poder clicar de novo depois
      que o edital ganha mais um requisito sem duplicar os que já
      existem. Reafirmei que "níveis de maturidade" continuam enum fixo
      por design (RN-004 já dizia isso) — o que é parametrizável são os
      limiares, não os quatro nomes.
    Migração `ec51d69e4f77` — sem gotcha nenhum dos dois de sempre (sem
    enum, tabela nova sem coluna `NOT NULL` retroativa). Testado via curl
    (CNPJ/CPF/UF válidos e inválidos nos três pontos de escrita, import
    com linha inválida vira erro-por-linha sem derrubar o resto,
    idempotência do "usar requisitos do edital" chamado duas vezes) e
    Playwright (`rf014_003_shot.js` — criar requisito novo no edital via
    UI, ir na tela da CPL, clicar "usar requisitos do edital", confirmar
    que só o requisito novo aparece como item novo) mais rerun da suíte
    de regressão, sem erros de console nem 500 reais no log.
37. **RF-043: pacote de submissão com índice e checklist** e **RNF-012:
    observabilidade** — usuário pediu "implementar a RF-043 e a
    RNF-012". RF-043 estava marcado parcial com uma premissa
    desatualizada ("depende do módulo de Editais/Reconhecimento, ainda
    não construído" — o módulo existe desde o item 10/RF-024); RNF-012
    era o único não-funcional totalmente pendente além de RNF-013.
    - **RF-043**: `pacote_submissao_habilitacao()`
      (`app/services/maturidade.py`) reúne o checklist de habilitação
      jurídica de uma CPL perante um edital (`ItemHabilitacaoJuridica`,
      RF-027) contra o template de documentos exigidos do próprio
      edital (`RequisitoHabilitacaoEdital`, RF-003 — mesma composição já
      usada no botão "usar requisitos do edital", agora reaproveitada
      pra saber o que ainda falta instanciar, não só o que já é item),
      mais a avaliação de maturidade mais recente contra o mesmo edital,
      se existir. `gerar_pdf_pacote_submissao()`
      (`app/services/geracao_documentos.py`) só formata — mesmo padrão
      dos outros nove PDFs do módulo, reaproveitando `_GeradorPDF`.
      Botão "Gerar pacote de submissão" (com seletor de edital) ao lado
      do já existente "Usar requisitos do edital" no card de habilitação
      de `cpl_avaliacoes.html`; `POST
      /api/maturidade/cpls/{id}/pacote-submissao` e equivalente web,
      mesmo padrão de salvar como `Documento` (RF-042) e redirecionar
      pra `/painel/documentos/cpls/{id}` de todo relatório do RF-048.
      DOCX ficou deliberadamente fora — PDF cobre o caso de uso e é o
      formato já usado em todos os outros relatórios.
    - **RNF-012**: três peças novas, nenhuma infraestrutura externa
      (sem Prometheus/Grafana/Sentry — tudo no próprio Postgres/processo).
      `RegistroFalha` (`app/models/observabilidade.py`) é o mesmo padrão
      "log que só acumula" de `RegistroAuditoria`/`Notificacao` — uma
      linha por exceção não tratada (não por 4xx esperado, que é fluxo
      de controle). Métricas de requisição (`app/services/observabilidade.py`)
      ficam em memória do processo (contadores que reiniciam a cada
      deploy — aceitável pra "desde o último deploy", não uma série
      histórica). Logs estruturados em JSON
      (`app/core/logging_config.py`) com `request_id` por requisição
      (também devolvido em `X-Request-ID`), emitidos pelo mesmo
      middleware `contexto_auditoria` que já decodifica o token — não
      criei um segundo middleware só pra não decodificar duas vezes.
      **Bug pego e corrigido antes de fechar a fatia**: a primeira
      versão registrava a falha via `@app.exception_handler(Exception)`
      separado — só que o Starlette move um handler de `Exception`
      "crua" pro `ServerErrorMiddleware`, que fica ACIMA do middleware
      custom; nessa altura os contextvars de auditoria já tinham sido
      resetados pelo `finally` do middleware, e o ASGI ainda logava a
      exceção de novo como "Exception in ASGI application" por baixo
      dos panos (efeito colateral conhecido de `BaseHTTPMiddleware` +
      handler de `Exception`) — um 500 duplicado no log a cada falha
      real, que teria poluído a disciplina de "zero 500 real no log"
      usada pra validar toda fatia desta sessão. Corrigido movendo a
      captura pra dentro do próprio `try/except` do middleware
      `contexto_auditoria`, sem handler de `Exception` separado —
      confirmado via rota de teste temporária (`/api/_test-falha`,
      removida antes do commit) que o log parou de duplicar. Alerta por
      limiar (padrão 5 falhas/15min, configurável via
      `observabilidade_alerta_*` em `Settings`) mostra banner no painel
      e tenta e-mail aos administradores via `app/services/email.py`
      (RF-004) — melhor esforço, nunca derruba nada se o SMTP não
      estiver configurado (não está, em produção, ver item 14 de "O que
      falta"), no máximo uma vez por janela. `/api/saude` passou a
      checar `SELECT 1` no banco (retorna 503 se falhar) — antes só
      respondia "ok" sem checar nada; continua público/rápido porque o
      healthcheck do Traefik em produção usa essa rota. Painel de saúde
      novo em `/painel/administracao/saude` (admin, `PAPEIS_EDITAL_GESTAO`)
      e `GET /api/metricas` (mesmo grupo).
    Migração `4fc9db3f454d` — sem gotcha nenhum dos dois de sempre (sem
    enum, tabela nova sem coluna `NOT NULL` retroativa). Testado via
    curl (pacote de submissão gerado e baixado como PDF válido, conteúdo
    conferido via `pypdf` — o "?" que aparece no terminal git-bash é só
    exibição, o PDF em si renderiza acentuação corretamente, mesma
    classe de falso-positivo já documentada; RBAC 401/403 nos endpoints
    novos) e Playwright (`rf043_rnf012_shot.js` — gerar pacote de
    submissão via UI, navegar até o painel de saúde) mais rerun de
    `maturidade_shot.js`/`maturidade_shot2.js`/`rbac_403_shot.js`/
    `documentos_shot.js`, sem erros de console nem 500 reais no log
    (confirmado tanto antes quanto depois do fix do bug de log
    duplicado acima).
38. **RF-050: eventos, capacitações, mentorias, missões técnicas** e
    **RF-051: biblioteca de conhecimento** — usuário perguntou "quais as
    pendências do backlog" e, entre os candidatos levantados, pediu pra
    seguir com estes dois — ambos eram os únicos "S" ainda 100%
    ❌ pendentes que reaproveitavam padrões já existentes no sistema, sem
    depender de módulo novo nenhum.
    - **RF-050 (eventos)**: `Evento` (`app/models/evento.py`) — mesmo
      raciocínio de `Edital`/RN-006: `cpl_id` nulo é aberto a todas as
      CPLs (gerido por `PAPEIS_EDITAL_GESTAO`), `cpl_id` preenchido é
      local de uma CPL (gerido por `PAPEIS_GESTAO` dela). Decisão de
      design deliberada: inscrição, presença e avaliação viraram um
      único registro por pessoa+evento (`InscricaoEvento`), não três
      tabelas — são estados sucessivos do mesmo vínculo (inscrita →
      presente/ausente → avaliação), não entidades independentes.
      `presente` fica `None` até alguém marcar, diferente de
      `Presenca.presente` em Governança (sempre preenchido na criação,
      porque ali o registro só existe depois da reunião acontecer — aqui
      a inscrição existe antes do evento). Inscrição é feita por quem
      tem papel de gestão, mesmo padrão de `MembroOrgao`/`Presenca` — ao
      revisar como `MembroOrgao` já funciona, descobri que o sistema
      **não** valida que a `Pessoa` escolhida já tenha vínculo formal com
      a CPL (dropdown lista todas as pessoas, sem filtro); alinhei
      `InscricaoEvento` ao mesmo comportamento em vez de inventar uma
      validação mais rígida — um evento pode inclusive ser a porta de
      entrada de alguém ainda não vinculado. Limite de vagas verificado
      na inscrição (conta inscritos existentes contra `Evento.vagas`).
      `/painel/eventos` (lista + criação) → `/painel/eventos/{id}`
      (inscrever, marcar presença, avaliar, atualizar status).
    - **RF-051 (biblioteca)**: `RecursoBiblioteca`
      (`app/models/biblioteca.py`) — conteúdo compartilhado entre todas
      as CPLs, **sem** `cpl_id` (diferente de `Documento`/RF-042, que
      exige uma CPL) — por isso não reaproveita esse modelo, só o
      mecanismo de armazenamento em disco (`salvar_arquivo_biblioteca`
      em `app/services/armazenamento.py`, mesma lógica de
      `salvar_arquivo` mas numa subpasta fixa `_biblioteca/` em vez de
      uma por CPL). Seis tipos citados no requisito viraram enum
      (`modelo`/`estudo`/`boa_pratica`/`edital`/`oportunidade`/
      `conteudo_tecnico`) — "atas" ficou de fora de propósito, já é
      `Documento`/RF-042. Um recurso pode ser arquivo, link externo ou
      só texto (`descricao`) — ao menos um dos três é exigido, validado
      na rota. `publicado` controla rascunho (só quem administra vê) vs.
      publicado (qualquer usuário autenticado navega). Gerido por
      `PAPEIS_EDITAL_GESTAO`, mesma autoridade de `Edital`.
    - **Bug pego e corrigido durante o desenvolvimento**: a primeira
      versão de `criar_recurso` (API e web) declarava `arquivo:
      UploadFile | None = None` sem `File(None)` explícito, misturado
      com parâmetros `Form(...)`. FastAPI exige que, quando a rota tem
      qualquer parâmetro de arquivo, TODOS os campos não-arquivo do
      corpo sejam declarados `Form(...)` explicitamente — sem isso a
      rota nem chega a levantar erro em teste manual simples (só
      apareceria num caso de uso que dependesse da inferência correta).
      Corrigido usando `File(None)` explícito pro parâmetro opcional,
      seguindo o mesmo padrão já usado em `enviar_documento`
      (RF-042/`app/api/routes/documentos.py`) pro caso obrigatório.
    Migração `3163d6162f16` — sem gotcha nenhum dos dois de sempre (dois
    enums novos, nenhum reaproveitado; tabelas novas sem coluna
    `NOT NULL` retroativa). Testado via curl (criar evento global e local,
    inscrever pessoa, marcar presença/avaliação com nota 1-5 validada,
    rejeitar reinscrição duplicada, rejeitar inscrição além do limite de
    vagas, rejeitar inscrição em evento local por CPL diferente da dona;
    criar recurso de biblioteca só com texto, com arquivo, rejeitar
    recurso sem nenhum conteúdo, baixar arquivo) e Playwright
    (`rf050_051_shot.js` — criar evento aberto a todas as CPLs via UI,
    inscrever pessoa, criar recurso de biblioteca via UI) mais rerun de
    `maturidade_shot.js`/`maturidade_shot2.js`/`rbac_403_shot.js`/
    `documentos_shot.js`/`rf043_rnf012_shot.js`, sem erros de console nem
    500 reais no log. **Achadinho no teste com Playwright, não no
    código**: o script de teste selecionava `select[name=tipo]` sem
    escopo, batendo no `<select>` do formulário de FILTRO da biblioteca
    (que tem `onchange="this.form.submit()"`) em vez do formulário de
    criação — dois elementos com o mesmo `name` na mesma página, mesma
    classe de cuidado do item "armadilhas" sobre reaproveitar seletor
    sem checar ambiguidade, mas aqui do lado do teste, não do app.
39. **RF-052: matchmaking de inovação** e **RF-054: integrações
    externas** — usuário pediu "elaborar a RF-052 e a RF-054"; perguntei
    se "elaborar" queria dizer implementar em código ou escrever uma
    proposta de design primeiro (palavra diferente de "implementar",
    usada em todo pedido anterior da sessão) — resposta foi implementar
    em código, mesmo padrão de sempre.
    - **RF-052 (matchmaking)**: `MatchInovacao`
      (`app/models/inovacao.py`) fecha o meio do fluxo F09 (demanda
      empresarial → busca de competência → matchmaking → projeto de
      P&D → instrumento jurídico → acompanhamento) reaproveitando
      `DemandaProjeto` (RF-031, `origem_tipo=empresa` já é "demanda das
      empresas") em vez de criar uma "demanda de inovação" paralela, e
      `OfertaEntidade` (RF-010) pra "competência" — o documento de
      requisitos já não distingue os dois conceitos (seção 10, modelo
      conceitual). A ponta final do fluxo (matchmaking → projeto) não
      precisou de nada novo — `POST /api/projetos/demandas/{id}/converter`
      já existia desde RF-031/032. `buscar_competencias()`
      (`app/services/inovacao.py`) só filtra candidatos por tipo (mapeei
      "fornecedor"→`PRESTADOR`, "ambiente SPAI"→`AMBIENTE_INOVACAO`;
      "startup" não tem tipo próprio, vira `EMPRESA`) e texto (nome da
      entidade ou de alguma oferta) — quem sugere e decide o status
      (`sugerido`/`em_conversa`/`firmado`/`descartado`) é sempre uma
      pessoa (RN-016). Ao revisar como `MembroOrgao` já inscreve pessoa
      em órgão de governança, notei que o sistema **não** valida que a
      pessoa escolhida já tenha vínculo com a CPL (dropdown lista
      todas) — alinhei a validação de `MatchInovacao` ao mesmo
      comportamento em vez de inventar uma regra mais rígida que não
      existe em nenhum outro lugar do sistema. UI web em
      `/painel/inovacao/demandas/{id}`, acessível por um botão na tela
      da demanda (só aparece pra origem empresa, ainda não convertida/
      rejeitada).
    - **RF-054 (integrações)**: dependência de contrato com terceiro é
      real pra 2 das 4 integrações citadas (assinatura eletrônica,
      "sistemas institucionais" — nenhum nomeado no documento) — não
      dá pra implementar essas sem escolher um provedor específico,
      decisão de negócio, não técnica. As outras 2 são "tecnicamente
      disponíveis" sem contrato, então foram implementadas de verdade:
      **dados cadastrais públicos** — consulta de CNPJ via BrasilAPI
      (pública/gratuita), `app/services/integracao_publica.py`, usando
      `urllib.request` da biblioteca padrão em vez de adicionar
      `httpx`/`requests` como dependência nova só pra uma chamada (as
      rotas que chamam são síncronas, então já rodam em threadpool,
      mesmo padrão de toda chamada bloqueante existente — psycopg,
      SMTP). Tela de conferência em
      `/painel/cadastro/entidades/{id}` (botão "Conferir dados
      públicos") com tabela cadastrado-vs-oficial e botão "usar dados
      da base pública" que reconsulta (nunca confia em valor de
      formulário) e aplica só os campos com correspondência direta no
      cadastro (`Entidade` não tem telefone/e-mail — ficam só na
      conferência). **BI** — `feed_bi_cpls()`
      (`app/services/indicadores.py`) achata `resumo_cadastral()` pra
      uma linha por CPL sem dict/Counter aninhado (a maioria dos
      conectores de BI não entende bem estrutura aninhada), exposta em
      `GET /api/indicadores/bi-feed?formato=json|csv`.
    - **Bug pego e corrigido durante o desenvolvimento**: a primeira
      chamada real pra BrasilAPI via `urllib.request` devolveu 403
      Forbidden, mesmo a mesma URL funcionando via `curl` direto no
      terminal — confirmado isolando a chamada fora da aplicação. Causa:
      a BrasilAPI bloqueia o User-Agent padrão do `urllib` (proteção
      anti-bot genérica, não falta de autorização de verdade — o CNPJ
      de teste é público). Corrigido enviando um `User-Agent`
      identificável (`SIG-CPL/1.0 (...)`) na requisição. **Regra**: ao
      integrar com uma API pública de terceiro pela primeira vez, testar
      a chamada real (não só ler a documentação) antes de assumir que
      "pública e sem credencial" significa "sem nenhuma configuração de
      requisição necessária" — bloqueio por User-Agent é comum o
      suficiente pra não presumir que não vai acontecer.
    Migração `bc65b64e9955` — sem gotcha nenhum dos dois de sempre (enum
    novo, tabela nova sem coluna `NOT NULL` retroativa; RF-054 não
    precisou de migração, só reaproveitou campos já existentes de
    `Entidade`). Testado via curl (busca de competência por tipo/texto,
    sugerir match, rejeitar match duplicado, atualizar status até
    firmado; consulta de CNPJ público com CNPJ de teste real, aplicar
    dados públicos no cadastro, feed de BI em JSON e CSV, formato
    inválido rejeitado) e Playwright (`rf052_054_shot.js` — matchmaking
    via UI a partir da tela da demanda, busca com filtro de texto,
    conferência de dados públicos numa entidade) mais rerun de
    `maturidade_shot.js`/`maturidade_shot2.js`/`rbac_403_shot.js`/
    `documentos_shot.js`/`rf043_rnf012_shot.js`/`rf050_051_shot.js`, sem
    erros de console nem 500 reais no log.

40. **RF-011: georreferenciamento e mapa da cadeia** e **RNF-011:
    manutenibilidade (testes automatizados + CI)** — usuário pediu
    "Implementar a RF-011 e fechar a RNF-011"; segui direto sem
    perguntar nada (precedente forte da sessão de fazer chamadas
    técnicas livres quando o pedido já é "implementar").
    - **RF-011**: `Entidade.latitude`/`longitude` (`Float` opcionais —
      nem toda entidade tem endereço completo o bastante pra
      geocodificar). `app/services/geocodificacao.py::geocodificar_endereco`
      consulta o Nominatim/OpenStreetMap (pública, gratuita, mesmo
      raciocínio "tecnicamente disponível sem contrato" do RF-054/item
      39) — mesmo gotcha de bloqueio de User-Agent do item 18 se
      repetiu, mas desta vez testado com `curl -A "..."` durante o
      design, antes de escrever qualquer código, então não houve
      retrabalho. `POST /api/entidades/{id}/geocodificar`, `PATCH
      /api/entidades/{id}/localizacao` e `GET /api/cpls/{id}/mapa`
      (só entidades vinculadas e já geocodificadas). UI: card
      "Localização" na tela de detalhe da entidade e
      `/painel/cadastro/cpls/{id}/mapa` com Leaflet + tiles OSM (via CDN
      unpkg — confirmei que o projeto não tem middleware de
      CSP/CORS que bloqueasse isso antes de adicionar), marcador
      colorido por `tipo_entidade` como proxy de diversidade da cadeia.
      **Escopo deliberado**: "relações da cadeia" do requisito não virou
      aresta de verdade no mapa porque `EntidadeElo` (RF-009) ainda não
      tem rota de CRUD própria — construir isso agora seria escopo novo,
      não fechamento do RF-011. `base.html` ganhou
      `{% block extra_head %}{% endblock %}` (não existia) pra permitir
      CSS/JS só na página do mapa sem tocar nos outros templates —
      única exceção deliberada à regra geral de "zero JavaScript além de
      formulário simples" do projeto, porque mapa é widget
      inerentemente visual/interativo.
    - **RNF-011**: nenhum teste automatizado existia até aqui, apesar do
      projeto já ser versionado/modular/documentado. Criei `tests/`
      (pytest) com banco `sigcpl_test` isolado (Postgres de verdade, não
      sqlite — o projeto usa `UUID`/`JSONB`) e `tests/conftest.py` com o
      padrão de SAVEPOINT aninhado do SQLAlchemy (necessário porque toda
      rota já chama `db.commit()` internamente — sem isso, testes
      vazariam estado entre si). 43 testes cobrindo autenticação,
      cadastro/RBAC (inclusive isolamento entre CPLs), geocodificação
      (RF-011), governança, maturidade, matchmaking (RF-052) e
      observabilidade (RNF-012) — 49% de cobertura de statements.
      Configurei ruff (`select = ["E", "F", "I", "UP", "B"]`) pela
      primeira vez no projeto: 927 erros na primeira rodada, quase todos
      falso-positivo de dois padrões estruturais do projeto —
      `extend-immutable-calls` pro idiom `Depends()`/`Query()` do
      FastAPI (782 ocorrências de B008) e ignore documentado de F821 (47
      ocorrências, todas `Mapped["NomeDaClasse"]` do SQLAlchemy, resolvido
      pelo mapper em runtime, não pelo Python) — corrigidos com
      configuração, não supressão cega, pra não esconder mutável de
      verdade ou nome indefinido de verdade em outro lugar. `--fix`
      automático (import sorting, `datetime.timezone.utc`→`datetime.UTC`)
      resolveu o resto até sobrar só 4 (3 `B904` raise-sem-`from` em
      `routes_auditoria.py`/`routes_observabilidade.py`, corrigidos com
      `from None` — são substituição deliberada de um 403 genérico por
      mensagem mais amigável, não engolir exceção sem querer; 1 `B905`
      zip-sem-`strict` em `validadores.py`). `.github/workflows/ci.yml`
      novo — GitHub Actions com serviço Postgres efêmero, rodando
      `ruff check .` + `pytest` a cada push/PR contra `master`. CD
      (implantação automática) não entrou — reimplantação em produção
      segue manual via `deploy.sh`, é próximo passo, não parte deste
      fechamento.
    Testado: RF-011 via curl (geocodificação real com CNPJ/endereço de
    teste, localização manual, feed do mapa filtrando corretamente,
    400 em endereço vazio) e Playwright (`rf011_shot.js` — mapa Leaflet
    renderizado, zero erro de console) mais rerun de toda a suíte de
    Playwright existente; RNF-011 via `pytest` (43 passando) e
    `ruff check .` (limpo) — nenhum erro real de servidor/500/traceback
    no log em nenhuma das duas verificações.

41. **RF-055: portal público de transparência** — usuário perguntou
    "qual próxima etapa de implementação?" depois do fechamento do
    RF-011/RNF-011; categorizei o que restava do documento de requisitos
    (não iniciado / decisão de negócio / config pendente / escopo
    deliberado / RNF de maturidade organizacional) e recomendei RF-055
    por ser o único RF de alto valor genuinamente não iniciado sem
    bloqueio externo; usuário pediu "Implementar RF-055" em seguida.
    Nenhuma tabela nova, nenhuma migração — é composição de dado que já
    existe, só numa rota sem autenticação. `GET /cpls` (lista de CPLs
    ativas) e `GET /cpls/{id}` (página por CPL) em
    `app/web/routes_publico.py`. A restrição "sem exposição de dados
    pessoais ou sigilosos" do próprio requisito moldou cada decisão:
    - **Governança**: reaproveitou `resumo_governanca()` (RF-045, já
      agregado) direto; função nova `estrutura_governanca_publica()`
      (`app/services/indicadores.py`) lista órgãos por
      nome/tipo/periodicidade + **contagem** de membros ativos, nunca
      nome de pessoa. Testado com `assert "<nome>" not in
      resposta.text` — confirmando que o dado não chega na resposta, não
      só que o template não o imprime.
    - **Agenda**: função nova `agenda_publica()` combina `Reuniao`
      futuras (status `agendada`, só data/título/local — pauta fica de
      fora, pode tratar de algo ainda não deliberado) com `Evento`
      abertos (RF-050, globais ou da CPL), ordenados juntos por data.
    - **Resultados**: reaproveitou `resumo_cadastral()` (RF-046/047) sem
      nenhuma alteração — já era um agregado sem dado individual.
    - **Projetos autorizados**: função nova `projetos_autorizados()`
      (`app/services/projeto.py`) filtra só estágio
      `aprovado`/`em_execucao`/`concluido` — critério pra "autorizado"
      não estava explícito no requisito, então mapeei pro subconjunto de
      `EstagioProjeto` que já passou por decisão formal (`demanda`/
      `em_elaboracao`/`submetido` ainda não são resultado decidido, pode
      vazar estratégia da empresa demandante antes de ser pública;
      `rejeitado`/`cancelado` não é resultado a divulgar). Só campos
      textuais (título/descrição/eixo) — sem `responsavel_id` nem
      qualquer valor financeiro, que `resumo_projetos_cpl` (RF-045)
      inclui mas não é apropriado pro portal público.
    - **Escopo deliberado, não esquecido**: mapa da cadeia (RF-011)
      continua restrito à área logada — RF-055 não pede
      georreferenciamento, publicar localização/CNPJ de empresa sem
      RF-011 ter sido desenhado pra isso seria escopo novo. "Notícia"/
      "aviso" como conteúdo editorial próprio também não ganhou modelo —
      o requisito não distingue esse conceito de "agenda"/"resultados",
      já cobertos pelo que existe.
    Sem migração (zero tabela/coluna nova). Testado: local via curl
    (lista pública, detalhe de uma CPL real do banco de dev, 404 pra CPL
    inexistente) e um teste manual direto no banco confirmando que o
    nome de uma pessoa membro de órgão de governança **não** aparece no
    HTML renderizado; Playwright (`rf055_shot.js`, zero erro de console,
    screenshot confirmando layout); 4 testes automatizados novos
    (`tests/test_portal_publico.py`) cobrindo autenticação zero, ausência
    de nome de pessoa, 404 de CPL inexistente e filtro correto de
    estágio de projeto — suíte completa em 47 (43 + 4), ruff limpo.

42. **RF-057: assistente de IA** — usuário pediu "Implementar a RF-057"
    logo depois do fechamento do RF-055. Diferente de todo RF anterior
    desta sessão, este dependia de duas decisões que só o usuário podia
    tomar (qual provedor de IA; se já havia credencial) — perguntei via
    `AskUserQuestion` em vez de decidir sozinho, mesma classe de situação
    do RF-054 (assinatura eletrônica/sistemas institucionais, que ficaram
    pendentes por essa mesma razão). Respostas: **Anthropic (Claude)**,
    construir com **degradação graciosa** (sem chave ainda) — mesmo
    padrão já usado pro SMTP (RF-004).
    - Adicionada dependência `anthropic` (SDK oficial) ao `pyproject.toml`
      e `anthropic_api_key`/`anthropic_model` (padrão `claude-sonnet-5`)
      a `app/core/config.py` — `anthropic_api_key` ausente é o sinal de
      "não configurado", mesmo raciocínio de `smtp_host`.
    - `app/services/ia_assistente.py` (novo) — `ia_disponivel()` checa
      se a chave existe; `gerar_assistente_ia(cpl, cadastral, governanca,
      planejamento, projetos_resumo, maturidade)` monta um contexto
      JSON curado manualmente a partir dos mesmos agregados já usados no
      dashboard de indicadores (RF-045) — nunca a lista de objetos
      (`avaliacoes`, `projetos`) nem dado de pessoa, mesmo cuidado do
      portal público (RF-055) — envia ao Claude pedindo um JSON
      estruturado de volta (`sintese`, `verificacao_consistencia`,
      `lacunas_sugeridas`) e devolve um dict. `IAIndisponivel` levantada
      sem chave, em qualquer `anthropic.APIError` (rede/autenticação/
      limite) ou resposta em formato inesperado (JSON malformado) — nunca
      um 500 pro usuário final.
    - **Bug pego durante o desenvolvimento, antes de qualquer teste
      rodar**: `lacunas_avaliacao_vigente` (de `resumo_recadastramento`,
      RF-048) é uma lista de objetos ORM `AvaliacaoCriterio`, não
      serializável em JSON — meu primeiro rascunho passava a lista
      direto pro `json.dumps()`, que teria quebrado na primeira chamada
      de verdade. Corrigido extraindo o mesmo texto que o dashboard já
      renderiza (`f"{nota.criterio.nome}: nota {nota.nota} (corte:
      {nota.criterio.nota_corte})"`) antes de montar o contexto.
    - `app/web/routes_indicadores.py` — refatorei a construção do
      contexto do dashboard pra uma função `_dados_dashboard()`
      compartilhada entre o `GET` (exibição) e o novo
      `POST /painel/indicadores/cpls/{id}/assistente-ia`
      (`PAPEIS_GESTAO`, mesma restrição da geração de relatório em PDF —
      é uma "ação", não só leitura). O `POST` nunca persiste nada: só
      reapresenta a mesma página do dashboard com o resultado (ou o erro
      amigável) — "revisão humana obrigatória" do requisito veio daí:
      recarregar a página descarta a sugestão, ela nunca vira uma
      decisão automática de nada.
    - Template `cpl_dashboard.html` — botão "Assistente de IA (RF-057)"
      (desabilitado quando `ia_disponivel` é falso, com aviso explicando
      o motivo) e um card novo mostrando síntese/pontos de
      atenção/lacunas sugeridas quando há resultado, rotulado "Revisão
      humana obrigatória" de forma bem visível.
    - Testado: 8 testes automatizados novos (`tests/test_ia_assistente.py`)
      — sem chave (levanta `IAIndisponivel`), sucesso mockado, JSON
      malformado mockado, erro de API mockado (`anthropic.APIConnectionError`),
      RBAC (papel sem `PAPEIS_GESTAO` recebe 403), rota degradando sem
      chave configurada. **Também testado contra o endpoint real da
      Anthropic com uma chave inválida** (não só mock) — confirmado que
      o erro 401 de verdade vira a mensagem amigável "Assistente de IA
      indisponível no momento." em vez de vazar o corpo bruto da
      resposta (ajustado depois de ver o texto completo do erro exposto
      na tela na primeira tentativa — mensagem curta de propósito,
      mesmo padrão de `GeocodificacaoIndisponivel`/
      `ConsultaCNPJIndisponivel`). Playwright confirmando botão
      desabilitado sem chave e degradação graciosa com chave inválida,
      zero erro de console. Suíte completa em 55 (47 + 8), ruff limpo.
      **Com isso, todo RF do documento de requisitos original foi
      endereçado de alguma forma** — resta só RNF de maturidade
      organizacional (privacidade formal, retenção, qualidade de dados,
      continuidade) e o fluxo F01 de autoatendimento, nenhum RF numerado.

43. **F01: fluxo de autoatendimento (adesão de membro)** — usuário pediu
    "Vamos implementar o fluxo F01" logo depois do fechamento do RF-057
    (quando ficou claro que era o único item do modelo conceitual ainda
    sem cobertura nenhuma). Antes de escrever qualquer código, rodei uma
    pesquisa (agente Explore) pra mapear o que já existia — descobriu
    duas lacunas importantes: `EntidadeElo` (RF-009) nunca teve rota de
    CRUD em lugar nenhum (só leitura, usado no mapa do RF-011), e
    `PessoaVinculo` nunca foi escrita por nenhum fluxo do sistema em
    toda a história do projeto (só lida, usada na resolução de
    visibilidade do RBAC) — ambas viraram parte natural do "vínculo à
    CPL"/"classificação de elo"/"cadastro" deste fluxo.
    - **Modelo novo** `SolicitacaoAdesao`
      (`app/models/adesao.py`) — cadastro básico da entidade + elo
      pretendido + contato + consentimento LGPD (`consentimento_lgpd`/
      `consentimento_em`, congelado no momento da submissão) + campos de
      validação (`status`/`parecer`/`analisado_por_id`/`data_analise`,
      mesmo padrão de `ItemHabilitacaoJuridica`, RF-027) +
      `entidade_id` (preenchido só na aprovação). Enum novo
      `StatusSolicitacaoAdesao` (pendente/aprovada/rejeitada).
    - **Serviço** `app/services/adesao.py` — `criar_solicitacao` valida
      consentimento (obrigatório) e formato de CNPJ/CPF/UF (reaproveita
      `app/services/validadores.py`, RF-014, mesmo padrão dos outros
      pontos de escrita — este é o quarto). `aprovar_solicitacao` é o
      coração do fluxo: busca `Entidade` existente por CNPJ/CPF antes de
      criar (RN-003 — mesma organização pode pedir adesão a uma segunda
      CPL sem duplicar cadastro), cria/reaproveita `EntidadeCPL` e
      `EntidadeElo` (idempotente — checa existência antes de inserir, não
      confia em `try/except IntegrityError`) e registra o contato como
      `PessoaVinculo` (papel `EMPRESA_MEMBRO`, sem criar `Usuario`/login —
      isso continua sendo uma ação separada de quem administra).
      `rejeitar_solicitacao` só muda status/parecer, não cria nada.
      Reanalisar uma solicitação já decidida levanta `SolicitacaoInvalida`
      (400) — decisão é definitiva, mesmo raciocínio de "nunca sobrescrever
      uma decisão humana silenciosamente" já usado em outros lugares.
    - **Rotas**: API pública `POST /api/cpls/{id}/solicitacoes-adesao`
      (sem `Depends(get_current_user)` — é a porta de entrada de quem
      ainda não tem vínculo nenhum) + `GET`/`aprovar`/`rejeitar`
      (`PAPEIS_GESTAO`, escopado à CPL da solicitação). Web: formulário
      público em `app/web/routes_publico.py` (`GET`/`POST
      /cpls/{id}/solicitar-adesao`, linkado a partir da página pública da
      CPL, RF-055) e tela de gestão em `app/web/routes_cadastro.py`
      (`/painel/cadastro/cpls/{id}/solicitacoes-adesao`, listar + aprovar
      + rejeitar, linkada a partir de `cpl_cadastro.html`).
    - **Migração** `92eefc2fd38f` — gotcha real dos dois de sempre (enum
      reaproveitado), ver item 29 da lista de migrações acima.
    - **Escopo deliberado**: "convite" (a outra metade de "Convite/
      solicitação" do requisito) não ganhou token/e-mail dedicado — a
      gestão só compartilha a URL pública do formulário, é o mesmo
      formulário da "solicitação". Criar `Usuario`/login pro contato
      também ficou de fora — self-service de conta de acesso é uma
      feature bem mais sensível (segurança) que o requisito não pede
      explicitamente, e a válvula de bootstrap do primeiro admin já
      estabelece que criação de conta é deliberadamente controlada por
      quem administra, não auto-serviço.
    Testado: local via curl (fluxo completo API — solicitar sem
    consentimento rejeitado, CNPJ inválido rejeitado, aprovar cria
    Entidade/EntidadeCPL/EntidadeElo/PessoaVinculo, **aprovar uma segunda
    solicitação com o mesmo CNPJ pra CPL diferente reaproveita a mesma
    Entidade em vez de duplicar** — confirmado consultando o banco
    direto) e Playwright (`f01_shot.js` — formulário público → erro de
    CNPJ inválido → reenvio válido → página de obrigado → login →
    tela de gestão → aprovar → aparece no histórico, zero erro de
    console) mais rerun de `cadastro.js`/`rbac_403_shot.js`/
    `maturidade_shot.js`/`rf050_051_shot.js` (todos limpos;
    `cpl_edit_shot.js` falhou por não-idempotência própria do script —
    sigla fixa colidindo com execução anterior, não relacionado a esta
    fatia). 11 testes automatizados novos (`tests/test_adesao.py`,
    inclusive o teste de dedup de entidade por CNPJ entre CPLs
    diferentes) — suíte completa em 66 (55 + 11), ruff limpo.

44. **Configuração de SMTP em produção (RF-004)** — usuário pediu ajuda
    pra configurar o servidor de e-mail, usando o e-mail do próprio
    plano Hostinger. A API da Hostinger **não tem endpoint nenhum pra
    caixa de e-mail** (sem listar, criar ou resetar senha via API) — só
    dá pra confirmar infraestrutura via DNS. Consultei
    `DNS_getDNSRecordsV1` pro domínio `dedev.cloud` e confirmei que o
    Titan Mail do Hostinger já estava ativo (MX `mx1`/`mx2.hostinger.com`,
    DKIM `hostingermail-*`, `autoconfig`/`autodiscover.mail.hostinger.com`)
    — isso validou os parâmetros de SMTP padrão do Hostinger
    (`smtp.hostinger.com`) antes de qualquer coisa ser escrita. Perguntei
    ao usuário (via `AskUserQuestion`) qual endereço usar e como preferia
    passar a senha — escolheu `no-reply@dedev.cloud` e "prefiro editar o
    `.env.prod` eu mesmo"; ele criou a caixa no hPanel e, na mensagem
    seguinte, colou a senha direto no chat (mudando de ideia sobre quem
    editaria o arquivo) — segui a partir daí.
    - Confirmei via `grep` (só nomes de chave, nunca valor) que nenhuma
      variável `SMTP_*`/`APP_BASE_URL` existia ainda em `.env.prod`.
    - Adicionei as duas de uma vez via `cat <<'EOF' | ssh ... "cat >>
      .env.prod"` — heredoc com delimitador entre aspas simples (evita
      expansão local) + `cat >>` remoto (escreve os bytes crus, sem o
      shell remoto interpretar nada como comando). `SMTP_PASSWORD` e
      `SMTP_FROM` entre aspas simples no arquivo — necessário porque
      `deploy.sh` faz `. ./.env.prod` (fonte como shell script de
      verdade, não parse tipo dotenv), e `SMTP_FROM` tem `<`/`>`
      (metacaracteres de redirecionamento em shell) e a senha tem `!`.
      Nunca imprimi a senha em nenhuma saída de comando.
    - Redeploy via `./deploy.sh` (recria o container, único jeito de
      pegar variável de ambiente nova — só editar o arquivo não basta).
      Verificação: `docker exec sigcpl_backend env | grep SMTP_HOST` etc.
      (valores não sensíveis) + `grep -c '^SMTP_PASSWORD='` (só confirma
      presença, sem imprimir o valor) — container com poucos segundos de
      uptime, confirmando que era a instância nova.
    - **Teste real, não só configuração**: `POST
      /api/auth/esqueci-senha` direto contra produção pro
      `admin@sigcpl.dedev.cloud` — 200 em ~2,5s (tempo compatível com
      uma conexão SMTP de verdade completando, não com uma falha rápida
      de autenticação) e log do container sem traceback. A rota não tem
      `try/except` em volta de `enviar_email` — se a senha estivesse
      errada, teria propagado como 500, não 200. Essa ausência de
      try/except foi o que tornou o teste conclusivo sem precisar
      inspecionar a caixa de e-mail de destino.

45. **Configuração de `ANTHROPIC_API_KEY` em produção (RF-057) + bug real
    pego na primeira chamada de verdade** — usuário pediu "Configurar a
    AI" logo depois do SMTP; mesmo fluxo (`AskUserQuestion` sobre já ter
    chave e como passá-la, usuário colou a chave direto no chat).
    - Adicionei `ANTHROPIC_API_KEY` ao `.env.prod` do mesmo jeito que o
      SMTP (heredoc com delimitador entre aspas simples `| ssh ... "cat
      >> .env.prod"`, nunca imprimindo o valor), redeploy, confirmei
      `ia_disponivel() == True` dentro do container.
    - **Primeiro teste real (não mockado) contra produção quebrou com
      500** — log estruturado mostrou `AttributeError: 'ThinkingBlock'
      object has no attribute 'text'` em
      `resposta.content[0].text` (`app/services/ia_assistente.py:139`
      antes do ajuste). Causa: o modelo, com extended thinking ativo por
      padrão, devolveu um `ThinkingBlock` como primeiro item de
      `content` — `content[0]` não é garantidamente o bloco de texto.
      Reproduzi isolado (fora da aplicação, script direto contra a API
      real com a chave de produção) antes de mexer no código, confirmando
      a causa antes de "consertar às cegas".
    - **Duas correções, não uma só**: (1) `thinking={"type": "disabled"}`
      explícito na chamada — a causa raiz de verdade não era só "pegar o
      bloco errado", era o orçamento de `max_tokens=1500` sendo
      consumido inteiro em "pensar" e sobrando zero pra resposta; extended
      thinking não faz sentido nenhum pra uma tarefa de síntese/JSON
      estruturado, então desliguei em vez de só aumentar o orçamento; (2)
      seleção do bloco de conteúdo por `next(b for b in content if
      b.type == "text")` em vez de índice fixo, defensivo contra
      qualquer ordem futura de blocos (mesmo com thinking desligado).
    - **Segundo problema, achado no mesmo teste real**: com o bug acima
      corrigido, a resposta ainda veio como ` ```json\n{...}\n``` ` —
      cerca de código markdown ao redor do JSON, apesar do
      `_PROMPT_SISTEMA` instruir explicitamente "responda ESTRITAMENTE
      em JSON, sem nenhum texto fora do JSON". Comportamento comum de
      modelo (obedece a maior parte da instrução, mas mantém o hábito de
      formatar código em markdown) — não vale insistir só no prompt.
      Corrigido com `_sem_cerca_markdown()` (novo, remove ` ```json `/
      ` ``` ` das pontas antes do `json.loads`), não com mais uma volta
      de ajuste de prompt.
    - Teste de regressão novo
      (`test_gerar_assistente_so_com_bloco_de_pensamento_levanta_indisponivel`)
      cobrindo especificamente "resposta só com `ThinkingBlock`, sem
      `TextBlock` nenhum" — cenário real que já aconteceu, não hipotético.
      Mock de `_client_falso` ajustado pra setar `type="text"`
      explicitamente (antes um `MagicMock()` sem `.type` setado passava
      despercebido pelos testes, porque `MagicMock().type == "text"` é
      `False`, mas o filtro antigo por índice não checava tipo nenhum —
      os testes só pegavam essa lacuna depois do bug já existir em
      produção, não antes).
    - Confirmei o fix chamando `gerar_assistente_ia` de verdade (não
      mock) com a chave de produção antes do redeploy — resposta com
      síntese/pontos de atenção/lacunas coerentes e específicas dos
      dados de teste (ex.: notou 11 projetos sem nenhum dado financeiro
      preenchido). Suíte completa em 67 (66 + 1), ruff limpo, commit +
      push + redeploy.
    **Lição pra próxima vez que integrar com um modelo de IA por API**:
    testar contra o endpoint real (não só mock) antes de considerar a
    feature pronta — os dois bugs desta entrada só apareceram com uma
    chamada de verdade, nenhum teste mockado (nem os que eu mesmo
    escrevi) os pegaria, porque o mock reflete a suposição de quem
    escreveu o código, não o comportamento real da API.

46. **`EMPRESA_MEMBRO` sem permissão nenhuma anexada — lacuna de RBAC real,
    não pendência de configuração** — usuário reportou que
    `juliana.prado` (usuária de demonstração) "não está acessando nenhuma
    funcionalidade". Investigando: `Usuario.pessoa_id` dela era `None`
    (sem `Pessoa` vinculada), mas o problema de verdade era mais fundo —
    `grep -rn "EMPRESA_MEMBRO" app/` confirmou que esse papel **nunca
    apareceu em nenhum grupo `PAPEIS_*`** usado por `verificar_papel()`/
    `cpl_ids_visiveis()` em lugar nenhum do código, só existia no enum e
    (desde o F01) como valor default de `PessoaVinculo.papel`. Ou seja:
    mesmo com `Pessoa`/`PessoaVinculo` perfeitamente configurados, ela
    continuaria sem enxergar nada — não era um problema de dado dela, era
    o papel inteiro sem permissão de verdade.
    - Reportei o achado ao usuário com clareza (não tentei só "consertar
      o dado da Juliana" e seguir em frente) e pedi pra ele desenhar o
      escopo, já que "o que um empresa_membro deveria ver" é decisão de
      produto que nunca tinha sido tomada — ele pediu de volta "preciso
      que você desenhe esse processo". Levantei o RBAC de cada módulo
      (Indicadores, Cadastro/entidade, Eventos, Biblioteca, Notificações)
      antes de propor, then usei `AskUserQuestion` só no ponto genuinamente
      em aberto (implementar autoinscrição em eventos ou só leitura).
    - **`app/core/rbac.py`**: `PAPEIS_LEITURA_MEMBRO = PAPEIS_GOVERNANCA_
      LEITURA | {EMPRESA_MEMBRO}` — grupo novo e separado, não alterei
      `PAPEIS_GOVERNANCA_LEITURA` em si (continua excluindo EMPRESA_MEMBRO
      dos endpoints de órgão/reunião/deliberação, exclusão que já era
      proposital). `cpl_ids_membro()` (CPLs onde tem papel EMPRESA_MEMBRO)
      e `entidade_e_da_pessoa()` (via `PessoaVinculo`) — **decidi não**
      alargar `cpl_ids_visiveis()` em si, que é consumida por praticamente
      todo módulo (`grep -rl` achou uso em Documentos/Maturidade/
      Planejamento/Projetos/Auditoria também) — alargar ali abriria muito
      mais que o escopo combinado; cada tela soma `cpl_ids_membro()` só
      onde decidi abrir.
    - **Indicadores**: `dashboard()` trocou `PAPEIS_GOVERNANCA_LEITURA` por
      `PAPEIS_LEITURA_MEMBRO`; `selecionar_cpl()` (o seletor) passou a
      somar `cpl_ids_membro()`, senão ela só chegaria no dashboard
      digitando a URL direto, sem aparecer na lista.
    - **Cadastro**: `_entidade_visivel_ou_none()` ganhou um `if
      entidade_e_da_pessoa(...): return entidade` antes da checagem por
      CPL visível; `detalhe_entidade()` trocou a checagem inicial pra
      `PAPEIS_LEITURA_MEMBRO` (com `cpl_id=None` — checagem grosseira só
      pra provar que ela é *algum* membro de empresa; a checagem fina de
      "esta entidade específica" é a função acima).
    - **Eventos**: `detalhe()` mesma troca de grupo; `listar()` soma
      `cpl_ids_membro()` no filtro; rota nova `POST
      /{evento_id}/inscrever-me` — deriva `pessoa_id`/`cpl_id` do próprio
      usuário logado (nunca aceita por formulário, pra ninguém conseguir
      inscrever outra pessoa por essa rota), bloqueia se evento não
      `agendado`, já inscrita, sem vaga, ou sem `pessoa_id` vinculado.
      Template ganhou um card "Sua inscrição" separado do card de gestão
      "Inscrever pessoa" (que continua intacto, só pra quem tem
      `PAPEIS_GESTAO`).
    - **Dado da `juliana.prado` em produção**: já existia uma `Pessoa`
      "Juliana Prado" pré-cadastrada (órfã, sem `PessoaVinculo` nenhum) —
      linkei `Usuario.pessoa_id` a ela e criei o `PessoaVinculo` pra
      "Bragantina Autopeças Ltda" (primeira empresa do tipo certo na CPL
      de demonstração), direto via `docker exec` (mesmo padrão de sempre,
      sem migração — é dado, não schema).
    - Testado: 10 testes automatizados novos
      (`tests/test_empresa_membro.py`) — `cpl_ids_membro`/
      `entidade_e_da_pessoa` isolados, dashboard da própria CPL (200) vs.
      de outra (403), própria entidade (200) vs. de outra empresa
      (redirect 303), ver+autoinscrever em evento da própria CPL,
      autoinscrição dupla rejeitada (400), autoinscrição em evento de
      outra CPL rejeitada (403), usuário sem `pessoa_id` não autoinscreve
      (400). Local via Playwright (`empresa_membro_shot.js`) com um
      usuário de teste espelhando o cenário real — dashboard, entidade
      própria e autoinscrição em evento, tudo renderizando e funcionando,
      zero erro de console. Suíte completa em 77 (67 + 10), ruff limpo.
    **Achado não corrigido, deixado como observação**: a barra lateral
    mostra todos os módulos do menu pra qualquer papel, mesmo os que vão
    dar 403 ao clicar (Governança, Documentos, Maturidade, Projetos,
    Auditoria continuam aparecendo pra EMPRESA_MEMBRO) — não é regressão
    desta fatia, já acontecia antes pra outros papéis sub-providos; fica
    como próximo passo de polimento de UI, não pedido aqui. Mesma coisa
    pros botões de ação na própria página de entidade (canais digitais,
    ofertas, geocodificação) — aparecem mas dão 403 ao usar, porque só a
    leitura foi liberada nesta fatia, não a escrita.

47. **Três pedidos pontuais do módulo Cadastro e dados** — usuário pediu,
    numerados (a) entidade gestora + usuário responsável, (b) modelo de
    planilha, (c) RBAC de quem cadastra entidade pra CPL. Antes de tocar
    em código, rodei uma pesquisa (agente Explore) pra mapear exatamente
    o que já existia em cada um dos três — valeu a pena: o achado
    principal foi que (c) **já estava certo tecnicamente**
    (`POST /api/entidades` já usava `PAPEIS_GESTAO`, o conjunto exato de
    três papéis pedido) — a lacuna real era a área restrita não ter
    formulário nenhum pra isso, só API crua.
    - **(a) Entidade gestora + usuário responsável** — `CPL.
      entidade_gestora_id` já existia e era editável, mas só via
      `<select>` de entidades já cadastradas (sem "criar na hora") e sem
      nenhum conceito de "usuário responsável" em lugar nenhum do
      sistema. `app/web/routes_cpl.py` ganhou duas rotas novas,
      administrador-only (mesma restrição que a edição de dados
      cadastrais da CPL já tinha, não ampliei pra `PAPEIS_GESTAO` porque
      o pedido foi especificamente "o administrador"):
      `POST /{cpl_id}/entidade-gestora` (cria `Entidade` + define
      `cpl.entidade_gestora_id` num passo) e
      `POST /{cpl_id}/usuario-responsavel` (exige entidade gestora já
      definida; cria `Usuario`+`Pessoa`+`PessoaVinculo`+`UsuarioPapel`,
      papel escolhido entre `entidade_gestora`/`dirigente_entidade_gestora`
      — reaproveitei o mesmo padrão de identidade completa já usado na
      aprovação de adesão do F01, não só a conta de acesso).
      Validação de e-mail duplicado e de papel fora do conjunto
      permitido, ambos 400.
    - **(b) Modelo de planilha** — `GET /painel/cadastro/modelo-planilha`
      (+ espelho em `/api/cadastro/modelo-planilha`), `formato=xlsx|csv`.
      Reaproveitou `gerar_xlsx_entidades`/`gerar_csv_entidades` (RF-053)
      passando lista vazia — **zero linha de código nova nessas duas
      funções**, só a rota que as chama diferente (sem `exportar_entidades`
      antes). Não escopado por CPL (o cabeçalho é sempre o mesmo,
      `CAMPOS_CONHECIDOS`).
    - **(c) Cadastrar entidade pela área restrita** —
      `POST /painel/cadastro/cpls/{id}/entidades`, cria e já vincula à
      CPL num passo só. Escopado por `cpl_id` via `PAPEIS_GESTAO` — mais
      estrito que `POST /api/entidades` (que deliberadamente não tem
      escopo de CPL, documentado desde que foi construído: cadastrar não
      implica vínculo imediato), mas aqui faz sentido porque o vínculo É
      imediato. O card "vincular entidade existente" tinha um link
      apontando literalmente pro Swagger (`/docs#/Cadastro%20e%20cadeia`)
      como alternativa quando não havia entidade disponível — removido,
      substituído pelo formulário de verdade.
    - **Achado de segurança adjacente, não corrigido nesta fatia**:
      `POST /api/auth/registrar` não tem RBAC nenhum — o próprio
      docstring do endpoint já dizia "em produção deve ser restrito a
      administradores... aberto aqui apenas para viabilizar o bootstrap".
      Construir uma forma sancionada e escopada de criar `Usuario`
      (`usuario-responsavel` acima) bem ao lado de um endpoint que
      qualquer um pode chamar sem autenticação nenhuma é uma
      inconsistência real — mas fechar isso é mudança de comportamento
      de autenticação em produção, não pedida explicitamente, então
      reportei ao usuário em vez de decidir sozinho.
    Testado: local via curl (cadeia completa checada direto no banco —
    `CPL.entidade_gestora_id`, `Usuario.pessoa_id`, `UsuarioPapel.
    entidade_id`, `PessoaVinculo` — e o usuário recém-criado de fato
    logando e exercendo `PAPEIS_GESTAO`) e Playwright
    (`cadastro_gestora_shot.js`, zero erro de console, screenshots
    confirmando os três formulários renderizando certo). 12 testes
    automatizados novos (`tests/test_cadastro_gestora.py`) — suíte
    completa em 89 (77 + 12), ruff limpo.

48. **Fecha `POST /api/auth/registrar` sem restrição nenhuma** — achado
    do item 47 (construindo o cadastro de "usuário responsável"), não
    corrigido na hora porque é mudança de comportamento de autenticação
    em produção, não pedida explicitamente — reportei ao usuário
    ("Quer que eu feche essa brecha também?"), ele respondeu "Sim".
    - `app/api/routes/auth.py::registrar_usuario` ganhou
      `usuario_atual: Usuario | None = Depends(get_current_user_optional)`
      e a mesma válvula já usada em `POST /api/usuarios/{id}/papeis`
      (`app/api/routes/usuario_papel.py`): `if existe_administrador(db):`
      exige `usuario_atual` autenticado com `ADMINISTRADOR_PLATAFORMA`
      (401 se `None`, 403 se autenticado mas sem o papel); enquanto não
      existir nenhum admin, continua aberto — é assim que se sai do
      zero, comportamento de bootstrap preservado.
    - **Quebrou um teste existente**: `test_valvula_bootstrap_fecha_apos_
      primeiro_admin` usava a fixture `admin_usuario` (cria um admin no
      banco) e depois chamava `client.post("/api/auth/registrar", ...)`
      sem autenticação, esperando 201 — com a válvula fechada, isso
      agora 401. Corrigido trocando pra `admin_client.post(...)` (a
      fixture `admin_usuario` já garantia que havia um admin; só faltava
      autenticar como ele pra registrar o usuário de teste) — o resto do
      teste (usuário recém-criado tentando se autoconceder admin, 403)
      continua igual. Lição: uma mudança de RBAC pode quebrar
      pressupostos de teste que não são sobre o endpoint mudado
      diretamente — rodar a suíte inteira depois, não confiar só no
      arquivo óbvio.
    - Produção já tem admin (`admin@sigcpl.dedev.cloud`, criado na sessão
      de deploy) — o deploy deste item já nasce com a válvula fechada
      de vez, sem passar por uma janela de bootstrap aberta em produção.
    - Testado: 3 testes automatizados novos em `tests/test_auth.py`
      (sem autenticação com admin já existente → 401; admin autenticado
      → 201; autenticado mas não-admin → 403), suíte completa depois do
      ajuste do teste quebrado, ruff limpo.

49. **Setor/Município/UF viram listbox no cadastro de CPL** — pedido
    explícito: Setor restrito aos valores já cadastrados, Município e
    Estado também em listbox, Estado antes de Município, escolher o
    Estado filtra o Município, buscando a lista completa de estados e
    municípios do Brasil numa API gratuita, sem ocupar espaço de banco.
    - Fonte escolhida: API pública de Localidades do IBGE
      (`servicodados.ibge.gov.br/api/v1/localidades`, gratuita, sem
      credencial) — mesmo raciocínio já usado pra CNPJ (BrasilAPI,
      RF-054) e geocodificação (Nominatim, RF-011): testar a chamada
      real via `curl` e via `urllib` puro (não só `curl`) antes de
      escrever qualquer código, porque cada serviço público falha de um
      jeito diferente.
    - **Armadilha nova, diferente da de User-Agent já vista em
      BrasilAPI/Nominatim**: o IBGE sempre devolve `Content-Encoding:
      gzip`, mesmo sem o cliente pedir — `urllib.request` não
      descomprime sozinho (só `requests`/navegador fazem isso), então
      ler a resposta crua quebrava com `UnicodeDecodeError` (byte
      inicial `\x8b`, a assinatura gzip). Corrigido checando o header e
      chamando `gzip.decompress()` antes do `json.loads()`.
    - `app/services/localidades.py` (novo): `estados()` e
      `municipios_do_estado(uf)`, ambos `@lru_cache` (cache só em
      memória do processo, `maxsize=1` e `maxsize=27` respectivamente —
      as 27 UFs são o teto de combinações possíveis). Zero tabela nova,
      zero linha gravada além do que `CPL.municipio`/`CPL.uf` já
      guardavam — decisão explícita pra atender "não ocupar muito
      espaço de banco de dados". O IBGE manda `Cache-Control:
      max-age=2592000` (30 dias) nas próprias respostas, então cache
      pela vida do processo é bem mais conservador que isso.
      `estados()` cai pra uma lista de reserva fixa das 27 UFs se o
      IBGE cair (nunca mudam, vale embutir); `municipios_do_estado()`
      não tem reserva (~5.570 nomes, não vale embutir) — se falhar, só
      aquele estado fica sem opção de município, sem quebrar o resto do
      formulário.
    - `app/web/routes_cpl.py`: `_setores_cadastrados()` (`DISTINCT
      CPL.setor`) e `_setor_final(setor, setor_outro)` — Setor virou
      `<select>` restrito aos valores já usados, com um `<input
      name="setor_outro">` ao lado que tem precedência se preenchido
      (minha decisão, não pedida explicitamente, mas necessária: sem
      isso a primeira CPL de um setor novo — ou o sistema recém-
      instalado sem nenhuma CPL — ficaria num beco sem saída, sem
      nenhuma opção pra escolher). Nova rota `GET
      /painel/cpls/municipios-fragment` (fragmento HTMX, devolve só o
      `<select>` de município filtrado pela UF) — **precisa estar
      registrada antes de `GET /{cpl_id}` no arquivo**, senão o
      FastAPI tenta casar "municipios-fragment" contra o
      `{cpl_id}: uuid.UUID` primeiro (registrado antes) e devolve 422
      em vez de chegar na rota certa.
    - Templates (`lista.html` criação, `detail.html` edição): UF
      reordenado pra antes de Município; UF é `<select>` com
      `hx-get="/painel/cpls/municipios-fragment" hx-trigger="change"
      hx-target="#municipio-select-wrapper" hx-swap="innerHTML"`;
      Município é um `{% include
      "restrito/cpls/fragments/municipio_select.html" %}` (fragmento
      novo, reaproveitado tanto no include inicial quanto na resposta
      HTMX) — como o Jinja `{% include %}` herda o contexto do
      template pai, tanto `listar()` quanto `detalhe()` precisaram
      passar explicitamente `municipios`/`municipio_selecionado` no
      contexto, senão o `Undefined` padrão do Jinja quebra ao iterar.
    - Testado: local via `curl` (IBGE real, antes de escrever
      `localidades.py`) e Playwright (`localidades_shot.js`) contra o
      app rodando de verdade — confirmando que trocar UF pra RJ de fato
      filtra o `<select>` de município pra cidades do RJ (Rio de
      Janeiro aparece, Atibaia/SP não aparece) e que o cadastro
      completo (escolher UF, esperar o HTMX trocar o município,
      escolher Niterói, submeter) persiste certo. 15 testes
      automatizados novos (`tests/test_localidades.py`, serviço
      mockando `urlopen` como `test_geocodificacao.py` já fazia, rotas
      mockando `routes_cpl.estados`/`routes_cpl.municipios_do_estado`
      no ponto de uso) — suíte completa em 107 (92 + 15), ruff limpo.
      Gotcha de teste: `lru_cache` persiste entre testes no mesmo
      processo pytest — precisou de fixture `autouse=True` chamando
      `.cache_clear()` antes E depois de cada teste, senão o resultado
      do primeiro teste "vazava" pros seguintes.

50. **Tela "Solicitar adesão" (F01): Município/UF em listbox, telefone com
    máscara, e-mail reforçado** — pedido explícito, mesmo tratamento de
    Estado/Município do item 49, agora aplicado à tela pública de adesão.
    - `app/web/routes_publico.py` ganhou `GET /cpls/{id}/solicitar-adesao/
      municipios-fragment` — mesmo fragmento HTMX
      (`restrito/cpls/fragments/municipio_select.html`, reaproveitado
      direto, apesar do nome da pasta) e mesmo serviço
      (`app/services/localidades.py`) do item 49, mas **sem exigir
      login** (`_exigir_login` não é chamado aqui — a tela inteira é
      pública). UF virou `<select>` (antes era `<input>` livre),
      reordenado pra antes de Município no formulário, com
      `hx-get`/`hx-trigger="change"` disparando o fragmento.
    - **Telefone**: máscara `(99) 99999-9999` formatada em tempo real —
      **primeiro JavaScript escrito à mão do projeto** (`<script>` inline
      em `solicitar_adesao.html`, ouvindo o evento `input` do campo).
      Todo o resto do sistema usa só HTMX pra dinamismo; uma máscara de
      digitação (inserir `(`, `)`, espaço e `-` enquanto a pessoa digita)
      não é algo que HTMX resolve, então não dava pra manter a disciplina
      de "zero JS" aqui sem piorar a experiência. Ainda assim, o JS é só
      cosmético — quem desabilita JavaScript consegue digitar o telefone
      sem máscara e a submissão funciona igual, porque a validação de
      verdade é sempre no servidor.
    - `app/services/validadores.py` ganhou `telefone_valido()`/
      `normalizar_telefone()` — mesmo padrão de `cnpj_valido`/`cpf_valido`
      (só valida quando o campo vem preenchido, já que telefone não é
      obrigatório): aceita 10 ou 11 dígitos depois de tirar a máscara
      (fixo ou celular), sem dígito verificador (telefone não tem um
      oficial). Chamada em `criar_solicitacao`
      (`app/services/adesao.py`) — cobre tanto o formulário web quanto
      `POST /api/cpls/{id}/solicitacoes-adesao`, já que os dois passam
      pelo mesmo service.
    - **E-mail**: já era validado no servidor por `EmailStr` (Pydantic)
      desde que este fluxo existe (retorna "E-mail de contato inválido."
      em caso de erro) — o pedido de "verificar se tem @ e pontos" já
      estava coberto; só reforcei com `pattern="[^\s@]+@[^\s@]+\.[^\s@]+"`
      e `title` no `<input type="email">`, pra rejeitar no navegador
      antes mesmo de enviar, sem esperar o round-trip ao servidor.
    - Testado: local via Playwright contra o app rodando de verdade
      (`adesao_localidades_shot.js`) — confirmando a cascata UF→Município
      real (RJ filtra pra 93 municípios reais, Rio de Janeiro aparece),
      a máscara formatando "11987654321" digitado em
      "(11) 98765-4321" enquanto o usuário digita, o fluxo completo de
      envio funcionando (chega na página de "obrigado"), e-mail inválido
      barrado pelo navegador antes do envio (`checkValidity() === false`),
      zero erro de console. 13 testes automatizados novos (4 em
      `tests/test_validadores.py`, 6 em `tests/test_adesao.py`) — suíte
      completa em 117 (107 + ~10, alguns testes de outros arquivos também
      cresceram nesse intervalo), ruff limpo.

51. **Convite de campanha (RF-012) passa a enviar e-mail de verdade** —
    usuário relatou um caso real: "uma empresa cadastrada não recebeu o
    e-mail de participação da campanha". Investiguei antes de mexer:
    `convidar_entidade` (`app/api/routes/cadastro_dinamico.py` e
    `app/web/routes_cadastro.py`, duplicado nos dois) sempre só criou um
    `CampanhaConvite` com link/token — **nunca existiu envio de e-mail
    nenhum**, apesar do botão da tela usar ícone de envelope. Reportei o
    achado (não era bug de "algo quebrou", era recurso que nunca foi
    construído, mesmo padrão do "convite" de F01/adesão) e perguntei se
    quer o envio automático agora que o SMTP já está configurado (RF-004)
    — resposta: sim, e também "criar um campo de e-mail vinculado à
    entidade" e "quando tiver contato vinculado, enviar também pra eles".
    - `Entidade.email` (nova coluna) — `Entidade` nunca teve e-mail
      próprio, só `Pessoa.email` via `PessoaVinculo`; sem isso, uma
      entidade sem nenhum contato cadastrado não tinha pra quem mandar
      nada. Exposto nos três formulários que criam `Entidade` (cadastro
      de uma CPL, cadastro de entidade gestora, API) e com uma tela/rota
      dedicada pra editar depois (`PATCH /api/entidades/{id}/email`,
      `POST /painel/cadastro/entidades/{id}/email`) — precisa continuar
      editável porque é o destinatário do envio automático, não só um
      dado de cadastro estático.
    - `app/services/campanhas.py` (novo): `contatos_da_entidade()`
      resolve o e-mail da entidade **mais** o de cada `Pessoa` com
      vínculo vigente (`PessoaVinculo.data_fim` nulo ou no futuro),
      deduplicado; `enviar_convite_email()` manda pra todos e grava o
      resultado no próprio `CampanhaConvite`
      (`email_enviado`/`email_enviado_em`/`email_destinatarios`
      JSONB/`email_erro`) — gravar no convite, não só logar, é o que deixa
      a gestão voltar na tela depois e ver se saiu de verdade, pra quem, e
      por quê não quando não saiu.
    - **Nunca bloqueia a criação do convite**: SMTP fora do ar (ou
      ausente, como no dev local) só grava `email_erro`, o convite
      continua existindo com o link copiável de sempre como alternativa.
      Sem contato nenhum também não é erro (`email_erro=None`) — a tela
      distingue os dois casos com textos diferentes.
    - Chamado nos dois pontos de criação de convite (API e web, mesmo
      service) — evita a mesma divergência que já apareceu outras vezes
      neste projeto quando uma regra só é aplicada num dos dois.
    - Migração `834a3a9e7775`: `entidades.email` e as quatro colunas novas
      de `campanha_convites` — `email_enviado` é `NOT NULL` com
      `server_default=false` (mesmo padrão já usado em migrações
      anteriores pra não quebrar linhas existentes, ex.: `marco` em
      RF-039/040), as outras três são nullable.
    - Testado: local sem SMTP configurado (cenário real de dev, não
      simulado) via Playwright contra o app rodando de verdade — convite
      pra entidade com e-mail mostrou "Falha ao enviar e-mail (SMTP não
      configurado...)"; convite pra entidade sem nenhum contato mostrou
      "Nenhum e-mail cadastrado"; editar o e-mail da entidade persistiu e
      apareceu no cabeçalho. 15 testes automatizados novos
      (`tests/test_campanhas.py`, `enviar_email` mockado em
      `app.services.campanhas.enviar_email` — mesmo padrão "mockar no
      ponto de uso" de `test_localidades.py`/`test_geocodificacao.py`) —
      suíte completa em 132 (117 + 15), ruff limpo, `campanhas.py` com
      100% de cobertura.

52. **Referências a RF-/RN-/RNF-/F0x removidas das interfaces** — pedido
    explícito: os códigos do documento de requisitos ("Relatórios
    (RF-041)", "Solicitações de adesão (F01)", etc.) apareciam em títulos
    de card, subtítulos e rótulos de botão em cerca de 25 templates da
    área restrita — vocabulário interno de rastreabilidade entre código e
    documento, sem sentido nenhum pra quem usa o sistema no dia a dia de
    uma CPL. Removidos ~30 parênteses assim (só texto visível — mantive
    os mesmos códigos nas docstrings/comentários Python e Jinja, que são
    documentação pra quem mexe no código, não "interface").
    - Aproveitado pra corrigir, na mesma passada, um estado vazio
      desatualizado em `governanca/cpls.html`: quando a CPL não tinha
      nenhum órgão de governança, o texto ainda mandava o usuário criar a
      CPL via `POST /api/cpls` no Swagger (`/docs`) — sobra de quando
      `/painel/cpls` não existia. Trocado por um link direto pra tela de
      cadastro de CPL que já existe há muito tempo.
    - Nenhum código Python mudou — só HTML/Jinja, então nada de teste
      novo (as asserções já existentes que checam texto de tela
      continuam batendo; nenhuma checava literalmente por "(RF-...)").
      Confirmado com Playwright contra o app rodando de verdade em várias
      telas, checando que nenhuma delas mostra mais essas referências, e
      suíte completa (132) + ruff, sem regressão.

**Se for adicionar um novo módulo, o caminho mais previsível é repetir esse
padrão**: modelos em `app/models/<modulo>.py`, enums novos em
`app/models/enums.py` (reaproveite os que já existem quando o conceito for
o mesmo — ex. `StatusTarefa` já serve para qualquer "item com ciclo de vida
pendente → em andamento → concluído"), schemas em
`app/schemas/<modulo>.py`, API em `app/api/routes/<modulo>.py`, UI web em
`app/web/routes_<modulo>.py` + templates em
`app/templates/restrito/<modulo>/`, RBAC reaproveitando os grupos de
`app/core/rbac.py` quando fizer sentido semântico (não crie um grupo novo
só porque é um módulo novo).

## Armadilhas já resolvidas (não redescobrir)

1. **`passlib` + `bcrypt` 4.x/5.x são incompatíveis** — passlib está sem
   manutenção e quebra com bcrypt moderno (`ValueError: password cannot be
   longer than 72 bytes` mesmo com senhas curtas). Solução aplicada: usar o
   pacote `bcrypt` diretamente em `app/core/security.py`
   (`bcrypt.hashpw`/`bcrypt.checkpw`), sem passlib. Não reintroduza passlib.
2. **Alembic + Postgres + ENUM reaproveitado entre migrações** — quando um
   `Enum` Python (ex. `Elo`, `StatusTarefa`) já foi usado numa migração
   anterior e uma tabela nova volta a referenciá-lo, o autogenerate do
   Alembic gera `sa.Enum(..., name='elo')` de novo, que tenta `CREATE TYPE`
   um tipo que já existe → `DuplicateObject`. Solução: editar a migração
   gerada e trocar por `postgresql.ENUM(..., name='elo', create_type=False)`
   para o(s) enum(s) que já existem no banco. Ver
   `alembic/versions/5dd913b79202_*.py` como exemplo de correção já feita.
   **Sempre rode `alembic upgrade head` logo após gerar uma migração nova
   com enums reaproveitados** e cheque o traceback antes de assumir sucesso.
   **Aconteceu de novo em `336459855cb9`** (etapas de projeto, RF-034,
   reaproveitando `StatusTarefa`) mesmo já documentado — confiança
   excessiva depois de várias migrações seguidas sem precisar de ajuste
   manual. Rollback foi limpo (DDL transacional), mas o ideal é nunca
   deixar acontecer: **grep `sa.Enum(` no arquivo de migração gerado
   antes de rodar `upgrade head`**, todas as vezes, não só quando "acha
   que" o enum é reaproveitado — é fácil esquecer justamente quando
   parece rotina.
   **3ª ocorrência em `777ba9fa79ad`** (metas de projeto, finalização do
   RF-034, de novo reaproveitando `StatusTarefa`) — desta vez o grep
   preventivo funcionou e pegou antes de aplicar, sem rollback. A lição
   "sempre grepar antes de aplicar" finalmente virou hábito automático
   em vez de intenção; mantenha assim daqui pra frente.
3. **Portas ocupadas por outros projetos do usuário** — o usuário tem outro
   projeto (`rh-nepen`) rodando via Docker que ocupa a porta 5432 (Postgres)
   e 8000 (backend). Por isso este projeto usa 5433 e (nas sessões de teste)
   8010. Confira com `docker ps` e `netstat -ano | grep <porta>` antes de
   assumir que uma porta padrão está livre.
4. **Testes visuais em navegador** — não há Playwright/chromium-cli
   instalado no ambiente por padrão. Nesta sessão, instalei Playwright
   ad-hoc num diretório temporário fora do projeto
   (`AppData/Local/Temp/claude/sigcpl_screenshot_test`, não faz parte do
   repo) para tirar screenshots reais via `node shot.js <url> <arquivo>`.
   Repita esse padrão se precisar validar UI visualmente — não assuma que
   "renderizou sem erro 500" é o mesmo que "está bonito". **Foi assim que
   se achou o gotcha nº 5** — só apareceu no screenshot, não em teste de API.
5. **Jinja renderiza `None` como o texto literal "None"** — em qualquer
   template, `{{ objeto.campo if objeto else '' }}` não protege contra o
   campo em si ser `None` (só protege contra `objeto` ser `None`). Sempre
   que popular um `<input value="">`/`<textarea>` a partir de um campo
   opcional do banco, use `{{ (objeto.campo or '') if objeto else '' }}`
   (ou, para números onde `0` é um valor válido,
   `{{ (objeto.campo if objeto.campo is not none else '') if objeto else '' }}`).
   Já corrigido em `publico/atualizacao_form.html` — confira os outros
   templates com formulários pré-preenchidos se for mexer neles.
6. **`pypdf.extract_text()` não é confiável pra validar fonte TrueType do
   fpdf2** — depois de embutir uma fonte Unicode (`add_font`) pra corrigir
   acentuação/travessão na geração de PDF (`app/services/
   geracao_documentos.py`), usei `pypdf` pra "confirmar" o conteúdo e vi
   texto todo trocado por `�`/`?` — parecia que a fonte não tinha resolvido
   nada. **Era o extractor, não o PDF**: rasterizando a página de verdade
   (`PyMuPDF`/`fitz`, `page.get_pixmap()`) o texto aparece perfeito, acentos
   e travessão inclusos. Se for mexer em geração de PDF, valide por
   rasterização (ou abrindo num leitor de verdade), não por
   `pypdf.extract_text()` — ele engana.
7. **Chromium headless (via Playwright) não renderiza PDF inline por
   padrão** — nem navegando direto pro arquivo (`page.goto` dispara
   download em vez de exibir) nem via `<embed>`/`<iframe>` ("Couldn't load
   plugin"). Pra validar PDF visualmente, use `PyMuPDF` (`fitz`) pra
   rasterizar a página em PNG e leia a imagem — não tente forçar o
   Chromium do Playwright a exibir o PDF.
8. **`before_flush` roda ANTES dos `default=` do SQLAlchemy serem
   aplicados** — ao implementar a trilha de auditoria automática
   (`app/services/auditoria.py`), a primeira versão serializava o objeto
   recém-criado dentro de `before_flush` e capturava `id`/`ativo`/
   `created_at` como `None`, porque colunas com `default=callable` (ou
   `server_default`) só são preenchidas quando o INSERT de fato executa —
   o que acontece DEPOIS do `before_flush`. Corrigido guardando só a
   referência ao objeto (via `session.info`) em `before_flush` e
   serializando de verdade em `after_flush`, quando os valores gerados já
   existem. Nesse ponto, `session.add()` não é mais aceito pelo
   SQLAlchemy (regra do próprio `after_flush`) — use
   `session.execute(insert(Tabela.__table__), [...])` (Core, não ORM) pra
   inserir as linhas de auditoria de criação. Se for mexer nesse listener,
   teste literalmente lendo o valor de volta do banco (não confie em
   "não deu erro") — foi assim que o bug apareceu.
9. **`<select>` HTML sempre manda o campo, mesmo com a opção "Todos"
   selecionada** — um filtro com `<option value="">Todos</option>` como
   padrão faz o form submeter `campo=` (string vazia), não omitir o
   parâmetro. Em FastAPI, `campo: str | None = None` trata `""` como um
   valor válido (não None) — um filtro `if campo is not None` bloqueia
   tudo incorretamente; use `if campo:` (falsy). Pior ainda se o parâmetro
   for tipado como `Enum | None`: `""` não é um membro válido e o FastAPI
   retorna 422 pro usuário. Solução aplicada em
   `app/web/routes_auditoria.py`: receber como `str | None` e converter
   manualmente pro enum só se truthy (`AcaoAuditoria(acao) if acao else None`).
   Qualquer tela nova com filtro por `<select>` deve seguir esse padrão,
   não o padrão "ingênuo" de tipar o parâmetro direto como Enum.
10. **Converter uma pasta com arquivo de segredos em working directory git
    (`git init` numa pasta já existente) pode apagar o arquivo de
    segredos** — ao transformar `/opt/sigcpl` (até então só uma cópia de
    arquivo via `tar`) num clone git de verdade, o roteiro óbvio (`git
    init` && `git add -A` && `git commit` && `git reset --hard
    origin/master`) tem uma pegadinha: o `.gitignore` que já estava na
    pasta era uma versão **anterior** à que passou a excluir `.env.prod`
    (esse padrão só foi adicionado ao `.gitignore` numa sessão posterior
    ao deploy original) — então o `git add -A` local commitou o
    `.env.prod` de verdade num commit efêmero, e o `git reset --hard
    origin/master` seguinte, ao não achar esse arquivo na origem,
    **apagou-o do disco** (comportamento correto do `reset --hard` pra
    arquivos rastreados, mas destrutivo aqui). Detectado e corrigido na
    hora (purgado do `.git` com `reflog expire --expire=now --all` +
    `gc --prune=now`, arquivo recriado com os mesmos valores, containers
    nunca reiniciaram, zero downtime), mas o jeito certo de fazer essa
    conversão é: **mover qualquer arquivo de segredo pra fora da pasta
    antes** de rodar `git add`/`reset --hard` nela, e só devolvê-lo depois
    de confirmar que o `.gitignore` do commit de destino já o exclui.
11. **`python -c "texto com acento"` via git-bash no Windows corrompe o
    texto antes mesmo de chegar no Python** — não é um bug do app. Ao
    investigar um "bug" de acentuação no relatório executivo (RF-048),
    `repr()` de uma string lida do banco mostrava `�` (U+FFFD) no lugar de
    "ó"/"—". Rastreei até a fonte: o argv passado a `python -c` por esse
    ambiente (Bash tool → subprocess do Windows) já chega corrompido pro
    interpretador — confirmado testando um literal Python digitado direto
    no `-c` (`'Relatório...'`), que saiu corrompido **antes de qualquer
    banco de dados estar envolvido**. Os bytes de verdade (checados
    escrevendo em arquivo binário e lendo com `xxd`, sem passar por
    `print`/console) estavam corretos o tempo todo, e o PDF gerado
    renderiza os acentos perfeitamente (confirmado via rasterização
    PyMuPDF, mesmo padrão do gotcha nº 6). **Se for depurar acentuação de
    novo**: nunca confie em `repr()`/`print()` de string com acento
    impressa por um script Python invocado via `-c` neste ambiente —
    escreva em arquivo e leia os bytes brutos (`xxd`), ou confira via
    navegador/PDF renderizado, que são os caminhos que realmente importam.
12. **"Gateway Timeout" ao cadastrar CPL em produção — causa era o próprio
    redeploy, e revelou um bug real de infra ao investigar.** Usuário
    reportou o erro; primeira investigação encontrou: tabela `cpls` em
    produção **vazia** (nada foi criado, mesmo silenciosamente — sem
    risco de duplicata), **nenhum erro de aplicação** logado, container
    `sigcpl_backend` recriado ~40 min antes do relato (redeploy do
    relatório de recadastramento, sessão anterior), e revisão do código
    de criação de CPL sem achar nada que explicasse um timeout de
    verdade (é só um SELECT de unicidade + INSERT + commit). Hipótese
    inicial: request caiu na janela em que o container antigo já tinha
    parado mas o novo ainda não respondia. Apliquei uma correção
    (healthcheck ativo do Traefik em `/api/saude`, faz Traefik só
    rotear pro backend quando ele responder de verdade) e, ao
    reimplantar pra validar, **o site inteiro caiu com 503** — o que
    expôs a causa raiz de verdade: `sigcpl_backend` está em **duas
    redes Docker** (`internal`, com o Postgres, e `n8n_default`, onde o
    Traefik escuta) e o label `traefik.docker.network` nunca foi
    definido explicitamente. Sem essa rede fixada, o provider Docker do
    Traefik escolhe uma rede "livremente" quando descobre o container —
    nesse redeploy escolheu `internal` (rede que o Traefik nem está
    conectado), registrou o backend como `serverStatus: DOWN` (IP
    `172.21.0.3`, inalcançável) e passou a devolver 503/504 pra
    **qualquer** rota, não só criação de CPL. Confirmado consultando a
    API do próprio Traefik de dentro do container
    (`docker exec n8n-traefik-1 wget -qO- http://localhost:8080/api/
    http/services` — porta 8080 do dashboard não é publicada no host,
    só acessível de dentro do container) e comparando com
    `rh_nepen_backend` (mesmo padrão de 2 redes, mas sem o problema
    nesse momento — a escolha da rede parece não-determinística por
    instância de container, não uma regra fixa tipo "primeira rede
    declarada"). Como a escolha errada é por sorte a cada recriação do
    container, isso pode ter acontecido silenciosamente em qualquer
    redeploy anterior também — inclusive o que motivou o relato original
    do usuário; a "janela de restart" não está descartada, mas essa
    ambiguidade de rede é a explicação mais provável e mais grave, já
    que ela não se autorresolve como uma janela de restart resolveria.
    **Correção de verdade aplicada**: label
    `traefik.docker.network=n8n_default` explícito em
    `docker-compose.prod.yml`, eliminando a ambiguidade — reimplantado e
    confirmado via a mesma consulta à API do Traefik (`serverStatus: UP`
    em `172.18.0.6:8000`, a rede certa) e smoke test em `/`, `/login`,
    `/docs`, `/api/saude`, todos 200. **Se for adicionar outro serviço
    Traefik neste projeto (ou em qualquer outro nesta VPS) que fique em
    mais de uma rede Docker, sempre declare `traefik.docker.network`
    explicitamente — não confie na escolha automática.** Healthcheck
    ativo do Traefik em `/api/saude` (`interval=5s`/`timeout=3s`)
    permanece como camada extra de proteção — reduz a janela de erro em
    redeploys futuros (Traefik só roteia quando o backend responder de
    verdade), mas não elimina 100%: é um único container (sem
    blue-green), então ainda há um instante sem backend saudável entre
    o container antigo parar e o novo passar no healthcheck. Solução de
    verdade pra isso, se algum dia for inaceitável: 2 réplicas atrás do
    mesmo serviço (exige remover `container_name` fixo) ou blue-green
    explícito — nenhum dos dois foi implementado.
    **Achado paralelo, projeto diferente mas mesma VPS**:
    `cervejeira-app-1` em crash-loop com >5000 reinicializações desde
    30/07 — não é a causa deste incidente (já estava assim há dias,
    contido em seu próprio container/rede), mas consome recursos à toa;
    não mexi nele sem confirmação do usuário, é outro projeto.
13. **FastAPI/Starlette casam rotas na ordem em que são registradas — um
    sub-recurso "global" (path fixo, sem `{param}` antes dele) definido
    DEPOIS de uma rota `GET /{id}` genérica no mesmo router nunca é
    alcançado.** Ao adicionar `GET /api/projetos/editais-fomento` (RF-029,
    item 25) depois de `GET /api/projetos/{projeto_id}` (já existente,
    RF-032) no mesmo arquivo, toda chamada a `/editais-fomento` caía
    primeiro em `/{projeto_id}`, que tentava interpretar a string
    `"editais-fomento"` como UUID e devolvia 422 — sem esse endpoint
    nunca "quebrar" de um jeito óbvio (404 seria mais fácil de notar que
    um 422 de validação). Pego testando via curl direto na API — o
    Playwright/teste web nunca bateu nesse path específico (a UI usa
    outras rotas), então **testar só pela UI não seria suficiente pra
    achar isso**. Corrigido movendo o bloco inteiro das rotas de edital
    de fomento pra antes da seção que define `GET /{projeto_id}` no
    arquivo. **Regra pra não repetir**: sempre que adicionar uma rota
    GET com path fixo (sem parâmetro variável na posição inicial) a um
    router que já tem uma rota `GET /{algo}` genérica no mesmo nível,
    registre a rota fixa ANTES da genérica — e teste com curl direto na
    API (não só a UI web) pra pegar colisões desse tipo cedo.
14. **Alembic autogenerate não adiciona `server_default` sozinho ao
    adicionar uma coluna `Boolean`/`NOT NULL` nova a uma tabela já
    populada** — ele só copia o `server_default` que estiver explícito
    no `mapped_column(...)` do modelo; o `default=False` do
    SQLAlchemy/Python (aplicado só em `INSERT`s novos feitos pelo ORM)
    é invisível pro autogenerate. Ao adicionar
    `AquisicaoProjeto.contrapartida` (`Boolean, default=False,
    nullable=False`) numa tabela (`aquisicoes_projeto`) que já tinha
    linhas de sessões de teste anteriores, a migração gerada teria
    falhado com violação de `NOT NULL` nas linhas existentes. Pego
    antes de aplicar (revisão de rotina do arquivo gerado, mesmo hábito
    que virou automático pro gotcha de enum) — corrigido adicionando
    `server_default=sa.text('false')` na chamada `op.add_column(...)`.
    **Sempre que adicionar uma coluna `NOT NULL` sem explicit
    `server_default` no modelo a uma tabela que já existe (não é
    `create_table`), revisar se a tabela pode ter linhas e, se sim,
    adicionar `server_default` manualmente na migração** — o
    autogenerate não avisa, só falha na hora de aplicar.
15. **Form HTML que precisa "criar X pra um Y escolhido num select" não
    deve montar a URL de submissão dinamicamente com JS** — ao desenhar
    o form de nova cotação (RF-037, item 27), a primeira versão tinha
    `<select name=aquisicao_id>` mas submetia pra
    `/aquisicoes/{aquisicao_id}/cotacoes` (path param), o que exigiria
    JS (`onsubmit` reescrevendo `this.action`) pra funcionar — único
    lugar do projeto que precisaria disso, quebrando o padrão de forms
    HTML puros usado em todo o resto do sistema. Corrigido antes de
    testar: a rota web mudou pra aceitar `aquisicao_id` como campo de
    form normal (`POST /{projeto_id}/cotacoes`), igual a
    `responsavel_id`/`etapa_id`/`origem_recurso_id` em outros forms —
    zero JS. A API manteve o path param (`/aquisicoes/{id}/cotacoes`),
    que é o design REST correto pra um cliente HTTP, sem o mesmo
    problema. **Regra geral**: se uma entidade relacionada precisa ser
    escolhida num `<select>` antes de submeter, ela é sempre um campo de
    form, nunca parte do path da action — path params dinâmicos vêm só
    de links (`href`) ou de IDs já conhecidos no momento em que a
    página renderiza (ex.: `/etapas/{etapa.id}/status`, onde `etapa.id`
    já existe fixo em cada linha da tabela).
16. **Flag de contexto que esconde/mostra um form no template precisa
    corresponder exatamente ao grupo de papéis que o backend valida —
    não ao flag "parecido" mais próximo já disponível.** Ao construir
    "decidir alteração de plano" e "aprovar entrega" (RF-039, item 28),
    copiei por hábito o padrão de `RecursoSubmissaoProjeto`
    (`e_administrador`, que reflete `PAPEIS_EDITAL_GESTAO` — só
    `ADMINISTRADOR_PLATAFORMA`). Mas a autorização de verdade dessas
    duas ações no backend é `PAPEIS_GESTAO`, um grupo mais amplo que
    também inclui `ENTIDADE_GESTORA`/`DIRIGENTE_ENTIDADE_GESTORA`. Um
    usuário com um desses papéis teria a ação aceita pelo backend mas
    **nunca veria o form** (`e_administrador` calcula `False` pra ele) —
    bug de UI que não aparece em teste de API (só testando como aquele
    papel específico pela UI). Pego na revisão do template antes de
    testar, não durante — corrigido criando `_pode_gestao(db, usuario,
    cpl_id)` em `routes_projeto.py` (checa `PAPEIS_GESTAO` de verdade
    via `papeis_do_usuario`, não só admin) e usando esse flag nos dois
    forms em vez de `e_administrador`. **Regra**: antes de reaproveitar
    um flag de contexto existente (`e_administrador` ou qualquer outro)
    pra esconder/mostrar um form, conferir contra qual `PAPEIS_*`
    exatamente a rota de submissão desse form chama `verificar_papel` —
    se não for o mesmo conjunto, o flag existente vai mentir pra algum
    papel autorizado.
17. **`@app.exception_handler(Exception)` junto com um `@app.middleware("http")`
    custom duplica o log de todo 500 real** (RNF-012, item 37). O
    Starlette trata um handler registrado pro tipo `Exception` "cru"
    como especial: em vez de instalá-lo no `ExceptionMiddleware` de
    sempre, ele move pro `ServerErrorMiddleware`, que fica ACIMA de
    qualquer `@app.middleware("http")` customizado (não abaixo, como se
    esperaria). Resultado: quando uma exceção não tratada sobe, ela
    passa pelo middleware custom primeiro — cujo `finally` já reseta os
    contextvars de auditoria — e só é capturada pelo handler depois, na
    borda externa; nesse meio-tempo, o mecanismo interno do
    `BaseHTTPMiddleware` (usado por baixo de todo `@app.middleware("http")`)
    também loga a mesma exceção como "Exception in ASGI application",
    então cada falha real vira dois 500 no log em vez de um — quebra
    silenciosamente a disciplina de "conferir zero 500 real no log
    depois de cada mudança" usada a sessão inteira, porque o segundo
    500 não é um bug novo, é ruído do próprio mecanismo de captura.
    **Regra**: se o middleware custom já existe e precisa reagir a
    exceção não tratada (registrar falha, medir duração mesmo em erro),
    capture com `try/except Exception` dentro do próprio middleware, não
    com um `@app.exception_handler(Exception)` à parte — a exceção nunca
    escapa do middleware, então nada sobra pra o `ServerErrorMiddleware`
    logar de novo.
18. **API pública de terceiro pode bloquear o User-Agent padrão do
    `urllib`, mesmo sem exigir credencial nenhuma** (RF-054, item 39).
    A primeira chamada real pra BrasilAPI devolveu 403 Forbidden via
    `urllib.request` puro, enquanto a mesma URL funcionava normalmente
    via `curl` no terminal — não é bloqueio por falta de autorização (o
    CNPJ testado é público, sem chave de acesso nenhuma), é proteção
    anti-bot genérica reagindo ao User-Agent padrão que o `urllib`
    manda (`Python-urllib/x.x`). Corrigido passando um `User-Agent`
    identificável explícito na requisição. **Regra**: ao integrar com
    uma API pública de terceiro pela primeira vez, testar a chamada
    real antes de assumir que "pública e sem credencial" quer dizer
    "sem nenhuma configuração de requisição necessária" — teste isolado
    fora da aplicação (como fiz aqui) é a forma mais rápida de separar
    "bug no meu código" de "a API exige algo que a documentação não
    deixou óbvio". **Reaplicado com sucesso no RF-011/Nominatim (item
    40)** — desta vez testado com `curl -A` já na fase de design, antes
    de escrever qualquer código, então não houve retrabalho nenhum.

## O que falta (priorizado)

Ver `docs/requisitos_macros.md` para o texto completo de cada requisito e
`README.md` (seção "Próximos passos sugeridos") para a lista mais atual.
**A Fase 1/MVP está completa e a Fase 2 foi iniciada** (Maturidade e
reconhecimento, RF-024 a RF-028, implementado nesta sessão). Resumo na
ordem recomendada para o que vem depois:

1. ~~Fechar limitações conhecidas do RBAC~~ — **feito nesta sessão**: escopo
   por órgão específico (`verificar_participacao_orgao`), escopo de CPL
   para Entidade/Pessoa na leitura, página 403 amigável no portal web. Ver
   README, seção "Controle de acesso" → "Limitações conhecidas".
2. ~~Tela de criação/edição de CPL no portal restrito~~ — **feito nesta
   sessão**: `/painel/cpls`, restrito a administrador (ver README).
3. ~~Remapeamento manual de colunas na importação de planilha~~ — **feito
   nesta sessão**: fluxo em 2 passos (upload → conferir/ajustar mapeamento
   → confirmar), ver README e item 13 da seção "Ordem em que este projeto
   foi construído".
4. ~~Fonte Unicode para PDF em produção~~ — **resolvido no deploy**: em vez
   de bundlar o arquivo `.ttf` no repositório, o `Dockerfile` instala o
   pacote apt `fonts-dejavu-core` na imagem, que já entrega
   `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf` — caminho que
   `app/services/geracao_documentos.py` já procurava desde antes, então
   nenhum código mudou.
5. ~~Iniciar módulo de Projetos~~ — **RF-029 a RF-041, módulo inteiro
   completo** (itens 20 a 29 da seção "Ordem em que este projeto foi
   construído"): `DemandaProjeto` (RF-031), `Projeto`/portfólio
   (RF-032), plano de trabalho completo — informações básicas,
   impactos socioambientais, continuidade e escalabilidade
   (RF-033/034/035), RF-034 completo (`EtapaProjeto`, `MetaProjeto`,
   `IndicadorProjeto`, `RiscoProjeto`), RF-035 completo
   (`EquipeProjeto`, `OrigemRecursoProjeto`, `AquisicaoProjeto`,
   cronograma físico-financeiro em `EtapaProjeto`), RF-029/030
   completos (`EditalFomento`, submissão de projeto,
   `RecursoSubmissaoProjeto`), RF-036/037/038 completos
   (`AquisicaoProjeto` estendido, `CotacaoAquisicao`, `DesembolsoProjeto`),
   RF-039/040 completos (`marco` em `EtapaProjeto`, `EntregaProjeto`
   com aprovação, `AlteracaoPlanoProjeto` com decisão via
   `PAPEIS_GESTAO`, `evidencia_documento_id` em `RiscoProjeto`) e
   RF-041 completo (relatório de execução, relatório financeiro e
   dossiê de evidências em PDF, `app/services/projeto.py`, sem
   entidade nova), em `/painel/projetos`.
6. ~~Deploy na VPS Hostinger~~ — **feito nesta sessão** (numa sessão
   anterior a esta), ver seção "Deploy em produção" abaixo para todos os
   detalhes (como foi feito, segredos, como reimplantar).
7. ~~Trilha de auditoria: visão global e paginação~~ — **feito nesta
   sessão**: (a) visão "global" (`/painel/auditoria/global`,
   `GET /api/auditoria/global`), restrita a `ADMINISTRADOR_PLATAFORMA`,
   pra eventos sem CPL resolvível (login, criação de `Usuario`/`Pessoa`/
   `CPL` em si); (b) paginação de verdade (`offset`/página, com total via
   `X-Total-Count` na API e "página X de Y" com anterior/próxima na web) —
   ver item 14 da seção "Ordem em que este projeto foi construído".
   Segue pendente, sem relação com este trabalho: `DELETE` não é exposto
   em nenhum endpoint do sistema hoje, então a captura de EXCLUSAO nunca
   roda em uso real — foi testada diretamente via sessão SQLAlchemy num
   script ad-hoc, não através de um endpoint HTTP real.
8. ~~RF-046/047: qualificação, novos empregos, sustentabilidade,
   certificações, digitalização~~ — **feito**: ver item 15 da seção "Ordem
   em que este projeto foi construído" para os detalhes (campos novos em
   `DiagnosticoCadastral`, `DiagnosticoCadastralHistorico` para "novos
   empregos", os 3 pontos de escrita atualizados). RF-048 ganhou também
   **relatório de recadastramento** (item 16), **relatório anual**
   (item 18), **relatório de comissão + relatório de impacto** (item
   19) e **relatório de execução/financeiro/dossiê de evidências de
   projeto** (item 29, RF-041) — **RF-048 está completo, todos os 6
   tipos**; o requisito não descreve um formato próprio pra "de
   projeto" além do que RF-041 já pede, então não houve um 7º tipo a
   construir. RF-045 nesta época só cobria governança/planejamento/
   cadastro — completo desde os itens 30/31 (projetos/finanças e
   maturidade, ver seção "O que falta", item 12).
9. ~~Maturidade e reconhecimento: limitações conhecidas~~ — "habilitação
   jurídica" (RF-027) e "simular cenários" (RF-026) **feitos**, ver item
   35 da seção "Ordem em que este projeto foi construído". Segue como
   limitação deliberada (não pendência): validade/versão de evidência
   (RF-025) dependem do versionamento que `Documento` já tem, não algo
   modelado à parte para maturidade.
10. ~~Notificações automáticas (RF-049)~~ — **feito**: reunião próxima,
    tarefa/meta com prazo vencendo, documento perdendo validade e
    recadastramento de CPL vencendo — ver item 17 da seção "Ordem em que
    este projeto foi construído". Sem canal de e-mail/push (só dentro do
    sistema) e sem agendador (varredura sob demanda) — ambos recortes de
    escopo deliberados, não pendências.
11. ~~RF-053 (exportação XLSX/CSV) e RF-045 (painel agregado de
    projetos)~~ — **feito**: ver item 30 da seção "Ordem em que este
    projeto foi construído". Exportação de entidades+diagnóstico
    simétrica à importação (RF-013), testada com round-trip real; card
    de portfólio/financeiro/execução agregados de todos os projetos de
    uma CPL no dashboard de indicadores. Segue pendente, sem relação com
    este trabalho: exportação de outras listagens (projetos, documentos,
    auditoria).
12. ~~Painel de maturidade (resto do RF-045)~~ — **feito**: ver item 31
    da seção "Ordem em que este projeto foi construído". Reaproveitou
    `resumo_recadastramento()` (já existia desde o RF-048), sem nenhuma
    agregação nova — só um card a mais no dashboard de indicadores.
    **RF-045 está completo**: os cinco painéis do requisito (governança,
    planejamento/cadastro, projetos, finanças, maturidade) existem no
    mesmo dashboard consolidado por CPL. As limitações conhecidas do
    módulo de Maturidade em si (item 9 acima — habilitação jurídica,
    simular cenários, validade/versão de evidência) não têm relação com
    o painel e seguem como estavam.
13. ~~RF-017: anexos de arquivo em reuniões~~ — **feito**: ver item 32
    da seção "Ordem em que este projeto foi construído". Zero entidade
    nova, zero migração — reaproveitou `Documento.reuniao_id`, que já
    existia desde a geração de ata em PDF (RF-043). De brinde, corrigida
    a marcação desatualizada do RF-019 (alertas automáticos de tarefa já
    existiam via RF-049, só a documentação estava desatualizada).
    **Com isso, RF-015 a RF-020 (módulo de Governança) estão completos.**
14. ~~RF-004: recuperação de senha e MFA~~ — **feito**: ver item 33 da
    seção "Ordem em que este projeto foi construído". Duas decisões de
    escopo tomadas com o usuário antes de codar (canal de recuperação =
    e-mail de verdade; provedor = SMTP genérico). Token de uso único +
    SMTP genérico (`app/services/email.py`, sem provedor embutido) pra
    recuperação; TOTP com ativação em 2 passos + 8 códigos de backup pra
    MFA; login web em 2 etapas (cookie pendente que `get_current_user`
    rejeita explicitamente, nunca aceito como sessão — bug de segurança
    pego antes de testar, ver item 33). De brinde: `CampanhaConvite.token`
    (RF-012), que nunca tinha sido redigido na auditoria, passou a ser.
    **Pendência real, não de código**: variáveis `SMTP_*` em produção
    (`.env.prod`) ainda vazias — `/esqueci-senha` vai 500 em produção
    até serem preenchidas com credenciais reais.
15. ~~RF-010: produtos, serviços, tecnologias, canais digitais e
    capacidade produtiva~~ — **feito**: ver item 34 da seção "Ordem em
    que este projeto foi construído". `OfertaEntidade` (tabela nova),
    `Entidade.canais_digitais` (campo órfão desde o RF-006/008, nunca
    tinha schema/rota/UI — descoberto e corrigido nesta fatia), e
    `DiagnosticoCadastral.capacidade_produtiva` (novo, nos 3 pontos de
    escrita de sempre, e automaticamente exportável pelo RF-053 sem
    código extra). Nova tela de detalhe de entidade
    (`/painel/cadastro/entidades/{id}`), que não existia antes.
16. ~~RF-014: máscaras + validade temporal~~ e ~~RF-003: requisitos de
    habilitação parametrizáveis~~ — **feito**: ver item 36 da seção
    "Ordem em que este projeto foi construído". `app/services/
    validadores.py` novo (CNPJ/CPF por dígito verificador, UF pela lista
    fechada), aplicado nos 3 pontos de escrita de sempre; validade
    temporal do diagnóstico é função pura, sem campo novo no banco.
    `RequisitoHabilitacaoEdital` fecha a peça de RF-003 que ainda
    faltava (a marcação de "depende do módulo de Maturidade" estava
    desatualizada — editais já eram parametrizáveis via UI desde o
    RF-024). **Pendência real, não de código**: nenhuma — item 14 acima
    (SMTP em produção) é a única pendência de configuração aberta no
    projeto.
17. ~~RF-043: pacote de submissão com índice e checklist~~ e ~~RNF-012:
    observabilidade~~ — **feito**: ver item 37 da seção "Ordem em que
    este projeto foi construído". Pacote de submissão junta habilitação
    jurídica (RF-027, contra o template do RF-003) e avaliação de
    maturidade de uma CPL perante um edital num PDF só; DOCX
    deliberadamente fora de escopo. Observabilidade: logs estruturados,
    métricas em memória, `RegistroFalha`, alerta por limiar e painel de
    saúde — sem infraestrutura externa nova. Ver item 17 de "Armadilhas
    já resolvidas" pro bug de log duplicado pego e corrigido nesta
    fatia (`@app.exception_handler(Exception)` + `BaseHTTPMiddleware`).
    **Pendência real, não de código**: nenhuma nova — SMTP em produção
    (item 14) segue sendo a única, e agora também afeta o alerta por
    e-mail do RNF-012 (mesmo mecanismo, mesma pendência).
18. ~~RF-050: eventos, capacitações, mentorias, missões técnicas~~ e
    ~~RF-051: biblioteca de conhecimento~~ — **feito**: ver item 38 da
    seção "Ordem em que este projeto foi construído". `Evento`/
    `InscricaoEvento` reaproveitam o raciocínio de `Edital` (global vs.
    local de uma CPL) e de `Presenca`/`MembroOrgao` (quem gere
    inscreve); inscrição/presença/avaliação viraram um único registro
    por pessoa+evento, decisão deliberada de não normalizar em três
    tabelas. `RecursoBiblioteca` é conteúdo global (sem `cpl_id`), com
    armazenamento próprio (`salvar_arquivo_biblioteca`) em vez de
    reaproveitar `Documento` (que exige uma CPL). **Pendência real, não
    de código**: nenhuma nova — SMTP em produção (item 14) segue sendo a
    única pendência de configuração aberta. Do documento de requisitos,
    seguem ❌ pendentes nesta altura (não candidatos óbvios pra próxima
    fatia, cada um depende de escopo/infra que ainda não existe): RF-011
    (georreferenciamento), RF-052 (matchmaking), RF-054 (integrações
    externas), RF-055 (portal público expandido) e RF-057 (IA
    assistiva, fora do MVP por definição).
19. ~~RF-052: matchmaking de inovação~~ e ~~RF-054: integrações
    externas~~ — **feito**: ver item 39 da seção "Ordem em que este
    projeto foi construído". `MatchInovacao` reaproveita
    `DemandaProjeto`/`OfertaEntidade` já existentes pra fechar o meio do
    fluxo F09; a conversão demanda→projeto já existia. RF-054 ficou
    deliberadamente parcial: consulta pública de CNPJ (BrasilAPI) e
    feed de BI implementados de verdade; assinatura eletrônica e
    "sistemas institucionais" dependem de escolher um provedor
    específico (decisão de negócio, não técnica) — ver item 18 de
    "Armadilhas já resolvidas" pro gotcha de User-Agent bloqueado pego
    nesta fatia. **Pendência real, não de código**: nenhuma nova — SMTP
    em produção (item 14) segue sendo a única pendência de configuração
    aberta, mais a escolha de provedor de assinatura
    eletrônica/sistemas institucionais citada acima (decisão externa,
    não uma tarefa de código pendente). Do documento de requisitos,
    seguem ❌ pendentes: RF-011 (georreferenciamento), RF-055 (portal
    público expandido) e RF-057 (IA assistiva, fora do MVP por
    definição) — os três restantes depois desta fatia.
20. ~~RF-011: georreferenciamento e mapa da cadeia~~ e ~~RNF-011:
    manutenibilidade (testes automatizados + CI)~~ — **feito**: ver item
    40 da seção "Ordem em que este projeto foi construído".
    `Entidade.latitude`/`longitude` opcionais, geocodificados via
    Nominatim/OpenStreetMap ou definidos manualmente; mapa Leaflet por
    CPL com marcador colorido por tipo de entidade — "relações da
    cadeia" ficou por fazer de propósito, dependendo de `EntidadeElo`
    (RF-009) ganhar rota de CRUD própria primeiro. 43 testes automatizados
    (pytest, banco Postgres isolado por SAVEPOINT, 49% de cobertura),
    ruff limpo e CI (`.github/workflows/ci.yml`, GitHub Actions) rodando
    lint + testes a cada push/PR. **Pendência real, não de código**:
    nenhuma nova — SMTP em produção (item 14) segue sendo a única
    pendência de configuração aberta. Do documento de requisitos, seguem
    ❌ pendentes: RF-055 (portal público expandido) e RF-057 (IA
    assistiva, fora do MVP por definição) — os dois únicos restantes.
    CD (implantação automática em produção) não entrou neste
    fechamento — reimplantação segue manual via `deploy.sh`.
21. ~~RF-055: portal público de transparência~~ — **feito**: ver item 41
    da seção "Ordem em que este projeto foi construído". `/cpls`
    (lista) e `/cpls/{id}` (detalhe: governança, agenda, resultados e
    projetos autorizados), sem autenticação — cada seção reaproveita
    agregação já existente (`resumo_governanca`/`resumo_cadastral`) ou
    filtra pra excluir dado pessoal/ainda-não-decidido
    (`estrutura_governanca_publica`, `agenda_publica`,
    `projetos_autorizados`, todas novas). **Pendência real, não de
    código**: nenhuma nova — SMTP em produção (item 14) segue sendo a
    única pendência de configuração aberta. **Do documento de
    requisitos original, só resta RF-057** (assistência de IA),
    declaradamente fora do MVP — é o único requisito funcional que
    ainda não foi endereçado de alguma forma (implementado, parcial por
    decisão de negócio, ou escopo deliberadamente adiado).
22. ~~RF-057: assistente de IA~~ — **feito**: ver item 42 da seção
    "Ordem em que este projeto foi construído". Provedor Anthropic
    (Claude), decisão do usuário via `AskUserQuestion`; botão no
    dashboard de indicadores de uma CPL (`PAPEIS_GESTAO`) gerando
    síntese/verificação de consistência/lacunas sugeridas sobre os
    agregados já existentes, sempre rotulado "revisão humana
    obrigatória", nunca persistido. **Pendência real, não de código**:
    `ANTHROPIC_API_KEY` ainda não existe em produção — mesma natureza da
    pendência de SMTP (item 14); até lá, o botão fica desabilitado, sem
    quebrar nada. **Com isso, todo requisito funcional (RF) do documento
    de requisitos original foi endereçado de alguma forma.** O que resta
    no projeto agora são só RNFs de maturidade organizacional (RNF-002
    privacidade formal, RNF-005 continuidade/backup, RNF-013 qualidade
    de dados, RNF-015 retenção) e o fluxo F01 (adesão de membro por
    autoatendimento) — nenhum dos dois um RF numerado.
23. ~~F01: fluxo de autoatendimento (adesão de membro)~~ — **feito**: ver
    item 43 da seção "Ordem em que este projeto foi construído".
    Formulário público de solicitação (cadastro + consentimento LGPD) →
    tela de gestão pra validar → aprovar cria/reaproveita `Entidade`
    (por CNPJ/CPF, RN-003), vincula à CPL e classifica o elo
    (`EntidadeElo`, RF-009, ganhou rota de escrita pela primeira vez) —
    "convite" ficou sem token dedicado, é a mesma URL pública
    compartilhada por quem convida. **Pendência real, não de código**:
    nenhuma nova — `ANTHROPIC_API_KEY` (item 22) segue sendo a única
    pendência de configuração aberta. **Com isso, tanto todo RF quanto o
    único fluxo de autoatendimento do modelo conceitual (F01) estão
    endereçados.** O que resta no projeto são só RNFs de maturidade
    organizacional — RNF-002 (privacidade formal/LGPD como mecanismo
    genérico, não só no fluxo de adesão), RNF-005 (backup automático),
    RNF-013 (dicionário de dados/deduplicação/qualidade) e RNF-015
    (retenção) — nenhum é um requisito funcional numerado, todos são
    trabalho transversal de maturidade organizacional, não uma feature
    isolada de implementar.
24. ~~SMTP em produção (RF-004)~~ — **feito**: ver item 44 da seção
    "Ordem em que este projeto foi construído". `.env.prod` configurado
    com o Titan Mail do Hostinger (`smtp.hostinger.com:587`, STARTTLS,
    caixa `no-reply@dedev.cloud`) + `APP_BASE_URL`; confirmado com um
    `POST /api/auth/esqueci-senha` real contra produção (200, sem
    traceback). Essa era a única pendência de configuração citada desde
    o item 14 — daqui pra frente, "pendência de SMTP" nos itens
    anteriores desta lista é histórico, não estado atual.
25. ~~`ANTHROPIC_API_KEY` em produção (RF-057)~~ — **feito**: ver item 45
    da seção "Ordem em que este projeto foi construído". Configurar a
    chave em si foi rápido (mesmo padrão do SMTP), mas a primeira
    chamada real contra a API achou dois bugs de verdade que nenhum
    teste mockado pegaria — `ThinkingBlock` sem `.text` (corrigido
    desligando extended thinking + selecionando bloco por tipo) e
    resposta envolvida em cerca de código markdown (corrigido removendo
    a cerca antes do `json.loads`, não insistindo só no prompt).
    Confirmado com chamada real de ponta a ponta antes do redeploy final.
    **Com isso, não resta nenhuma pendência de configuração conhecida em
    produção** — todo RF, o fluxo F01 e as duas credenciais que
    dependiam de decisão externa (SMTP, IA) estão resolvidos. O que
    resta no projeto são só os RNFs de maturidade organizacional
    (RNF-002, RNF-005, RNF-013, RNF-015), que não são pendência de
    configuração nem feature isolada — são trabalho transversal.

## Deploy em produção

Feito nesta sessão. **https://sigcpl.dedev.cloud** está no ar, na mesma VPS
Hostinger que já hospeda `rh-nepen`/`n8n`/`cervejeira` do usuário
(`srv1206123.hstgr.cloud`, 72.62.104.149, VM id `1206123` nas ferramentas
MCP `hostinger-*`).

**Como foi feito** (replicando o padrão exato do `rh-nepen`, sem inventar
um novo):
1. DNS: registro `A` `sigcpl` → `72.62.104.149` criado via MCP
   `hostinger-dns` (`DNS_updateDNSRecordsV1`, `overwrite: false` — só
   adiciona, não mexe nos registros existentes do domínio).
2. Descobri que já existe **acesso SSH root de sessões anteriores**:
   `~/.ssh/rh_nepen_hostinger` (chave privada) +
   `~/.ssh/config` com o host `rh-nepen-hostinger` apontando pra mesma VPS.
   **Não criei chave nova nem toquei em `VPS_setRootPasswordV1`** — reaproveitei
   o que já existia. Testado com
   `ssh rh-nepen-hostinger "whoami && docker --version"` antes de qualquer
   mudança.
3. Inspecionei `/opt/rh-nepen/` (via SSH, só leitura) pra copiar o padrão:
   `Dockerfile.prod` (`python:3.12-slim`, build direto sem registry),
   `docker-compose.prod.yml` com rede `internal` (db↔backend) + rede
   externa `n8n_default` (onde o Traefik do projeto `n8n` escuta), labels
   `traefik.http.routers.*` com `Host()`, `certresolver=mytlschallenge`.
   Reaproveitei essa mesma rede/resolver — **não criei Traefik novo nem
   mexi no do `n8n`**.
4. Criei `Dockerfile` e `docker-compose.prod.yml` na raiz do projeto local
   (arquivos novos, não confundir com o `docker-compose.yml` de dev que
   continua intocado — só sobe o Postgres local).
5. Gerei segredos de produção (`SECRET_KEY`, senha do Postgres) via
   `secrets.token_urlsafe` local e escrevi `/opt/sigcpl/.env.prod`
   **diretamente na VPS via SSH heredoc** (`chmod 600`, dono `root`) — o
   texto dos segredos nunca foi salvo em disco local em nenhum momento.
6. Copiei o código pra `/opt/sigcpl/` via `tar czf - ... | ssh ... "tar xzf -"`
   (não há `rsync` disponível no ambiente local Windows/git-bash) —
   excluindo `.venv/`, `uploads/`, `__pycache__/`, `.git/`, `.env*`.
7. `ssh ... "cd /opt/sigcpl && set -a && source .env.prod && set +a && \
   docker compose -f docker-compose.prod.yml up -d --build"` — o `CMD` do
   `Dockerfile` roda `alembic upgrade head` antes do `uvicorn`, então as 6
   migrações já aplicadas em dev rodaram sozinhas em produção também.
8. Validado: `docker ps` mostra `sigcpl_db` (healthy) e `sigcpl_backend`
   (up); `https://sigcpl.dedev.cloud/api/saude`, `/login`, `/`, `/docs`
   todos `200`; certificado TLS confirmado como Let's Encrypt de verdade
   (`openssl s_client` — `issuer=Let's Encrypt`, não self-signed).

**Onde as coisas vivem na VPS:**
- Código: `/opt/sigcpl/` — cópia de arquivo via `tar`+`ssh`, não é um clone
  git (o repositório local existe desde esta sessão, mas não tem remoto, e
  o deploy não passa por ele — reimplantar continua sendo o mesmo comando
  de cópia de arquivo, não um `git pull` na VPS).
- Segredos: `/opt/sigcpl/.env.prod` (só na VPS, `chmod 600`, nunca esteve
  neste repositório nem em texto puro no disco local).
- Volumes Docker nomeados: `sigcpl_pgdata` (dados do Postgres) e
  `sigcpl_uploads` (repositório de documentos, RF-042) — sobrevivem a
  `docker compose down`/redeploys, só some com `docker volume rm` explícito.

**Como reimplantar depois de mudar código** — comandos completos na seção
"Infraestrutura de implantação — em produção" do `README.md` (não repito
aqui pra não desincronizar as duas cópias).

**Válvula de bootstrap: já fechada.** Criei o primeiro administrador
(`admin@sigcpl.dedev.cloud`, senha gerada e entregue ao usuário no chat
desta sessão, não repetida aqui) logo após validar que o deploy respondia
— confirmado com um segundo usuário de teste tentando se autoconceder
`administrador_plataforma` e recebendo `403`. Se for criar mais contas
administrativas em produção, use esse primeiro admin pra conceder o papel
via `POST /api/usuarios/{id}/papeis` (a válvula não abre de novo).

## Decisões que são do usuário, não seu

Antes de implementar algo que dependa de uma dessas respostas, pergunte —
não assuma (ver seção "Decisões pendentes" no README e no documento de
requisitos):

- Multi-CPL desde já ou só a CPL Autopeças por enquanto? (o modelo já
  suporta multi-CPL, mas o *processo* real pode ser só uma por um tempo)
- Quem é a controladora dos dados (LGPD) vs. operadora tecnológica?
- Estratégia de saída da "válvula de bootstrap" do RBAC (hoje: sem nenhum
  admin no sistema, qualquer autenticado pode virar admin) — **agora com
  urgência real**, já que o sistema está publicamente acessível em
  https://sigcpl.dedev.cloud, não só em ambiente local.
- A matriz de permissões RBAC atual é uma interpretação minha do documento
  (seção 6), não uma tabela oficial — especificamente se Conselho/Comitê
  deveria poder concluir deliberações (hoje só Gestão pode) e se Comissão
  Temática deveria ver declarações de impedimento (hoje só Gestão+Auditoria).

## Como verificar que está tudo funcionando (smoke test)

```bash
cd /c/Users/andlu/sig-cpl
docker compose up -d                    # sobe Postgres (porta 5433)
source .venv/Scripts/activate           # ou .venv\Scripts\activate no cmd/PowerShell
alembic current                          # deve mostrar 5bff0df723be (head)
uvicorn app.main:app --host 127.0.0.1 --port 8010 &
sleep 3
curl http://127.0.0.1:8010/api/saude    # {"status":"ok",...}
```

Depois, abra `http://127.0.0.1:8010/login` no navegador e entre com
`admin@atibaia-autopecas.sp.gov.br` / `trocar-senha-123`.
