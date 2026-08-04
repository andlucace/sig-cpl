# DOCUMENTO DE REQUISITOS MACROS

## Sistema Integrado de Gestão de Cadeia Produtiva Local – SIG-CPL

- **Referência principal:** Programa SP Produz
- **Interface opcional:** Sistema Paulista de Ambientes de Inovação – SPAI
- **Projeto de referência:** CPL Autopeças de Atibaia/SP
- **Tipo de documento:** Especificação de requisitos em nível macro
- **Versão:** 1.0
- **Data:** 29 de julho de 2026

> Documento de concepção para validação do escopo, contratação e detalhamento posterior de requisitos.
>
> **Nota de proveniência:** este arquivo é uma transcrição fiel do PDF original
> (`Documento_Requisitos_Macros_SIG_CPL_SP_Produz.pdf`) fornecido pelo usuário
> durante a sessão que criou este repositório. O PDF em si não foi salvo no
> projeto — esta transcrição existe para que sessões futuras (humanas ou de
> IA) tenham a fonte completa sem precisar que o usuário reanexe o arquivo.

---

## 1. Identificação e controle do documento

| Campo | Conteúdo |
|---|---|
| Nome do sistema | Sistema Integrado de Gestão de Cadeia Produtiva Local – SIG-CPL |
| Finalidade | Apoiar a organização, governança, planejamento, reconhecimento, execução de projetos, monitoramento e prestação de contas de uma CPL. |
| Base regulatória principal | Programa Estadual de Desenvolvimento das Cadeias Produtivas Locais – Programa SP Produz. |
| Integração complementar | Ambientes de inovação vinculados ao SPAI, quando a CPL utilizar centros de inovação, incubadoras, parques ou hubs como parceiros. |
| Escopo inicial | CPL Autopeças de Atibaia/SP, com possibilidade de expansão para outras CPLs. |
| Público do documento | Entidade gestora, conselho da CPL, Prefeitura, parceiros institucionais, equipe de produto, analistas de negócio, arquitetura, desenvolvimento e segurança. |

### 1.1 Histórico de versões

| Versão | Data | Descrição | Responsável |
|---|---|---|---|
| 1.0 | 29/07/2026 | Versão inicial dos requisitos macros. | A validar pela entidade gestora e governança da CPL |

## 2. Sumário executivo

O SIG-CPL deverá constituir uma plataforma web para centralizar dados, processos, documentos, evidências, indicadores e decisões da Cadeia Produtiva Local. O sistema deverá apoiar tanto a gestão cotidiana da CPL quanto a preparação para processos de reconhecimento, recadastramento e fomento do Programa SP Produz.

A solução deve reduzir a dispersão de informações em formulários, planilhas, e-mails e arquivos isolados; assegurar rastreabilidade das decisões; permitir acompanhamento de metas e indicadores; e gerar os documentos necessários à governança, aos editais e à prestação de contas.

> **Decisão de enquadramento**
> Para Cadeias Produtivas Locais, o programa estadual aplicável é o SP Produz. O SPAI é voltado a ambientes de inovação. O sistema proposto mantém o SP Produz como referência funcional e prevê integração opcional com ambientes SPAI para projetos de inovação, laboratórios, incubação, P&D e transferência de tecnologia.

## 3. Contexto institucional e justificativa

O Programa SP Produz caracteriza a CPL como concentração geográfica de micro, pequenas e médias empresas de um mesmo setor ou segmento, organizadas sob uma estrutura comum de governança e cooperação com entidades públicas e privadas. O programa prevê reconhecimento em quatro níveis de maturidade, apoio técnico, capacitação, editais de fomento e recadastramento periódico.

No caso de Atibaia, os materiais fornecidos demonstram elevada relevância econômica da indústria de transformação e do segmento de autopeças, com presença articulada de grandes, médias e pequenas empresas, instituições de ensino, entidades de apoio e atores de inovação. Essa heterogeneidade exige gestão estruturada de atores, elos, demandas, projetos, metas, evidências e resultados.

A planilha interna "CPLS - FORMS.xlsx" já contempla um conjunto inicial de dados para cadastro e diagnóstico: identificação da organização, elo da cadeia, atividades e produtos, canais digitais, diferenciais competitivos, faturamento, empregos, participação associativa, compartilhamento de recursos, inovação, P&D, ODS, exportação e interesse em comissões temáticas. Esses campos devem ser absorvidos pelo modelo de dados do sistema, com controles de privacidade e qualidade.

## 4. Objetivos do sistema

- Centralizar o cadastro e o histórico de empresas, instituições, pessoas, elos e relações da CPL.
- Apoiar a governança: órgãos, comissões, reuniões, decisões, planos de ação e responsabilidades.
- Estruturar o Planejamento Estratégico de Negócios, com diagnóstico, objetivos, metas, indicadores e projetos.
- Preparar e manter evidências para reconhecimento, recadastramento e classificação de maturidade no SP Produz.
- Gerenciar portfólio de projetos, planos de trabalho, cronogramas, riscos, orçamento, contrapartidas e resultados.
- Monitorar impactos econômicos, sociais, ambientais, tecnológicos e de internacionalização.
- Gerar relatórios, painéis e documentos oficiais com rastreabilidade e versionamento.
- Facilitar a conexão da CPL com universidades, ICTs, centros de inovação, programas de fomento e ambientes SPAI.

## 5. Escopo funcional

### 5.1 Incluído no escopo

- Gestão de usuários, perfis, entidades e membros da CPL.
- Mapeamento da cadeia produtiva e do ecossistema de apoio.
- Governança, reuniões, deliberações e planos de ação.
- Planejamento estratégico, maturidade e gestão de evidências.
- Editais, inscrições, recursos, fomento e instrumentos de parceria.
- Projetos, metas, indicadores, riscos, orçamento e prestação de contas.
- Formulários, pesquisas, importação de dados e comunicação.
- Dashboards gerenciais e portal público de transparência.
- Integrações e APIs para fontes externas autorizadas.

### 5.2 Fora do escopo inicial

- Sistema contábil completo ou ERP financeiro da entidade gestora.
- Folha de pagamento, gestão fiscal ou emissão de notas fiscais.
- Sistema de compras públicas completo; o SIG-CPL apenas organiza demandas, pesquisas de preços, documentos e aprovações do projeto.
- Substituição da plataforma oficial do Governo do Estado; o sistema deverá preparar, validar e exportar informações para submissão oficial.
- Decisão automática de habilitação ou maturidade sem validação humana.

## 6. Partes interessadas e perfis de acesso

| Perfil | Responsabilidade principal |
|---|---|
| Administrador da plataforma | Configuração global, segurança, integrações e suporte técnico. |
| Entidade gestora da CPL | Administração do cadastro, governança, planejamento, projetos, documentos e submissões. |
| Dirigente da entidade gestora | Aprovações, assinaturas, declarações e envio de propostas. |
| Conselho/Comitê de governança | Deliberação, priorização de projetos e acompanhamento estratégico. |
| Comissões temáticas | Execução de planos de ação por tema: inovação, qualificação, sustentabilidade, exportação etc. |
| Empresa ou organização membro | Atualização de dados, resposta a pesquisas, participação em ações e acesso a informações autorizadas. |
| Instituição de ensino/ICT/ambiente SPAI | Oferta de competências, laboratórios, projetos de P&D, capacitação e apoio tecnológico. |
| Analista/Avaliador interno | Análise de evidências, conformidade, maturidade e qualidade documental. |
| Gestor de projeto | Plano de trabalho, execução, metas, orçamento, riscos e relatórios. |
| Auditoria/Controle | Consulta a trilhas, documentos, despesas, evidências e prestações de contas. |
| Público externo | Acesso ao portal de transparência, notícias, resultados agregados e oportunidades. |

