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
  exportação/associativismo, ODS mais citados. **Não introduz coleta de
  dado novo**: sustentabilidade, certificações, contatos internacionais e
  digitalização (também citados no RF-047) não têm campo no cadastro atual
  e por isso ficam de fora deste resumo.
- **Painéis** (RF-045): `resumo_governanca` e `resumo_planejamento`
  complementam o resumo cadastral acima, formando o dashboard de
  `/painel/indicadores/cpls/{cpl_id}`. Só cobre governança/planejamento/
  cadastro — maturidade, projetos, finanças e impacto territorial não têm
  painel porque esses módulos ainda não existem (Fase 2/3).
- **Relatório executivo em PDF** (RF-048) — dos seis tipos de relatório
  citados no requisito (executivo, anual, recadastramento, comissão,
  projeto, impacto), só este foi construído; decisão tomada com o usuário
  via `AskUserQuestion` antes de implementar, dado que comissão/projeto
  dependem de módulos que não existem e os demais não têm formato
  definido no documento de requisitos. Reaproveita a mesma infraestrutura
  da ata de reunião (`app/services/geracao_documentos.py` — a classe
  `_GeradorPDF`, antes `_GeradorAta`, foi generalizada pra servir aos
  dois): `POST /api/indicadores/cpls/{cpl_id}/relatorio-executivo` (e o
  botão equivalente em `/painel/indicadores`) gera o PDF e já cadastra
  como `Documento` (categoria `relatorio`), igual ao padrão da ata.
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
  `Host(sigcpl.dedev.cloud)` pra porta 8000).
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
5. Ampliar o resumo cadastral (RF-046/047) e os painéis (RF-045) conforme
   novos campos/módulos forem existindo: qualificação, novos empregos
   (variação no tempo), sustentabilidade, certificações, contatos
   internacionais, digitalização, e painéis de projetos/finanças/impacto
   territorial quando esses módulos forem construídos.
6. Outros tipos de relatório do RF-048 (anual, recadastramento, comissão,
   projeto, impacto) — hoje só o executivo existe; os demais não têm
   formato definido no documento de requisitos e alguns dependem de
   módulos ainda não construídos.
7. Restante da Fase 2 — plano de trabalho, orçamento, cotações e
   submissões (RF-029 em diante) — depende do módulo de Projetos, ainda
   não iniciado. "Simular cenários" (RF-026) e "habilitação jurídica"
   (RF-027) também ficaram de fora do que foi construído em Maturidade
   (ver seção do módulo acima).
