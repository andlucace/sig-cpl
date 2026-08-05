# SIG-CPL — Sistema Integrado de Gestão de Cadeia Produtiva Local

Esqueleto inicial da plataforma descrita no *Documento de Requisitos Macros*
(referência: Programa SP Produz; projeto de referência: CPL Autopeças de
Atibaia/SP — a transcrição completa do documento, com status de
implementação por requisito, está em `docs/requisitos_macros.md`). Este
repositório cobre **100% da Fase 1 (MVP)** e o início da **Fase 2** do
roadmap (com recortes de escopo documentados requisito a requisito):
fundação técnica, modelos de dados centrais, e os módulos de Identidade e
Acesso, Governança, Planejamento Estratégico, Cadastro dinâmico (campanhas
+ importação de planilha), Documentos (repositório + geração de ata em
PDF), Trilha de auditoria, Indicadores e relatórios (catálogo com série
histórica, painéis consolidados, relatório executivo em PDF) e Maturidade
e reconhecimento (editais/critérios, avaliação com evidências e lacunas,
decisão de nível, recadastro bienal com alertas) funcionando.
Projetos/fomento, Comunicação e Integrações existem como routers-stub,
prontos para receber implementação incremental.

## Stack

- **API/Backend:** FastAPI + SQLAlchemy 2.x + Alembic
- **Banco de dados:** PostgreSQL
- **Frontend:** Server-rendered com Jinja2 + HTMX (sem build de JS separado)
- **Auth:** JWT (cookie httponly para o portal restrito, Bearer para API/integrações — RF-053)

## Estrutura

```
app/
  core/       configuração (.env), segurança (hash/JWT), dependências de auth
  db/         base declarativa e sessão do SQLAlchemy
  models/     entidades de domínio (CPL, Entidade, Pessoa, Usuário, enums)
  schemas/    contratos Pydantic da API
  api/routes/ endpoints REST (/api/...), incluindo stubs dos módulos futuros
  web/        rotas HTML (portal restrito e portal público)
  templates/  templates Jinja2
  static/     CSS (sem dependência de build)
alembic/      migrações do banco
docker-compose.yml   Postgres local para desenvolvimento
```

## Modelos implementados nesta fase

Cobrem a seção 10 (Modelo conceitual de dados) parcialmente — CPL, Entidade,
Pessoa e Usuário/Papel — o suficiente para o módulo 1 (Identidade e acesso)
e o módulo 2 (Cadastro e cadeia) do documento:

- `CPL` (RF-001, RN-004, RN-005)
- `Entidade` + `EntidadeCPL` + `EntidadeElo` (RF-006, RF-008, RF-009, RN-003)
- `Pessoa` + `PessoaVinculo` (RF-007)
- `Usuario` + `UsuarioPapel` (RF-004, RF-005)

O bloco **Governança** do modelo conceitual também foi implementado
(RF-015 a RF-020):

- `OrgaoGovernanca` — conselho, câmara, comissão temática ou grupo de
  trabalho, com competências, quórum mínimo e periodicidade parametrizáveis.
- `MembroOrgao` — composição/mandato (pessoa, função, vigência).
- `Reuniao` — convocação, pauta, status e ata.
- `Presenca` — presença de cada membro na reunião.
- `Deliberacao` — decisão tomada, quórum necessário, responsável, prazo e
  evidência de execução.
- `VotoRegistro` — voto de cada membro por deliberação (inclui `impedido`
  como opção, ligado ao motivo do conflito de interesses).
- `TarefaGovernanca` — tarefa/plano de ação decorrente de uma deliberação,
  com responsável, prazo e status (RF-019).
- `DeclaracaoImpedimento` — declaração de conflito de interesses avulsa,
  não necessariamente ligada a um voto (RF-020).

O fluxo F03 do documento (convocação → pauta → presença/quórum →
deliberação → ata → tarefas → acompanhamento) está coberto ponta a ponta
tanto pelos endpoints em `/api/governanca/...` quanto pela UI HTMX em
`/painel/governanca`:

- `/painel/governanca` — seleciona a CPL (lista simples; criar CPL ainda só
  via API).
- `/painel/governanca/cpls/{cpl_id}` — lista órgãos da CPL + form de criação.
- `/painel/governanca/orgaos/{orgao_id}` — membros (com cadastro rápido de
  pessoa embutido) e reuniões do órgão.
- `/painel/governanca/reunioes/{reuniao_id}` — pauta, presença, deliberações
  e encerramento com ata/quórum.
- `/painel/governanca/deliberacoes/{deliberacao_id}` — votos, resultado e
  tarefas decorrentes.
- `/painel/governanca/cpls/{cpl_id}/tarefas` — lista de tarefas da CPL com
  atualização de status inline (`hx-patch`).

As adições (membro, reunião, presença, deliberação, voto, tarefa) usam
`hx-post`/`hx-patch` retornando fragmentos HTML que são inseridos na lista
sem recarregar a página; forms cujo valor é sempre único por página (ata da
reunião, resultado da deliberação) substituem o card inteiro via
`hx-swap="outerHTML"`.

O bloco **Planejamento** do modelo conceitual também foi implementado
(RF-021 a RF-023):

- `PlanejamentoEstrategico` — um registro por ciclo (ex.: "2026-2027") com as
  seções narrativas do PEN: caracterização, histórico, mercado, inovação,
  impactos e internacionalização. As seções "cadeia" e "governança" citadas
  no RF-021 **não** são duplicadas como texto — já são cobertas por
  Entidade/Elo e pelo módulo de Governança.
- `DiagnosticoItem` — item de diagnóstico (RF-022): SWOT (força/fraqueza/
  oportunidade/ameaça) + problema prioritário, demanda e lacuna de elo.
- `ObjetivoEstrategico` — hub que agrega metas, iniciativas e indicadores de
  um objetivo, com prazo (curto/médio/longo), responsável e orçamento
  estimado (RF-023).
- `MetaEstrategica` — meta com tipo, valor-alvo, método de aferição, prazo,
  responsável e evidência, conforme RN-010.
- `IniciativaEstrategica` — ação concreta para viabilizar o objetivo.
- `IndicadorEstrategico` — indicador de acompanhamento (fórmula, meta,
  valor atual, periodicidade) — base para o catálogo mais amplo do RF-044.

`ObjetivoEstrategico.status`/`MetaEstrategica.status`/
`IniciativaEstrategica.status` reaproveitam o enum `StatusTarefa` já usado
em Governança (mesmo ciclo de vida: pendente/em andamento/concluída/
atrasada/cancelada) — decisão deliberada para não duplicar um enum
idêntico.

A UI HTMX em `/painel/planejamento` segue a mesma hierarquia de 3 níveis da
Governança — CPL → ciclo → objetivo:

- `/painel/planejamento` — seleciona a CPL.
- `/painel/planejamento/cpls/{cpl_id}` — lista ciclos + form de criação.
- `/painel/planejamento/{planejamento_id}` — seções narrativas (editáveis
  via form tradicional, não HTMX — atualiza 6 campos de uma vez), status do
  ciclo, diagnóstico e objetivos.
- `/painel/planejamento/objetivos/{objetivo_id}` — metas, iniciativas e
  indicadores, com status inline (`hx-post` + `hx-swap="outerHTML"`) e
  atualização de valor do indicador via mini-formulário inline.

RBAC reaproveita os mesmos grupos de papéis da Governança (`PAPEIS_GESTAO`,
`PAPEIS_GOVERNANCA_LEITURA`, `PAPEIS_GOVERNANCA_PARTICIPACAO`,
`PAPEIS_TAREFA_EXECUCAO`) — criar/editar é `PAPEIS_GESTAO`; diagnóstico é
`PAPEIS_GOVERNANCA_PARTICIPACAO` (colaborativo, como as deliberações);
atualizar status/valor de objetivo/meta/iniciativa/indicador é
`PAPEIS_TAREFA_EXECUCAO` + o responsável pessoal (mesma exceção usada em
`TarefaGovernanca`).

Os demais blocos do modelo conceitual (Maturidade, Projeto, Financeiro do
projeto, Evento e comunicação) ainda não têm tabelas — ficam para as
próximas fases do roadmap. Documento e Auditoria já foram implementados
(ver seções abaixo).

O bloco **Cadastro dinâmico** (RF-012 a RF-014, "Formulários e dados") foi
implementado como um recorte deliberado do requisito — não é um construtor
de formulário genérico (tipo Google Forms), e sim três peças que cobrem o
caso de uso citado no documento (a planilha "CPLS - FORMS.xlsx"):

- `DiagnosticoCadastral` — campos de pesquisa/diagnóstico da planilha
  original (atividades e produtos, diferenciais, faturamento, empregos,
  participação associativa, inovação, P&D, ODS, exportação, interesse em
  comissões), separados do cadastro básico de `Entidade` (RF-006/008) para
  não misturar dado cadastral com dado de pesquisa.
- `CampanhaCadastral` + `CampanhaConvite` — campanha de atualização
  cadastral (RF-012 "campanhas de atualização cadastral") que gera, por
  entidade convidada, um **link público com token** (`/atualizacao/{token}`)
  onde a empresa autoatualiza seus dados **sem precisar de login** — a
  entidade convidada não necessariamente tem conta de usuário no sistema.
- `ImportacaoLote` + `ImportacaoLinha` — importação de planilha CSV/XLSX
  (RF-013/014) com **mapeamento automático de colunas por nome** (dicionário
  de aliases em `app/services/importacao_entidades.py`), deduplicação por
  CNPJ, criação/atualização de `Entidade` + `DiagnosticoCadastral` +
  vínculo `EntidadeCPL`, e relatório por linha (criada/atualizada/erro) —
  a "trilha de origem" exigida pelo requisito.

Também foi adicionado, como pré-requisito, o endpoint de vínculo
`EntidadeCPL` que faltava desde o módulo de Cadastro/Governança
(`POST/GET /api/cpls/{cpl_id}/entidades`) — antes só existia o modelo, sem
rota alguma.

**Remapeamento manual de colunas** — a planilha real "CPLS - FORMS.xlsx"
citada no documento nunca foi anexada ao projeto (ver
`docs/requisitos_macros.md`), então o dicionário de aliases é uma
aproximação, não calibrada contra o arquivo real — e qualquer outra
planilha do usuário pode ter cabeçalhos que o dicionário simplesmente não
prevê. Em vez de tentar adivinhar todo cabeçalho possível, a importação
virou um **fluxo em dois passos**:
1. Upload salva o arquivo (mesmo mecanismo de armazenamento do
   repositório de Documentos, RF-042) e sugere um mapeamento automático —
   `ImportacaoLote.status = pendente_mapeamento`, nenhuma linha é
   processada ainda.