> **Nota de implementação (SIG-CPL, este repo):** o enum `Papel` em
> `app/models/enums.py` mapeia estes 11 perfis 1:1 (com nomes em
> `snake_case` ASCII). O RBAC implementado (`app/core/rbac.py`) os agrupa
> em conjuntos por responsabilidade — ver `README.md`, seção "Controle de
> acesso (RBAC)".

## 7. Visão macro da solução

| Módulo | Capacidade |
|---|---|
| 1. Identidade e acesso | Autenticação, perfis, permissões, MFA, consentimentos e auditoria. |
| 2. Cadastro e cadeia | Empresas, instituições, pessoas, produtos, competências, elos, geolocalização e relações. |
| 3. Governança | Órgãos, comissões, reuniões, atas, deliberações, votação e tarefas. |
| 4. Estratégia e maturidade | Diagnóstico, PEN, metas, critérios, evidências, pontuação, reconhecimento e recadastro. |
| 5. Projetos e fomento | Portfólio, plano de trabalho, editais, orçamento, cronograma, riscos, execução e prestação de contas. |
| 6. Indicadores e BI | KPIs econômicos, sociais, ambientais, tecnológicos e painéis. |
| 7. Comunicação e conhecimento | Agenda, notificações, eventos, capacitações, repositório e portal público. |
| 8. Integrações | APIs, importações, exportações, assinatura eletrônica, dados públicos e sistemas institucionais. |

## 8. Requisitos funcionais macros

**Prioridades:** M = obrigatório para o MVP; S = importante para a primeira evolução; C = desejável em evolução posterior.

### Plataforma e configuração

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-001 | Permitir cadastrar e configurar uma ou mais CPLs, mantendo isolamento lógico de dados e parâmetros por CPL. | M | ✅ Implementado (`CPL`, `/api/cpls` + `PATCH /api/cpls/{id}`, UI em `/painel/cpls`) |
| RF-002 | Disponibilizar área restrita e portal público com conteúdos e permissões distintos. | M | ✅ Implementado (`/painel`, `/`) |
| RF-003 | Permitir parametrizar editais, etapas, critérios, pesos, prazos, documentos e níveis de maturidade sem alteração de código. | M | ❌ Pendente (depende do módulo de Maturidade/Editais) |

### Identidade e acesso

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-004 | Autenticar usuários por e-mail e senha, com recuperação segura e opção de MFA para perfis críticos. | M | ⚠️ Parcial — login/senha com bcrypt+JWT ok; recuperação de senha e MFA **não implementados** |
| RF-005 | Aplicar controle de acesso por papéis, CPL, entidade, projeto, comissão e tipo de dado. | M | ✅ Implementado — papel+CPL+entidade+comissão/órgão+projeto (`verificar_participacao_orgao`, escopo de CPL para Entidade/Pessoa, `PAPEIS_PROJETO_LEITURA`/`PAPEIS_PROJETO_GESTAO` escopados por CPL para demandas/portfólio). Não há RBAC granular por-projeto-específico (ex.: só o `responsavel_id` daquele projeto poder editá-lo) — é por papel escopado à CPL, igual ao resto do sistema |

### Cadastro de atores

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-006 | Cadastrar empresas, órgãos públicos, universidades, ICTs, associações, prestadores e ambientes de inovação. | M | ✅ Implementado (`Entidade`) |
| RF-007 | Cadastrar responsáveis, representantes legais, contatos e vínculos com histórico de vigência. | M | ✅ Implementado (`Pessoa`, `PessoaVinculo`) |
| RF-008 | Registrar CNPJ/CPF quando necessário, CNAE, porte, endereço, município, contatos, situação cadastral e documentos. | M | ✅ Implementado (campos em `Entidade`) |

### Mapeamento da cadeia

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-009 | Classificar cada ator nos elos da cadeia: insumos, produção, transformação, comercialização/distribuição e apoio institucional, admitindo múltiplos elos. | M | ✅ Implementado (`EntidadeElo`) |
| RF-010 | Registrar produtos, serviços, tecnologias, certificações, diferenciais competitivos, canais digitais e capacidade produtiva. | M | ❌ Pendente |
| RF-011 | Georreferenciar atores e exibir mapa da concentração territorial e das relações da cadeia. | S | ❌ Pendente |

### Formulários e dados

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-012 | Criar formulários configuráveis, pesquisas diagnósticas e campanhas de atualização cadastral. | M | ⚠️ Parcial — implementado como campanha + link público de autopreenchimento (`CampanhaCadastral`/`CampanhaConvite`), reaproveitando os campos já modelados em `Entidade`/`DiagnosticoCadastral`; **não** é um construtor de formulário genérico (decisão deliberada, ver README) |
| RF-013 | Importar dados de planilhas, com pré-validação, tratamento de duplicidades, relatório de erros e trilha de origem. | M | ✅ Implementado (`ImportacaoLote`/`ImportacaoLinha`, CSV/XLSX, dedup por CNPJ) — mapeamento automático por nome de cabeçalho, com **remapeamento manual** quando a sugestão erra ou deixa campo sem coluna (fluxo em 2 passos: upload → conferir/ajustar mapeamento → confirmar). Planilha real "CPLS - FORMS.xlsx" ainda não foi anexada para calibrar os aliases, mas isso já não bloqueia a importação |
| RF-014 | Aplicar regras de qualidade: campos obrigatórios, máscaras, consistência, unicidade e validade temporal. | M | ⚠️ Parcial — obrigatoriedade de razão social, normalização de CNPJ/UF e dedup por CNPJ implementados; sem máscaras de campo nem validade temporal |

### Governança

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-015 | Cadastrar estrutura de governança, estatuto/regimento, órgãos, mandatos, composição, competências, quórum e periodicidade. | M | ✅ Implementado (`OrgaoGovernanca`) |
| RF-016 | Criar conselhos, câmaras, grupos e comissões temáticas, com membros, papéis e vigência. | M | ✅ Implementado (`OrgaoGovernanca`, `MembroOrgao`) |
| RF-017 | Gerenciar agenda, convocação, pauta, presença, anexos, ata e registro de reuniões. | M | ⚠️ Parcial — tudo exceto anexos de arquivo (`Reuniao`, `Presenca`) |
| RF-018 | Registrar deliberações, votações, quórum, impedimentos, responsáveis, prazos e evidências de execução. | M | ✅ Implementado (`Deliberacao`, `VotoRegistro`) |
| RF-019 | Controlar tarefas e planos de ação decorrentes de decisões, com alertas e status. | M | ⚠️ Parcial — tarefas/status ok (`TarefaGovernanca`); alertas automáticos **não** |
| RF-020 | Registrar declaração de conflito de interesses e impedimentos em avaliações ou deliberações. | S | ✅ Implementado (`DeclaracaoImpedimento`) |

### Estratégia

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-021 | Estruturar o Planejamento Estratégico de Negócios com caracterização, histórico, cadeia, governança, mercado, inovação, impactos e internacionalização. | M | ✅ Implementado (`PlanejamentoEstrategico` — "cadeia" e "governança" não duplicadas como texto, referenciam os módulos próprios) |
| RF-022 | Permitir diagnóstico SWOT, problemas prioritários, demandas e análise de lacunas dos elos. | M | ✅ Implementado (`DiagnosticoItem`) |
| RF-023 | Cadastrar objetivos, metas de curto/médio/longo prazo, responsáveis, indicadores, iniciativas e orçamento estimado. | M | ✅ Implementado (`ObjetivoEstrategico`, `MetaEstrategica`, `IniciativaEstrategica`, `IndicadorEstrategico`) |

