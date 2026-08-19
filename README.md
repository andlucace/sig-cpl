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
- `Entidade` + `EntidadeCPL` + `EntidadeElo` + `OfertaEntidade` (RF-006, RF-008, RF-009, RF-010, RN-003)
- `Pessoa` + `PessoaVinculo` (RF-007)
- `Usuario` + `UsuarioPapel` (RF-004, RF-005)

**Produtos, serviços, tecnologias, canais digitais e capacidade
produtiva (RF-010)** — certificações e diferenciais competitivos já
existiam em `DiagnosticoCadastral` desde o RF-012/046; esta fatia fechou
o resto:
- `OfertaEntidade` — produto, serviço ou tecnologia ofertado por uma
  entidade, tabela repetível (`TipoOferta`: produto/serviço/tecnologia),
  com `ativo` (desativa, não exclui — mantém histórico).
  `POST/GET /api/entidades/{id}/ofertas`,
  `POST /api/entidades/ofertas/{id}/desativar`.
- `Entidade.canais_digitais` (JSONB) já existia no modelo desde o
  RF-006/008, mas era um **campo órfão** — sem schema, sem rota, sem UI,
  nunca escrito nem lido em lugar nenhum. Ganhou
  `PATCH /api/entidades/{id}/canais-digitais` e um formulário com um
  conjunto fixo e conhecido de canais (site, Instagram, Facebook,
  LinkedIn, WhatsApp) — não uma chave livre, pelo mesmo motivo de todo
  form sem JS do projeto: um `<input>` por canal conhecido em vez de
  "adicionar chave dinamicamente".
- `DiagnosticoCadastral.capacidade_produtiva` (texto livre — capacidade
  varia demais entre tipos de negócio pra caber num campo numérico
  único, mesmo raciocínio de `quantidade` em `AquisicaoProjeto`),
  coletável pelos mesmos 3 pontos de escrita das demais respostas de
  diagnóstico (formulário público de campanha, importação de planilha,
  API) — e automaticamente incluído na exportação do RF-053, sem
  nenhuma mudança extra ali (`CAMPOS_CONHECIDOS` é derivado do
  dicionário de aliases, não hardcoded).
- **Nova tela** `/painel/cadastro/entidades/{id}` — não existia
  nenhuma tela de detalhe de entidade antes desta fatia, só a lista por
  CPL (`/painel/cadastro/cpls/{id}`). Reúne ofertas + canais digitais
  (editáveis ali) e um resumo do diagnóstico cadastral (capacidade
  produtiva, diferenciais, certificações — read-only: o diagnóstico
  continua editável só via campanha/planilha/API, mesmo padrão já
  estabelecido, não uma decisão nova desta fatia).

O bloco **Governança** do modelo conceitual também foi implementado
(RF-015 a RF-020):

- `OrgaoGovernanca` — conselho, câmara, comissão temática ou grupo de
  trabalho, com competências, quórum mínimo e periodicidade parametrizáveis.
- `MembroOrgao` — composição/mandato (pessoa, função, vigência).
- `Reuniao` — convocação, pauta, status, ata e anexos de arquivo (RF-017,
  ver abaixo).
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

**Anexos de reunião** (RF-017) — última peça que faltava no módulo,
implementada sem entidade nova: `Documento` (RF-042) já tinha uma
`reuniao_id` opcional desde a geração de ata em PDF (RF-043); só faltava
deixar o usuário anexar um arquivo qualquer (não só a ata gerada
automaticamente) a uma reunião. `POST /api/documentos/cpls/{cpl_id}`
passou a aceitar `reuniao_id` como campo opcional (valida que a reunião
pertence à mesma CPL do upload), e `GET /api/documentos/reunioes/{id}`
lista os anexos de uma reunião. Upload é um formulário plano de arquivo
(sem JS), com uma rota web própria
(`POST /painel/documentos/reunioes/{id}/anexos`, não a genérica
`/painel/documentos/cpls/{cpl_id}`) porque precisa redirecionar de volta
pra tela da reunião, não pra lista geral de documentos da CPL.

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

**Regras de qualidade de dados — máscaras e validade temporal (RF-014)**
— obrigatoriedade de razão social e dedup por CNPJ (na importação) já
existiam; esta fatia fechou o resto:
- **Máscaras** (`app/services/validadores.py`) — "máscara" aqui significa
  validação de formato de verdade, não só normalização: dígito
  verificador oficial de CNPJ/CPF (módulo 11 — pega erro de digitação
  que só contar 14/11 dígitos não pegaria) e UF contra a lista fechada
  de 27 unidades da federação. Reaproveitado nos três pontos de escrita
  de sempre: criação direta via API (`POST /api/entidades`, rejeita com
  400), importação de planilha (linha com CNPJ/CPF/UF mal formado vira
  `ImportacaoLinha` de erro, com mensagem, em vez de gravar dado ruim
  silenciosamente) e formulário público de campanha (só valida UF ali —
  CNPJ não é editável nesse formulário, é a chave de identidade fixada
  na criação).
- **Validade temporal** — `diagnostico_desatualizado()`
  (`app/services/indicadores.py`) sinaliza (não invalida) um
  `DiagnosticoCadastral` sem nenhuma atualização há mais de um ano
  (`VALIDADE_DIAGNOSTICO_DIAS`, não fixado no documento de requisitos —
  mesma janela já usada como padrão em `_novos_empregos_diretos`).
  Contagem em `resumo_cadastral()` (card "Resumo cadastral" do
  dashboard de indicadores) e badge "desatualizado" na tela de detalhe
  da entidade — a última resposta continua valendo até alguém responder
  de novo, só fica sinalizada.

O bloco **Documentos** (RF-042/043) tem repositório completo (RF-042) e
geração de documento padronizado (RF-043) com duas peças: exportar a ata
de uma reunião em PDF e um pacote de submissão com índice e checklist,
escopado a uma CPL perante um edital:

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
- **Pacote de submissão com índice e checklist** (RF-043) —
  `gerar_pdf_pacote_submissao`, alimentado por
  `pacote_submissao_habilitacao()` (`app/services/maturidade.py`): reúne
  o checklist de habilitação jurídica de uma CPL perante um edital
  (`ItemHabilitacaoJuridica`, RF-027) contra o template de documentos
  exigidos do próprio edital (`RequisitoHabilitacaoEdital`, RF-003, pra
  listar também o que ainda nem foi iniciado como item, não só o que já
  foi), mais a avaliação de maturidade mais recente contra o mesmo
  edital, se existir. Botão "Gerar pacote de submissão" (com seletor de
  edital) na tela de habilitação da CPL
  (`/painel/maturidade/cpls/{id}`), `POST
  /api/maturidade/cpls/{id}/pacote-submissao`. DOCX segue fora de
  escopo — PDF cobre o mesmo caso de uso e é o formato já usado em todos
  os outros relatórios do sistema (RF-048).

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
- **Painéis** (RF-045, completo): `resumo_governanca` e
  `resumo_planejamento` complementam o resumo cadastral acima, formando
  o dashboard de `/painel/indicadores/cpls/{cpl_id}`. Ganhou depois um
  card de **projetos e finanças** — `resumo_projetos_cpl()` em
  `app/services/projeto.py`, agregando todo o portfólio da CPL (não um
  projeto só, que já é coberto pelos relatórios do RF-041): contagem por
  estágio/prioridade, financeiro (previsto/desembolsado/saldo somados de
  todas as origens de recurso e desembolsos dos projetos da CPL) e
  execução (etapas/marcos/entregas/metas/riscos agregados). Por fim, um
  card de **maturidade** — reaproveita `resumo_recadastramento()` (já
  existia desde o RF-048, nenhuma agregação nova) pra mostrar nível
  vigente, validade do reconhecimento (com o mesmo alerta de vencimento
  do relatório de recadastramento) e lacunas da avaliação vigente,
  fechando os cinco painéis que o requisito pede.
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
- **Simular cenários** (RF-026) — `simular_avaliacao()`
  (`app/services/maturidade.py`) reaproveita as mesmas funções puras já
  usadas pra conclusão real (`calcular_pontuacao`/`sugerir_nivel`/
  `lacunas`, nenhuma escreve no banco), mas chamadas **enquanto a
  avaliação ainda está em andamento** — mostra "se você concluir agora,
  o resultado seria X" com as notas já lançadas até aquele ponto, sem
  persistir nada em `Avaliacao`. Mudar uma nota (já suportado, `PUT
  .../notas`, chamável quantas vezes quiser antes de concluir) e
  recarregar a tela atualiza a simulação — não precisa concluir a
  avaliação de verdade só pra ver o efeito de uma nota diferente.
  `GET /api/maturidade/avaliacoes/{id}/simulacao`, card na tela de
  detalhe da avaliação (visível só enquanto `status = em_andamento`; a
  partir da conclusão, os campos reais de `Avaliacao` já respondem a
  mesma pergunta).
- **Habilitação jurídica** (RF-027) — `ItemHabilitacaoJuridica`, item de
  checklist por CPL+edital (`descricao` livre — o documento de
  requisitos não define uma lista fechada de documentos exigidos,
  mesmo raciocínio de `eixo_sp_produz`), com `documento_id`
  reaproveitando o repositório de Documentos (RF-042, mesmo padrão de
  `AvaliacaoCriterio.evidencia_documento_id`) e ciclo `pendente →
  entregue → aprovado/rejeitado`. Criar item/anexar comprovante é
  `PAPEIS_GESTAO` (a própria CPL reunindo a documentação); analisar
  (aprovar/rejeitar) é `PAPEIS_EDITAL_GESTAO` — mesma autoridade de
  `RecursoAvaliacao`, é o órgão externo do edital validando a
  regularidade jurídica, não uma decisão interna da CPL.
  `POST/GET /api/maturidade/cpls/{id}/habilitacao`,
  `POST /api/maturidade/habilitacao/{id}/analisar`.