2. Tela de conferência (`/painel/cadastro/importacoes/{id}/mapear`)
   mostra, campo a campo, qual coluna foi sugerida (ou "— não mapear —"
   se nada bateu) — o usuário ajusta manualmente o que precisar antes de
   confirmar. Só aí as linhas são processadas de verdade, e o mapeamento
   efetivamente usado fica registrado em `ImportacaoLote.mapeamento_colunas`
   (trilha de origem também para o próprio mapeamento, não só para o
   resultado por linha).

`processar_planilha()` (1 passo, só mapeamento automático) continua
existindo no serviço para quem prefere pular a conferência manual.

**Exportação de entidades** (RF-053) — simétrica à importação acima: mesmo
cabeçalho (`CAMPOS_CONHECIDOS`, o nome canônico de cada campo, que
`mapear_colunas` já reconhece como alias de si mesmo), então um arquivo
exportado por aqui pode ser reimportado sem remapeamento manual — testado
ponta a ponta (exportar → reimportar → conferir que as 35 colunas mapeiam
sozinhas). `exportar_entidades()` + `gerar_csv_entidades()`/
`gerar_xlsx_entidades()` em `app/services/importacao_entidades.py`;
`GET /api/cadastro/cpls/{cpl_id}/exportar-entidades?formato=xlsx|csv` (e
botões em `/painel/cadastro/cpls/{cpl_id}`), RBAC `PAPEIS_GOVERNANCA_LEITURA`
(mesma exigência de qualquer leitura do módulo). CSV sai com BOM
(`utf-8-sig`) — sem isso o Excel abre acentuação corrompida em duplo-clique
direto no arquivo. Escopo desta fatia é só entidades/diagnóstico — outras
listagens do sistema (projetos, documentos, auditoria) não ganharam
exportação própria.

UI web: `/painel/cadastro` (seleciona CPL) → `/painel/cadastro/cpls/{id}`
(entidades vinculadas + campanhas + importações) →
`/painel/cadastro/importacoes/{id}/mapear` (conferir/ajustar mapeamento,
só para lotes pendentes) → `/painel/cadastro/importacoes/{id}` (relatório
por linha) e `/painel/cadastro/campanhas/{id}` (convites, com link/token
copiável). RBAC reaproveita `PAPEIS_GESTAO`/`PAPEIS_GOVERNANCA_LEITURA`
dos módulos anteriores; a rota pública de autopreenchimento não passa por
RBAC nenhum (é intencionalmente sem autenticação — a segurança vem do
token ser imprevisível e de uso único por convite, não de login).

O bloco **Documentos** (RF-042/043) foi implementado com escopo recortado
deliberadamente — repositório completo (RF-042), mas geração de documento
padronizado (RF-043) limitada a exportar a ata de uma reunião em PDF, não
um construtor genérico de "pacotes de submissão com índice e checklist"
(que dependeria do módulo de Editais/Reconhecimento da Fase 2, ainda
inexistente):

- `Documento` — classificação (`CategoriaDocumento`: ata, plano de
  trabalho, declaração, comprovante, relatório, outro), confidencialidade
  (`ConfidencialidadeDocumento`: público, interno, confidencial — RN-014),
  metadados de arquivo, versionamento (`versao` + `documento_anterior_id`
  encadeando versões), validade, aprovação/assinatura e retenção.
- **Armazenamento em disco**, não blob no banco — `arquivo_path` é relativo
  a `settings.uploads_dir` (`app/services/armazenamento.py`); em dev é uma
  pasta local (`uploads/`, no `.gitignore`), e a mesma estrutura funciona
  numa VPS bastando montar um volume persistente nesse caminho — não muda
  código, só o que está montado ali.
- **Geração de PDF** (`app/services/geracao_documentos.py`, biblioteca
  `fpdf2`) — a fonte core do fpdf2 (Helvetica) só cobre latin-1 e não tem
  travessão, então o serviço tenta registrar uma fonte TrueType Unicode de
  verdade (`app/static/fonts/DejaVuSans.ttf` se existir, senão caminhos
  comuns do Linux/Windows) e só cai para a normalização "lossy" em latin-1
  se nenhuma fonte for encontrada. Confirmado via rasterização real da
  página (PyMuPDF) — **não confie em `pypdf.extract_text()` para validar
  fontes TrueType embarcadas do fpdf2**: ele decodifica errado mesmo
  quando o PDF renderiza certinho (isso me enganou uma vez nesta sessão).
- Endpoint `POST /api/documentos/reunioes/{reuniao_id}/ata-pdf` (e botão
  "Gerar ata em PDF" na tela da reunião) gera o PDF e já cadastra o
  `Documento` automaticamente, ligado à reunião de origem.

Confidencialidade controla leitura: documentos `confidencial` só para
`PAPEIS_IMPEDIMENTO_LEITURA` (gestão + auditoria — mesmo grupo já usado
para `DeclaracaoImpedimento` em Governança); `publico`/`interno` seguem
`PAPEIS_GOVERNANCA_LEITURA` normal. UI web em `/painel/documentos`.

O bloco **Trilha de auditoria** (RF-056/RNF-003) foi implementado como
mecanismo **automático e transversal**, não como um log manual adicionado
endpoint a endpoint:

- `RegistroAuditoria` — um registro por evento: quem (`usuario_id`, nulo
  para tentativas de login com credencial errada), o quê (`acao`: criação,
  atualização, exclusão, login com sucesso/falha, download), em qual
  registro (`entidade_tipo` + `entidade_id`), de qual CPL (`cpl_id`,
  quando resolvível), valor anterior/novo em JSON e IP de origem.
  **Imutável por design**: não existe endpoint de alteração/exclusão para
  esta tabela.
- **Captura automática de criação/atualização/exclusão** — um listener de
  eventos do SQLAlchemy (`app/services/auditoria.py`, `before_flush` +
  `after_flush` na `Session`) intercepta qualquer INSERT/UPDATE/DELETE de
  qualquer modelo mapeado e grava o registro correspondente, sem exigir
  que cada endpoint chame uma função de log manualmente. Isso cobre os
  ~30 endpoints de escrita já existentes retroativamente, e cobre módulos
  futuros automaticamente (nenhuma instrumentação extra é necessária ao
  adicionar um novo modelo).
  - `UPDATE`: só os campos que de fato mudaram entram em
    `dados_anteriores`/`dados_novos` (via `history` do SQLAlchemy), não a
    linha inteira.
  - `CRIACAO`: colunas com `default=` (ex. `id`, `ativo`) só são
    preenchidas pelo SQLAlchemy quando o INSERT executa de fato — depois
    do `before_flush`. Por isso a serialização completa é adiada para
    `after_flush` (ver comentário no código; foi uma armadilha real desta
    sessão, documentada no `HANDOFF.md`).
  - Campos sensíveis (`hashed_password`) nunca são gravados, mesmo que o
    modelo mude no futuro (lista de redação em `_CAMPOS_REDIGIDOS`).
- **Eventos que não são uma escrita de linha** (login, download de
  arquivo) são registrados explicitamente via `registrar_evento()`, nos
  pontos de login (API `app/api/routes/auth.py` e web
  `app/web/routes_restrito.py`) e de download de documento (API e web em
  `app/api/routes/documentos.py`/`app/web/routes_documentos.py`).
- **Contexto de quem fez a ação** chega ao listener via `contextvars`
  (`app/core/audit_context.py`), populados por um middleware em
  `app/main.py` que decodifica o JWT da requisição (cookie ou Bearer) sem
  consultar o banco — mantém o middleware leve mesmo rodando em toda
  requisição.
- Leitura via `GET /api/auditoria/cpls/{cpl_id}` (filtros opcionais por
  `acao`/`entidade_tipo`, paginação de verdade via `offset`/`limite` —
  página de até 50 por padrão, 200 no máximo — com total no header
  `X-Total-Count`) e UI web em `/painel/auditoria`, com os mesmos filtros,
  um botão "ver" que expande valor anterior/novo em JSON, e controles de
  página anterior/próxima. RBAC: `PAPEIS_IMPEDIMENTO_LEITURA` (gestão +
  auditoria) — mesmo grupo restrito usado para documentos confidenciais e
  declarações de impedimento.
- **Visão global**: eventos sem CPL resolvível (login, criação de
  `Usuario`/`Pessoa`/`CPL` em si) ficam gravados com `cpl_id=None`; agora
  têm tela própria (`GET /api/auditoria/global`, `/painel/auditoria/global`,
  linkada a partir do seletor de CPL só para quem enxerga todas as CPLs)
  restrita a `PAPEIS_EDITAL_GESTAO` (= `ADMINISTRADOR_PLATAFORMA`). A
  consulta paginada/filtrada de ambas as visões compartilha um único
  helper, `consultar_registros()` em `app/services/auditoria.py`.

O bloco **Indicadores e relatórios** (RF-044 a RF-048) fecha a Fase 1/MVP.
Não introduz um módulo isolado — é uma camada de agregação sobre dados que
os outros módulos já coletam:

- `IndicadorEstrategico` ganhou `fonte` (RN-011: "fonte de dados") e
  `responsavel_id`; `IndicadorValorHistorico` é a série histórica de
  verdade (RF-044) — cada aferição fica preservada, não só o `valor_atual`
  mais recente. Registrar um novo valor (via `PATCH
  /api/planejamento/indicadores/{id}` ou o form de `/painel/indicadores/
  {id}/historico`) grava os dois: atualiza `valor_atual` **e** adiciona
  uma linha ao histórico — a mesma função de serviço
  (`app/services/indicadores.py::registrar_valor_indicador`) é chamada
  pelos dois endpoints, pra não divergir.
- **Catálogo consolidado** (`catalogo_indicadores`): todos os indicadores
  de uma CPL através de **todos** os ciclos de planejamento, não só o mais
  recente — é isso que torna RF-044 um "catálogo" e não só uma lista por
  objetivo.
- **Resumo cadastral** (`resumo_cadastral`, RF-046/047): agrega o que já é
  coletado via `DiagnosticoCadastral` (campanha de atualização cadastral,
  módulo de Cadastro dinâmico) — empresas vinculadas, empregos diretos/
  indiretos, distribuição de faturamento por faixa, % inovação/P&D/
  exportação/associativismo/qualificação/sustentabilidade/contatos
  internacionais/certificações, ODS e certificações mais citados,
  distribuição por nível de digitalização.
