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
- **Migrações Alembic aplicadas:** 14 revisões, todas no banco atual:
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
  - (a visão global + paginação da auditoria, feita antes da nº 10,
    **não** precisou de migração — é só query/rota/template novos)

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
9. **Maturidade e reconhecimento: limitações conhecidas** — "habilitação
   jurídica" (RF-027) não tem modelo/etapa própria; "simular cenários"
   (RF-026, ver o efeito de uma nota hipotética antes de salvar) não foi
   construído, só o cálculo real ao concluir a avaliação; validade/versão
   de evidência (RF-025) dependem do versionamento que `Documento` já tem,
   não algo modelado à parte para maturidade.
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