- **Requisitos de habilitação por edital — template** (RF-003) —
  `RequisitoHabilitacaoEdital`, definido uma vez por edital por quem o
  administra (mesmo raciocínio de `CriterioMaturidade`: template por
  edital, gerido por `PAPEIS_EDITAL_GESTAO`). Fecha a peça de RF-003
  ("parametrizar... documentos... sem alteração de código") que ainda
  faltava — editais/critérios/pesos/prazos já eram configuráveis via UI
  desde o RF-024 (a marcação anterior de "depende do módulo de
  Maturidade" estava desatualizada). `POST
  /api/maturidade/cpls/{id}/habilitacao/usar-requisitos-edital`
  instancia o checklist de uma CPL a partir do template — idempotente
  (pula requisitos que a CPL já tem um item com a mesma descrição, pra
  poder clicar de novo depois que o edital ganha um requisito a mais
  sem duplicar os que já existem). Níveis de maturidade continuam um
  enum fixo — RN-004 já documentava que o que é "parametrizável" são os
  limiares (já configuráveis por edital), não os quatro nomes em si,
  definidos pelo programa estadual.
- **Limitação conhecida remanescente**: validade/versão de evidência
  (RF-025) dependem do versionamento que `Documento` já tem, não algo
  modelado à parte aqui — decisão de escopo deliberada, não pendência.
- UI web em `/painel/maturidade` (editais + seleção de CPL) →
  `/painel/maturidade/editais/{id}` (critérios + limiares, edição só pra
  administrador) → `/painel/maturidade/cpls/{id}` (avaliações da CPL +
  checklist de habilitação jurídica) →
  `/painel/maturidade/avaliacoes/{id}` (notas por critério com lacunas
  destacadas, simulação, conclusão, decisão de nível, recurso).

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
- Autenticação por **e-mail/senha com hash bcrypt** e token **JWT**;
  recuperação de senha e MFA (RF-004, completo) — ver seção própria
  abaixo; RBAC por papel/CPL (RF-005) está implementado, ver seção
  própria abaixo.
- Governança tem UI própria em `/painel/governanca` (HTMX): as rotas web
  (`app/web/routes_governanca.py`) consultam o banco diretamente via
  SQLAlchemy — não reaproveitam os endpoints de `/api/governanca/...` — para
  poder renderizar HTML/fragmentos diretamente, seguindo o mesmo padrão já
  usado em `routes_restrito.py`. Isso duplica a checagem de RBAC entre API e
  web (implementada duas vezes com a mesma função `verificar_papel`, mas em
  dois lugares) — funciona, mas é candidato a unificação futura.

## Autenticação: recuperação de senha e MFA (RF-004)

Login por e-mail/senha (bcrypt+JWT) já existia; esta fatia fechou as duas
peças que faltavam — decisão de escopo tomada com o usuário via
`AskUserQuestion` antes de implementar (canal de recuperação: e-mail
transacional de verdade via SMTP genérico, não reset assistido por
administrador; provedor: SMTP genérico configurável, não uma API
específica tipo Resend).

- **Recuperação de senha** — `TokenRecuperacaoSenha` (`app/models/usuario.py`):
  token de uso único (`secrets.token_urlsafe(32)`), validade curta
  (`password_reset_token_expire_minutes`, padrão 60 min), `usado_em`
  marca consumo (nunca reutilizável mesmo dentro da janela).
  `POST /api/auth/esqueci-senha` **sempre responde a mesma mensagem
  genérica**, exista o e-mail ou não — proteção padrão contra
  enumeração de contas (`solicitar_recuperacao_senha` em
  `app/services/recuperacao_senha.py` é silenciosa se o usuário não
  existir). `POST /api/auth/redefinir-senha` consome o token. UI web em
  `/esqueci-senha` e `/redefinir-senha/{token}`.
  - **E-mail via SMTP genérico** (`app/services/email.py`) — nenhum
    provedor específico embutido no código; configuração inteira via
    `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASSWORD`/`SMTP_FROM`/
    `SMTP_USE_TLS` (`app/core/config.py`). `SMTP_HOST` ausente faz
    `enviar_email` levantar `RuntimeError` (500 na rota) em vez de
    falhar silenciosamente — sinal claro de "e-mail não configurado
    ainda" em vez de fingir que enviou. **Configurado em produção**:
    `SMTP_*` aponta pro Titan Mail do Hostinger (`smtp.hostinger.com`,
    porta 587, STARTTLS) usando a caixa `no-reply@dedev.cloud`,
    confirmado com um `POST /api/auth/esqueci-senha` real (200, sem
    traceback no log) — ver "Deploy em produção" abaixo.
  - `app_base_url` (`app/core/config.py`) monta o link absoluto do
    e-mail (`{app_base_url}/redefinir-senha/{token}`) — diferente do
    resto do app, que só usa caminhos relativos (suficiente dentro do
    navegador, mas um e-mail não tem "app" pra resolver um link
    relativo). `https://sigcpl.dedev.cloud` em produção.
- **MFA (TOTP, RFC 6238)** — `pyotp` + `qrcode` (novas dependências).
  "Opção de MFA para perfis críticos" implementado como recurso que
  **qualquer usuário pode ativar** (não uma obrigação amarrada a um
  papel específico — o requisito não define uma lista fechada de
  "perfis críticos" nem pede bloqueio de quem não ativa), com a UI de
  configuração (`/painel/perfil`) recomendando explicitamente a
  ativação para administrador da plataforma/entidade gestora/dirigentes.
  - Ativação em dois passos (`app/services/mfa.py`), mesmo raciocínio do
    remapeamento de importação (RF-013) — nunca ativar direto:
    `iniciar_ativacao_mfa` gera e já salva o segredo
    (`Usuario.mfa_secret`), mas só `confirmar_ativacao_mfa` (com um
    código válido gerado a partir dele) liga `mfa_enabled`. Sem essa
    etapa, um segredo mal escaneado no autenticador trancaria o próprio
    usuário pra fora da conta.
  - Confirmação gera **8 códigos de backup** de uso único
    (`Usuario.mfa_backup_codes`, hash bcrypt — nunca texto puro, mesmo
    padrão de `hashed_password`), mostrados **uma única vez** na tela.
  - **Login web em duas etapas** quando `mfa_enabled`: senha correta
    emite um cookie `sigcpl_mfa_pending` separado (JWT, 5 min, claim
    `mfa_pending: true`) e redireciona pra `/login/mfa`; só o código
    (TOTP ou backup) emite o cookie de sessão real. **Nunca aceito como
    sessão** — `get_current_user` rejeita explicitamente qualquer token
    com a claim `mfa_pending`, então mesmo que esse cookie vazasse (ex.:
    reenviado manualmente como Bearer), ele não bypassa o segundo
    fator.
  - **Login por API é um passo só** — `POST /api/auth/login` aceita
    `mfa_code` opcional no mesmo request (campo `Form` a mais ao lado
    do `OAuth2PasswordRequestForm`), porque um cliente de API já é
    capaz de gerar o código na hora, sem precisar de tela intermediária.
  - `POST /api/auth/mfa/{iniciar-ativacao,confirmar-ativacao,desativar}`
    (API) e `/painel/perfil` + `/painel/perfil/mfa/{configurar,confirmar,desativar}`
    (web, com QR code renderizado como `<img>` base64 inline, sem
    salvar arquivo).
  - `mfa_secret`, `mfa_backup_codes` (e, por extensão, qualquer campo
    chamado `token` em qualquer modelo — cobre também
    `TokenRecuperacaoSenha.token` e retroativamente
    `CampanhaConvite.token`, que nunca tinha sido redigido) foram
    adicionados a `_CAMPOS_REDIGIDOS` em `app/services/auditoria.py` —
    nunca aparecem em texto reconhecível na trilha de auditoria, mesmo
    a captura automática de `ATUALIZACAO` que registra todo `UPDATE` de
    qualquer modelo.

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
| `PAPEIS_LEITURA_MEMBRO` | `PAPEIS_GOVERNANCA_LEITURA` + Empresa membro | Dashboard de indicadores da própria CPL e eventos da própria CPL — **não** reabre governança em si (grupo separado de propósito) |
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
- ~~`EMPRESA_MEMBRO` não acessava nenhuma funcionalidade~~ — **resolvido**.
  Achado ao investigar um usuário de demonstração (`juliana.prado`) sem
  acesso a nada: o papel existia no enum desde o início do projeto, mas
  nunca tinha sido incluído em nenhum grupo `PAPEIS_*` — não era um bug de
  dado dela, era o papel inteiro sem nenhuma permissão de verdade anexada.
  Desenhado com o usuário (ver "Membro de empresa" abaixo) e corrigido:
  `PAPEIS_LEITURA_MEMBRO` (dashboard de indicadores + eventos) e
  `entidade_e_da_pessoa()` (própria entidade, via `PessoaVinculo`).
- ~~`POST /api/auth/registrar` sem restrição nenhuma~~ — **resolvido**.
  Achado como efeito colateral de construir o cadastro de "usuário
  responsável pela entidade gestora" (ver seção "Cadastro e dados"
  abaixo): o próprio endpoint já tinha um comentário dizendo "em
  produção deve ser restrito", mas nunca foi restrito de fato — qualquer
  um, sem login nenhum, conseguia criar conta em produção. Reportei o
  achado ao usuário antes de mexer (mudança de comportamento de
  autenticação, não pedida explicitamente) e ele confirmou. Corrigido
  com a mesma válvula de bootstrap já usada em `POST /api/usuarios/{id}/
  papeis`: sem restrição só enquanto não existe nenhum
  `administrador_plataforma` no sistema — depois disso, exige um
  administrador autenticado.

## Membro de empresa (EMPRESA_MEMBRO)

Escopo desenhado com o usuário depois de descobrir que este papel não
tinha nenhuma permissão de verdade anexada (ver "Limitações conhecidas"
acima). Princípio: leitura do que já é essencialmente agregado/público
(o dashboard de indicadores mostra a mesma categoria de dado que já é
público sem login no portal de transparência, RF-055), mais autonomia
prática (ver e se inscrever em evento, ver a própria entidade) — sem
tocar em governança, documentos internos, maturidade ou gestão de
projetos, que continuam sem caso de uso definido pra esse papel.

- **Dashboard de indicadores** (`/painel/indicadores/cpls/{id}`) — leitura
  liberada via `PAPEIS_LEITURA_MEMBRO`. O seletor de CPL
  (`GET /painel/indicadores`) também passou a incluir as CPLs onde o
  usuário tem `EMPRESA_MEMBRO` (`cpl_ids_membro()`), não só as de
  `cpl_ids_visiveis()` — sem isso, ela só conseguiria chegar na própria
  CPL digitando a URL direto, sem aparecer na lista.
- **Própria entidade** (`/painel/cadastro/entidades/{id}`) —
  `entidade_e_da_pessoa(db, usuario, entidade_id)` (novo,
  `app/core/rbac.py`) verifica se a entidade é a mesma que o
  `PessoaVinculo` do usuário aponta, como alternativa à checagem por CPL
  visível já existente. Ações de escrita nessa página (canais digitais,
  ofertas, geocodificação) continuam gated por `PAPEIS_GESTAO`, sem
  mudança — a pessoa vê os próprios dados, mas editar continua sendo
  ação de quem administra a CPL. Ficou como próximo passo, não pedido
  nesta fatia.