- **Novos empregos diretos (RF-046, "variação no tempo")**:
  `DiagnosticoCadastral` só guarda o valor atual (sobrescrito a cada
  resposta de campanha ou importação), então uma tabela nova,
  `DiagnosticoCadastralHistorico`, preserva um snapshot de
  `empregos_diretos`/`empregos_indiretos` a cada atualização — mesmo
  padrão de `IndicadorValorHistorico`. `resumo_cadastral()` soma, por
  entidade, o crescimento entre o snapshot mais antigo dentro dos últimos
  12 meses e o mais recente (quedas não abatem o total — é "empregos
  criados", não "saldo líquido"); precisa de ao menos 2 snapshots por
  entidade dentro da janela pra contar alguma coisa. `registrar_snapshot_
  diagnostico()` em `app/services/indicadores.py` é chamado pelos 3
  pontos de escrita do diagnóstico (API `PUT /api/cadastro/entidades/
  {id}/diagnostico`, formulário público de campanha, importação de
  planilha).
- **Qualificação, sustentabilidade, contatos internacionais, certificações
  e digitalização (RF-046/047)**: campos novos em `DiagnosticoCadastral`
  (booleano + descrição livre, mesmo padrão de `realiza_inovacao`/
  `descricao_inovacao`; certificações é lista separada por vírgula, mesmo
  padrão de `ods_relacionados`). Coletáveis pelos 3 pontos de escrita —
  o formulário público de campanha (`/atualizacao/{token}`) ganhou uma
  seção nova; a importação de planilha reconhece os cabeçalhos via
  `_ALIASES_CAMPO` em `app/services/importacao_entidades.py` (ajuste ali
  se a planilha real usar nomes diferentes — o remapeamento manual cobre
  o resto). De quebra, `participacao_associativa`/`entidades_associativas`
  também passaram a ser coletáveis pelo formulário público — já existiam
  no modelo e no resumo (`percentual_associativismo`) desde antes, mas
  nunca tinham sido expostos nesse formulário, então na prática nunca
  eram preenchidos por uma entidade respondendo à campanha.
- **Painéis** (RF-045): `resumo_governanca` e `resumo_planejamento`
  complementam o resumo cadastral acima, formando o dashboard de
  `/painel/indicadores/cpls/{cpl_id}`. Ganhou depois um card de
  **projetos e finanças** — `resumo_projetos_cpl()` em
  `app/services/projeto.py`, agregando todo o portfólio da CPL (não um
  projeto só, que já é coberto pelos relatórios do RF-041): contagem por
  estágio/prioridade, financeiro (previsto/desembolsado/saldo somados de
  todas as origens de recurso e desembolsos dos projetos da CPL) e
  execução (etapas/marcos/entregas/metas/riscos agregados). Só
  **maturidade** ainda não tem painel próprio — não foi priorizado ainda.
- **Relatório executivo em PDF** (RF-048) — dos seis tipos de relatório
  citados no requisito (executivo, anual, recadastramento, comissão,
  projeto, impacto), dois foram construídos até agora (ver item seguinte
  para o de recadastramento); decisão tomada com o usuário via
  `AskUserQuestion` antes de implementar, dado que comissão/projeto
  dependem de módulos que não existem e os demais não têm formato
  definido no documento de requisitos. Reaproveita a mesma infraestrutura
  da ata de reunião (`app/services/geracao_documentos.py` — a classe
  `_GeradorPDF`, antes `_GeradorAta`, foi generalizada pra servir aos
  dois): `POST /api/indicadores/cpls/{cpl_id}/relatorio-executivo` (e o
  botão equivalente em `/painel/indicadores`) gera o PDF e já cadastra
  como `Documento` (categoria `relatorio`), igual ao padrão da ata.
- **Relatório de recadastramento em PDF** (RF-048) — segundo tipo de
  relatório construído, escolhido por reaproveitar quase só dado que o
  módulo de Maturidade já mantém (nenhuma coleta nova): nível de
  maturidade vigente, data de reconhecimento e validade (RN-005, bienal),
  quantos dias faltam pro vencimento, lacunas da avaliação vigente
  (critérios abaixo da nota de corte, via `lacunas()` já existente) e o
  histórico completo de avaliações com pontuação/nível sugerido/nível
  decidido/parecer de cada uma. `resumo_recadastramento()` e
  `gerar_pdf_relatorio_recadastramento()` seguem o mesmo par
  serviço-formata-PDF do executivo. Gerado via
  `POST /api/maturidade/cpls/{cpl_id}/relatorio-recadastramento` (e botão
  equivalente em `/painel/maturidade/cpls/{cpl_id}`), RBAC `PAPEIS_GESTAO`
  — mesma regra do executivo.
- **Relatório anual em PDF** (RF-048) — terceiro tipo de relatório
  construído. Diferença central pro executivo: o executivo é o
  **acumulado desde sempre**; o anual é **"o que aconteceu num
  ano-calendário específico"** — reuniões realizadas, deliberações
  aprovadas, tarefas/metas concluídas, documentos gerados, indicadores
  atualizados e novos empregos diretos, todos filtrados pra dentro de
  `[1º de janeiro, 31 de dezembro]` do ano informado. `resumo_anual(db,
  cpl_id, ano)` em `app/services/indicadores.py`. "Concluída no ano"
  para tarefa/meta usa `updated_at` como aproximação — nenhum dos dois
  modelos guarda uma data de conclusão própria (recorte de escopo, não
  bug). "Novos empregos no ano" reaproveita a mesma lógica de
  `DiagnosticoCadastralHistorico` do resumo cadastral (RF-046), mas
  generalizada para aceitar um intervalo `[início, fim]` explícito em
  vez de só uma janela rolante de N dias
  (`_novos_empregos_diretos_periodo`, com `_novos_empregos_diretos`
  agora implementado por cima dela). Gerado via
  `POST /api/indicadores/cpls/{cpl_id}/relatorio-anual?ano=` (e um
  campo de ano + botão em `/painel/indicadores/cpls/{cpl_id}`), RBAC
  `PAPEIS_GESTAO` — mesma regra dos outros dois relatórios. Testado
  gerando o mesmo relatório para dois anos diferentes (2026, com dados
  reais, e 2025, sem nenhum) e confirmando via PDF rasterizado que os
  números realmente mudam — não é só o mesmo acumulado com um título
  diferente.
- **Relatório de comissão em PDF** (RF-048) — quarto tipo de relatório,
  escopado a **um único órgão de governança** (`resumo_orgao(db,
  orgao_id)`, novo) em vez de toda a CPL como os anteriores. Serve
  qualquer `TipoOrgao` (conselho, câmara, comissão temática, grupo de
  trabalho) — o requisito fala especificamente de "comissão", mas não
  há razão técnica pra restringir a esse tipo. Mostra membros ativos,
  reuniões, deliberações e tarefas — mas só as tarefas **ligadas a uma
  deliberação daquele órgão** (`TarefaGovernanca.deliberacao_id`);
  tarefas soltas da CPL como um todo não são atribuíveis a um órgão
  específico. Gerado via
  `POST /api/governanca/orgaos/{orgao_id}/relatorio-comissao` (e botão
  em `/painel/governanca/orgaos/{orgao_id}`), RBAC `PAPEIS_GESTAO`.
  Testado confirmando que o relatório do "Conselho Gestor" não vaza
  reuniões/deliberações dos outros 3 órgãos da mesma CPL (ex.:
  "Comissão de Inovação") — o escopo é de verdade por-órgão, não
  por-CPL com um filtro cosmético.
- **Relatório de impacto em PDF** (RF-048/RF-047) — quinto tipo,
  o mais barato de construir: **reaproveita `resumo_cadastral()`
  (RF-046/047) sem nenhuma agregação nova**, só reapresenta um recorte
  focado em impacto socioeconômico/socioambiental (empregos,
  exportação, qualificação, sustentabilidade, ODS) e inovação/
  competitividade (P&D, certificações, digitalização), omitindo as
  seções de governança/planejamento/catálogo que o executivo tem.
  Gerado via `POST /api/indicadores/cpls/{cpl_id}/relatorio-impacto`
  (e botão em `/painel/indicadores/cpls/{cpl_id}`), RBAC
  `PAPEIS_GESTAO`.
- **Relatório de execução, relatório financeiro e dossiê de evidências
  de projeto em PDF** (RF-041/RF-048) — os três tipos de relatório do
  RF-041, escopados a um único `Projeto` em vez de uma CPL inteira
  (mesmo raciocínio de `resumo_orgao`/relatório de comissão). Fecham
  também o tipo "de projeto" que RF-048 tinha deixado em aberto — o
  requisito não descreve um formato próprio pra "relatório de projeto"
  além do que RF-041 já pede, então não há um sétimo tipo separado a
  construir. Dados vêm de três funções novas em `app/services/projeto.py`
  (`resumo_execucao_projeto`, `resumo_financeiro_projeto`,
  `dossie_evidencias_projeto`); o dossiê de evidências agrega, sem criar
  nenhum vínculo novo, os quatro pontos onde o módulo já linka
  documentos (cotação, comprovante de desembolso, evidência de
  mitigação de risco, documento de entrega). Gerados via
  `POST /api/projetos/{projeto_id}/relatorio-execucao`,
  `/relatorio-financeiro` e `/relatorio-dossie-evidencias` (e botões em
  `/painel/projetos/{projeto_id}`), RBAC `PAPEIS_GESTAO` — mesma
  convenção de todo relatório gerado no sistema, não `PAPEIS_PROJETO_GESTAO`.
- **RF-048 está completo** — os seis tipos de relatório citados no
  requisito (executivo, recadastramento, anual, comissão, impacto, de
  projeto) existem.
- RBAC: leitura (catálogo, resumo, painel) usa `PAPEIS_GOVERNANCA_LEITURA`;
  gerar relatório executivo usa `PAPEIS_GESTAO` (mesma exigência da ata);
  registrar novo valor de indicador usa `PAPEIS_TAREFA_EXECUCAO` **ou** o
  responsável pessoal do indicador (`Usuario.pessoa_id ==
  IndicadorEstrategico.responsavel_id`) — mesma exceção já usada em
  objetivo/meta/iniciativa, estendida ao indicador agora que ele também
  tem `responsavel_id`.

O bloco **Maturidade e reconhecimento** (RF-024 a RF-028, Fase 2 do
roadmap) foi implementado com escopo alinhado com o usuário via
`AskUserQuestion` antes de começar — em especial, se o fluxo de recursos
(apelação) entraria já nesta etapa (sim) e se edital/critérios são
compartilhados entre CPLs em vez de configuração por CPL (sim, RN-006):

- `Edital` + `CriterioMaturidade` (RF-024/RN-006) — **globais**, geridos só
  por `ADMINISTRADOR_PLATAFORMA` (chamado com `cpl_id=None` no
  `verificar_papel`, já que não há CPL nenhuma envolvida em criar/editar
  um edital). Critério tem dimensão (organização/governança/planejamento/
  dimensão/diversidade/impacto, enum `DimensaoMaturidade`), peso e nota de
  corte próprios.
- `Avaliacao` + `AvaliacaoCriterio` (RF-025/026) — avaliação de uma CPL
  contra um edital; nota e evidência por critério (evidência reaproveita
  o repositório de Documentos, RF-042, em vez de um mecanismo de anexo
  próprio). Ao **concluir** uma avaliação, `pontuacao_calculada` (média
  ponderada das notas) e `nivel_sugerido` (comparado aos limiares do
  edital) são calculados automaticamente; **lacunas** são os critérios
  cuja nota ficou abaixo da própria nota de corte.
- **RN-016 é reforçada em código, não só em política**: concluir a
  avaliação nunca muda `CPL.nivel_maturidade` — só um `nivel_sugerido`.
  Um segundo passo, `POST /api/maturidade/avaliacoes/{id}/decidir`,
  separado e restrito a `PAPEIS_GESTAO` (mais restrito que quem pode
  avaliar), registra a decisão humana (`nivel_decidido`, `parecer`,
  `decidido_por_id`) e só *esse* passo atualiza `CPL.nivel_maturidade`.
- **RF-028** — decidir o nível também renova `CPL.data_validade_reconhecimento`
  por um ciclo bienal a partir de hoje (RN-005). `GET
  /api/maturidade/cpls/vencimento-proximo` e um banner em
  `/painel/maturidade` alertam CPLs com reconhecimento vencendo ou já
  vencido, escopados às CPLs visíveis pelo usuário.
- **Recursos** (RF-027, apelação contra o resultado) — `RecursoAvaliacao`,
  um por avaliação (`UniqueConstraint`), solicitado por quem gere a CPL
  (`PAPEIS_GESTAO`) e decidido por quem gere os editais
  (`PAPEIS_EDITAL_GESTAO` — administrador da plataforma), autoridade
  deliberadamente diferente de quem avaliou/decidiu originalmente, por ser
  uma contestação.
- **Limitações conhecidas**: "habilitação jurídica" (RF-027) não tem
  modelo/etapa própria — poderia reaproveitar Documentos como checklist,
  mas não foi formalizado; "simular cenários" (RF-026, ver efeito de uma
  nota hipotética antes de salvar) não foi construído, só o cálculo real
  ao concluir; validade/versão de evidência (RF-025) dependem do
  versionamento que `Documento` já tem, não algo modelado à parte aqui.
- UI web em `/painel/maturidade` (editais + seleção de CPL) →
  `/painel/maturidade/editais/{id}` (critérios + limiares, edição só pra
  administrador) → `/painel/maturidade/cpls/{id}` (avaliações da CPL) →
  `/painel/maturidade/avaliacoes/{id}` (notas por critério com lacunas
  destacadas, conclusão, decisão de nível, recurso).

**Tela de criação/edição de CPL** (RF-001) — antes só existia via API
(`POST /api/cpls`), o que obrigava usar `/docs` até para o primeiro passo
de qualquer módulo. Agora em `/painel/cpls`: lista (escopada às CPLs
visíveis) + form de criação/edição restrito a `ADMINISTRADOR_PLATAFORMA`
(mesma regra da API — criar/editar CPL é decisão de nível de plataforma,
não de quem gere uma CPL específica). O form **não** inclui
`nivel_maturidade`/`data_reconhecimento`/`data_validade_reconhecimento`
de propósito — esses campos só mudam via o fluxo de avaliação de
maturidade (`POST /api/maturidade/avaliacoes/{id}/decidir`), pra não abrir
um atalho em volta de RN-016. Demais papéis veem os dados em modo leitura.

O bloco **Notificações** (RF-049) avisa sobre prazos e pendências que já
existem em outros módulos — não introduz coleta de dado nova, só varre o
que já está no banco:
- `Notificacao` (`app/models/notificacao.py`) — uma linha por (usuário,
  tipo, entidade), com `lida`/`lida_em` como único estado mutável, mesmo
  padrão "log que só acumula" de `RegistroAuditoria`/`IndicadorValorHistorico`.
- `app/services/notificacoes.py::gerar_notificacoes()` varre 5 fontes e
  materializa o que for novo (idempotente — nunca duplica o mesmo aviso
  pra o mesmo usuário, ver `_notificar`): reunião agendada nos próximos 7
  dias (avisa os membros ativos do órgão), tarefa/meta com prazo
  vencendo ou vencido (avisa o responsável), documento perdendo validade
  (avisa quem criou), recadastramento de CPL vencendo em até 90 dias —
  RN-005 (avisa os administradores da plataforma, reaproveitando
  `cpls_com_vencimento_proximo()` já existente do módulo de Maturidade).
  O recadastramento usa sua **própria** janela de 90 dias, independente
  da janela de 7 dias dos outros 4 tipos (prazo operacional × alerta de
  reconhecimento bienal são coisas de escala bem diferente — descoberto
  só ao testar de ponta a ponta, ver HANDOFF).
- **Sem agendador/worker** (sem Celery/cron neste stack): a varredura
  roda **sob demanda**, sempre que `/painel/notificacoes` ou
  `GET /api/notificacoes` é acessado — decisão deliberada pra não
  introduzir infraestrutura nova só para isso; a lista fica "fresca o
  suficiente" sem precisar de um processo em background.
- "Enviar" é dentro do próprio sistema, não e-mail/push/SMS — não há
  esse canal hoje, e o requisito não especifica um.
- RBAC é por posse, não por papel: qualquer usuário autenticado só vê e
  só marca como lida a própria notificação (`usuario_id` bate com o
  usuário logado) — não existe um grupo de papéis pra isso, é dado
  inerentemente pessoal.
- Sem badge de não lidas na barra lateral (as outras seções também não
  têm indicador equivalente — ex. Auditoria não mostra quantas entradas
  novas existem); a contagem aparece só dentro de `/painel/notificacoes`
  e via `GET /api/notificacoes/nao-lidas/contagem`. Recorte de escopo
  deliberado pra não introduzir um context processor Jinja2 (mecanismo
  não usado em nenhum outro lugar do projeto) só para isso.

O bloco **Projetos** (RF-029 a RF-041) cobre o módulo de Projetos e
Fomento **completo**: editais de fomento com submissão,
recursos/contrarrazões/diligências (RF-029/030), demanda/oportunidade →
conversão em projeto → portfólio → plano de trabalho completo,
incluindo o RF-034 inteiro (etapas/cronograma, metas, indicadores,
riscos, impactos socioambientais), o RF-035 inteiro (continuidade,
escalabilidade, equipe, origem dos recursos, aquisições e cronograma
físico-financeiro), o financeiro completo (RF-036 a RF-038: itens de
despesa, cotações com validação de mínimo de fornecedores, desembolsos
com saldo calculado e conciliação), a execução completa (RF-039/040:
marcos, entregas com aprovação, alterações de plano com decisão,
riscos com evidência de mitigação) e a prestação de contas (RF-041:
relatório de execução, relatório financeiro e dossiê de evidências em
PDF, ver seção de Indicadores e relatórios acima) — os 13 requisitos
em 6 sub-áreas (editais, demandas/portfólio, plano de trabalho,
financeiro, execução, prestação de contas) do módulo estão completos;
"sequência natural" escolhida sessão a sessão, sempre a camada mais
fundamental que ainda faltava.
- **`DemandaProjeto`** (RF-031) — título, descrição, origem
  (`OrigemDemanda`: empresa/comissão/instituição/edital) com uma
  referência solta pra origem (`origem_id`/`origem_detalhe`, mesmo padrão
  de `RegistroAuditoria.entidade_id` — não dá pra usar uma FK rígida
  porque a origem pode ser de tabelas diferentes) e status até virar
  projeto ou ser rejeitada.
- **`Projeto`** (RF-032) — estágio (`EstagioProjeto`, ciclo de vida
  completo modelado de uma vez — demanda → elaboração → submetido →
  aprovado → execução → concluído/rejeitado/cancelado — mas só os
  estágios iniciais são usados nesta fatia, evita migração nova quando
  RF-033 em diante forem construídos), prioridade, eixo do SP Produz
  (**texto livre**, não enum — o documento de requisitos não define uma
  lista fechada de eixos do programa), responsável (`Pessoa`) e vínculo a
  um `ObjetivoEstrategico` do planejamento estratégico (é assim que RF-032
  cumpre "vínculo ao planejamento estratégico" — reaproveita o módulo de
  Planejamento já existente, não duplica o conceito de objetivo).
- **Dois jeitos de criar um projeto**: converter uma demanda já registrada
  (`POST /api/projetos/demandas/{id}/converter` — a demanda não é
  apagada, fica com status `CONVERTIDA_EM_PROJETO` e um vínculo 1:1 com o
  projeto) ou criar direto no portfólio (`POST /api/projetos/cpls/{id}/projetos`,
  atalho pra quando já se sabe que é projeto, sem precisar do passo
  intermediário da demanda).
- **Plano de trabalho — informações básicas** (RF-033) — `introducao`,
  `objeto`, `objetivos`, `justificativa` e `impactos`, campos direto em
  `Projeto` (é 1:1, não haveria ganho em separar numa entidade
  `PlanoDeTrabalho` à parte). Form próprio na tela de detalhe do
  projeto (`POST /painel/projetos/{id}/plano-de-trabalho`), separado do
  form de portfólio — edição rápida de estágio/prioridade não devia
  ficar misturada com o preenchimento mais longo do plano de trabalho.
  Na API é o mesmo `PATCH /api/projetos/{id}` do portfólio (o schema
  `ProjetoUpdate` já inclui os campos novos).
- **RF-034 completo** — "etapas, atividades, cronograma, metas
  quantitativas e qualitativas, resultados, indicadores, riscos e
  impactos socioambientais", construído em duas rodadas (estrutural
  primeiro, depois o resto) por ser grande demais pra uma fatia só.
  - **Etapas e cronograma** — `EtapaProjeto`. "Etapa" e "atividade" do
    requisito são tratados como o mesmo nível — uma linha por
    etapa/atividade, sem hierarquia de dois níveis — mesma
    simplificação já usada em `TarefaGovernanca` (sem sub-tarefas).
    Cada etapa tem `data_inicio`/`data_fim` previstos, `ordem`
    (auto-incrementada — sempre entra no fim da lista, sem campo pro
    usuário gerenciar manualmente) e status (`StatusTarefa`,
    reaproveitado). `POST/GET /api/projetos/{id}/etapas`,
    `PATCH /api/projetos/etapas/{id}`.
  - **Metas** — `MetaProjeto`, quantitativa ou qualitativa (`TipoMeta`),
    com `valor_alvo`/`valor_alcancado` (só o valor mais recente, sem
    série histórica própria — mesmo recorte de `IndicadorProjeto`
    abaixo), `prazo`, responsável e status (`StatusTarefa`, de novo
    reaproveitado). `POST/GET /api/projetos/{id}/metas`,
    `PATCH /api/projetos/metas/{id}`.
  - **Indicadores** — `IndicadorProjeto`, versão mais simples do que
    `IndicadorEstrategico` (RF-044): nome, unidade de medida, meta e
    valor atual, sem série histórica (`IndicadorValorHistorico`) — se
    isso vier a ser necessário aqui também, seguir aquele padrão em vez
    de inventar um novo. `POST/GET /api/projetos/{id}/indicadores`,
    `PATCH /api/projetos/indicadores/{id}`.
  - **Riscos** — `RiscoProjeto`: descrição, probabilidade
    (`ProbabilidadeRisco`), impacto (`ImpactoRisco`), resposta/mitigação
    e status (`StatusRisco`: ativo/mitigado/materializado/encerrado).
    Deixado de fora deliberadamente na primeira rodada porque o RF-040
    (Execução, ainda não construído) pede risco com mais detalhe — mas
    o modelo aqui já foi desenhado pra ser estendido pelo RF-040 quando
    chegar a vez (ex.: ligar evidência de mitigação ao repositório de
    Documentos), não duplicado. `POST/GET /api/projetos/{id}/riscos`,
    `PATCH /api/projetos/riscos/{id}`.
  - **Impactos socioambientais** — campo `Text` a mais direto em
    `Projeto` (mesmo padrão 1:1 do RF-033), com label próprio no form
    de plano de trabalho — conceito distinto do campo "Impactos
    esperados" do RF-033 (esse é sobre resultados/efeitos gerais do
    projeto).
  - UI: tabela + form de criação + atualização inline pra cada um dos
    três recursos (metas/indicadores/riscos), no mesmo padrão visual das
    etapas, tudo na mesma tela de detalhe do projeto.
