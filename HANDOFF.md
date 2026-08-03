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
- **Migrações Alembic aplicadas:** 10 revisões, todas no banco atual:
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
  - (a visão global + paginação da auditoria, feita antes desta, **não**
    precisou de migração — é só query/rota/template novos)

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
5. **Restante da Fase 2** — plano de trabalho, orçamento, cotações e
   submissões (RF-029 em diante) dependem do módulo de Projetos, ainda não
   iniciado.
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
   empregos", os 3 pontos de escrita atualizados). RF-048 ganhou também o
   **relatório de recadastramento** — ver item 16. Seguem pendentes,
   sem relação com este trabalho: anual/comissão/projeto/impacto do
   RF-048 (comissão/projeto dependem de módulos ainda não construídos ou
   não dedicados). RF-045 só cobre
   governança/planejamento/cadastro — maturidade/projetos/finanças/
   impacto territorial ficam pra quando esses módulos tiverem painel
   próprio (maturidade já existe como módulo desde esta sessão, mas sem
   um "painel" resumo dedicado — só as próprias telas de avaliação, ver
   item 9).
9. **Maturidade e reconhecimento: limitações conhecidas** — "habilitação
   jurídica" (RF-027) não tem modelo/etapa própria; "simular cenários"
   (RF-026, ver o efeito de uma nota hipotética antes de salvar) não foi
   construído, só o cálculo real ao concluir a avaliação; validade/versão
   de evidência (RF-025) dependem do versionamento que `Documento` já tem,
   não algo modelado à parte para maturidade.

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