### Maturidade

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-024 | Manter matriz de critérios de maturidade por edição do edital e nível de classificação. | M | ✅ Implementado — `Edital` (global, gerido só por `ADMINISTRADOR_PLATAFORMA`, RN-006) + `CriterioMaturidade` (dimensão, peso, nota de corte, por edital) |
| RF-025 | Associar evidências documentais e dados quantitativos a cada critério, com validade, autoria e versão. | M | ⚠️ Parcial — `AvaliacaoCriterio` liga nota + evidência (reaproveita `Documento`, RF-042) + observação por critério. "Validade" e "versão" da evidência em si não são modeladas — dependem do versionamento do `Documento` já existente, não algo novo aqui |
| RF-026 | Calcular pontuação, simular cenários e indicar lacunas, sem substituir a decisão humana. | M | ⚠️ Parcial — pontuação (média ponderada) e lacunas (nota abaixo do corte do critério) calculadas automaticamente ao concluir a avaliação; nível **sugerido** também é calculado, mas só vira o nível oficial da CPL com decisão humana explícita (RN-016, `Avaliacao.nivel_decidido`). "Simular cenários" (interativo, ver efeito de mudar uma nota antes de salvar) não foi construído — recorte de escopo deliberado |

### Reconhecimento

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-027 | Gerenciar fluxo de habilitação jurídica, planejamento estratégico, avaliação de maturidade, resultados e recursos. | M | ⚠️ Parcial — avaliação de maturidade (`Avaliacao`/`AvaliacaoCriterio`), resultado (nível sugerido/decidido) e recursos (`RecursoAvaliacao`, decidido por administrador) implementados. "Habilitação jurídica" não tem modelo próprio — poderia reaproveitar o repositório de Documentos (RF-042) como checklist, mas não foi formalizado como etapa do fluxo. Planejamento estratégico já existe como módulo próprio (RF-021 a RF-023) |
| RF-028 | Controlar prazo de validade do reconhecimento e processo de recadastramento bienal, com alertas antecipados. | M | ✅ Implementado — decidir o nível de uma avaliação renova `CPL.data_validade_reconhecimento` por um ciclo bienal (RN-005) automaticamente; `GET /api/maturidade/cpls/vencimento-proximo` e o banner em `/painel/maturidade` alertam CPLs com reconhecimento vencendo ou vencido |

### Editais

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-029 | Cadastrar editais, cronogramas, requisitos, documentos, responsáveis e marcos de submissão. | M | ✅ Implementado — `EditalFomento` (`app/models/projeto.py`), distinto do `Edital` de maturidade (critérios/notas de avaliação, domínio diferente apesar do nome igual). Global, não escopado a uma CPL. Título, descrição, requisitos e documentos exigidos (texto livre — sem checklist estruturado, mudar `Documento.cpl_id` de `NOT NULL` pra aceitar documento global seria mudança maior do que esta fatia), datas de abertura/encerramento (encerramento = marco de submissão) e responsável. Gestão restrita a `PAPEIS_EDITAL_GESTAO` (só administrador da plataforma, mesmo grupo do edital de maturidade), leitura `PAPEIS_PROJETO_LEITURA`. `POST/GET/PATCH /api/projetos/editais-fomento`, UI em `/painel/projetos` + `/painel/projetos/editais-fomento/{id}`. Submissão de projeto ao edital: `POST /api/projetos/{id}/submeter`, seta `Projeto.edital_fomento_id` e move `estagio` para `SUBMETIDO` na mesma ação |
| RF-030 | Gerenciar recursos, contrarrazões, diligências, respostas e decisões com controle de prazo e protocolo. | S | ✅ Implementado — `RecursoSubmissaoProjeto`: `tipo` (`TipoRecursoSubmissao`: recurso/contrarrazão/diligência), protocolo, prazo, descrição e decisão (reaproveita `StatusRecurso` — pendente/deferido/indeferido — mesmo enum de `RecursoAvaliacao`/RF-027). Lista sem limite por projeto (diferente de `RecursoAvaliacao`, que é 1:1) — o processo real vai e volta (diligência → resposta → nova diligência ou decisão). Decisão restrita a `PAPEIS_EDITAL_GESTAO` (autoridade diferente de quem gere o projeto), mesmo raciocínio do RF-027. `POST/GET /api/projetos/{id}/recursos-submissao`, `POST /api/projetos/recursos-submissao/{id}/decidir`, UI na tela de detalhe do projeto |

### Projetos

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-031 | Cadastrar demandas coletivas e oportunidades de projeto originadas por empresas, comissões, instituições e editais. | M | ✅ Implementado — `DemandaProjeto` (`app/models/projeto.py`): título, descrição, origem (`OrigemDemanda` — empresa/comissão/instituição/edital, com referência solta `origem_id`/`origem_detalhe`, mesmo padrão de `RegistroAuditoria.entidade_id`) e status até virar projeto ou ser rejeitada |
| RF-032 | Gerenciar portfólio, priorização, estágio, eixo do SP Produz, responsável e vínculo ao planejamento estratégico. | M | ✅ Implementado — `Projeto`: estágio (`EstagioProjeto`, ciclo completo modelado mas só estágios iniciais em uso), prioridade, eixo do SP Produz (texto livre — documento não define uma lista fechada de eixos), responsável (`Pessoa`) e vínculo a `ObjetivoEstrategico` do planejamento estratégico. `GET/POST /api/projetos/cpls/{id}/projetos`, `PATCH /api/projetos/{id}`, UI em `/painel/projetos`. Plano de trabalho (RF-033), RF-034 completo (etapas/cronograma, metas, indicadores, riscos, impactos socioambientais), RF-035 completo (continuidade, escalabilidade, equipe, origem de recursos, aquisições, cronograma físico-financeiro) e financeiro (RF-036 a RF-038: cotações, desembolsos) também implementados. Execução (RF-039/040) ainda não faz parte deste módulo |