- **RF-035, completo** — "continuidade, escalabilidade, equipe,
  aquisições, origem dos recursos e cronograma físico-financeiro",
  construído em duas rodadas (fundação primeiro, depois o resto) por
  ser grande demais pra uma fatia só.
  - **Continuidade e escalabilidade** — campos `Text` a mais em
    `Projeto`, mesmo padrão narrativo do RF-033/034, no mesmo form de
    plano de trabalho.
  - **Equipe** — `EquipeProjeto`: pessoa, função (texto livre — funções
    variam demais entre projetos pra caber num enum fechado, mesmo
    raciocínio de `eixo_sp_produz`) e vigência (`data_inicio`/
    `data_fim`, `ativo`) — mirror exato de `MembroOrgao` (RF-016). Não
    reaproveita `PessoaVinculo` (RF-007): aquele é sobre papel de acesso
    numa entidade/CPL, um conceito diferente de "função exercida neste
    projeto". `POST/GET /api/projetos/{id}/equipe`,
    `PATCH /api/projetos/equipe/{id}`.
  - **Origem dos recursos** — `OrigemRecursoProjeto`: fonte (texto
    livre — recursos próprios, edital, parceria etc., sem lista fechada
    no documento), valor previsto e se exige contrapartida. **Primeiro
    campo monetário do sistema** — `Numeric(14, 2)`/`Decimal` de
    verdade, diferente do `valor_alvo` textual de `MetaProjeto` (que
    aceita metas não-numéricas). `POST/GET /api/projetos/{id}/origens-recurso`,
    `PATCH /api/projetos/origens-recurso/{id}`.
  - **Cronograma físico-financeiro** — não é uma entidade nova: dois
    campos a mais (`valor_previsto`, `valor_executado`, `Numeric`) em
    `EtapaProjeto`. O lado "físico" já existia (datas, status); o lado
    "financeiro" completa a mesma linha, em vez de uma tabela separada
    — cronograma físico-financeiro é fundamentalmente "etapa + dinheiro
    por etapa".
  - **Aquisições** — `AquisicaoProjeto`: item, descrição, categoria e
    quantidade (texto livre — quantidade pode vir com unidade não
    padronizada como "50 unidades" ou "200 kg", categoria não tem lista
    fechada no documento), valor estimado, data prevista, responsável e
    status (`StatusTarefa`, reaproveitado). Ver RF-036/037/038 abaixo
    para os campos de extensão (etapa, origem de recurso, contrapartida,
    cotações). `POST/GET /api/projetos/{id}/aquisicoes`,
    `PATCH /api/projetos/aquisicoes/{id}`.
  - UI: tabela + form de criação (e "encerrar" pra equipe, atualização
    inline de status/valor executado pra etapas e aquisições) pra cada
    recurso, mesmo padrão visual das seções anteriores, na mesma tela de
    detalhe do projeto — com totais somados nas tabelas de origem de
    recursos, etapas (previsto/executado) e aquisições.