- **Eventos** — ver evento da própria CPL liberado (mesmo grupo
  `PAPEIS_LEITURA_MEMBRO`); **autoinscrição** nova
  (`POST /painel/eventos/{id}/inscrever-me`, deriva `pessoa_id`/`cpl_id`
  do próprio usuário logado, não aceita por formulário — evita que
  alguém inscreva outra pessoa por essa rota) — diferente da inscrição
  por quem tem papel de gestão (`POST .../inscricoes`, continua existindo
  sem mudança, pra inscrever qualquer pessoa). Bloqueada se o evento não
  estiver `agendado`, se já estiver inscrita, se não houver vaga, ou se o
  usuário não tiver `Usuario.pessoa_id` vinculado.
- **Notificações e Biblioteca** — já funcionavam pra qualquer usuário
  logado, sem mudança nenhuma (só exigiam login, nunca papel específico).
- **Deliberadamente fora desta fatia**: Governança (já era exclusão
  proposital, mantida), Documentos, Maturidade, Planejamento, Projetos
  (gestão) e Auditoria — sem caso de uso claro definido ainda pra um
  membro de empresa.

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
- **`SMTP_*` (RF-004, recuperação de senha)** — **configurado**:
  `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASSWORD`/`SMTP_FROM`/
  `SMTP_USE_TLS` em `.env.prod` apontam pro Titan Mail do Hostinger
  (`smtp.hostinger.com:587`, STARTTLS, caixa `no-reply@dedev.cloud` —
  domínio já tinha MX/DKIM do Hostinger configurados via DNS, conferido
  antes de escrever a config). `APP_BASE_URL=https://sigcpl.dedev.cloud`
  também definido (usado para montar o link absoluto do e-mail — sem
  ele, o padrão de dev `http://127.0.0.1:8000` vazaria pro e-mail em
  produção). Confirmado com um `POST /api/auth/esqueci-senha` real
  contra produção (200, ~2,5s de duração — tempo compatível com uma
  conexão SMTP de verdade acontecendo, não com uma falha rápida de
  autenticação) e log do container sem traceback.
- **`ANTHROPIC_API_KEY` (RF-057, assistente de IA)**: ausente em
  `.env.prod` até alguém preencher uma chave real da Anthropic; até lá,
  o botão "Assistente de IA" do dashboard de indicadores fica
  desabilitado (degradação graciosa, não erro) — ver seção "Assistente
  de IA (RF-057)" acima. `ANTHROPIC_MODEL` é opcional (padrão
  `claude-sonnet-5`).

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
- CI (`.github/workflows/ci.yml`, ver RNF-011 abaixo) roda lint + testes a
  cada push/PR, mas a implantação em produção continua manual — reimplantar
  ainda é rodar `deploy.sh` (comandos acima); automatizar esse último passo
  (CD de verdade) fica como próximo passo.
- Repositório versionado no GitHub (`origin` → `andlucace/sig-cpl`) — a
  implantação em si não depende dele (é feita por cópia direta de arquivo
  pra VPS, replicando como o `rh-nepen` já funcionava); o remoto existe pra
  histórico, CI e revisão de código.

## Eventos (RF-050)

Capacitações, mentorias, missões técnicas e eventos genéricos do Programa SP
Produz, com inscrição, presença e avaliação:

- `Evento` (`app/models/evento.py`) — mesmo raciocínio de `Edital` (RN-006):
  `cpl_id` nulo é um evento aberto a todas as CPLs, gerido pela plataforma
  (`PAPEIS_EDITAL_GESTAO`); `cpl_id` preenchido é um evento local de uma CPL
  específica, gerido pela própria gestão dela (`PAPEIS_GESTAO`). Tipo
  (`capacitacao`/`mentoria`/`missao_tecnica`/`outro`), status
  (`agendado`/`realizado`/`cancelado`, mesmo raciocínio de `StatusReuniao`),
  local, vagas.
- `InscricaoEvento` — inscrição, presença e avaliação de uma pessoa num
  evento num único registro por pessoa+evento, não três tabelas separadas:
  são estados sucessivos do mesmo vínculo (inscrita → presente/ausente →
  avaliação), não entidades independentes. `presente` fica `None` até
  alguém marcar (diferente de `Presenca` em Governança, que já nasce
  preenchida — ali o registro só existe depois da reunião acontecer; aqui a
  inscrição existe antes do evento). Inscrição é feita por quem tem papel de
  gestão (mesmo padrão de `MembroOrgao`/`Presenca` — não é autoatendimento,
  e também não exige que a `Pessoa` já tenha vínculo formal com a CPL, já
  que um evento pode ser justamente a porta de entrada de alguém ainda não
  vinculado). Limite de vagas verificado na inscrição.
- UI web em `/painel/eventos` (lista + criação) →
  `/painel/eventos/{id}` (inscrever pessoa, marcar presença, registrar
  avaliação, atualizar status). `POST/GET /api/eventos`,
  `POST /api/eventos/{id}/inscricoes`,
  `PATCH /api/eventos/inscricoes/{id}`.

## Biblioteca de conhecimento (RF-051)

Conteúdo compartilhado entre todas as CPLs — modelos, estudos, boas
práticas, editais/oportunidades em destaque e conteúdo técnico. Diferente
do repositório de documentos operacionais de uma CPL (RF-042, `Documento`,
sempre preso a um `cpl_id`), por isso não reaproveita esse modelo:

- `RecursoBiblioteca` (`app/models/biblioteca.py`) — seis tipos (`modelo`,
  `estudo`, `boa_pratica`, `edital`, `oportunidade`, `conteudo_tecnico`);
  "atas" não virou um sétimo tipo porque já é `Documento`/RF-042 (ligada a
  uma `Reuniao`) — duplicar seria o mesmo conteúdo em dois lugares. Um
  recurso pode ser um arquivo enviado (`salvar_arquivo_biblioteca`, mesmo
  mecanismo de `salvar_arquivo` mas numa subpasta fixa em vez de uma por
  CPL, já que este conteúdo não pertence a nenhuma CPL específica), um link
  externo ou só texto — ao menos um dos três é exigido. `publicado`
  controla visibilidade: rascunho só é visível a quem administra
  (`PAPEIS_EDITAL_GESTAO`, mesma autoridade de `Edital` — conteúdo
  compartilhado gerido pela plataforma).
- UI web em `/painel/biblioteca` — lista com filtro por tipo, criação
  (multipart, arquivo opcional) e alternância publicar/despublicar, tudo
  numa página só. `POST/GET /api/biblioteca`,
  `GET /api/biblioteca/{id}/arquivo`.

## Matchmaking de inovação (RF-052)

Fecha o meio do fluxo F09 do modelo conceitual (demanda empresarial →
busca de competência → matchmaking → projeto de P&D → instrumento
jurídico → acompanhamento) — as duas pontas já existiam antes desta
fatia:

- `MatchInovacao` (`app/models/inovacao.py`) — reaproveita `DemandaProjeto`
  (RF-031) em vez de criar uma "demanda de inovação" paralela:
  `origem_tipo=empresa` já é exatamente "demanda das empresas" citada
  pelo requisito. "Competência" reaproveita `OfertaEntidade` (RF-010) —
  o documento de requisitos já não distingue os dois conceitos (ver
  seção "Modelo conceitual"). Um match cita a `Entidade` candidata
  (universidade, ICT, prestador/fornecedor, ambiente de inovação) e,
  opcionalmente, qual oferta dela motivou a sugestão.
- **Curadoria humana, não algoritmo** (RN-016: priorização não pode ser
  só algorítmica) — `buscar_competencias()`
  (`app/services/inovacao.py`) só filtra candidatos por tipo/texto
  (nome da entidade ou de alguma oferta dela); quem sugere um match e
  decide seu status (`sugerido` → `em_conversa` → `firmado`/`descartado`)
  é sempre uma pessoa.
- Uma vez `firmado`, formalizar em projeto usa o fluxo que já existia
  — `POST /api/projetos/demandas/{id}/converter` (RF-031/032) — sem
  nenhuma peça nova para essa etapa.
- UI web em `/painel/inovacao/demandas/{id}` (busca + sugestão + lista
  de matches com atualização de status), acessível a partir de um
  botão na tela da demanda (`/painel/projetos/demandas/{id}`, só
  aparece para demandas de origem empresa ainda não convertidas/
  rejeitadas). `POST/GET /api/inovacao/demandas/{id}/matches`,
  `GET /api/inovacao/competencias`, `PATCH /api/inovacao/matches/{id}`.

## Integrações externas (RF-054)

O requisito cita quatro integrações "quando autorizado e tecnicamente
disponível" — duas foram implementadas de verdade porque são
tecnicamente disponíveis sem depender de contrato com terceiro; as
outras duas dependem de escolher e contratar um provedor específico,
decisão de negócio que só o programa pode tomar (mesma natureza que a
pendência de SMTP em produção tinha antes de ser resolvida, RF-004):

- **Dados cadastrais públicos** — `app/services/integracao_publica.py::consultar_cnpj_publico`,
  consulta de CNPJ via [BrasilAPI](https://brasilapi.com.br) (pública,
  gratuita, sem credencial). Usa `urllib.request` da biblioteca padrão
  em vez de adicionar `httpx`/`requests` só pra uma chamada — as rotas
  que chamam são síncronas (`def`), então o FastAPI já roda numa
  threadpool, mesmo padrão de toda chamada bloqueante já existente no
  projeto (psycopg, SMTP). **Gotcha**: a BrasilAPI devolve 403 pro
  User-Agent padrão do `urllib` (bloqueio anti-bot genérico, não falta
  de autorização de verdade) — corrigido enviando um `User-Agent`
  identificável. Botão "Conferir dados públicos" na tela de detalhe da
  entidade (`/painel/cadastro/entidades/{id}`) mostra uma tabela
  comparando o cadastrado com o oficial (inclusive telefone/e-mail, só
  pra consulta — `Entidade` não tem esses campos) e um botão "usar
  dados da base pública" que reconsulta (nunca confia em valor vindo do
  formulário) e aplica os campos com correspondência direta no
  cadastro. `GET /api/entidades/{id}/cnpj-publico`,
  `PATCH /api/entidades/{id}/cnpj-publico/aplicar`.
- **BI** — `feed_bi_cpls()` (`app/services/indicadores.py`) achata
  `resumo_cadastral()` pra uma linha por CPL com KPIs escalares (sem
  dict/Counter aninhado, que conector de BI não entende bem), pronta
  pra consumo direto por qualquer ferramenta com conector de URL/JSON
  (Power BI, Metabase etc.) — formato aberto (RNF-010), sem precisar de
  acesso direto ao banco. `GET /api/indicadores/bi-feed?formato=json|csv`,
  admin vê todas as CPLs, os demais só as que já enxergam em qualquer
  outra tela.
- **Assinatura eletrônica** e **sistemas institucionais** seguem
  pendentes — não há provedor público/gratuito equivalente ao da
  BrasilAPI para essas duas, então integrá-las de verdade exigiria
  escolher e contratar um serviço específico (ex.: gov.br assinatura,
  Clicksign, DocuSign, para a primeira; sistema institucional nenhum é
  nomeado no documento de requisitos, para a segunda) antes de
  qualquer código fazer sentido — ver "O que falta" no HANDOFF.md.