### Plano de trabalho

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-033 | Estruturar informações básicas, introdução, objeto, objetivos, justificativa e impactos do projeto. | M | ✅ Implementado — campos novos direto em `Projeto` (`introducao`, `objeto`, `objetivos`, `justificativa`, `impactos`; "informações básicas" já cobertas por `titulo`/`descricao`/`eixo_sp_produz` do RF-032) — 1:1 com o projeto, sem entidade `PlanoDeTrabalho` separada. `POST /painel/projetos/{id}/plano-de-trabalho` (web) e `PATCH /api/projetos/{id}` (API, mesmo endpoint do portfólio). RF-034 e RF-035 completos também implementados — ver linhas próprias |
| RF-034 | Estruturar etapas, atividades, cronograma, metas quantitativas e qualitativas, resultados, indicadores, riscos e impactos socioambientais. | M | ✅ Implementado — **etapas/atividades/cronograma**: `EtapaProjeto`, etapa e atividade tratadas como o mesmo nível (mesma simplificação de `TarefaGovernanca`, sem sub-tarefas), `data_inicio`/`data_fim` previstos, `ordem` (auto-incrementada) e status (`StatusTarefa`, reaproveitado). **Metas** quantitativas/qualitativas: `MetaProjeto` (`TipoMeta`), `valor_alvo`/`valor_alcancado` (só valor mais recente, sem série histórica), prazo, responsável, status. **Indicadores**: `IndicadorProjeto`, versão mais simples do que `IndicadorEstrategico` (RF-044), sem série histórica própria. **Riscos**: `RiscoProjeto` — probabilidade (`ProbabilidadeRisco`), impacto (`ImpactoRisco`), resposta/mitigação, status (`StatusRisco`); modelo desenhado pra ser estendido pelo RF-040 (Execução) quando pedir mais detalhe, não duplicado. **Impactos socioambientais**: campo `Text` a mais em `Projeto` (1:1, mesmo padrão do RF-033), distinto do campo "impactos" geral do RF-033. `POST/GET /api/projetos/{id}/{etapas,metas,indicadores,riscos}`, `PATCH /api/projetos/{etapas,metas,indicadores,riscos}/{id}`, UI em `/painel/projetos/{id}` |
| RF-035 | Estruturar continuidade, escalabilidade, equipe, aquisições, origem dos recursos e cronograma físico-financeiro. | M | ✅ Implementado — **continuidade/escalabilidade**: campos `Text` a mais em `Projeto` (mesmo padrão do RF-033/034), no mesmo form de plano de trabalho. **Equipe**: `EquipeProjeto` — pessoa, função (texto livre), vigência (`data_inicio`/`data_fim`, `ativo`), mirror de `MembroOrgao` (RF-016); não reaproveita `PessoaVinculo` (RF-007), que é sobre papel de acesso, não função no projeto. **Origem dos recursos**: `OrigemRecursoProjeto` — fonte (texto livre), valor (`Numeric(14,2)`, primeiro campo monetário do sistema), contrapartida (booleana). **Cronograma físico-financeiro**: não é entidade nova — `valor_previsto`/`valor_executado` (`Numeric`) direto em `EtapaProjeto`, completando o lado financeiro do que já era o lado físico (datas/status). **Aquisições**: `AquisicaoProjeto` — item, descrição, categoria e quantidade (texto livre), valor estimado, data prevista, responsável, status (`StatusTarefa`); estendida pelo RF-036/037 — ver linhas próprias. `POST/GET /api/projetos/{id}/{equipe,origens-recurso,aquisicoes}`, `PATCH /api/projetos/{equipe,origens-recurso,aquisicoes}/{id}`, UI em `/painel/projetos/{id}` |

### Financeiro de projeto

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-036 | Cadastrar itens de despesa, quantidades, valores, categorias, fontes, contrapartida e vinculação a etapas. | M | ✅ Implementado — não é uma tabela nova: `AquisicaoProjeto` (RF-035) estendida com `etapa_id` (vinculação a etapas), `origem_recurso_id` (fonte) e `contrapartida` (booleana) — RF-036 é o mesmo item de aquisição visto pelo ângulo financeiro, não um `ItemDespesaProjeto` duplicado |
| RF-037 | Anexar pesquisas de preço e cotações, validar quantidade mínima de fornecedores e registrar justificativas de exceção. | M | ✅ Implementado — `CotacaoAquisicao`: fornecedor, valor, anexo opcional via Documentos (RF-042), `selecionada`. Validação de quantidade mínima é regra de negócio de verdade: `POST /api/projetos/cotacoes/{id}/selecionar` conta as cotações da aquisição e exige `justificativa_excecao` (em `AquisicaoProjeto`, não na cotação) se houver menos que `MINIMO_COTACOES` (constante `= 3` — não fixado no documento de requisitos, prática comum de pesquisa de mercado no setor público brasileiro); seleção desmarca a vencedora anterior da mesma aquisição. `POST/GET /api/projetos/aquisicoes/{id}/cotacoes` |
| RF-038 | Controlar desembolsos, saldos, comprovações, bens adquiridos e conciliação por projeto. | S | ✅ Implementado — `DesembolsoProjeto`: data, valor, aquisição e origem de recursos ligadas (opcionais), bem adquirido (texto livre), comprovante via Documentos, `conciliado` (booleano). "Saldos" não é armazenado — calculado a cada carregamento (`OrigemRecursoProjeto.valor` menos soma dos desembolsos ligados). "Conciliação por projeto" é a leitura agregada da tabela de desembolsos, não uma entidade própria. `POST/GET /api/projetos/{id}/desembolsos`, `PATCH /api/projetos/desembolsos/{id}` |

### Execução

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-039 | Acompanhar execução física e financeira, entregas, marcos, alterações de plano e aprovações. | M | ❌ Pendente |
| RF-040 | Gerenciar riscos com probabilidade, impacto, resposta, responsável e evidência de mitigação. | M | ❌ Pendente |

### Prestação de contas

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-041 | Gerar relatório de execução do objeto, relatório financeiro e dossiê de evidências. | S | ❌ Pendente |

### Documentos

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-042 | Manter repositório com classificação, metadados, versão, validade, assinatura, aprovação e retenção. | M | ✅ Implementado (`Documento` — categoria, confidencialidade, versionamento por `documento_anterior_id`, validade, aprovado/assinado, retenção; arquivo em disco via `app/services/armazenamento.py`) |
| RF-043 | Gerar documentos padronizados em PDF/DOCX e pacotes de submissão com índice e checklist. | M | ⚠️ Parcial — só exportação de ata de reunião em PDF (`gerar_pdf_ata`); "pacote de submissão com índice e checklist" depende do módulo de Editais/Reconhecimento (Fase 2), ainda não construído; DOCX não implementado |

### Indicadores

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-044 | Manter catálogo de indicadores com fórmula, fonte, periodicidade, responsável, meta e série histórica. | M | ✅ Implementado — `IndicadorEstrategico` ganhou `fonte` e `responsavel_id`; `IndicadorValorHistorico` guarda a série (cada aferição, não só o valor atual). Catálogo consolidado (através de todos os ciclos de planejamento de uma CPL) em `/painel/indicadores` e `GET /api/indicadores/cpls/{id}/catalogo` |
| RF-045 | Disponibilizar painéis de governança, maturidade, projetos, finanças e impacto territorial. | M | ⚠️ Parcial — painel de governança (`/painel`) + painel consolidado de governança/planejamento/cadastro por CPL (`/painel/indicadores/cpls/{id}`). Projetos tem uma tela de portfólio (`/painel/projetos/cpls/{id}`, lista + filtros visuais) e detalhe com plano de trabalho e financeiro completos (RF-034 a RF-038), mas não um "painel" de indicadores agregados como os outros módulos. Maturidade, finanças e impacto territorial não têm painel próprio — maturidade porque não foi priorizado ainda, finanças/impacto territorial porque dependem de execução do módulo de Projetos (RF-039/040), ainda não construída |
| RF-046 | Monitorar empresas participantes, empregos diretos/indiretos, novos empregos, faturamento por faixa, inovação, qualificação e cooperação. | M | ✅ Implementado — `resumo_cadastral()` agrega empresas vinculadas, empregos diretos/indiretos, faturamento por faixa e % de inovação/associativismo a partir do `DiagnosticoCadastral`. "Novos empregos" (variação no tempo) agora é calculável via `DiagnosticoCadastralHistorico` (snapshot de empregos a cada atualização de diagnóstico — API, formulário público de campanha e importação); "qualificação" ganhou campo próprio (`oferece_qualificacao_colaboradores`/`descricao_qualificacao`) |
| RF-047 | Monitorar ODS, sustentabilidade, exportação, contatos internacionais, certificações e digitalização. | S | ✅ Implementado — ODS mais citados e % de exportação já cobertos; sustentabilidade, contatos internacionais, certificações (com lista dos mais citados, mesmo padrão de ODS) e nível de digitalização ganharam campo próprio em `DiagnosticoCadastral` e passaram a ser coletados pelos 3 pontos de escrita (API, formulário público, importação de planilha) |