- **Financeiro do projeto (RF-036/037/038)** — "cadastrar itens de
  despesa... e vinculação a etapas" (RF-036), "cotações... e validar
  quantidade mínima de fornecedores" (RF-037) e "controlar desembolsos,
  saldos, comprovações, bens adquiridos e conciliação" (RF-038).
  - **RF-036 não é uma tabela nova** — é `AquisicaoProjeto` (RF-035)
    visto pelo ângulo financeiro: `etapa_id` (vínculo a etapa),
    `origem_recurso_id` (fonte) e `contrapartida` foram adicionados à
    mesma tabela em vez de um `ItemDespesaProjeto` duplicado.
  - **RF-037** — `CotacaoAquisicao`: fornecedor, valor, anexo opcional
    via Documentos (RF-042, mesmo padrão de
    `AvaliacaoCriterio.evidencia_documento_id`), `selecionada`. A
    "validação de quantidade mínima" é regra de negócio de verdade, não
    só descritiva: `POST /api/projetos/cotacoes/{id}/selecionar` conta
    as cotações da aquisição e, com menos que `MINIMO_COTACOES` (`= 3`
    — **não fixado no documento de requisitos**, prática comum de
    pesquisa de mercado no setor público brasileiro), exige
    `justificativa_excecao` (senão `400`); a seleção desmarca qualquer
    cotação vencedora anterior da mesma aquisição. `justificativa_excecao`
    fica gravada em `AquisicaoProjeto`, não em `CotacaoAquisicao` — é
    uma propriedade do processo de aquisição, não de uma cotação
    específica. `POST/GET /api/projetos/aquisicoes/{id}/cotacoes`.
  - **RF-038** — `DesembolsoProjeto`: data, valor, aquisição e origem de
    recursos ligadas (opcionais), bem adquirido (texto livre — nem toda
    aquisição gera um bem patrimonial rastreável), comprovante via
    Documentos, `conciliado` (booleano). **"Saldos" não é armazenado**
    — é `OrigemRecursoProjeto.valor` menos a soma dos desembolsos
    ligados àquela origem, calculado a cada carregamento da tela, nunca
    dessincronizado. "Conciliação por projeto" também não é uma
    entidade própria — é a leitura agregada da tabela de desembolsos
    com o toggle `conciliado` por linha.
    `POST/GET /api/projetos/{id}/desembolsos`,
    `PATCH /api/projetos/desembolsos/{id}`.
  - **Form web sem JS** — a "nova cotação" escolhe a aquisição por um
    `<select>`; pra não precisar de JS montando a URL de submissão
    dinamicamente (único lugar do projeto que precisaria disso), a rota
    web recebe `aquisicao_id` como campo de form normal
    (`POST /{id}/cotacoes`), não como path param — mesmo padrão de
    `responsavel_id`/`etapa_id` em outros forms. A API mantém o path
    param (`/aquisicoes/{id}/cotacoes`), que é o design REST correto
    pra um cliente HTTP.
- **Execução do projeto (RF-039/040)** — "acompanhar execução física e
  financeira, entregas, marcos, alterações de plano e aprovações"
  (RF-039) e "gerenciar riscos com probabilidade, impacto, resposta,
  responsável e evidência de mitigação" (RF-040). A parte física/
  financeira do RF-039 já estava coberta desde o RF-035/038
  (`EtapaProjeto` status/valores, `DesembolsoProjeto`); faltavam três
  conceitos novos.
  - **RF-040 foi a extensão mais barata do módulo inteiro** — 4 dos 5
    campos pedidos (probabilidade, impacto, resposta, responsável) já
    existiam em `RiscoProjeto` desde o RF-034; só faltou
    `evidencia_documento_id` (Documentos/RF-042), exatamente como a
    docstring original do modelo já previa.
  - **Marcos** — não é entidade nova: `marco: Boolean` a mais em
    `EtapaProjeto`, mesmo padrão de não duplicar já usado pro
    cronograma físico-financeiro e pra `AquisicaoProjeto` (RF-036).
  - **Entregas** — `EntregaProjeto`: título, etapa opcional, datas
    prevista/entrega, documento opcional e aprovação
    (`aprovado`/`aprovado_por_id`/`data_aprovacao`), mesmo padrão de
    aprovação que `Documento` já usa (não um workflow genérico à
    parte). `data_entrega` preenchida ou não já sinaliza se foi
    entregue; `aprovado` é uma decisão independente sobre o que foi
    entregue. `POST/GET /api/projetos/{id}/entregas`,
    `POST /api/projetos/entregas/{id}/aprovar`.
  - **Alterações de plano** — `AlteracaoPlanoProjeto`: `tipo` (texto
    livre), descrição/justificativa, solicitação e decisão,
    reaproveitando `StatusRecurso` e o mesmo formato de campos já
    usado em `RecursoSubmissaoProjeto` (RF-030). **Autoridade
    diferente**: decisão é `PAPEIS_GESTAO` (governança interna do
    projeto — entidade gestora/administrador), não
    `PAPEIS_EDITAL_GESTAO` como em `RecursoSubmissaoProjeto` (que
    contesta uma decisão do órgão externo do edital) — aprovação de
    entrega usa a mesma autoridade (`PAPEIS_GESTAO`) pelo mesmo
    raciocínio. `POST/GET /api/projetos/{id}/alteracoes-plano`,
    `POST /api/projetos/alteracoes-plano/{id}/decidir`.
  - UI: os forms de "decidir alteração" e "aprovar entrega" só
    aparecem pra quem tem `PAPEIS_GESTAO` de verdade (helper
    `_pode_gestao`), não pra `e_administrador` — são grupos diferentes
    (`PAPEIS_GESTAO` inclui entidade gestora, não só administrador da
    plataforma).