## Georreferenciamento e mapa da cadeia (RF-011)

- `Entidade.latitude`/`longitude` (`app/models/entidade.py`) — `Float`
  opcionais, nunca obrigatórios: nem toda entidade tem endereço completo
  o bastante pra geocodificar bem, e a ausência não deveria bloquear
  cadastro.
- `app/services/geocodificacao.py::geocodificar_endereco` — consulta a
  API pública do [Nominatim/OpenStreetMap](https://nominatim.org)
  (gratuita, sem credencial), mesmo raciocínio de "tecnicamente
  disponível sem contrato" já usado na consulta de CNPJ do RF-054, e
  reaproveitando o mesmo padrão de `urllib.request` da biblioteca
  padrão. **Mesmo gotcha do RF-054**: o Nominatim também bloqueia o
  User-Agent padrão do `urllib` com 403 (bloqueio anti-bot genérico) —
  corrigido enviando um `User-Agent` identificável, confirmado por teste
  direto com `curl` antes de fechar o design.
- `POST /api/entidades/{id}/geocodificar` (`PAPEIS_GESTAO`) — geocodifica
  a partir do `endereco`/`municipio`/`uf` já cadastrados; `PATCH
  /api/entidades/{id}/localizacao` (`PAPEIS_GESTAO`) — define
  latitude/longitude manualmente, pra quando a geocodificação automática
  erra ou o endereço não é preciso o bastante. Botões equivalentes na
  tela de detalhe da entidade (`/painel/cadastro/entidades/{id}`, card
  "Localização").
- `GET /api/cpls/{id}/mapa` (`PAPEIS_GOVERNANCA_LEITURA`) — feed das
  entidades vinculadas à CPL e já geocodificadas (as duas condições:
  vínculo ativo + lat/lng preenchidos). `/painel/cadastro/cpls/{id}/mapa`
  renderiza isso num mapa [Leaflet](https://leafletjs.com) + tiles OSM
  (via CDN unpkg — sem CSP/CORS restritivo no projeto que bloqueasse
  isso, confirmado antes de adicionar), com marcador colorido por
  `tipo_entidade` (empresa/universidade/ICT/prestador/ambiente de
  inovação/órgão público) e legenda — a única exceção deliberada à regra
  geral do projeto de "zero JavaScript além de formulário simples", já
  que mapa é widget inerentemente visual/interativo. Acessível a partir
  de um botão na tela de cadastro da CPL.
- **Escopo deliberado**: o requisito também pede "relações da cadeia" no
  mapa, mas `EntidadeElo` (RF-009) ainda não tem rota de CRUD própria —
  construí-la agora seria escopo novo, não fechamento do RF-011. Em vez
  disso, a diversidade da cadeia fica representada pela cor do marcador
  por tipo de entidade; arestas de relação de verdade ficam para quando
  `EntidadeElo` ganhar sua própria API.
- `base.html` ganhou um bloco `{% block extra_head %}{% endblock %}`
  (não existia antes) pra permitir CSS/JS por página sem tocar em todos
  os outros templates — usado só pela página do mapa por enquanto.

## Testes automatizados e integração contínua (RNF-011)

Manutenibilidade era o único pilar do RNF-011 sem cobertura nenhuma até
aqui — código já era versionado (Git/GitHub), modular (camadas
`models`/`schemas`/`services`/`api`/`web`) e documentado (este README,
`HANDOFF.md`, `docs/requisitos_macros.md`); faltava testes automatizados
e um pipeline de CI/CD:

- **`tests/`** (pytest) — 43 testes cobrindo autenticação (RF-001/002),
  cadastro + RBAC (inclusive isolamento entre CPLs), geocodificação e
  mapa (RF-011), governança (fluxo completo reunião → presença →
  deliberação → voto → ata), maturidade (cálculo de pontuação/nível,
  RN-016), matchmaking de inovação (RF-052, fluxo completo demanda →
  match → conversão em projeto), observabilidade (RNF-012) e integração
  pública de CNPJ (RF-054). 49% de cobertura de statements
  (`--cov=app`, ver `pyproject.toml`) — não é 100%, mas cobre os fluxos
  de negócio centrais de cada módulo, não só função pura isolada.
- **Banco de teste isolado** — Postgres de verdade (não sqlite: o
  projeto usa tipos específicos do Postgres, `UUID`/`JSONB`, em vários
  models), banco `sigcpl_test` dedicado no mesmo container de dev.
  `tests/conftest.py` isola cada teste com o padrão de SAVEPOINT
  aninhado do próprio SQLAlchemy (`connection.begin_nested()` +
  listener `after_transaction_end` que reabre o savepoint), necessário
  porque o código de aplicação já chama `db.commit()` internamente em
  toda rota — sem isso, testes vazariam estado uns pros outros mesmo com
  rollback externo. Fixtures `client`/`admin_client`/`client_sem_papel`
  passam pelo fluxo de login de verdade (`POST /api/auth/login`), não só
  injetam um usuário — cobre hashing, JWT e RBAC de ponta a ponta, não
  só contorna a autenticação.
- **Lint (ruff)** — `pyproject.toml` configura `select = ["E", "F", "I",
  "UP", "B"]`. Duas categorias de falso-positivo tratadas com
  configuração, não com supressão cega: `B008` (782 ocorrências na
  primeira rodada) é o idiom de injeção de dependência do FastAPI
  (`Depends()`/`Query()`/etc.) sendo confundido com "mutável em
  argumento padrão" — corrigido com
  `[tool.ruff.lint.flake8-bugbear] extend-immutable-calls`, que
  permanece detectando mutável de verdade em outro lugar; `F821` (47
  ocorrências) é o padrão `Mapped["NomeDaClasse"]` do SQLAlchemy
  (resolvido pelo mapper em tempo de execução, não pelo Python) sendo
  lido como nome indefinido — ignorado globalmente com comentário
  explicando o motivo, em vez de reescrever ~15 arquivos de model com
  `TYPE_CHECKING` só pra satisfazer o linter sem ganho nenhum em tempo
  de execução. `UP042` (str+Enum → StrEnum) também ignorado
  deliberadamente — modernizar dezenas de enums existentes é refatoração
  própria, não algo pra fazer de passagem aqui.
- **CI** — `.github/workflows/ci.yml` (GitHub Actions): a cada push/PR
  contra `master`, sobe um serviço Postgres efêmero, instala as
  dependências (`pip install -e ".[dev]"`), roda `ruff check .` e depois
  `pytest`. Não inclui CD (implantação em produção continua manual via
  `deploy.sh`) — automatizar esse último passo é próximo passo, não
  parte deste fechamento.

## Cadastro e dados — entidade gestora, modelo de planilha, cadastro de entidade (RF-001/RF-006/RF-013)

Três pedidos pontuais do módulo Cadastro e dados, todos endereçando
lacunas reais entre o que a API já suportava e o que a área restrita
efetivamente expunha:

- **Entidade gestora + usuário responsável** (`/painel/cpls/{id}`,
  administrador) — `CPL.entidade_gestora_id` já existia e era editável
  (um `<select>` de entidades já cadastradas), mas (a) não tinha jeito de
  cadastrar a entidade gestora *na hora*, só escolher entre as já
  existentes, e (b) não existia nenhum conceito de "usuário responsável"
  em lugar nenhum do sistema — criar um `Usuario` só existia via
  `POST /api/auth/registrar` cru, sem escopo de CPL/entidade, seguido de
  `POST /api/usuarios/{id}/papeis` à parte, nenhum dos dois exposto na
  área restrita. Dois formulários novos, ambos administrador-only (mesma
  restrição que já existia pra editar dados cadastrais da CPL):
  - **"Cadastrar nova entidade gestora"** — cria a `Entidade` e já define
    `cpl.entidade_gestora_id` num passo só.
  - **"Usuário responsável pela entidade gestora"** — exige que a CPL já
    tenha entidade gestora definida; cria `Usuario`+`Pessoa`+
    `PessoaVinculo`+`UsuarioPapel` (papel `entidade_gestora` ou
    `dirigente_entidade_gestora`, escolhido no formulário — os dois
    papéis que fazem sentido como "responsável"), tudo escopado à CPL e
    à entidade gestora. Reaproveita o mesmo padrão de identidade completa
    (não só a conta de acesso) já usado na aprovação de adesão (F01).
- **Modelo de planilha** (`/painel/cadastro/modelo-planilha?formato=xlsx|csv`,
  também espelhado em `GET /api/cadastro/modelo-planilha`) — pedido
  explícito pra ajudar quem vai importar. Reaproveita
  `gerar_xlsx_entidades`/`gerar_csv_entidades` (RF-053, exportação) com
  uma lista vazia — mesmo cabeçalho de `CAMPOS_CONHECIDOS`, zero linha de
  dado, nenhuma mudança nessas duas funções foi necessária. Não é
  escopado por CPL (o cabeçalho é sempre o mesmo); link colocado direto
  no card "Importar planilha" de `/painel/cadastro/cpls/{id}`.
- **Cadastrar entidade nova pela área restrita** (`POST
  /painel/cadastro/cpls/{id}/entidades`) — `POST /api/entidades` já
  usava exatamente o RBAC pedido (`PAPEIS_GESTAO` = administrador +
  entidade gestora + dirigente, sem nenhum papel a mais nem a menos),
  mas só existia via API — o card "Vincular entidade existente" chegava
  a apontar pro Swagger como alternativa quando não havia nenhuma
  entidade disponível pra vincular. Cadastra e já vincula à CPL num
  passo só, escopado por `cpl_id` (mais estrito que a API, que
  deliberadamente não tem escopo de CPL porque cadastrar não implica
  vínculo imediato — aqui implica, então escopar faz sentido).

## Setor/Município/UF como listbox no cadastro de CPL (RF-001)

Pedido explícito: o campo Setor do formulário de CPL (`/painel/cpls`
criação e `/painel/cpls/{id}` edição) virou listbox restrita, Município e
Estado também viraram listbox, Estado antes de Município, e escolher o
Estado filtra as opções de Município — tudo sem criar tabela nova nem
gastar espaço de banco.

- **Setor** — `<select>` com os valores já usados por alguma CPL
  (`DISTINCT CPL.setor`, ordenado), sem tabela nova. Um `<input
  name="setor_outro">` ao lado permite digitar um setor que ainda não
  existe (evita um beco sem saída pra primeira CPL de um setor genuíno,
  ou pro sistema recém-instalado sem nenhuma CPL ainda) — se preenchido,
  tem precedência sobre o `<select>` (`_setor_final()` em
  `app/web/routes_cpl.py`).
- **Estado e Município** — fonte é a API pública de Localidades do IBGE
  (`https://servicodados.ibge.gov.br/api/v1/localidades`, gratuita, sem
  autenticação), consumida por `app/services/localidades.py`. Estado
  escolhido primeiro; ao mudar o `<select>` de UF, HTMX
  (`hx-get="/painel/cpls/municipios-fragment"`) busca só os municípios
  daquele estado e substitui o `<select>` de Município, sem JavaScript
  escrito à mão nem reload de página.
- **Nada é persistido além do que já existia** — `CPL.municipio` e
  `CPL.uf` são as mesmas duas colunas de sempre. A lista de 27 estados e
  ~5.570 municípios em si só fica em cache de memória do processo
  (`functools.lru_cache`, um `maxsize=1` pros estados e `maxsize=27` pros
  municípios, um por UF), válido até o próximo deploy/restart — zero
  tabela nova, atendendo ao pedido explícito de não ocupar espaço de
  banco. O próprio IBGE manda `Cache-Control: max-age=2592000` (30 dias)
  nas respostas, então cache em memória pela vida do processo já é bem
  mais conservador que isso.
- **Resiliência**: se o IBGE cair, `estados()` cai pra uma lista de
  reserva fixa das 27 UFs (nunca mudam) embutida no código, então o
  formulário de CPL nunca fica sem opção de Estado; `municipios_do_estado()`
  não tem reserva (são muitos e mudam raramente, mas não vale embutir
  ~5.570 nomes) — se falhar, só aquele estado específico fica sem opções
  de município, sem quebrar o resto do formulário.
- **Gotcha real ao integrar** (diferente do problema de User-Agent já
  visto em BrasilAPI/Nominatim): o IBGE sempre devolve `Content-Encoding:
  gzip`, mesmo sem o cliente pedir, e `urllib.request` não descomprime
  sozinho — ler a resposta crua quebra com `UnicodeDecodeError`. Corrigido
  detectando o header e chamando `gzip.decompress()` antes do
  `json.loads()`.

## Convite de campanha envia e-mail de verdade (RF-012)

Achado investigando um relato real: "uma empresa cadastrada não recebeu
o e-mail de convite da campanha". A resposta era que **nenhuma campanha
jamais enviou e-mail nenhum** — `convidar_entidade` sempre só gerou um
`CampanhaConvite` com link/token e devolveu isso pra a gestão copiar e
compartilhar manualmente (mesmo padrão do "convite" de F01/adesão), apesar
do botão da tela usar um ícone de envelope que sugere o contrário. Já
existia um serviço de e-mail funcional (`app/services/email.py`, SMTP
configurado em produção desde a fatia de recuperação de senha, RF-004) —
só faltava alguém chamar `enviar_email` neste fluxo.

- **`Entidade.email`** (novo) — e-mail "de comunicações" da própria
  entidade, distinto do e-mail pessoal de um contato vinculado
  (`Pessoa.email`, via `PessoaVinculo`). Motivo de existir separado:
  `Entidade` nunca teve e-mail próprio (só `Pessoa` tinha), então não
  havia pra quem mandar nada quando a entidade não tinha nenhum contato
  cadastrado. Exposto nos três formulários que criam `Entidade`
  (cadastro direto de uma CPL, cadastro de entidade gestora, API) e
  editável depois a qualquer momento (`PATCH /api/entidades/{id}/email`
  e a tela de detalhe da entidade) — precisa continuar editável porque é
  o destinatário usado pelo envio automático.
- **`app/services/campanhas.py::contatos_da_entidade`** — resolve pra
  quem mandar: o e-mail da própria entidade, se cadastrado, **mais** o
  e-mail de cada `Pessoa` com vínculo vigente (`PessoaVinculo.data_fim`
  nulo ou no futuro), sem repetir endereço. Cobre o caso pedido
  explicitamente: "quando tiver um contato vinculado ou mais, enviar
  também para estes contatos" — soma, não substitui.
- **`enviar_convite_email`** — chamada logo depois de criar o
  `CampanhaConvite` (tanto na rota web quanto na API, mesmo service pras
  duas) e grava o resultado no próprio convite: `email_enviado`,
  `email_enviado_em`, `email_destinatarios` (lista JSONB dos endereços
  que efetivamente saíram) e `email_erro`. Gravar isso no convite (não só
  logar) é o que permite a gestão voltar na tela da campanha depois e ver
  se o e-mail saiu de verdade, pra quem, e por que não saiu quando não
  saiu — exatamente a pergunta que motivou esta fatia.
- **Nunca bloqueia a criação do convite** — SMTP fora do ar (ou não
  configurado, caso comum em dev local) só grava `email_erro` e o convite
  continua existindo, com o link copiável funcionando como alternativa
  manual de sempre. Sem contato nenhum cadastrado (nem entidade, nem
  pessoa vinculada) também não é erro — `email_enviado=False`,
  `email_erro=None`, distinção que a tela mostra em textos diferentes
  ("nenhum e-mail cadastrado" vs. "falha ao enviar e-mail: `<motivo>`").
- Testado local (sem SMTP configurado em dev, cenário real de "SMTP
  ausente") via Playwright contra o app rodando de verdade — convite pra
  entidade com e-mail mostra "Falha ao enviar e-mail (SMTP não
  configurado...)"; convite pra entidade sem nenhum contato mostra
  "Nenhum e-mail cadastrado"; editar o e-mail da entidade persiste e
  aparece no cabeçalho da página. 15 testes automatizados novos
  (`tests/test_campanhas.py`, `enviar_email` mockado no ponto de uso,
  cobrindo dedup de endereço, vínculo encerrado excluído, falha de SMTP
  não bloqueando o convite, e paridade entre a rota web e a API) — suíte
  completa em 132 (117 + 15), ruff limpo, `campanhas.py` com 100% de
  cobertura.

## Governança — exclusão de membro com motivo, documento de posse e convocação por e-mail (RF-016/RF-017)

Quatro pedidos pontuais no módulo de Governança (órgãos, conselhos e
comissões), todos usados por quem tem `PAPEIS_GESTAO` (entidade
gestora, dirigente, administrador):

- **Convocar reunião limpa o formulário e confirma** — o formulário de
  convocação (`/painel/governanca/orgaos/{id}`) é HTMX
  (`hx-target="#lista-reunioes" hx-swap="afterbegin"`), então a resposta
  nunca tocava o próprio formulário — os campos ficavam preenchidos
  depois de convocar. Resolvido com `hx-on::after-request="if
  (event.detail.successful) this.reset()"` direto no `<form>` — atributo
  declarativo do HTMX, não JavaScript escrito à mão. A confirmação usa
  **out-of-band swap** (`hx-swap-oob="true"`): a mesma resposta que
  insere o item da reunião na lista também substitui um
  `<div id="convocacao-confirmacao">` vazio (colocado acima da lista)
  por um alerta de sucesso — novo fragmento
  `fragments/reuniao_convocada.html`, que inclui `reuniao_item.html` e
  adiciona esse bloco.
- **Excluir membro exige motivo, registrado na auditoria** —
  `MembroOrgao` ganhou `motivo_remocao` (texto). Excluir é desativação
  (`ativo=False`, `data_fim` preenchido se ainda vazio), não `DELETE`:
  preserva presenças e votos já registrados em nome desse mandato, e o
  membro continua visível na lista, marcado "inativo", com o motivo à
  mostra — nada desaparece silenciosamente. Como é uma alteração de
  linha comum, a trilha de auditoria automática (RF-056) já captura o
  antes/depois de `ativo` e `motivo_remocao` sozinha — **nenhuma chamada
  manual a `registrar_evento` foi necessária**, diferente de eventos
  como login/download que não correspondem a uma escrita de linha.
  `POST /api/governanca/membros/{id}/remover` (JSON) e
  `POST /painel/governanca/membros/{id}/remover` (form, HTMX,
  `hx-swap="outerHTML"` no próprio item — reaparece já como inativo).
- **Documento de posse do órgão, visível também em Documentos** —
  `Documento` ganhou `orgao_id` opcional, mesmo padrão de `reuniao_id`
  já usado pelos anexos de reunião (RF-017) e pela ata em PDF (RF-043):
  mesmo repositório (RF-042), sem tabela nova. Upload em
  `/painel/governanca/orgaos/{id}` (`POST
  /painel/documentos/orgaos/{id}/anexos`, card "Documentos do órgão",
  qualquer categoria — não só "documento de posse", só era o exemplo
  citado no pedido). Como a listagem geral de
  `/painel/documentos/cpls/{cpl_id}` nunca filtrou por
  `reuniao_id`/`orgao_id`, o documento aparece lá **automaticamente**,
  sem nenhum código a mais — "visível no módulo de documentos" já saía
  de graça da forma como RF-042 já estava implementado. Espelhado
  na API: `orgao_id` como campo opcional do mesmo
  `POST /api/documentos/cpls/{cpl_id}` que já aceitava `reuniao_id`
  (não uma rota nova), mais `GET /api/documentos/orgaos/{id}`.
- **E-mail de convocação para todos os membros** — `app/services/
  governanca.py::enviar_convocacao_email`, mesmo padrão resiliente já
  estabelecido em `campanhas.py::enviar_convite_email` (RF-012): resolve
  destinatários (e-mail de cada `MembroOrgao.pessoa` ativo, deduplicado),
  envia um a um parando no primeiro erro, e **nunca bloqueia a
  convocação** — SMTP fora do ar só grava o motivo, a reunião já foi
  criada e continua válida. Resultado persistido em
  `Reuniao.email_convocacao_enviado`/`_enviado_em`/`_destinatarios`
  (JSONB)/`_erro`, mostrado tanto na confirmação transiente quanto,
  depois, na própria tela da reunião (revisitável a qualquer momento,
  não só no instante da convocação).
- Migração `00adf8a90706`: `membros_orgao.motivo_remocao`,
  `reunioes.email_convocacao_*` (`email_convocacao_enviado` é `NOT NULL`
  com `server_default=false`, mesmo padrão de sempre pra não quebrar
  linhas existentes) e `documentos.orgao_id`.
- Testado: Playwright contra o app rodando de verdade, sem SMTP
  configurado localmente (cenário real) — confirmando que o formulário
  de convocação de fato limpa, a confirmação aparece com o texto certo
  ("Falha ao enviar e-mail de convocação (SMTP não configurado...)"),
  excluir membro mostra "inativo" + motivo na hora, e o documento
  enviado no card do órgão aparece tanto ali quanto na lista geral de
  Documentos da CPL. 12 testes automatizados novos em
  `tests/test_governanca.py` (exclusão exige motivo, gera registro de
  auditoria com o motivo no `dados_novos`, exige `PAPEIS_GESTAO`;
  convocação envia e-mail só a membros ativos com e-mail cadastrado,
  ignora membro removido, não quebra com SMTP fora do ar; upload de
  documento do órgão aparece nas duas listagens e rejeita órgão de outra
  CPL) — suíte completa em 144 (132 + 12), ruff limpo.

## Cadastro e dados, Documentos e Indicadores — pedidos pontuais do Dirigente da entidade (RF-012/RF-042/RF-044)

Sete pedidos pontuais em três módulos, todos usados por quem tem
`PAPEIS_GESTAO`:

- **Reenviar convite de campanha** — a lista de entidades convidáveis
  (`entidades_convidaveis`) já excluía quem já tinha convite, então não
  dava pra convidar a mesma entidade de novo. Em vez de remover esse
  filtro (o que criaria convites duplicados, tokens diferentes pra
  mesma entidade), cada convite pendente ganhou um botão "Reenviar"
  (`POST /painel/cadastro/campanhas/convites/{id}/reenviar` e o
  espelho em `/api/cadastro/campanhas/convites/{id}/reenviar`) que
  dispara `enviar_convite_email` de novo pro **mesmo** convite —
  mesmo token, mesmo link, só o e-mail sai de novo. Útil quando o
  primeiro e-mail falhou (SMTP fora do ar) ou só pra lembrar quem
  ainda não respondeu.
- **Convidar todas as entidades de uma vez** — botão "Convidar todas as
  entidades" ao lado do formulário de convite individual
  (`POST .../convites/todas`, web e API), que cria e envia um convite
  pra cada entidade da CPL ainda sem convite nesta campanha, num loop
  reaproveitando o mesmo `enviar_convite_email`. Não duplica quem já
  foi convidado — mesmo critério de `entidades_convidaveis`, só que
  agindo sobre todas de uma vez.
- **Campos que faltavam no link de diagnóstico** — comparado
  `atualizacao_form.html` (o formulário público de campanha) contra
  `CAMPOS_CONHECIDOS` (`app/services/importacao_entidades.py`, os
  campos que a importação de planilha reconhece), faltavam 3 dos 26
  campos de `DiagnosticoCadastral`: `compartilha_recursos`,
  `recursos_compartilhados` e `ods_relacionados`. Adicionados ao
  formulário público e ao handler de `POST /atualizacao/{token}` —
  agora o link tem exatamente os mesmos campos que a planilha de
  importação reconhece, nem mais nem menos.
- **Resumo do diagnóstico mostrava só 3 de 26 campos** — a tela de
  detalhe da entidade (`/painel/cadastro/entidades/{id}`) resumia o
  diagnóstico cadastral mostrando só capacidade produtiva,
  diferenciais competitivos e certificações; os outros 23 campos
  respondidos (atividades e produtos, faturamento, empregos, ODS,
  exportação, sustentabilidade, qualificação, contatos internacionais
  etc.) ficavam invisíveis ali, apesar de já estarem salvos no banco.
  Reescrito como uma lista de definição (`<dl>`) cobrindo todos os
  campos — com um cuidado que não existia antes: campos booleanos
  (ex.: "Realiza inovação?") só aparecem se a pergunta **de fato foi
  respondida**, distinguindo "nunca respondido" (não aparece, campo é
  `None` no banco) de "respondido como Não" (aparece, é uma resposta
  de verdade, `False` explícito) — um `{% if valor %}` ingênuo
  esconderia os dois casos igual, o que seria enganoso.
- **Código do documento e busca por nome/código** — `Documento` ganhou
  `codigo` (formato `DOC-000123`), gerado pelo próprio Postgres via
  `nextval()` de uma sequência dedicada (`documentos_codigo_seq`) como
  `server_default` da coluna — decisão deliberada pra não precisar
  tocar nos ~20 pontos do código que criam um `Documento` (relatórios
  automáticos, atas, anexos de reunião/órgão etc.); qualquer `INSERT`
  novo já sai com código, de graça, e o `ADD COLUMN` da migração já
  preencheu retroativamente os documentos existentes (cada um com seu
  próprio número da sequência). Busca por nome ou código
  (`?q=...`, `ilike` case-insensitive em `titulo` **ou** `codigo`) na
  lista de documentos da CPL, web e API.
- **Quantas e quais aprovações/assinaturas um documento exige** — até
  aqui só existia `Documento.aprovado`/`assinado`, dois booleanos
  simples sem saber "aprovado por quem" ou "quantos ainda faltam".
  Novo modelo `AprovacaoDocumento` (`documento_id`, `pessoa_id`, `tipo`
  — `aprovacao` ou `assinatura` —, `concluido`, `concluido_em`) registra
  exigências específicas; nova tela `/painel/documentos/{id}` mostra
  "X de Y concluídas" com a lista de quem falta e quem já concluiu, e
  um formulário pra adicionar novas exigências. Os dois mecanismos
  convivem — um documento sem nenhuma exigência cadastrada aqui
  simplesmente não mostra a contagem, continua funcionando só com o
  aprovado/assinado simples de sempre.
- **Como montar o campo valor, ao registrar um indicador** — o
  mini-formulário inline de "valor atual" em
  `/painel/planejamento/objetivos/{id}` já mostrava fórmula/fonte/
  unidade do indicador como texto solto acima do formulário, mas não
  amarrava essa informação ao ato de preencher o valor. Ganhou uma
  linha de ajuda logo abaixo do campo, combinando os três numa frase
  ("siga a fórmula X, expresso em Y — fonte: Z") e lembrando que cada
  valor registrado vira um novo ponto da série histórica
  (`IndicadorValorHistorico`), não sobrescreve o anterior — resposta
  direta a "como é montado o campo valor".
- Migração `776412f023c7`: `documentos_codigo_seq` (sequência,
  `CREATE SEQUENCE` explícito — precisa existir antes da coluna que a
  referencia), `documentos.codigo` e a tabela `aprovacoes_documento`.
  A mesma sequência também precisou ser declarada como
  `sqlalchemy.Sequence` presa à `Base.metadata`
  (`app/models/documento.py`) — a suíte de testes cria o schema via
  `Base.metadata.create_all()`, não roda as migrações do Alembic, então
  sem isso o `CREATE TABLE documentos` falharia nos testes por não
  achar a sequência (funcionava em produção, que sempre passa pela
  migração, mas quebrava local).
- Testado com Playwright contra o app rodando de verdade (convidar
  todas as entidades restantes numa campanha, reenviar um convite já
  existente, preencher e enviar o formulário público com os 3 campos
  novos, conferir o resumo expandido na tela da entidade, criar um
  documento e ver o código gerado, buscar por nome e por código, exigir
  uma assinatura e marcá-la concluída, e ver a linha de ajuda do valor
  do indicador) e 27 testes automatizados novos (`tests/
  test_campanhas.py` +7, `tests/test_diagnostico.py` novo com 6,
  `tests/test_documentos.py` novo com 14, mais os já existentes que
  passaram a cobrir `codigo`/`orgao_id`) — suíte completa em 171
  (144 + 27), ruff limpo.

## Portal de transparência (RF-055)

O portal público (`app/web/routes_publico.py`) até aqui só tinha uma página
institucional estática. RF-055 pede pra publicar governança, agenda,
resultados e projetos autorizados "sem exposição de dados pessoais ou
sigilosos" — a restrição de privacidade moldou cada decisão abaixo:

- **`GET /cpls`** — lista de todas as CPLs ativas do programa (nome,
  sigla, setor, município/UF, nível de maturidade), sem autenticação.
  **`GET /cpls/{id}`** — página de uma CPL, também sem autenticação.
- **Governança**: reaproveita `resumo_governanca()` (RF-045, já um dict
  agregado — total de órgãos, reuniões realizadas, deliberações
  aprovadas) e uma função nova, `estrutura_governanca_publica()`
  (`app/services/indicadores.py`), que lista os órgãos ativos por
  nome/tipo/periodicidade e a **quantidade** de membros ativos — nunca o
  nome de quem os compõe. Testado explicitamente (`assert "<nome da
  pessoa>" not in resposta.text`) pra não confiar só em "não escrevi o
  campo no template", e sim confirmar que o dado nem chega na resposta.
- **Agenda**: `agenda_publica()` combina reuniões de governança futuras
  (`Reuniao.status == AGENDADA`, só data/título/local — a pauta fica de
  fora, pode tratar de assunto ainda não deliberado) com eventos abertos
  (RF-050, capacitações/mentorias/missões técnicas, globais da
  plataforma ou locais da CPL), ordenados juntos por data.
- **Resultados**: reaproveita `resumo_cadastral()` (RF-046/047) — já é
  um agregado sem dado individual (percentuais, somas, distribuições),
  então não precisou de tratamento adicional pra ir ao público.
- **Projetos autorizados**: `projetos_autorizados()`
  (`app/services/projeto.py`) filtra só os estágios
  `aprovado`/`em_execucao`/`concluido` — `demanda`/`em_elaboracao`/
  `submetido` ficam de fora porque ainda não são um resultado decidido
  (podem revelar estratégia de uma empresa demandante antes de ser
  pública) e `rejeitado`/`cancelado` não é resultado a divulgar. Só
  título, descrição e eixo do Programa SP Produz aparecem — nunca
  `responsavel_id` nem valores financeiros (RF-041/045 já cobrem esses
  detalhes para quem está autenticado; não é o propósito deste portal).
- **Fora de escopo desta fatia**: o mapa da cadeia (RF-011) continua
  restrito à área logada — RF-055 não pede georreferenciamento, e
  publicar CNPJ/localização de empresa sem que RF-011 tenha sido pensado
  para isso seria escopo novo, não fechamento do RF-055. "Notícia"/
  "aviso" como conteúdo editorial (texto livre, não vinculado a um
  evento ou reunião existente) também não ganhou modelo — o requisito
  não define esse conceito separado de "agenda"/"resultados", que já
  estão cobertos.

## Assistente de IA (RF-057)

O requisito original marcava isto como "evolução futura", fora do MVP —
foi deliberadamente deixado pendente em toda a documentação até o usuário
pedir explicitamente pra implementar. Depende de duas decisões que só ele
podia tomar (qual provedor de IA, e se já havia credencial disponível),
resolvidas via `AskUserQuestion`: provedor **Anthropic (Claude)**,
construído com degradação graciosa (mesmo padrão do SMTP, RF-004) até
uma `ANTHROPIC_API_KEY` real existir em produção.

- **Onde aparece**: botão "Assistente de IA (RF-057)" no dashboard de
  indicadores de uma CPL (`/painel/indicadores/cpls/{id}`,
  `PAPEIS_GESTAO` — mesma restrição já usada pra gerar relatório em PDF,
  já que também é uma "ação", não só leitura). Desabilitado quando a
  função não está configurada, com um aviso explicando o motivo.
- **O que faz**: `app/services/ia_assistente.py::gerar_assistente_ia`
  envia ao Claude uma curadoria manual dos mesmos agregados já
  mostrados no próprio dashboard (`resumo_cadastral`, `resumo_governanca`,
  `resumo_planejamento`, `resumo_projetos_cpl`, `resumo_recadastramento`
  — nunca a lista de objetos ou dado de pessoa, mesmo cuidado de
  anonimização do portal público, RF-055) e pede de volta um JSON
  estruturado com três seções: **síntese** (parágrafo em linguagem
  clara), **verificação de consistência** (contradições/sinais de
  atenção nos números) e **lacunas sugeridas** (o que os dados não
  cobrem, complementando — sem repetir — as lacunas já calculadas por
  regra em `lacunas_avaliacao_vigente`, RF-024).
- **"Revisão humana obrigatória"**: o resultado nunca é persistido no
  banco nem aplicado a nada automaticamente — é só reapresentado na
  mesma tela do dashboard, com o rótulo "revisão humana obrigatória"
  visível, pra quem já tem papel de gestão ler e decidir o que fazer com
  ele (copiar pra um relatório, ignorar, investigar um ponto de
  atenção). Recarregar a página descarta o resultado.
- **Degradação graciosa**: sem `ANTHROPIC_API_KEY`, `ia_disponivel()`
  retorna `False` (botão desabilitado) e `gerar_assistente_ia()` levanta
  `IAIndisponivel` direto, sem tentar rede — mesmo raciocínio de
  `smtp_host` ausente (RF-004). Qualquer falha da API (rede, autenticação,
  resposta em formato inesperado) também vira `IAIndisponivel`, capturada
  na rota e mostrada como aviso — nunca um 500. Testado tanto mockado
  (`tests/test_ia_assistente.py`, sem chamada de rede real) quanto contra
  o endpoint real da Anthropic com uma chave inválida, confirmando que o
  caminho de erro de fato funciona fim a fim, não só no mock.
- **Sem dependência nova de infraestrutura**: usa o SDK oficial
  (`anthropic`, adicionado às dependências do projeto), chamado de forma
  síncrona nas rotas síncronas de sempre (mesmo padrão de toda chamada
  bloqueante já existente — psycopg, SMTP, geocodificação).
- **Configurado e testado em produção** — `ANTHROPIC_API_KEY` real em
  `.env.prod`. A primeira chamada de verdade (não mockada) contra a API
  quebrou com um 500 real, pego pelo log estruturado: o modelo às vezes
  responde com um `ThinkingBlock` (extended thinking) antes do
  `TextBlock` — `resposta.content[0].text` presumia posição fixa e
  quebrou com `AttributeError`. Duas correções, não uma só: (1)
  `thinking={"type": "disabled"}` explícito na chamada — a causa raiz de
  verdade era o orçamento de `max_tokens` sendo consumido inteiro
  "pensando" em vez de gerar a resposta, então a extended thinking nem
  fazia sentido pra uma tarefa de síntese/JSON estruturado; (2) seleção
  do bloco de conteúdo por `.type == "text"` em vez de índice fixo,
  defensivo contra qualquer ordem futura de blocos. Depois desse ajuste,
  a resposta real ainda veio envolvida em cerca de código markdown
  (```` ```json ... ``` ````) apesar da instrução explícita pra não
  fazer isso — `_sem_cerca_markdown()` remove antes do `json.loads`, sem
  depender do modelo acertar o formato toda vez. Reproduzido, corrigido
  e confirmado com uma chamada real de ponta a ponta (não só mock) antes
  do redeploy — ver item 45 do HANDOFF.md.

## Adesão de membro — autoatendimento (F01)

Único fluxo do modelo conceitual (seção 11 do documento de requisitos)
que ainda dependia inteiramente de alguém com papel de gestão: "Convite/
solicitação → cadastro → consentimento → validação → vínculo à CPL →
classificação de elo → ativação". Até aqui, toda `Entidade` era
cadastrada e vinculada direto por quem já tinha acesso — sem porta de
entrada pra quem está de fora.

- **Solicitação (pública, sem login)** — `GET/POST
  /cpls/{cpl_id}/solicitar-adesao`, linkado a partir da própria página
  pública da CPL (portal de transparência, RF-055). Cobre "cadastro"
  (dados básicos da entidade + elo pretendido + contato de quem está
  solicitando) e "consentimento" (checkbox de LGPD obrigatório —
  submissão sem ele é rejeitada, nunca silenciosamente ignorada).
  `app/services/adesao.py::criar_solicitacao` valida CNPJ/CPF/UF
  (reaproveita `app/services/validadores.py`, RF-014, mesmo padrão dos
  outros pontos de escrita) e grava um `SolicitacaoAdesao` com
  `status=PENDENTE` — **nunca cria `Entidade`/vínculo nenhum na hora da
  submissão**, só o pedido.
- **Validação (restrita, `PAPEIS_GESTAO`)** — `/painel/cadastro/cpls/{cpl_id}/solicitacoes-adesao`
  lista pendentes e histórico. Aprovar
  (`aprovar_solicitacao`) é o que efetivamente:
  1. **cria ou reaproveita a `Entidade`** — busca por CNPJ/CPF já
     existente antes de criar, pra não duplicar cadastro quando a mesma
     organização pede adesão a uma segunda CPL (RN-003);
  2. **cria o vínculo à CPL** (`EntidadeCPL`, idempotente — não duplica
     se já existir);
  3. **classifica o elo** (`EntidadeElo`, RF-009) — **primeira vez que
     esse modelo ganha uma rota de escrita**; até aqui existia só como
     leitura (usado no mapa do RF-011), sem nenhum jeito de criar uma
     classificação nova;
  4. **registra o contato como `PessoaVinculo`** (papel
     `EMPRESA_MEMBRO`) — **primeira vez que esse modelo é escrito por
     qualquer fluxo do sistema** (existia só pra leitura, usado na
     resolução de visibilidade do RBAC). Não cria `Usuario`/login — isso
     continua sendo uma ação separada de quem administra.
  Rejeitar (`rejeitar_solicitacao`) só muda o status e grava o parecer —
  não cria nada. Reanalisar uma solicitação já decidida é rejeitado
  (400) — cada pedido só pode ser decidido uma vez.
- **"Ativação"** é o estado resultante da aprovação: `EntidadeCPL.ativo`
  e a solicitação em `status=APROVADA` — não é uma etapa separada com
  tela própria.
- **Decisão deliberada — sem "convite" com token dedicado**: o requisito
  fala "Convite/solicitação", mas construir um sistema de convite
  próprio (token, e-mail, expiração — como o de `CampanhaConvite`,
  RF-012) só faria sentido pra rastrear quem foi convidado
  especificamente, o que não foi pedido aqui. Na prática, "convite" é a
  gestão da CPL compartilhar a URL pública do formulário com quem quiser
  — é o mesmo formulário da "solicitação", só descoberto por um canal
  diferente.
- **Município/UF em listbox, telefone com máscara, e-mail reforçado**
  (pedido explícito) — o formulário de solicitação ganhou o mesmo
  tratamento de Estado/Município já aplicado ao cadastro de CPL
  (RF-001): `<select>` de UF antes de Município, Município filtrado pela
  UF escolhida via HTMX contra a API do IBGE
  (`app/services/localidades.py`), fragmento próprio e **público**
  (`GET /cpls/{id}/solicitar-adesao/municipios-fragment`, sem exigir
  login — diferente do fragmento equivalente em `/painel/cpls`, que
  exige). Telefone ganhou máscara `(99) 99999-9999` formatada em tempo
  real por um pequeno `<script>` inline (o primeiro JavaScript escrito à
  mão do projeto — todo o resto do sistema usa só HTMX; aqui não dava
  pra fugir, uma máscara de digitação não é algo que HTMX resolve) mais
  `pattern`/`title` HTML pra feedback do navegador; a validação de
  verdade continua no servidor, `telefone_valido()`
  (`app/services/validadores.py`, mesmo padrão de `cnpj_valido`/
  `cpf_valido` — só valida quando preenchido, 10 ou 11 dígitos depois de
  tirar a formatação), chamada em `criar_solicitacao` (cobre tanto o
  formulário web quanto `POST /api/cpls/{id}/solicitacoes-adesao`, mesmo
  service). E-mail já era validado no servidor por `EmailStr`
  (Pydantic) desde que este fluxo existe — ganhou só um `pattern` HTML
  a mais, pra rejeitar no navegador antes mesmo de enviar.

## Observabilidade (RNF-012)

Sem infraestrutura externa nova (Prometheus/Grafana/Sentry) — falhas
persistidas no próprio Postgres, métricas em memória do processo, alerta
por e-mail reaproveitando o SMTP genérico do RF-004:

- **Logs centralizados** — `app/core/logging_config.py` formata cada
  linha como JSON (`{"timestamp", "nivel", "logger", "mensagem", ...}`)
  em vez de texto solto, pra ficar filtrável/agregável em qualquer
  coletor que leia stdout do container (Docker já centraliza a coleta;
  isto só estrutura o conteúdo). Um `request_id` (UUID) é gerado por
  requisição em `contexto_auditoria` (`app/main.py`), devolvido também
  no header `X-Request-ID`, e amarra a linha de log da requisição à
  linha de log de uma eventual falha na mesma requisição. Coexiste com
  o access log padrão do uvicorn — não foi desligado.
- **Métricas** — contadores em memória (`app/services/observabilidade.py`):
  total de requisições, contagem por classe de status (`2xx`/`3xx`/`4xx`/`5xx`)
  e latência média, todos "desde o último deploy" (reiniciam com o
  processo — não é uma série histórica, é operação corrente). `GET
  /api/metricas` (admin, `PAPEIS_EDITAL_GESTAO`).
- **Rastreamento de falhas** — `RegistroFalha` (mesmo padrão "log que só
  acumula" de `RegistroAuditoria`/`Notificacao`): uma linha por exceção
  não tratada (não por 4xx esperado — validação, RBAC, 404 são fluxo de
  controle, não falha), com tipo, mensagem, traceback resumido, rota,
  usuário (se autenticado) e `request_id`. Capturada dentro do próprio
  middleware `contexto_auditoria`, não via
  `@app.exception_handler(Exception)` — Starlette move um handler de
  `Exception` "crua" pro `ServerErrorMiddleware`, acima do middleware
  custom, e nessa altura os contextvars de auditoria já foram resetados
  e o ASGI loga a exceção de novo como "Exception in ASGI application"
  (efeito colateral conhecido de `BaseHTTPMiddleware` + handler de
  `Exception`, que gerava 500 duplicado no log — pego e corrigido antes
  de dar por encerrada esta fatia).
- **Alerta por limiar** — se `registros_falha` acumular pelo menos
  `observabilidade_alerta_limiar_falhas` (padrão: 5) linhas nos últimos
  `observabilidade_alerta_janela_minutos` (padrão: 15) minutos, o painel
  de saúde mostra um banner vermelho e tenta notificar os administradores
  por e-mail — melhor esforço via `app/services/email.py` (RF-004), nunca
  derruba nada se o SMTP ainda não estiver configurado; no máximo um
  e-mail por janela, pra não inundar a caixa de entrada.
- **Painel de saúde** — `/painel/administracao/saude` (admin,
  `PAPEIS_EDITAL_GESTAO`): status do banco, uptime do processo, métricas
  de requisição, requisições por classe de status e tabela de falhas
  recentes. `GET /api/saude` (público, sem autenticação — é o que o
  healthcheck do Traefik usa em produção) passou a checar conectividade
  real com o banco (`SELECT 1`) em vez de só responder "ok" sem checar
  nada; retorna `503` se o banco estiver indisponível.

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
   por projeto do RF-041 — ver seção "Painéis" acima. Painel de
   maturidade (resto do RF-045) também feito, ver item 10 abaixo —
   **RF-045 está completo**.
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
   ganharam exportação própria.
10. ~~Painel de maturidade (resto do RF-045)~~ — **feito**: card
    "Maturidade" no mesmo dashboard de indicadores, reaproveitando
    `resumo_recadastramento()` (RF-048, nenhuma agregação nova) — nível
    vigente, validade do reconhecimento com alerta de vencimento e
    lacunas da avaliação vigente. **RF-045 está completo, os cinco
    painéis do requisito** (governança, planejamento/cadastro, projetos,
    finanças, maturidade) existem no mesmo dashboard consolidado por
    CPL.
11. ~~RF-017: anexos de arquivo em reuniões~~ — **feito**: única peça que
    faltava no módulo de Governança. Sem entidade nova — `Documento`
    (RF-042) já tinha `reuniao_id` desde a ata em PDF (RF-043); ver seção
    "Governança" acima para os detalhes de rota. Com isso, RF-015 a
    RF-020 (Governança) estão completos.
12. ~~RF-004: recuperação de senha e MFA~~ — **feito**: ver seção
    "Autenticação: recuperação de senha e MFA" acima. Recuperação por
    e-mail via SMTP genérico (`TokenRecuperacaoSenha`, token de uso
    único) e MFA por TOTP (`pyotp`/`qrcode`, ativação em 2 passos, 8
    códigos de backup, login web em 2 etapas). Na época deste item,
    `SMTP_*` ainda não tinha credenciais reais em produção — **resolvido
    depois**: `.env.prod` configurado com o Titan Mail do Hostinger
    (`no-reply@dedev.cloud`), ver "Deploy em produção" abaixo.
13. ~~RF-010: produtos, serviços, tecnologias, canais digitais e
    capacidade produtiva~~ — **feito**: ver seção "Modelos implementados
    nesta fase" acima. `OfertaEntidade` (tabela nova, repetível),
    `Entidade.canais_digitais` (campo órfão desde o RF-006/008, ganhou
    schema/rota/UI pela primeira vez) e
    `DiagnosticoCadastral.capacidade_produtiva` (novo, nos 3 pontos de
    escrita de sempre — campanha/planilha/API — e automaticamente
    exportável pelo RF-053, sem código extra ali). Nova tela de detalhe
    de entidade, que não existia antes. Certificações e diferenciais
    competitivos já estavam prontos desde antes; "competência" não
    ganhou campo próprio (não é um conceito claramente distinto de
    serviço/tecnologia no documento).
14. ~~RF-026: simular cenários~~ e ~~RF-027: habilitação jurídica~~ —
    **feitos**: ver seção "Maturidade e reconhecimento" acima.
    Simulação reaproveita as mesmas funções puras da conclusão real
    (`calcular_pontuacao`/`sugerir_nivel`/`lacunas`), só chamadas antes
    da avaliação ser concluída, sem persistir nada.
    `ItemHabilitacaoJuridica` fecha o checklist de habilitação jurídica
    por CPL+edital, reaproveitando o repositório de Documentos.
    **Com isso, RF-024 a RF-028 (módulo de Maturidade) estão completos**
    — só a limitação deliberada de validade/versão de evidência (RF-025)
    permanece, por depender do versionamento que `Documento` já tem.
15. ~~RF-014: máscaras + validade temporal~~ e ~~RF-003: requisitos de
    habilitação parametrizáveis~~ — **feitos**: ver seções "Regras de
    qualidade de dados" e "Requisitos de habilitação por edital —
    template" acima. `app/services/validadores.py` (CNPJ/CPF por dígito
    verificador, UF pela lista fechada de 27 unidades) aplicado nos 3
    pontos de escrita de sempre; validade temporal do diagnóstico
    cadastral é função pura, sem campo novo no banco.
    `RequisitoHabilitacaoEdital` fecha a peça de RF-003 que ainda
    faltava — a marcação anterior de "depende do módulo de Maturidade"
    estava desatualizada, o módulo existe desde o RF-024.
16. ~~RF-043: pacote de submissão com índice e checklist~~ e ~~RNF-012:
    observabilidade~~ — **feitos**: ver seções "Documentos" e
    "Observabilidade (RNF-012)" acima. Pacote de submissão reúne
    habilitação jurídica (RF-027, contra o template do RF-003) e
    avaliação de maturidade de uma CPL perante um edital num único PDF
    com índice e checklist. Observabilidade acrescenta logs
    estruturados, métricas em memória, rastreamento de falhas
    (`RegistroFalha`), alerta por limiar e painel de saúde — sem
    infraestrutura externa nova.
17. ~~RF-050: eventos, capacitações, mentorias, missões técnicas~~ e
    ~~RF-051: biblioteca de conhecimento~~ — **feitos**: ver seções
    "Eventos (RF-050)" e "Biblioteca de conhecimento (RF-051)" acima.
    `Evento`/`InscricaoEvento` reaproveitam o raciocínio de `Edital`
    (conteúdo aberto a todas as CPLs ou local de uma só) e de
    `Presenca`/`MembroOrgao` (quem gere inscreve, não é autoatendimento).
    `RecursoBiblioteca` é conteúdo global (sem `cpl_id`), com
    armazenamento próprio em vez de reaproveitar `Documento` (que exige
    uma CPL). Restam no documento de requisitos, ainda não iniciados
    nesta altura: RF-011 (georreferenciamento), RF-052 (matchmaking),
    RF-054 (integrações externas), RF-055 (portal público expandido) e
    RF-057 (assistência de IA, declaradamente fora do MVP) — ver
    `docs/requisitos_macros.md` para o levantamento completo.
18. ~~RF-052: matchmaking de inovação~~ e ~~RF-054: integrações
    externas~~ — **feitos**: ver seções "Matchmaking de inovação
    (RF-052)" e "Integrações externas (RF-054)" acima.
    `MatchInovacao` fecha o meio do fluxo F09 reaproveitando
    `DemandaProjeto`/`OfertaEntidade` já existentes, sem entidade
    "demanda de inovação" paralela. RF-054 ficou parcial por design:
    consulta pública de CNPJ (BrasilAPI) e feed de BI foram
    implementados de verdade (não dependem de contrato); assinatura
    eletrônica e "sistemas institucionais" seguem pendentes até o
    programa escolher um provedor específico — não é algo que dê pra
    implementar sem essa decisão de negócio. Restam no documento de
    requisitos, ainda não iniciados: RF-055 (portal público expandido)
    e RF-057 (assistência de IA, declaradamente fora do MVP).
19. ~~RF-011: georreferenciamento e mapa da cadeia~~ e ~~RNF-011:
    testes automatizados + pipeline de CI~~ — **feitos**: ver seções
    "Georreferenciamento e mapa da cadeia (RF-011)" e "Testes
    automatizados e integração contínua (RNF-011)" abaixo.
    `Entidade.latitude`/`longitude` opcionais, geocodificados via
    Nominatim/OpenStreetMap (mesmo raciocínio de "API pública sem
    contrato" do RF-054) ou definidos manualmente; mapa Leaflet por CPL
    com marcador colorido por tipo de entidade. 43 testes automatizados
    (pytest, banco Postgres de teste isolado) e lint (ruff) limpos,
    rodando em CI (GitHub Actions) a cada push/PR. Restou no documento
    de requisitos, ainda não iniciado nesta altura: RF-055 (portal
    público expandido) — RF-057 (assistência de IA) segue
    declaradamente fora do MVP.
20. ~~RF-055: portal público de transparência~~ — **feito**: ver seção
    "Portal de transparência (RF-055)" abaixo. `/cpls` (lista de CPLs
    ativas) e `/cpls/{id}` (governança, agenda, resultados e projetos
    autorizados de uma CPL), sem autenticação nenhuma. Com isso, **do
    documento de requisitos original só resta RF-057** (assistência de
    IA), declaradamente fora do MVP.
21. ~~RF-057: assistência de IA~~ — **feito**: ver seção "Assistente de
    IA (RF-057)" abaixo. Botão no dashboard de indicadores de uma CPL,
    usando a API da Anthropic sobre os mesmos agregados já mostrados no
    painel; devolve síntese, verificação de consistência e lacunas
    sugeridas, sempre rotulado "revisão humana obrigatória", nunca
    persistido nem aplicado a nada automaticamente. Sem
    `ANTHROPIC_API_KEY`, degrada graciosamente (mesmo padrão do SMTP,
    RF-004) — pendência de credencial em produção, não de código. **Com
    isso, todo requisito funcional do documento original foi endereçado**
    de alguma forma (implementado, parcial por decisão de negócio
    documentada, ou config pendente) — o que restava no projeto era
    só os RNFs de maturidade organizacional e o fluxo F01 de
    autoatendimento, nenhum dos dois um RF numerado do documento.
22. ~~F01: fluxo de autoatendimento (adesão de membro)~~ — **feito**: ver
    seção "Adesão de membro — autoatendimento (F01)" abaixo. Formulário
    público (`/cpls/{id}/solicitar-adesao`, linkado do portal de
    transparência RF-055) cobre cadastro + consentimento LGPD; validação
    é uma tela de gestão (`PAPEIS_GESTAO`) que aprova (cria/reaproveita
    `Entidade`, vincula à CPL, classifica o elo — `EntidadeElo`, RF-009,
    ganhou rota de escrita pela primeira vez) ou rejeita (não cria
    nada). "Convite" não ganhou infraestrutura própria — a gestão só
    compartilha o link público, decisão documentada. Com isso, o único
    fluxo de autoatendimento do modelo conceitual que faltava está
    fechado; o que resta no projeto são só RNFs de maturidade
    organizacional (RNF-002 privacidade formal, RNF-005
    continuidade/backup, RNF-013 qualidade de dados, RNF-015 retenção)
    e RF-057 continua sendo o único RF que dependia de config de
    produção (`ANTHROPIC_API_KEY`) pra funcionar de fato.