### Relatórios

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-048 | Gerar relatórios executivo, anual, de recadastramento, de comissão, de projeto e de impacto. | M | ✅ Implementado, exceto "de projeto" — **executivo** (acumulado desde sempre), **de recadastramento** (nível de maturidade vigente, validade, lacunas, histórico de avaliações), **anual** (mesma base do executivo, recortada a um ano-calendário), **de comissão** (`POST /api/governanca/orgaos/{id}/relatorio-comissao` — escopado a um único órgão de governança em vez de toda a CPL: membros ativos, reuniões, deliberações e tarefas daquele órgão específico; serve qualquer `TipoOrgao`, não só comissão temática) e **de impacto** (`POST /api/indicadores/cpls/{id}/relatorio-impacto` — recorte do resumo cadastral do RF-046/047 focado em sustentabilidade/ODS/exportação/certificações/empregos/inovação, sem consolidar governança/planejamento como o executivo; reaproveita `resumo_cadastral()` sem nenhuma agregação nova) construídos, todos salvos no repositório de Documentos. Só **"de projeto"** falta — o módulo de Projetos agora tem RF-029 a RF-038 completos (fundação, plano de trabalho, edital de fomento, submissão, equipe, recursos, aquisições, cronograma físico-financeiro, cotações, desembolsos), mas ainda sem execução e prestação de contas (RF-039 a RF-041) que um relatório de projeto precisaria consolidar |

### Comunicação

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-049 | Enviar notificações de prazos, pendências, reuniões, tarefas, validade documental e metas. | M | ✅ Implementado — `Notificacao` (`app/models/notificacao.py`) + `app/services/notificacoes.py::gerar_notificacoes()`, cobrindo as 5 fontes citadas: reunião agendada nos próximos 7 dias (aos membros ativos do órgão), tarefa/meta com prazo vencendo ou vencido (ao responsável), documento perdendo validade (a quem criou), e recadastramento de CPL vencendo em até 90 dias — RN-005 (aos administradores da plataforma). "Enviar" é dentro do próprio sistema (`/painel/notificacoes`, `GET /api/notificacoes`), não e-mail/push — não há esse canal hoje. Sem agendador/worker (sem Celery/cron neste stack): a varredura roda sob demanda, sempre que a tela/endpoint é acessado, idempotente (nunca duplica o mesmo aviso) |
| RF-050 | Gerenciar eventos, capacitações, mentorias, missões técnicas, inscrições, presença e avaliação. | S | ❌ Pendente |

### Conhecimento

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-051 | Manter biblioteca de modelos, atas, estudos, boas práticas, editais, oportunidades e conteúdos técnicos. | S | ❌ Pendente |

### Ecossistema

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-052 | Realizar matchmaking entre demandas das empresas e competências de universidades, ICTs, fornecedores, startups e ambientes SPAI. | C | ❌ Pendente |

### Integrações

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-053 | Disponibilizar API e importação/exportação em XLSX, CSV, PDF e formatos interoperáveis. | M | ⚠️ Parcial — API REST/JSON completa existe; import/export XLSX/CSV/PDF **não** |
| RF-054 | Integrar, quando autorizado e tecnicamente disponível, com assinatura eletrônica, dados cadastrais públicos, BI e sistemas institucionais. | S | ❌ Pendente |

### Transparência

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-055 | Publicar informações agregadas, governança, agenda, resultados e projetos autorizados, sem exposição de dados pessoais ou sigilosos. | S | ❌ Pendente (portal público hoje é só institucional/estático) |

### Administração

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-056 | Disponibilizar trilha de auditoria, logs, gestão de parâmetros, tabelas auxiliares, perfis e retenção. | M | ✅ Implementado — `RegistroAuditoria` (`app/models/auditoria.py`), captura automática de criação/atualização/exclusão via listener SQLAlchemy (`app/services/auditoria.py`) + registro explícito de login e download; leitura em `/api/auditoria` e `/painel/auditoria`, com paginação real (offset/limite, `X-Total-Count` na API; página anterior/próxima na web) e visão global (`/api/auditoria/global`, `/painel/auditoria/global`) para eventos sem CPL resolvível (login, criação de `Usuario`/`Pessoa`/CPL), restrita ao administrador da plataforma. "Gestão de parâmetros/tabelas auxiliares/perfis" não tem tela dedicada própria (fica coberto indiretamente pela trilha de qualquer alteração nos modelos existentes, incl. `UsuarioPapel`) |

### Assistência inteligente

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-057 | Oferecer, em evolução futura, apoio de IA para síntese, verificação de consistência e sugestão de lacunas, com revisão humana obrigatória. | C | ❌ Pendente (evolução futura, fora do MVP) |

## 9. Regras de negócio principais

| ID | Regra de negócio |
|---|---|
| RN-001 | O sistema deve distinguir claramente CPL, entidade gestora, entidade membro, pessoa e ambiente de inovação. |
| RN-002 | A entidade gestora é responsável pela representação formal da CPL nos processos de reconhecimento e fomento. |
| RN-003 | Uma organização pode participar de mais de uma CPL, mas seus dados e permissões devem ser tratados por vínculo. |
| RN-004 | Os quatro níveis de maturidade devem ser parametrizáveis: Aglomerado Produtivo, CPL em Desenvolvimento, CPL Consolidada e CPL Madura. |
| RN-005 | O reconhecimento possui validade temporal e deve gerar processo de recadastramento conforme regra vigente, atualmente bienal. |
| RN-006 | Critérios, pesos, notas de corte, documentos e etapas devem ser versionados por edição do edital. |
| RN-007 | Nenhuma pontuação pode ser alterada sem registro de usuário, data, justificativa e versão. |
| RN-008 | Documentos vencidos ou ilegíveis devem ser sinalizados antes da submissão. |
| RN-009 | A submissão oficial somente poderá ser marcada como concluída após checklist e aprovação do dirigente autorizado. |
| RN-010 | Metas devem possuir tipo, valor-alvo, prazo, responsável, método de aferição e evidência. |
| RN-011 | Indicadores devem estar ligados a objetivos, etapas, resultados e fonte de dados. |
| RN-012 | Itens de orçamento devem estar associados a fonte, categoria, etapa e documentação de preço. |
| RN-013 | Alterações de plano de trabalho após aprovação devem seguir fluxo de solicitação, justificativa e autorização. |
| RN-014 | Dados pessoais e informações empresariais sensíveis somente serão exibidos a perfis autorizados. |
| RN-015 | Informações publicadas no portal público devem ser agregadas e submetidas a aprovação editorial. |
| RN-016 | Decisões de maturidade, habilitação e priorização não podem ser tomadas exclusivamente por algoritmo. |