- **Prestação de contas do projeto (RF-041)** — "gerar relatório de
  execução do objeto, relatório financeiro e dossiê de evidências",
  fecha o módulo de Projetos. Mesmo padrão de resumo-agregado-pronto-
  pra-formatação do RF-048 (ver seção de Indicadores e relatórios),
  mas sem entidade nova nenhuma — as três funções novas em
  `app/services/projeto.py` só leem o que já existe:
  - **Relatório de execução** — cronograma (etapas concluídas/marcos),
    metas, indicadores, entregas (realizadas/aprovadas), riscos (por
    status) e alterações de plano pendentes.
  - **Relatório financeiro** — origens de recursos com saldo calculado
    (mesmo cálculo da tela de detalhe, não armazenado), aquisições com
    valor estimado total e desembolsos com total/conciliados.
  - **Dossiê de evidências** — agrega, sem criar nenhum vínculo novo,
    os quatro pontos onde o módulo já linka documentos: cotação
    (`CotacaoAquisicao.documento_id`), comprovante de desembolso
    (`DesembolsoProjeto.documento_comprovante_id`), evidência de
    mitigação de risco (`RiscoProjeto.evidencia_documento_id`) e
    documento de entrega (`EntregaProjeto.documento_id`).
  - Gerados via `POST /api/projetos/{projeto_id}/relatorio-execucao`,
    `/relatorio-financeiro` e `/relatorio-dossie-evidencias` (e botões
    em `/painel/projetos/{projeto_id}`), RBAC `PAPEIS_GESTAO` — mesma
    convenção de todo relatório gerado no sistema (não
    `PAPEIS_PROJETO_GESTAO`, que é a autoridade do dia a dia do
    projeto, não a de emitir prestação de contas). Redirecionam pro
    repositório de documentos da CPL (`/painel/documentos/cpls/{id}`),
    mesmo padrão dos relatórios do RF-048.
  - **Fecha também o "de projeto" do RF-048** — o requisito não
    descreve um formato próprio pra esse tipo além do que RF-041 já
    pede, então não há um sétimo tipo de relatório a construir; os
    seis tipos citados no RF-048 estão completos.
- **Edital de fomento (RF-029/030)** — distinto do `Edital` de
  maturidade (`app/models/maturidade.py`, que guarda critérios/pesos/
  notas de corte pra avaliação de maturidade); mesmo nome em português,
  domínios diferentes, distinção decidida explicitamente com o usuário
  antes de começar a construir o módulo de Projetos.
  - **`EditalFomento`** (RF-029) — título, descrição, requisitos e
    documentos exigidos (texto livre — o documento não define um
    checklist estruturado, e estruturar exigiria mudar `Documento.cpl_id`,
    hoje `NOT NULL`, pra aceitar documento sem CPL), datas de
    abertura/encerramento (o encerramento é o "marco de submissão") e
    responsável. Global, não escopado a uma CPL — mesmo padrão do
    `Edital` de maturidade. Gestão restrita a `PAPEIS_EDITAL_GESTAO`
    (só `ADMINISTRADOR_PLATAFORMA`, mesmo grupo do edital de
    maturidade); leitura é `PAPEIS_PROJETO_LEITURA`.
    `POST/GET/PATCH /api/projetos/editais-fomento`, UI em
    `/painel/projetos` (lista + form) e
    `/painel/projetos/editais-fomento/{id}` (detalhe/edição).
  - **Submissão** — `Projeto.edital_fomento_id`, setado só pela ação
    explícita `POST /api/projetos/{id}/submeter`, que também move
    `estagio` pra `SUBMETIDO` na mesma transação — não editável pelo
    PATCH genérico de portfólio, pra manter a submissão como evento
    deliberado, não efeito colateral de editar outro campo.
  - **`RecursoSubmissaoProjeto`** (RF-030) — recurso, contrarrazão ou
    diligência no processo de submissão: `tipo`
    (`TipoRecursoSubmissao`), protocolo, prazo, descrição e decisão
    (reaproveita `StatusRecurso` — pendente/deferido/indeferido, mesmo
    enum de `RecursoAvaliacao`/RF-027). Diferente de `RecursoAvaliacao`
    (1:1, no máximo um recurso), aqui é uma lista sem limite — o
    processo real vai e volta (diligência → resposta → nova diligência
    ou decisão). Decisão é `PAPEIS_EDITAL_GESTAO` (autoridade diferente
    de quem gere o projeto que solicitou), mesmo raciocínio do RF-027.
    `POST/GET /api/projetos/{id}/recursos-submissao`,
    `POST /api/projetos/recursos-submissao/{id}/decidir`.
  - Hoje `DemandaProjeto.origem_tipo == EDITAL` continua só registrando
    a origem como texto (`origem_detalhe`) — a referência solta
    (`origem_id`) poderia apontar pra um `EditalFomento.id` agora que o
    modelo existe, mas isso é sobre de onde a *demanda* nasceu, um
    conceito diferente de a que edital o *projeto formal* foi submetido
    (`Projeto.edital_fomento_id`); não foram unificados propositalmente.
- UI web em `/painel/projetos` (seleção de CPL) →
  `/painel/projetos/cpls/{id}` (demandas pendentes + portfólio + forms de
  registrar demanda/criar projeto direto) → `/painel/projetos/demandas/{id}`
  (detalhe da demanda + form de conversão) → `/painel/projetos/{id}`
  (detalhe do projeto, edição de portfólio).
- RBAC: `PAPEIS_PROJETO_LEITURA`/`PAPEIS_PROJETO_GESTAO` (ver matriz
  acima) — não há RBAC por-projeto-específico (ex.: só o
  `responsavel_id` daquele projeto poder editá-lo), é por papel escopado
  à CPL, igual ao resto do sistema.
- Testado de ponta a ponta via Playwright: registrar demanda → ver
  detalhe → converter em projeto → editar estágio no portfólio →
  confirmar que a demanda convertida some da lista de "pendentes" mas o
  projeto aparece na tabela de portfólio; depois, preencher o plano de
  trabalho e confirmar que os campos persistem e recarregam corretos,
  sem interferir nos campos de portfólio salvos por outro form na mesma
  página. Adicionadas 2 etapas com datas diferentes e confirmado que
  aparecem na ordem certa (auto-incrementada) e que trocar o status de
  uma via o `<select>` inline não afeta as outras. RBAC testado
  confirmando que Conselho/Comitê lê mas não escreve (403 ao tentar
  criar demanda, editar plano de trabalho ou criar etapa sem o papel
  `GESTOR_PROJETO`).

## Como rodar localmente

1. Suba o Postgres de desenvolvimento:
   ```
   docker compose up -d
   ```