> **Status de implementação das RN:** RN-001, RN-003, RN-004 e RN-007 estão
> refletidas no modelo de dados/RBAC atual — RN-007 em particular ganhou
> reforço concreto com a trilha de auditoria (RF-056): qualquer alteração
> em qualquer registro do sistema agora fica com usuário, data e valor
> anterior/novo automaticamente, sem depender de cada módulo implementar
> isso por conta própria (falta só "justificativa" como campo dedicado,
> hoje coberto de forma ad-hoc por campos como `evidencia_execucao` em
> `Deliberacao`/`TarefaGovernanca`, não de forma genérica). RN-010 está
> implementada em `MetaEstrategica`
> (tipo/valor-alvo/prazo/responsável/método/evidência). RN-011 também está
> implementada: `IndicadorEstrategico` liga indicador a objetivo (via
> `objetivo_id`, que por sua vez liga a metas/etapas) e a fonte de dados
> (`fonte`, novo campo). RN-005 e RN-006 também estão implementadas: o
> reconhecimento tem validade e recadastro bienal automático (`Avaliacao`
> → `CPL.data_validade_reconhecimento`), e `Edital`/`CriterioMaturidade`
> são versionados por edição, cada um com seus próprios pesos/notas de
> corte. RN-016 (decisão de maturidade não pode ser só algorítmica) é
> reforçada em código, não só em política: `concluir_avaliacao()` calcula
> um nível *sugerido*, mas só `decidir_nivel()` — que exige uma chamada
> humana explícita separada — atualiza `CPL.nivel_maturidade` de verdade.
> As demais (RN-002, RN-008, RN-009, RN-012 a RN-015; RN-016 também
> cobre "habilitação" e "priorização", que ainda não têm fluxo próprio)
> dependem de módulos ainda não construídos (Projetos, Portal público
> avançado).

## 10. Modelo conceitual de dados

| Entidade conceitual | Descrição | Status no repo |
|---|---|---|
| CPL | Identificação, setor, território, entidade gestora, reconhecimento, nível e vigência. | ✅ `CPL` |
| Entidade | Empresa, órgão, associação, universidade, ICT, startup, fornecedor ou ambiente de inovação. | ✅ `Entidade`, `EntidadeCPL` |
| Pessoa e vínculo | Representante, papel, mandato, contato, consentimento e relação com entidades/CPL. | ✅ `Pessoa`, `PessoaVinculo` |
| Elo e oferta | Elo da cadeia, produto, serviço, tecnologia, competência, certificação e capacidade. | ⚠️ Elo ok (`EntidadeElo`); produto/serviço/competência (RF-010) pendente |
| Governança | Órgão, comissão, mandato, reunião, presença, votação, decisão e tarefa. | ✅ Completo (módulo Governança) |
| Planejamento | Diagnóstico, objetivo, meta, iniciativa, indicador e risco. | ⚠️ Completo exceto "risco" (não modelado ainda) |
| Maturidade | Edital, critério, peso, evidência, avaliação, nota, parecer e nível. | ✅ `Edital`, `CriterioMaturidade`, `Avaliacao`, `AvaliacaoCriterio`, `RecursoAvaliacao` |
| Projeto | Demanda, proposta, eixo, plano de trabalho, equipe, etapa, atividade, entrega e resultado. | ⚠️ Parcial — `DemandaProjeto`, `Projeto` e `EtapaProjeto` implementados (demanda/proposta, eixo, portfólio, informações básicas do plano de trabalho, etapa/atividade com cronograma); equipe, entrega e resultado ainda não têm modelo próprio |
| Financeiro do projeto | Item, cotação, fornecedor, fonte, contrapartida, desembolso, comprovante e saldo. | ❌ Pendente |
| Documento | Tipo, arquivo, metadados, validade, versão, aprovação, assinatura e confidencialidade. | ✅ `Documento` |
| Evento e comunicação | Evento, inscrição, presença, notícia, aviso, notificação e campanha. | ❌ Pendente |
| Auditoria | Evento de sistema, usuário, data, objeto, ação, valor anterior e valor posterior. | ✅ `RegistroAuditoria` |

## 11. Fluxos de negócio prioritários

| Fluxo | Etapas principais | Status no repo |
|---|---|---|
| F01 – Adesão de membro | Convite/solicitação → cadastro → consentimento → validação → vínculo à CPL → classificação de elo → ativação. | ❌ Pendente (hoje cadastro é feito diretamente por quem tem papel de gestão, sem fluxo de autoatendimento) |
| F02 – Atualização diagnóstica | Criação de campanha → envio de formulário → resposta → validação → consolidação → indicadores. | ✅ **Implementado ponta a ponta** — campanha → convite (link/token) → resposta pública → consolidação em `resumo_cadastral()` (RF-046/047), exibida em `/painel/indicadores` |
| F03 – Reunião e decisão | Convocação → pauta → presença/quórum → deliberação → ata → tarefas → acompanhamento. | ✅ **Implementado ponta a ponta** (API + UI HTMX) |
| F04 – Planejamento estratégico | Diagnóstico → priorização → objetivos → metas → indicadores → aprovação → monitoramento. | ✅ **Implementado ponta a ponta** (API + UI HTMX) |
| F05 – Reconhecimento/recadastro | Edital → habilitação → PEN → evidências de maturidade → avaliação → submissão → resultado → recurso. | ⚠️ Parcial — edital → PEN (já existe) → evidências → avaliação → resultado (sugerido + decidido) → recurso todos implementados; "habilitação jurídica" e "submissão" formal não têm etapa própria no fluxo ainda |
| F06 – Projeto de fomento | Oportunidade → priorização → plano de trabalho → orçamento/cotações → aprovação → submissão → parceria. | ❌ Pendente |
| F07 – Execução do projeto | Kickoff → atividades → desembolsos → entregas → metas/indicadores → riscos → relatórios → encerramento. | ❌ Pendente |
| F08 – Prestação de contas | Consolidação física → consolidação financeira → validação → relatório → aprovação → protocolo → diligências. | ❌ Pendente |
| F09 – Oportunidade de inovação | Demanda empresarial → busca de competência → matchmaking → projeto de P&D → instrumento jurídico → acompanhamento. | ❌ Pendente |

## 12. Indicadores e painéis recomendados

| Dimensão | Indicadores exemplificativos |
|---|---|
| Governança | Número de membros ativos; participação em reuniões; deliberações executadas; tarefas vencidas; diversidade de atores. |
| Estrutura da cadeia | Empresas por porte/elo/município; lacunas de elos; concentração territorial; competências e certificações. |
| Economia e trabalho | Empregos diretos/indiretos; empregos previstos; faturamento por faixa; salário médio quando houver fonte agregada. |
| Cooperação | Parcerias, recursos compartilhados, projetos coletivos, participação associativa e frequência de interação. |
| Inovação | Inovações implantadas, projetos de P&D, empresas atendidas, startups apoiadas, tecnologias transferidas e propriedade intelectual. |
| Mercado | Canais digitais, novos produtos, expansão, exportadores, mercados-alvo e conexões internacionais. |
| Qualificação | Cursos, pessoas capacitadas, horas de formação, aderência de competências às demandas. |
| Sustentabilidade | ODS associados, eficiência, circularidade, descarbonização, impactos sociais e ambientais. |
| Maturidade | Pontuação por dimensão, lacunas, evidências pendentes, evolução entre ciclos e nível estimado. |
| Projetos | Carteira, orçamento, execução física/financeira, metas, riscos, resultados e impacto. |

## 13. Integrações e interoperabilidade

| Integração | Finalidade | Prioridade |
|---|---|---|
| Plataforma oficial SP Produz | Preparação e exportação de dados/documentos; integração direta somente se houver API oficial e autorização. | Alta |
| Assinatura eletrônica | Assinatura de atas, declarações, planos, termos e aprovações. | Alta |
| E-mail e calendário | Convocações, notificações, agendas e prazos. | Alta |
| Dados cadastrais públicos | Consulta de CNPJ, CNAE e situação cadastral, respeitando disponibilidade e termos de uso. | Média |
| Fontes estatísticas | Importação de séries agregadas de IBGE, SEADE, RAIS e outras fontes oficiais. | Média |
| BI e geoprocessamento | Conector para painéis analíticos e mapas. | Média |
| Sistemas da entidade gestora | Documentos, financeiro, protocolo ou gestão de projetos, por API ou arquivo. | Média |
| Ambientes SPAI e ICTs | Catálogo de competências, laboratórios, oportunidades e projetos de inovação. | Baixa/estratégica |