2. Crie e ative o ambiente virtual, e instale as dependências:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -e ".[dev]"
   ```
3. Copie `.env.example` para `.env` e ajuste `DATABASE_URL` para a porta do
   Postgres local (o `docker-compose.yml` expõe `5433` para não colidir com
   uma instância padrão na `5432`).
4. Aplique as migrações:
   ```
   alembic upgrade head
   ```
5. Suba o servidor:
   ```
   uvicorn app.main:app --reload
   ```
6. Acesse:
   - Portal público: http://127.0.0.1:8000/
   - Login (área restrita): http://127.0.0.1:8000/login
   - Painel: http://127.0.0.1:8000/painel
   - CPLs (criar/editar, HTMX): http://127.0.0.1:8000/painel/cpls
   - Governança (HTMX): http://127.0.0.1:8000/painel/governanca
   - Planejamento Estratégico (HTMX): http://127.0.0.1:8000/painel/planejamento
   - Cadastro e dados / campanhas / importação (HTMX): http://127.0.0.1:8000/painel/cadastro
   - Documentos (HTMX): http://127.0.0.1:8000/painel/documentos
   - Trilha de auditoria (HTMX): http://127.0.0.1:8000/painel/auditoria
   - Indicadores e relatórios (HTMX): http://127.0.0.1:8000/painel/indicadores
   - Maturidade e reconhecimento (HTMX): http://127.0.0.1:8000/painel/maturidade
   - Documentação da API: http://127.0.0.1:8000/docs

Para criar o primeiro usuário administrativo:

1. `POST /api/auth/registrar` (endpoint aberto — hoje sem restrição, ver
   "Controle de acesso" abaixo) para criar a conta.
2. Login (`POST /api/auth/login`) e `POST /api/usuarios/{usuario_id}/papeis`
   com `{"papel": "administrador_plataforma"}` — funciona sem ninguém
   autorizar porque **nenhum administrador existe ainda no sistema** (válvula
   de bootstrap, ver abaixo). Assim que o primeiro existir, esse endpoint
   passa a exigir um administrador autenticado para conceder novos papéis.

## Decisões já tomadas

- **PostgreSQL** como banco (suporta multi-tenant por CPL, JSON e permite
  evoluir para PostGIS caso o RF-011 de georreferenciamento avance).
- **Server-rendered (Jinja2 + HTMX)** em vez de SPA separada — mais simples
  de manter para o escopo previsto.
- **Bootstrap 5 + Bootstrap Icons via CDN** para toda a área restrita e o
  portal público — sem build (Node.js), consistente com o resto do projeto
  ser 100% Python. Layout com sidebar escura fixa (`restrito/_layout.html`)
  + área de conteúdo que segue o tema claro/escuro do sistema operacional
  (`prefers-color-scheme`, sincronizado com `data-bs-theme` do Bootstrap via
  um pequeno script em `base.html`). O `/painel` ganhou KPIs reais (CPLs,
  órgãos ativos, reuniões agendadas, tarefas pendentes/atrasadas, membros
  ativos), calculados em `_kpis_dashboard()` em `routes_restrito.py`,
  respeitando o mesmo escopo de RBAC (`cpl_ids_visiveis`) usado no resto do
  sistema — cada usuário só vê números das CPLs que pode enxergar.
- Autenticação por **e-mail/senha com hash bcrypt** e token **JWT**; MFA
  (RF-004) ainda não implementado — RBAC por papel/CPL (RF-005) está
  implementado, ver seção própria abaixo.
- Governança tem UI própria em `/painel/governanca` (HTMX): as rotas web
  (`app/web/routes_governanca.py`) consultam o banco diretamente via
  SQLAlchemy — não reaproveitam os endpoints de `/api/governanca/...` — para
  poder renderizar HTML/fragmentos diretamente, seguindo o mesmo padrão já
  usado em `routes_restrito.py`. Isso duplica a checagem de RBAC entre API e
  web (implementada duas vezes com a mesma função `verificar_papel`, mas em
  dois lugares) — funciona, mas é candidato a unificação futura.

## Controle de acesso (RBAC)

RF-005 exige controle por papéis, escopado a CPL/entidade/projeto/comissão.
Implementado em `app/core/rbac.py`:

- **`UsuarioPapel`** já existia como modelo (papel + `cpl_id`/`entidade_id`
  opcionais) mas não tinha endpoint algum — agora gerenciável via
  `POST/GET /api/usuarios/{usuario_id}/papeis` e
  `DELETE /api/usuarios/papeis/{usuario_papel_id}` (só administrador da
  plataforma concede/revoga, exceto na válvula de bootstrap abaixo).
- **`verificar_papel(db, usuario, papeis_permitidos, cpl_id=...)`** é a
  função central: levanta 403 se o usuário não tiver nenhum papel permitido
  escopado à CPL do recurso (ou um papel global, caso de administrador).
  Chamada explicitamente no corpo de cada endpoint, depois de buscar o
  recurso (não como `Depends` genérico) — rotas aninhadas como
  `/orgaos/{orgao_id}/membros` não têm `cpl_id` no path, então a checagem
  precisa buscar o recurso primeiro para descobrir a qual CPL ele pertence.
- **Válvula de bootstrap**: `POST /api/usuarios/{id}/papeis` permite que
  qualquer usuário autenticado se autoconceda `administrador_plataforma`
  enquanto **nenhum** existir no sistema (`existe_administrador(db)`).
  Assim que o primeiro é criado, a válvula fecha sozinha — decisão tomada
  para não construir um comando CLI de seed separado nesta fase; revisar
  antes de qualquer ambiente compartilhado (ver "Decisões pendentes").

### Matriz de permissões (grupos definidos em `app/core/rbac.py`)

| Grupo | Papéis incluídos | Usado para |
|---|---|---|
| `PAPEIS_GESTAO` | Administrador, Entidade gestora, Dirigente | Criar CPL/órgão, convocar reunião, registrar presença, encerrar com ata, concluir deliberação, cadastrar Entidade/Pessoa |
| `PAPEIS_GOVERNANCA_LEITURA` | Gestão + Conselho/Comitê, Comissão temática, Auditoria | Ler órgãos/reuniões/deliberações/votos/tarefas — **não** inclui Empresa membro nem Instituição de ensino |
| `PAPEIS_GOVERNANCA_PARTICIPACAO` | Gestão + Conselho/Comitê | Registrar deliberação, votar, criar tarefa, declarar impedimento |
| `PAPEIS_TAREFA_EXECUCAO` | Gestão + Comissão temática, Gestor de projeto | Atualizar status de tarefa (+ o responsável pessoal da tarefa, sempre, via `Usuario.pessoa_id`) |
| `PAPEIS_IMPEDIMENTO_LEITURA` | Gestão + Auditoria | Ler declarações de impedimento (RN-014, dado sensível — mais restrito que o resto da governança) |
| `PAPEIS_EDITAL_GESTAO` | Administrador | Criar/editar edital e critérios de maturidade (RF-024/RN-006 — configuração global, não por CPL) |
| `PAPEIS_AVALIACAO_EXECUCAO` | Gestão + Analista avaliador | Lançar nota/evidência e concluir avaliação de maturidade — decidir o nível final é sempre `PAPEIS_GESTAO` (RN-016) |
| `PAPEIS_PROJETO_LEITURA` | Gestão + Conselho/Comitê, Comissão temática, Auditoria, Gestor de projeto | Ler demandas e portfólio de projetos de uma CPL — mesmo público de `PAPEIS_GOVERNANCA_LEITURA`, mais Gestor de projeto |
| `PAPEIS_PROJETO_GESTAO` | Gestão + Gestor de projeto | Registrar demanda, converter em projeto e atualizar portfólio (estágio, prioridade, eixo, responsável, vínculo ao planejamento) |

Além dos grupos por papel, `verificar_participacao_orgao(db, usuario, orgao_id,
cpl_id)` escopa **por órgão específico**, não só por CPL: quem tem papel de
gestão continua agindo em qualquer órgão da CPL, mas `CONSELHO_COMITE` (ou
qualquer papel fora de `PAPEIS_GESTAO`) só participa (votar, deliberar,
criar tarefa de deliberação) se for `MembroOrgao` ativo daquele órgão
específico — não de qualquer órgão da CPL. Ver "Limitações conhecidas"
abaixo, que documentava essa lacuna antes dela ser fechada.

Essa matriz é uma **simplificação deliberada**: o documento descreve
responsabilidades por perfil (seção 6), não uma matriz CRUD estrita — foi
validada com o usuário apenas em dois pontos-chave (bootstrap e "leitura de
governança restrita por papel"); o resto é uma interpretação razoável a
revisar com a governança real da CPL.

### Limitações conhecidas

- ~~Entidade e Pessoa não são escopadas por CPL~~ — **resolvido**. Criar
  continua sem escopo de CPL de propósito (o registro pode não ter nenhum
  vínculo ainda), mas **leitura agora é escopada**: `listar_entidades`/
  `obter_entidade` só mostram entidades vinculadas (via `EntidadeCPL`) a
  uma CPL visível pelo usuário; `listar_pessoas`/`obter_pessoa` idem, via
  três caminhos possíveis (`PessoaVinculo.cpl_id` direto, `PessoaVinculo`
  → `EntidadeCPL`, ou `MembroOrgao` → `OrgaoGovernanca.cpl_id` — qualquer
  um conta). Administrador continua vendo tudo.
- ~~Escopo por comissão/órgão específico não é checado~~ — **resolvido**.
  `verificar_participacao_orgao()` (ver "Matriz de permissões" acima) liga
  `MembroOrgao` ao RBAC para registrar deliberação, votar e criar tarefa de
  deliberação — `CONSELHO_COMITE` só participa no(s) órgão(s) que integra
  de fato, não em qualquer órgão da CPL. `declarar_impedimento` continua
  escopado só por CPL (a declaração não é obrigatoriamente ligada a um
  órgão específico no modelo).
- ~~403 sem página amigável no portal web~~ — **resolvido**. Um
  `@app.exception_handler` global em `app/main.py` troca o JSON cru por
  `app/templates/erro_403.html` — mas só para navegação de página inteira
  (GET) fora de `/api/`; chamadas de API e requisições HTMX (`HX-Request`
  header) continuam recebendo JSON, porque HTMX não faz swap de conteúdo
  em resposta não-2xx de qualquer forma.
- **RF-005 também cita escopo por "projeto"** — módulo de projetos ainda não
  existe (roadmap Fase 2/3), então esse eixo do RBAC não tem onde se
  pendurar ainda.

## Decisões pendentes (seção 20 do documento de requisitos)

Ainda não respondidas — bloqueiam o detalhamento de escopo e regras de
acesso mais finas, e devem ser revisitadas com a entidade gestora/governança
da CPL antes da Fase 1 avançar:

- Sistema exclusivo da CPL Autopeças ou multi-CPL desde a v1?
- Controladora dos dados vs. operadora tecnológica?
- Perfis que podem ver dados individuais vs. agregados?
- Solução de assinatura eletrônica (gov.br, ICP-Brasil, outra)?
- Sistemas municipais/institucionais a integrar?
- Volume inicial esperado de usuários, empresas, documentos e projetos?
- **A matriz de permissões da seção "Controle de acesso" está correta?** —
  em especial: Conselho/Comitê deve conseguir concluir deliberação (hoje só
  Entidade gestora/Dirigente/Admin podem "aprovar"), e Comissão temática
  deveria ver/declarar impedimento (hoje restrito a Gestão + Auditoria)?
- **Como sai do bootstrap aberto antes de qualquer ambiente compartilhado?**
  — CLI de seed, migração com admin fixo, ou manter a válvula "primeiro a
  chegar vira admin" mesmo em produção?

## Infraestrutura de implantação — em produção

O SIG-CPL está implantado em produção em **https://sigcpl.dedev.cloud**,
replicando exatamente o padrão já usado pelo `rh-nepen` do usuário na mesma
VPS Hostinger:

- **VPS**: `srv1206123.hstgr.cloud` (72.62.104.149 — KVM 2, 2 vCPU/8GB/100GB,
  Ubuntu 24.04), que também roda `n8n` (com **Traefik** na frente, portas
  80/443, TLS automático via Let's Encrypt — resolver `mytlschallenge`),
  `rh-nepen` e `cervejeira` (parado, não relacionado). O SIG-CPL é um **4º
  projeto Docker Compose** nessa mesma VPS, isolado dos demais (rede própria
  `internal` para `db`↔`backend`, só o `backend` entra também na rede
  `n8n_default` para o Traefik conseguir rotear até ele).
- **DNS**: registro `A` `sigcpl.dedev.cloud` → `72.62.104.149` (TTL 300),
  criado via MCP `hostinger-dns` no mesmo padrão do registro `rh-nepen` já
  existente.
- **Acesso à VPS**: via SSH com chave já existente em `~/.ssh/rh_nepen_hostinger`
  (reaproveitada — não foi criada uma chave nova), configurada em
  `~/.ssh/config` como host `rh-nepen-hostinger`. **Não foi usado nenhum
  mecanismo de deploy automático do Hostinger** (`VPS_createNewProjectV1`).
- **Repositório remoto**: https://github.com/andlucace/sig-cpl (privado ou
  público, decisão do usuário — verificar direto no GitHub). Autenticação
  por **duas deploy keys separadas** (uma por máquina, prática recomendada
  em vez de reaproveitar a mesma chave em dois lugares):
  - Local (este computador): `~/.ssh/sigcpl_github`, com **escrita**
    habilitada (`git push`), host alias `github.com-sigcpl` em
    `~/.ssh/config`.
  - VPS: `/root/.ssh/sigcpl_github`, **só leitura** (não marcada como
    "Allow write access" no GitHub), mesmo host alias em
    `/root/.ssh/config`. Não faz sentido a VPS ter permissão de escrita —
    ela só puxa (`git pull`), nunca empurra.
- **Arquivos em produção**: `/opt/sigcpl/` na VPS é um **working directory
  git de verdade** (branch `master`, tracking `origin/master`), não mais
  uma cópia de arquivo — reimplantar é `git pull` + rebuild (ver
  `deploy.sh` abaixo). `.env.prod` (segredos de produção) fica na mesma
  pasta mas **fora do controle de versão** (`.gitignore`), criado direto na
  VPS via SSH heredoc, nunca passou pelo disco local em texto puro;
  permissão `600`, dono `root`.
  - **Atenção, armadilha real desta sessão**: ao converter `/opt/sigcpl` de
    "cópia de arquivo" pra "working directory git" (`git init` na pasta já
    existente + `git reset --hard origin/master`), um `git add -A`
    apressado usou o `.gitignore` *antigo* (de antes do deploy, que ainda
    não excluía `.env.prod`) e chegou a commitar o arquivo de segredos
    localmente antes do `reset --hard` sobrescrever tudo — o que, por sua
    vez, **apagou o `.env.prod` do disco** (porque ele virou um arquivo
    *rastreado* que não existe em `origin/master`). Detectado na hora,
    purgado do `.git` (`reflog expire` + `gc --prune=now`) e o arquivo
    recriado com os mesmos valores antes de qualquer redeploy real
    acontecer — sem downtime. Lição: ao fazer essa conversão em qualquer
    outro projeto, **mova o `.env`/segredos pra fora da pasta antes** de
    rodar `git add`/`reset --hard`, não confie que o `.gitignore` do
    momento já está correto.
- **`Dockerfile`** (raiz do projeto, novo) — `python:3.12-slim` + `pip install -e .`
  + `apt-get install fonts-dejavu-core` (resolve o gotcha da fonte Unicode
  pro `fpdf2` em Linux, ver seção de gotchas do `HANDOFF.md` — a detecção de
  fonte em `app/services/geracao_documentos.py` já procurava esse caminho
  exato, `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`, então não precisou
  mudar código, só instalar o pacote). `CMD` roda `alembic upgrade head`
  antes de subir o `uvicorn`.
- **`docker-compose.prod.yml`** (raiz do projeto, novo, não confundir com o
  `docker-compose.yml` de dev que continua só com o Postgres local) — serviço
  `db` (Postgres 16, rede `internal`, sem porta publicada) + serviço
  `backend` (build do `Dockerfile`, `env_file: .env.prod`, volume nomeado
  `uploads` montado em `/app/uploads`, labels Traefik roteando
  `Host(sigcpl.dedev.cloud)` pra porta 8000, com `traefik.docker.network`
  **explícito** apontando pra `n8n_default` — obrigatório porque o
  backend está em 2 redes Docker, ver gotcha abaixo — e **healthcheck
  ativo do Traefik** em `/api/saude`, que só passa a rotear tráfego pro
  container quando esse endpoint responder de fato, não assim que o
  container existir; ver "Gotcha: `traefik.docker.network` explícito é
  obrigatório" abaixo).
- **Segredos de produção**: `SECRET_KEY` e senha do Postgres gerados via
  `secrets.token_urlsafe` (não são os valores de dev do `.env` local).
  `SESSION_COOKIE_SECURE=true` e `ENVIRONMENT=production` (diferente do
  `.env` de dev). Vivem só em `/opt/sigcpl/.env.prod` na VPS — não estão
  neste repositório nem em nenhum arquivo local.

### Como reimplantar depois de mudar código

Desde que o remote GitHub foi configurado, `/opt/sigcpl` na VPS é um
working directory git (branch `master`, tracking `origin/master`) — o fluxo
é simplesmente: **commitar e dar push localmente, depois `./deploy.sh` na
VPS** (script versionado no repositório, faz `git pull` + rebuild):

```bash
# No seu computador
cd /c/Users/andlu/sig-cpl
git add -A && git commit -m "..." && git push origin master