## 14. Requisitos não funcionais

| ID | Requisito | Status no repo |
|---|---|---|
| RNF-001 – Segurança | Criptografia em trânsito e em repouso; segregação de ambientes; gestão de segredos; proteção contra vulnerabilidades comuns. | ⚠️ Parcial — hash bcrypt, JWT; sem gestão formal de segredos/vault |
| RNF-002 – Privacidade | Privacy by design, minimização, finalidade, base legal, consentimento quando aplicável, direitos do titular e anonimização de relatórios. | ❌ Pendente |
| RNF-003 – Auditoria | Trilha imutável para autenticação, alterações, avaliações, aprovações, downloads e submissões. | ✅ Implementado (= RF-056) — cobre autenticação (login sucesso/falha), alterações (criação/atualização/exclusão automáticas), aprovações (captadas como alteração, ex. `Documento.aprovado`) e downloads. "Avaliações" e "submissões" ainda não existem como conceito no sistema (dependem do módulo de Editais/Fase 2) |
| RNF-004 – Disponibilidade | Meta inicial de 99,5% ao mês, a confirmar em contrato, com janela de manutenção comunicada. | N/A (infra de produção não existe ainda — só dev local) |
| RNF-005 – Continuidade | Backup automático, restauração testada e metas propostas de RPO até 24 h e RTO até 8 h, a validar. | ❌ Pendente |
| RNF-006 – Desempenho | 95% das operações de consulta em até 3 segundos em carga nominal; relatórios extensos podem ser processados de forma assíncrona. | Não testado sob carga (só uso local/dev) |
| RNF-007 – Escalabilidade | Arquitetura preparada para crescimento de usuários, documentos, CPLs, projetos e séries históricas. | ⚠️ Multi-CPL já suportado no modelo de dados |
| RNF-008 – Acessibilidade | Interface responsiva e aderente, no mínimo, a WCAG nível AA e práticas de acessibilidade digital do governo. | ⚠️ Bootstrap 5 ajuda (componentes acessíveis por padrão), mas não foi auditado formalmente |
| RNF-009 – Usabilidade | Fluxos orientados por etapas, checklists, mensagens claras, salvamento automático e prevenção de perda de dados. | ⚠️ Parcial — UI HTMX evita reload, mas sem salvamento automático de rascunho |
| RNF-010 – Interoperabilidade | APIs REST/JSON, webhooks quando cabíveis e exportação em formatos abertos. | ⚠️ REST/JSON ok; webhooks e exportação de arquivo pendentes |
| RNF-011 – Manutenibilidade | Código versionado, testes automatizados, documentação técnica, modularidade e pipeline de implantação. | ⚠️ Modular e documentado (README); **sem testes automatizados ainda**; sem Git nem CI/CD |
| RNF-012 – Observabilidade | Logs centralizados, métricas, alertas, rastreamento de falhas e painel de saúde. | ❌ Pendente (só `/api/saude` simples) |
| RNF-013 – Qualidade de dados | Dicionário de dados, validações, deduplicação, data lineage e indicadores de completude. | ❌ Pendente |
| RNF-014 – Portabilidade | Funcionamento nos navegadores modernos e em dispositivos móveis, sem dependência de plugin proprietário. | ✅ Bootstrap 5 responsivo, sem plugins |
| RNF-015 – Retenção | Política configurável de guarda, descarte e bloqueio legal de documentos e dados. | ❌ Pendente |
| RNF-016 – Localização | Idioma português do Brasil, datas, números e valores no padrão pt-BR. | ✅ Todo o sistema em pt-BR |

## 15. Segurança, LGPD e classificação da informação

- Classificar dados em públicos, internos, confidenciais e pessoais/sensíveis, com regra de acesso e publicação por classe.
- Restringir CPF, RG, telefone, e-mail pessoal, documentos societários e informações financeiras a perfis autorizados.
- Registrar base legal/finalidade do tratamento e aceite dos termos de privacidade quando aplicável.
- Permitir consulta, correção, exportação e tratamento de solicitações de titulares.
- Aplicar anonimização ou agregação em dashboards públicos e relatórios externos.
- Implementar revisão periódica de acessos, expiração de vínculos e bloqueio imediato de usuários desligados.
- Manter registro de incidentes, plano de resposta e canal de comunicação ao controlador/encarregado.

> Nenhum destes pontos está implementado além do controle de acesso por
> papel (RBAC). É um bloco inteiro pendente, tipicamente junto com o módulo
> de Documentos e a trilha de auditoria.

## 16. Arquitetura de referência em nível macro

| Camada | Componentes | Equivalente no SIG-CPL |
|---|---|---|
| Camada de experiência | Portal web responsivo, área restrita, portal público e formulários externos. | Jinja2 + HTMX + Bootstrap 5 (`app/templates`, `app/web`) |
| Camada de aplicação | Serviços de cadastro, governança, estratégia, maturidade, projetos, financeiro, documentos e comunicação. | `app/api/routes/*` (parcial — cadastro, governança, estratégia, maturidade e documentos prontos; projetos, financeiro e comunicação pendentes) |
| Camada de dados | Banco relacional, repositório de documentos, mecanismo de busca e base analítica. | PostgreSQL (`app/models`); sem repositório de documentos/busca/base analítica ainda |
| Identidade e segurança | IAM, MFA, RBAC/ABAC, criptografia, consentimento e auditoria. | JWT + bcrypt + RBAC (`app/core/security.py`, `app/core/rbac.py`) + trilha de auditoria (`app/models/auditoria.py`, `app/services/auditoria.py`); sem MFA/consentimento |
| Integração | API gateway, conectores, importação/exportação e filas de processamento. | FastAPI expõe REST direto; sem gateway, filas ou conectores externos |
| Analytics | ETL, indicadores, dashboards, georreferenciamento e relatórios. | KPIs simples no `/painel`; sem ETL, geo ou relatórios |
| Operação | Ambientes separados, CI/CD, monitoramento, backup, suporte e gestão de incidentes. | Só ambiente de desenvolvimento local (`docker-compose.yml` com Postgres); sem CI/CD nem monitoramento |

## 17. Priorização sugerida e roadmap

| Fase | Entregas principais | Status no repo |
|---|---|---|
| Fase 0 – Descoberta (4–6 semanas) | Validação de processos, matriz de perfis, dicionário de dados, protótipos, integração da planilha atual e backlog detalhado. | Pulado — este projeto começou direto na construção técnica |
| Fase 1 – MVP (3–4 meses) | Identidade, cadastro, cadeia, formulários, governança, planejamento, documentos, tarefas, indicadores básicos, relatórios e auditoria. | ✅ **Completa** (com recortes de escopo documentados por requisito). Feito: identidade, cadastro (parcial) + campanhas/importação, governança, planejamento, documentos (repositório + ata em PDF), tarefas (dentro de governança), catálogo de indicadores com série histórica (RF-044), painéis consolidados (RF-045, parcial), resumo cadastral (RF-046/047, parcial), cinco dos seis tipos de relatório em PDF (RF-048 — só "de projeto" falta), trilha de auditoria (RF-056). |
| Fase 2 – Conformidade SP Produz (2–3 meses) | Maturidade, reconhecimento/recadastro, editais, plano de trabalho, orçamento, cotações, submissões e alertas. | ⚠️ **Iniciada.** Feito: maturidade, editais/critérios, avaliação com nota/evidência/lacunas, decisão de nível (RN-016), recadastro bienal com alertas (RF-024 a RF-028); módulo de Projetos — edital de fomento com submissão e recursos/contrarrazões/diligências, demandas, portfólio e plano de trabalho completo (etapas/cronograma, metas, indicadores, riscos, impactos socioambientais, continuidade, escalabilidade, equipe, origem de recursos, aquisições, cronograma físico-financeiro) e financeiro completo (itens de despesa, cotações com validação de mínimo de fornecedores, desembolsos com saldo e conciliação) — RF-029 a RF-038, todos completos. Falta: execução e prestação de contas (RF-039 a RF-041). |
| Fase 3 – Execução e fomento (2–3 meses) | Execução física/financeira, prestação de contas, riscos, bens, relatórios e portal de transparência. | ❌ Não iniciado |
| Fase 4 – Ecossistema e inovação | Matchmaking, catálogo de competências, integração SPAI/ICTs, mapas de rede, IA assistiva e análises avançadas. | ❌ Não iniciado |