# Na VPS
ssh rh-nepen-hostinger "cd /opt/sigcpl && ./deploy.sh"
```

`deploy.sh` roda `git pull origin master`, carrega `.env.prod` e sobe
`docker compose -f docker-compose.prod.yml up -d --build`. Não há deploy
automático no push (sem GitHub Actions/webhook) — o `ssh ... ./deploy.sh`
final é sempre manual, de propósito, pra nunca reimplantar em produção sem
alguém decidir isso explicitamente.

Isso reconstrói a imagem e roda `alembic upgrade head` automaticamente (via
`CMD` do `Dockerfile`) antes de subir o servidor — migrações novas são
aplicadas sozinhas a cada reimplantação, sem passo manual.

### Gotcha: `traefik.docker.network` explícito é obrigatório

`sigcpl_backend` está em **duas redes Docker** (`internal`, com o
Postgres, e `n8n_default`, onde o Traefik escuta). Sem o label
`traefik.docker.network=n8n_default` **explícito**, o provider Docker do
Traefik pode escolher a rede errada (`internal`, à qual o próprio Traefik
nem está conectado) ao descobrir o container — resultado observado em
produção: backend marcado `serverStatus: DOWN` e **todo o site fora do ar
(503/504)**, não só uma rota específica. A escolha parece
não-determinística por instância de container (não é "sempre a primeira
rede da lista"), então o mesmo redeploy pode funcionar hoje e falhar no
próximo sem nenhuma mudança de código — só recriando o container. **Se
for adicionar outro serviço Traefik que fique em mais de uma rede Docker
(neste projeto ou em qualquer outro dessa VPS), sempre declare
`traefik.docker.network` explicitamente.** Pra diagnosticar isso de
novo: a API do Traefik (`/api/http/services`) mostra `serverStatus` e a
URL/IP que ele está tentando usar — só é acessível de dentro do próprio
container Traefik, já que a porta 8080 (dashboard) não é publicada no
host (`docker exec n8n-traefik-1 wget -qO- http://localhost:8080/api/http/services`).

Separado disso, `docker compose up -d --build` recria o container — pára
o antigo, sobe o novo — e nesse intervalo (migração + boot do `uvicorn`)
qualquer request pode receber 502/504 mesmo com a rede correta. O
healthcheck do Traefik em `/api/saude` (ver acima) reduz essa janela —
só roteia quando o backend responder de verdade — mas não elimina, por
ser um único container (sem blue-green). Solução de verdade pra isso, se
virar problema recorrente: 2 réplicas atrás do mesmo serviço (exige
remover o `container_name` fixo) ou deploy blue-green explícito —
nenhuma das duas foi implementada. Na prática: evite reimplantar durante
uso ativo do sistema, ou avise antes.

### Primeiro usuário administrativo em produção

Já criado (`admin@sigcpl.dedev.cloud`) logo após o deploy, pra fechar a
válvula de bootstrap antes que outra pessoa a usasse primeiro — confirmado
com um usuário de teste que tentou se autoconceder `administrador_plataforma`
e recebeu `403`. A senha foi entregue ao usuário fora deste arquivo (chat da
sessão de deploy). Pra conceder o papel a mais alguém, use esse admin em
`POST /api/usuarios/{usuario_id}/papeis` — a válvula de bootstrap não abre
de novo enquanto existir pelo menos um administrador.

### Limitações conhecidas deste deploy

- Sem backup automático do volume `pgdata`/`uploads` configurado ainda
  (RNF-005 — pendente).
- Sem CI/CD — reimplantação é manual (comandos acima).
- O projeto tem repositório git local (sem remoto/GitHub ainda) — a
  implantação não depende dele (é feita por cópia direta de arquivo,
  replicando como o `rh-nepen` já funcionava). Nada impede de configurar um
  remoto depois se for útil (ex.: para revisão de código ou CI/CD futuro).

## Próximos passos sugeridos

Seguindo o roadmap (seção 17 do documento). **A Fase 1/MVP está completa**
e a **Fase 2 foi iniciada** (Maturidade/Reconhecimento). O que resta:

1. ~~Fechar as limitações conhecidas do RBAC~~ — **feito**: escopo por
   órgão/comissão via `MembroOrgao`, escopo de CPL para Entidade/Pessoa e
   página 403 amigável (ver "Controle de acesso" acima).
2. ~~Tela de criação/edição de CPL no portal restrito~~ — **feito**:
   `/painel/cpls` (criar/editar restrito a administrador da plataforma,
   mesma regra do endpoint de API; demais papéis veem só as CPLs
   visíveis, em modo leitura).
3. ~~Remapeamento manual de colunas na importação de planilha~~ — **feito**:
   fluxo em 2 passos (upload → conferir/ajustar mapeamento → confirmar),
   ver seção do módulo de Cadastro dinâmico acima. Calibrar os aliases em
   `app/services/importacao_entidades.py` contra a planilha real "CPLS -
   FORMS.xlsx" (se algum dia for anexada) continua reduzindo o trabalho
   manual, mas não é mais bloqueante.
4. ~~Visão "global" da trilha de auditoria e paginação de verdade~~ —
   **feito**: `/painel/auditoria/global` (e `GET /api/auditoria/global`,
   restrito ao administrador da plataforma) para eventos sem CPL
   resolvível, e paginação real por `offset`/página em ambas as visões
   (antes era um limite fixo de 200 registros mais recentes, sem próxima
   página).
5. ~~Ampliar o resumo cadastral (RF-046/047)~~ — **feito**: qualificação,
   novos empregos (variação no tempo, via `DiagnosticoCadastralHistorico`),
   sustentabilidade, certificações e digitalização ganharam campo e
   entraram no resumo/painel/relatório executivo — ver seção "Indicadores
   e relatórios" acima. ~~Painel de projetos (parte do RF-045)~~ —
   **feito**: card "Projetos" no mesmo dashboard, agregando todo o
   portfólio da CPL (contagem por estágio/prioridade, financeiro e
   execução somados de todos os projetos), complementando os relatórios
   por projeto do RF-041 — ver seção "Painéis" acima. Só falta
   **maturidade** no RF-045 (não priorizado ainda).
6. ~~RF-048: recadastramento, anual, comissão, impacto e de projeto~~ —
   **feito, todos os seis tipos**: recadastramento (dossiê de
   maturidade), anual (mesma base do executivo recortada a um
   ano-calendário), comissão (escopado a um único órgão de governança,
   não toda a CPL), impacto (recorte do resumo cadastral focado em
   sustentabilidade/ODS/inovação, sem agregação nova) e de projeto
   (execução/financeiro/dossiê de evidências, RF-041, escopado a um
   único `Projeto`) — ver seção "Indicadores e relatórios" acima.
7. ~~Iniciar módulo de Projetos~~ — **RF-029 a RF-041, módulo inteiro
   completo**: `DemandaProjeto` (RF-031), `Projeto`/portfólio (RF-032),
   plano de trabalho completo (RF-033/034/035), RF-034 completo
   (`EtapaProjeto`, `MetaProjeto`, `IndicadorProjeto`, `RiscoProjeto`),
   RF-035 completo (`EquipeProjeto`, `OrigemRecursoProjeto`,
   `AquisicaoProjeto`, cronograma físico-financeiro), RF-029/030
   completos (`EditalFomento`, submissão, `RecursoSubmissaoProjeto`),
   RF-036/037/038 completos (`AquisicaoProjeto` estendido,
   `CotacaoAquisicao`, `DesembolsoProjeto`), RF-039/040 completos
   (`marco`, `EntregaProjeto`, `AlteracaoPlanoProjeto`,
   `evidencia_documento_id` em `RiscoProjeto`) e RF-041 completo
   (relatório de execução, relatório financeiro e dossiê de evidências
   em PDF, sem entidade nova) — ver seção "Projetos" acima.
   "Simular cenários" (RF-026) e "habilitação jurídica" (RF-027) também
   ficaram de fora do que foi construído em Maturidade (ver seção do
   módulo acima).
8. ~~Notificações automáticas (RF-049)~~ — **feito**: reunião próxima,
   tarefa/meta com prazo vencendo, documento perdendo validade e
   recadastramento de CPL vencendo — ver seção "Notificações" acima.
   "Enviar" é só dentro do sistema (`/painel/notificacoes`), sem
   e-mail/push; sem agendador — a varredura roda sob demanda.
9. ~~RF-053 (exportação XLSX/CSV) e RF-045 (painel agregado de
   projetos)~~ — **feito**: exportação de entidades + diagnóstico
   cadastral de uma CPL em XLSX/CSV, simétrica à importação do RF-013
   (mesmo cabeçalho de `CAMPOS_CONHECIDOS`, testado ponta a ponta —
   arquivo exportado se reimporta sem remapeamento manual); card
   "Projetos" novo no dashboard de indicadores, agregando portfólio,
   financeiro e execução de todos os projetos de uma CPL — ver seções
   "Cadastro dinâmico" e "Painéis" acima. Exportação fica restrita a
   entidades — outras listagens (projetos, documentos, auditoria) não
   ganharam exportação própria; painel de maturidade (resto do RF-045)
   segue sem priorização.