## 18. Critérios macros de aceite

1. Usuários conseguem cadastrar uma entidade e vinculá-la corretamente à CPL e a um ou mais elos. ✅
2. A entidade gestora consegue criar uma reunião, registrar ata, decisão, responsável e acompanhar a execução. ✅
3. O sistema consegue representar o planejamento estratégico, metas, indicadores e projetos vinculados. ⚠️ (projetos ainda não existem como módulo — só planejamento)
4. A matriz de maturidade pode ser configurada por edital e recebe evidências, notas, justificativas e pareceres. ❌
5. O sistema gera checklist de reconhecimento/recadastro e identifica pendências de prazo, documento e evidência. ❌
6. Um plano de trabalho completo pode ser preenchido, versionado, aprovado e exportado. ❌
7. O orçamento aceita cotações, contrapartidas e cronograma físico-financeiro, mantendo rastreabilidade. ❌
8. Dashboards apresentam indicadores consolidados sem expor dados pessoais indevidamente. ⚠️ (dashboard existe, mas não foi auditado quanto a exposição de dados pessoais)
9. Logs permitem reconstruir as principais alterações, avaliações, aprovações e submissões. ❌
10. Importação da planilha atual produz registros consistentes, relatório de inconsistências e controle de duplicidade. ❌

## 19. Premissas, riscos e dependências

| Tipo | Descrição | Tratamento |
|---|---|---|
| Premissa | A entidade gestora definirá responsáveis pelos dados, governança, documentos e atualização dos indicadores. | Formalizar papéis e rotina de governança de dados. |
| Risco | Mudança anual de editais, critérios e documentos. | Parametrização, versionamento e módulo de configuração. |
| Risco | Baixa adesão das empresas à atualização cadastral. | Campanhas, formulários simples, lembretes e benefício visível aos participantes. |
| Risco | Dados incompletos, duplicados ou divergentes. | Validações, deduplicação, aprovação e indicadores de qualidade. |
| Risco | Exposição de dados pessoais ou empresariais sensíveis. | RBAC, classificação, criptografia, anonimização e revisão de publicação. |
| Risco | Dependência de APIs públicas ou integração com plataformas oficiais. | Operação por importação/exportação quando integração direta não existir. |
| Dependência | Definição de identidade visual, domínio, hospedagem, política de privacidade e termos de uso. | Concluir antes do piloto externo. |
| Dependência | Validação jurídica dos fluxos de edital, assinatura e retenção documental. | Revisão por assessoria jurídica e encarregado de dados. |

## 20. Decisões pendentes para detalhamento

*(reproduzidas do documento original — ver também `README.md`, seção "Decisões pendentes", que soma perguntas técnicas levantadas durante a implementação)*

- O sistema será exclusivo da CPL Autopeças ou multi-CPL desde a primeira versão?
- Qual organização será a controladora dos dados e qual será a operadora tecnológica?
- Quais perfis poderão visualizar dados empresariais individuais e indicadores agregados?
- A entidade gestora utilizará assinatura gov.br, certificado ICP-Brasil ou outra solução?
- Quais sistemas municipais/institucionais deverão ser integrados?
- Qual volume inicial de usuários, empresas, documentos e projetos?
- Quais indicadores serão obrigatórios no primeiro ciclo e quais fontes os alimentarão?
- Quais documentos do edital vigente deverão ser gerados automaticamente?

## 21. Glossário

| Termo | Definição |
|---|---|
| CPL | Cadeia Produtiva Local. |
| SP Produz | Programa Estadual de Desenvolvimento das Cadeias Produtivas Locais do Estado de São Paulo. |
| SPAI | Sistema Paulista de Ambientes de Inovação. |
| PEN | Planejamento Estratégico de Negócios. |
| Entidade gestora | Pessoa jurídica que representa e administra a CPL perante o programa e demais parceiros. |
| Evidência | Documento, registro ou dado utilizado para comprovar atendimento a requisito ou resultado. |
| Maturidade | Classificação da capacidade de organização, governança, planejamento, dimensão, diversidade e impacto da CPL. |
| Contrapartida | Bens e/ou serviços economicamente mensuráveis oferecidos pela proponente, quando aplicável. |
| RPO/RTO | Objetivos de perda máxima de dados e tempo de recuperação após incidente. |
| RBAC/ABAC | Controle de acesso baseado em papéis e atributos. |

## 22. Referências

- SÃO PAULO (Estado). Decreto nº 68.648, de 25 de junho de 2024. Institui, junto à Secretaria de Desenvolvimento Econômico, o Programa Estadual de Desenvolvimento das Cadeias Produtivas Locais – Programa SP Produz.
- SÃO PAULO (Estado). Portal de Serviços ao Cidadão. Programa Estadual de Desenvolvimento das Cadeias Produtivas Locais – Programa SP Produz. Atualização indicada: 18 jul. 2025.
- SÃO PAULO (Estado). Secretaria de Desenvolvimento Econômico. Edital SDE/CDRT nº 02/2024: chamamento público para fomento de Cadeias Produtivas Locais reconhecidas ou em processo de reconhecimento no âmbito do Programa SP Produz.
- SÃO PAULO (Estado). Secretaria de Desenvolvimento Econômico. Edital SDE/SCDER nº 01/2025: chamamento público para reconhecimento de Cadeias Produtivas Locais e classificação de maturidade no âmbito do Programa SP Produz. 2025.
- SÃO PAULO (Estado). Decreto nº 60.286, de 25 de março de 2014. Institui o Sistema Paulista de Ambientes de Inovação – SPAI.
- SÃO PAULO (Estado). Decreto nº 68.636, de 20 de junho de 2024. Altera o Decreto nº 60.286/2014, relativo ao SPAI.
- BRASIL. Lei nº 13.709, de 14 de agosto de 2018. Lei Geral de Proteção de Dados Pessoais – LGPD.
- BRASIL. Lei nº 13.019, de 31 de julho de 2014. Marco Regulatório das Organizações da Sociedade Civil.
- ATIBAIA. Atibaia_AutopecasVF 1 (1).pptx. Material institucional fornecido para este levantamento, 2025. *(não anexado ao repositório)*
- ATIBAIA. CPLS - FORMS.xlsx. Base interna de formulários e respostas da CPL Autopeças, fornecida para este levantamento. *(não anexado ao repositório — necessário para RF-013)*

> **Próxima etapa recomendada (do documento original):** Validar processos, backlog, dados, perfis e protótipos em oficina multissetorial.
