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
| RF-001 | Permitir cadastrar e configurar uma ou mais CPLs, mantendo isolamento lógico de dados e parâmetros por CPL. | M | ✅ Implementado (`CPL`, `/api/cpls` + `PATCH /api/cpls/{id}`, UI em `/painel/cpls`). **Entidade gestora + usuário responsável** (pedido explícito): `/painel/cpls/{id}` (administrador) ganhou "Cadastrar nova entidade gestora" (cria a `Entidade` e já define `CPL.entidade_gestora_id`, sem precisar escolher entre as já existentes no `<select>`) e "Usuário responsável pela entidade gestora" (cria `Usuario`+`Pessoa`+`PessoaVinculo`+`UsuarioPapel`, papel `entidade_gestora` ou `dirigente_entidade_gestora` escolhido no formulário, escopado a esta CPL — até então só existia via API crua em duas chamadas separadas, sem tela nenhuma). **Setor/Município/UF viraram listbox** (pedido explícito): Setor restrito aos valores já usados por alguma CPL (`DISTINCT CPL.setor`, sem tabela nova) com um campo "outro" ao lado pra não travar o cadastro da primeira CPL de um setor novo; Estado e Município vêm da API pública de Localidades do IBGE (`app/services/localidades.py`), Estado antes de Município no formulário e Município filtrado pelo Estado escolhido via HTMX (`GET /painel/cpls/municipios-fragment`); nada é gravado no banco além dos dois campos já existentes (`CPL.municipio`/`CPL.uf`) — a lista de estados/municípios em si só fica em cache de memória do processo (`functools.lru_cache`), zero tabela nova, conforme pedido explícito de não ocupar espaço de banco |
| RF-002 | Disponibilizar área restrita e portal público com conteúdos e permissões distintos. | M | ✅ Implementado (`/painel`, `/`) |
| RF-003 | Permitir parametrizar editais, etapas, critérios, pesos, prazos, documentos e níveis de maturidade sem alteração de código. | M | ✅ Implementado — a marcação anterior ("depende do módulo de Maturidade/Editais") estava desatualizada: esse módulo existe há várias sessões, e editais/critérios/pesos/notas de corte/prazos já eram 100% parametrizáveis via UI (`criar_edital`, `criar_criterio`, `atualizar_edital`) antes desta fatia. O que faltava era só **documentos** — `RequisitoHabilitacaoEdital` (`app/models/maturidade.py`) fecha isso: template de documento exigido definido uma vez por edital (mesmo raciocínio de `CriterioMaturidade` — template — vs. `AvaliacaoCriterio` — instância; aqui é `RequisitoHabilitacaoEdital` vs. `ItemHabilitacaoJuridica`, RF-027), com `POST /api/maturidade/cpls/{id}/habilitacao/usar-requisitos-edital` instanciando o checklist da CPL a partir do template (idempotente — pula requisitos já instanciados). **Níveis de maturidade** continuam um enum Python fixo por decisão de design documentada (RN-004: "quatro níveis parametrizáveis pelo Programa SP Produz" — o que é parametrizável são os *limiares* que separam os níveis, já configuráveis por edital; os quatro nomes são definidos pelo programa estadual, não algo que cada CPL/edital deveria poder inventar) — não uma lacuna |

### Identidade e acesso

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-004 | Autenticar usuários por e-mail e senha, com recuperação segura e opção de MFA para perfis críticos. | M | ✅ Implementado — login/senha com bcrypt+JWT (já existia). **Recuperação de senha**: `TokenRecuperacaoSenha` (token de uso único, curta validade), e-mail enviado via SMTP genérico (`app/services/email.py`, configurável via `SMTP_*`, sem provedor específico embutido no código), `POST /api/auth/esqueci-senha` (sempre responde a mesma mensagem — não revela se o e-mail existe) e `POST /api/auth/redefinir-senha`; UI em `/esqueci-senha` e `/redefinir-senha/{token}`. **MFA**: TOTP (RFC 6238, `pyotp`) — "opção... para perfis críticos" implementado como recurso que qualquer usuário pode ativar (não uma obrigação por papel, já que o requisito não define uma lista fechada de "perfis críticos"), com QR code (`qrcode`) + segredo manual, confirmação em 2 passos (só ativa depois de validar um código) e 8 códigos de backup de uso único (hash, nunca texto puro). Login web em 2 etapas quando MFA ativo (cookie `mfa_pending` de 5 min, nunca aceito como sessão — ver `get_current_user`); login por API é 1 passo só (`mfa_code` no mesmo request). UI em `/painel/perfil`. Campos sensíveis (`mfa_secret`, `mfa_backup_codes`, `token`) redigidos na trilha de auditoria. **`POST /api/auth/registrar` fechado** — não tinha nenhuma restrição de acesso, mesmo em produção (achado ao construir o cadastro de "usuário responsável pela entidade gestora"); agora usa a mesma válvula de bootstrap já usada em `POST /api/usuarios/{id}/papeis`: sem autenticação só enquanto não existir nenhum `administrador_plataforma` no sistema, depois disso exige um administrador autenticado |
| RF-005 | Aplicar controle de acesso por papéis, CPL, entidade, projeto, comissão e tipo de dado. | M | ✅ Implementado — papel+CPL+entidade+comissão/órgão+projeto (`verificar_participacao_orgao`, escopo de CPL para Entidade/Pessoa, `PAPEIS_PROJETO_LEITURA`/`PAPEIS_PROJETO_GESTAO` escopados por CPL para demandas/portfólio). Não há RBAC granular por-projeto-específico (ex.: só o `responsavel_id` daquele projeto poder editá-lo) — é por papel escopado à CPL, igual ao resto do sistema. **Lacuna real encontrada e corrigida**: `Papel.EMPRESA_MEMBRO` existia no enum desde o início do projeto mas nunca tinha sido incluído em nenhum grupo `PAPEIS_*` usado pelas rotas — quem só tinha esse papel não acessava nenhuma funcionalidade (achado ao investigar por que um usuário de demonstração, `juliana.prado`, não conseguia acessar nada). Desenhado com o usuário e implementado: `PAPEIS_LEITURA_MEMBRO` dá leitura ao dashboard de indicadores da própria CPL e a eventos da própria CPL (com autoinscrição, `POST .../inscrever-me`); `entidade_e_da_pessoa()` (via `PessoaVinculo`) dá acesso à própria entidade independente de papel de governança. Governança, Documentos, Maturidade, Planejamento e Projetos continuam deliberadamente fechados pra esse papel — sem caso de uso definido ainda |

### Cadastro de atores

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-006 | Cadastrar empresas, órgãos públicos, universidades, ICTs, associações, prestadores e ambientes de inovação. | M | ✅ Implementado (`Entidade`). **Cadastro pela área restrita** (pedido explícito) — `POST /api/entidades` já era `PAPEIS_GESTAO` (administrador/entidade gestora/dirigente, exatamente os três papéis pedidos), mas não tinha formulário web nenhum, só API crua (o rodapé do card de vínculo chegava a apontar pro Swagger). `POST /painel/cadastro/cpls/{id}/entidades` (novo) cadastra e já vincula à CPL num passo só, escopado por `cpl_id` (mais estrito que a API, que não tem escopo de CPL porque nem sempre há vínculo na hora de cadastrar) |
| RF-007 | Cadastrar responsáveis, representantes legais, contatos e vínculos com histórico de vigência. | M | ✅ Implementado (`Pessoa`, `PessoaVinculo`) |
| RF-008 | Registrar CNPJ/CPF quando necessário, CNAE, porte, endereço, município, contatos, situação cadastral e documentos. | M | ✅ Implementado (campos em `Entidade`) |

### Mapeamento da cadeia

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-009 | Classificar cada ator nos elos da cadeia: insumos, produção, transformação, comercialização/distribuição e apoio institucional, admitindo múltiplos elos. | M | ✅ Implementado (`EntidadeElo`) |
| RF-010 | Registrar produtos, serviços, tecnologias, certificações, diferenciais competitivos, canais digitais e capacidade produtiva. | M | ✅ Implementado — certificações e diferenciais competitivos já existiam em `DiagnosticoCadastral` (RF-012/046). Nesta fatia: **produtos/serviços/tecnologias** — `OfertaEntidade` (`app/models/entidade.py`), tabela repetível (uma entidade pode ofertar vários), `tipo` (`TipoOferta`: produto/serviço/tecnologia), nome, descrição, `ativo` (desativação em vez de exclusão). **Canais digitais** — `Entidade.canais_digitais` (JSONB) já existia no modelo desde o RF-006/008 mas nunca tinha schema/rota/UI (campo órfão); ganhou `PATCH /api/entidades/{id}/canais-digitais` e formulário (site/Instagram/Facebook/LinkedIn/WhatsApp — conjunto fixo e conhecido, não chave livre, pelo padrão de formulário sem JS do projeto). **Capacidade produtiva** — campo novo `DiagnosticoCadastral.capacidade_produtiva` (texto livre), coletável pelos mesmos 3 pontos de escrita das demais respostas de diagnóstico (formulário público de campanha, importação de planilha via `_ALIASES_CAMPO`, API). Nova tela `/painel/cadastro/entidades/{id}` (detalhe de uma entidade — não existia nenhuma antes desta fatia; só havia lista por CPL) reúne ofertas + canais digitais + resumo do diagnóstico (ofertas/canais editáveis ali; diagnóstico continua só editável via campanha/planilha/API, mesmo padrão já estabelecido) |
| RF-011 | Georreferenciar atores e exibir mapa da concentração territorial e das relações da cadeia. | S | ✅ Implementado — `Entidade.latitude`/`longitude` (opcionais, nem toda entidade tem endereço completo o bastante pra geocodificar); geocodificação automática a partir de endereço/município/UF via Nominatim/OpenStreetMap (pública, gratuita, mesmo raciocínio do RF-054) ou definição manual; mapa da cadeia por CPL (`/painel/cadastro/cpls/{id}/mapa`, Leaflet + OSM) plotando as entidades vinculadas e geocodificadas, com marcador colorido por `tipo_entidade` como proxy visual de diversidade/relações da cadeia (`EntidadeElo` do RF-009 ainda não tem rota de CRUD própria — decisão deliberada de não plotar arestas de relação nesta rodada) |

### Formulários e dados

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-012 | Criar formulários configuráveis, pesquisas diagnósticas e campanhas de atualização cadastral. | M | ⚠️ Parcial — implementado como campanha + link público de autopreenchimento (`CampanhaCadastral`/`CampanhaConvite`), reaproveitando os campos já modelados em `Entidade`/`DiagnosticoCadastral`; **não** é um construtor de formulário genérico (decisão deliberada, ver README). **Convite passou a enviar e-mail de verdade** (achado a partir de um relato real de empresa que não recebeu o convite): até então só gerava o link/token pra a gestão copiar manualmente, apesar do ícone de envelope na tela já sugerir envio automático. `Entidade` ganhou um campo `email` próprio "de comunicações"; ao convidar, `app/services/campanhas.py::enviar_convite_email` manda pra esse e-mail **e** pra todo contato (`Pessoa`, via `PessoaVinculo` vigente) ligado à entidade, registrando no próprio convite se enviou, pra quem, e por que não quando não enviou — sem bloquear a criação do convite se o SMTP falhar (o link copiável continua funcionando como alternativa). **Reenviar convite e convidar todas de uma vez** (pedidos explícitos): botão "Reenviar" em cada convite pendente (mesmo token/link, só dispara `enviar_convite_email` de novo) e botão "Convidar todas as entidades", que convida de uma vez todas as entidades da CPL ainda não convidadas na campanha, sem precisar selecionar uma por vez. **Link de diagnóstico com todos os campos da planilha de importação** (pedido explícito): comparado o formulário público (`atualizacao_form.html`) contra `CAMPOS_CONHECIDOS` (`app/services/importacao_entidades.py`) faltavam 3 dos 26 campos de `DiagnosticoCadastral` — `compartilha_recursos`, `recursos_compartilhados` e `ods_relacionados` — adicionados ao formulário. **Resumo do diagnóstico na tela da entidade** (pedido explícito, avaliação dos campos "não presentes no anexo"): o resumo em `/painel/cadastro/entidades/{id}` só mostrava 3 dos 26 campos (capacidade produtiva, diferenciais competitivos, certificações); passou a mostrar todos os campos respondidos, distinguindo "nunca respondido" (não aparece) de "respondido como Não" (aparece, já que é uma resposta de verdade). **Gap-fill contra o gabarito real da planilha "CPLS - FORMS.xlsx"** (pedido explícito, planilha finalmente anexada ao projeto como PDF estruturado — "Cadastro de Empresas Participantes das CPLs", 14 seções/59 campos): diff campo a campo contra `Entidade`/`DiagnosticoCadastral` encontrou ~29 campos ausentes, adicionados ao formulário público, à importação de planilha e ao resumo da entidade — endereço estruturado (`cep`/`numero`/`complemento`/`bairro`/`possui_filiais` em `Entidade`), responsável pela empresa (captura nome/cargo/telefone/WhatsApp/e-mail e vincula como `PessoaVinculo` — papel `EMPRESA_MEMBRO` — mesmo raciocínio de `adesao.py::_vincular_pessoa_contato`, RF-007/F01; `Pessoa` ganhou `whatsapp`), elos da cadeia (checkboxes no formulário público sincronizando `EntidadeElo` do RF-009 — ativa os marcados, desativa os desmarcados — em vez de duplicar como texto livre), capital humano granular (CLT/terceirizados/aprendizes/PCD), relacionamento na cadeia (matéria-prima principal, produto principal, compra de/vende para, parcerias institucionais), investimento e digitalização, inovação granular (produtos/processos novos, setor de P&D, patente, registro de software, marca registrada, recursos públicos), internacionalização granular (importa, clientes internacionais, feiras internacionais, interesse em exportar), demandas da empresa, e **consentimento LGPD obrigatório** no formulário público (que não pedia nenhum até então — `CampanhaConvite` ganhou `consentimento_lgpd`/`consentimento_em`, mesmo raciocínio de `SolicitacaoAdesao.consentimento_lgpd`, RF-007/F01). **ODS relacionados virou listbox de seleção múltipla** (pedido explícito) — os 17 Objetivos de Desenvolvimento Sustentável (títulos oficiais da tradução ONU Brasil) num `<select multiple>`, em vez de texto livre; `DiagnosticoCadastral.ods_relacionados` ampliado de `VARCHAR(255)` pra `Text` e o separador de itens virou `"; "` (não vírgula — vários títulos de ODS já têm vírgula, ex. "Indústria, inovação e infraestrutura", o que quebraria tanto a listbox quanto a contagem de `ods_mais_citados`; `indicadores.py::contador_lista` ganhou um parâmetro `separador` pra não afetar a contagem de `certificacoes`, que continua por vírgula). **15 campos de texto viraram `<textarea>`** (pedido explícito, aceitam quebra de linha com Enter): mercados de exportação, interesse em comissões temáticas, entidades associativas, recursos compartilhados, países/parceiros, práticas ambientais, matéria-prima/produto principal, compra de/vende para, parcerias institucionais, investimentos recentes, tecnologias utilizadas, necessidades da empresa e outras demandas |
| RF-013 | Importar dados de planilhas, com pré-validação, tratamento de duplicidades, relatório de erros e trilha de origem. | M | ✅ Implementado (`ImportacaoLote`/`ImportacaoLinha`, CSV/XLSX, dedup por CNPJ) — mapeamento automático por nome de cabeçalho, com **remapeamento manual** quando a sugestão erra ou deixa campo sem coluna (fluxo em 2 passos: upload → conferir/ajustar mapeamento → confirmar). Planilha real "CPLS - FORMS.xlsx" foi anexada ao projeto (como PDF estruturado, "Cadastro de Empresas Participantes das CPLs") — `_ALIASES_CAMPO` recalibrado contra o gabarito real (RF-012 tem o detalhe dos ~29 campos que faltavam). **Modelo de planilha pra baixar** (`/painel/cadastro/modelo-planilha?formato=xlsx\|csv`, pedido explícito dos gestores) — mesmo cabeçalho de `CAMPOS_CONHECIDOS` que a importação reconhece, sem linha de dado nenhuma; reaproveita `gerar_xlsx_entidades`/`gerar_csv_entidades` (RF-053) passando lista vazia, sem precisar de código novo nessas funções |
| RF-014 | Aplicar regras de qualidade: campos obrigatórios, máscaras, consistência, unicidade e validade temporal. | M | ✅ Implementado — obrigatoriedade de razão social e dedup por CNPJ (import) já existiam. **Máscaras**: `app/services/validadores.py` — dígito verificador oficial de CNPJ/CPF (módulo 11, não só contagem de dígitos — pega erro de digitação que 14 dígitos aleatórios não pegariam) e UF contra a lista fechada de 27 unidades da federação, reaproveitados nos três pontos de escrita de sempre (criação direta via API, importação de planilha — linha com CNPJ/CPF/UF mal formado vira erro em vez de gravar dado ruim — e formulário público de campanha, que só valida UF, já que CNPJ não é editável ali). **Validade temporal**: `diagnostico_desatualizado()` (`app/services/indicadores.py`) sinaliza (não invalida) um diagnóstico cadastral sem atualização há mais de um ano — contagem em `resumo_cadastral()` e badge na tela de detalhe da entidade |

### Governança

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-015 | Cadastrar estrutura de governança, estatuto/regimento, órgãos, mandatos, composição, competências, quórum e periodicidade. | M | ✅ Implementado (`OrgaoGovernanca`) |
| RF-016 | Criar conselhos, câmaras, grupos e comissões temáticas, com membros, papéis e vigência. | M | ✅ Implementado (`OrgaoGovernanca`, `MembroOrgao`). **Excluir membro com motivo** (pedido explícito): `MembroOrgao` ganhou `motivo_remocao` (texto); excluir é desativação (`ativo=False`, `data_fim` preenchido se ainda vazio), não `DELETE` de verdade — preserva o histórico de presenças/votos já registrados em nome desse mandato. A alteração cai sozinha na trilha de auditoria automática (RF-056), sem chamada manual: `ativo`/`motivo_remocao` aparecem no antes/depois do registro `ATUALIZACAO`. `POST /api/governanca/membros/{id}/remover` (JSON `{motivo}`) e `POST /painel/governanca/membros/{id}/remover` (form), ambos `PAPEIS_GESTAO`. **Documento de posse** (pedido explícito): `Documento` ganhou `orgao_id` opcional (mesmo padrão de `reuniao_id`, RF-017/RF-042) — anexado em `/painel/governanca/orgaos/{id}` (`POST /painel/documentos/orgaos/{id}/anexos`), aparece ali e também na lista geral de Documentos da CPL, sem trabalho extra (a listagem geral não filtra por `orgao_id`/`reuniao_id`) |
| RF-017 | Gerenciar agenda, convocação, pauta, presença, anexos, ata e registro de reuniões. | M | ✅ Implementado — `Reuniao`, `Presenca` cobrem agenda/convocação/pauta/presença/ata; **anexos de arquivo** reaproveitam o repositório de Documentos (RF-042, mesma `reuniao_id` já usada pela ata gerada em PDF, RF-043), sem entidade nova. `POST /api/documentos/cpls/{cpl_id}` aceita `reuniao_id` opcional (valida que a reunião pertence à mesma CPL do upload); `GET /api/documentos/reunioes/{reuniao_id}` lista os anexos. UI: card "Anexos" + formulário de upload em `/painel/governanca/reunioes/{id}` (rota web própria, `POST /painel/documentos/reunioes/{id}/anexos`, redireciona de volta pra tela da reunião — não pra lista geral de documentos da CPL). **Convocação** (pedidos explícitos): o formulário limpa os campos após convocar com sucesso (`hx-on::after-request="if (event.detail.successful) this.reset()"`, sem JavaScript escrito à mão) e uma mensagem de confirmação aparece via HTMX out-of-band swap (`hx-swap-oob`); **e-mail de convocação enviado a todos os membros ativos** do órgão (`app/services/governanca.py::enviar_convocacao_email`, mesmo padrão resiliente de `CampanhaConvite` — RF-012 — nunca bloqueia a convocação se o SMTP falhar, resultado gravado em `Reuniao.email_convocacao_*` e mostrado tanto na confirmação quanto, depois, na própria tela da reunião) |
| RF-018 | Registrar deliberações, votações, quórum, impedimentos, responsáveis, prazos e evidências de execução. | M | ✅ Implementado (`Deliberacao`, `VotoRegistro`) |
| RF-019 | Controlar tarefas e planos de ação decorrentes de decisões, com alertas e status. | M | ✅ Implementado — tarefas/status (`TarefaGovernanca`); alertas automáticos de prazo vencendo/vencido cobertos pelo motor de notificações do RF-049 (`_gerar_tarefas_com_prazo()` em `app/services/notificacoes.py`, ao responsável) — não uma tela separada, mesma `Notificacao` usada pelos outros 4 tipos de alerta do sistema |
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
| RF-026 | Calcular pontuação, simular cenários e indicar lacunas, sem substituir a decisão humana. | M | ✅ Implementado — pontuação (média ponderada) e lacunas (nota abaixo do corte do critério) calculadas automaticamente ao concluir a avaliação; nível **sugerido** também é calculado, mas só vira o nível oficial da CPL com decisão humana explícita (RN-016, `Avaliacao.nivel_decidido`). **Simular cenários**: `simular_avaliacao()` (`app/services/maturidade.py`) reaproveita as mesmas funções puras (`calcular_pontuacao`/`sugerir_nivel`/`lacunas`, nenhuma escreve no banco) pra mostrar, **enquanto a avaliação ainda está em andamento**, "se você concluir agora, o resultado seria X" — com as notas já lançadas até aquele momento, sem persistir nada. Mudar uma nota (já suportado, `PUT .../notas`, reaproveitável) e recarregar a tela atualiza a simulação — não precisa concluir pra ver o efeito. `GET /api/maturidade/avaliacoes/{id}/simulacao`, exibido como card na tela de detalhe da avaliação |

### Reconhecimento

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-027 | Gerenciar fluxo de habilitação jurídica, planejamento estratégico, avaliação de maturidade, resultados e recursos. | M | ✅ Implementado — avaliação de maturidade (`Avaliacao`/`AvaliacaoCriterio`), resultado (nível sugerido/decidido) e recursos (`RecursoAvaliacao`, decidido por administrador) já existiam; planejamento estratégico já existe como módulo próprio (RF-021 a RF-023). **Habilitação jurídica**: `ItemHabilitacaoJuridica` (`app/models/maturidade.py`) — checklist por CPL+edital, `descricao` livre (tipo de documento exigido — o documento de requisitos não define uma lista fechada), `documento_id` reaproveitando o repositório de Documentos (RF-042, mesmo padrão de `AvaliacaoCriterio.evidencia_documento_id`), ciclo `pendente → entregue → aprovado/rejeitado` (`StatusItemHabilitacao`). Criação/anexo de comprovante é `PAPEIS_GESTAO` (a CPL), análise (aprovar/rejeitar) é `PAPEIS_EDITAL_GESTAO` — mesma autoridade de `RecursoAvaliacao`, é o órgão externo do edital validando a regularidade jurídica, não uma decisão interna da CPL. `POST/GET /api/maturidade/cpls/{id}/habilitacao`, `POST /api/maturidade/habilitacao/{id}/analisar`, UI na tela de maturidade da CPL |
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
| RF-032 | Gerenciar portfólio, priorização, estágio, eixo do SP Produz, responsável e vínculo ao planejamento estratégico. | M | ✅ Implementado — `Projeto`: estágio (`EstagioProjeto`, ciclo completo modelado mas só estágios iniciais em uso), prioridade, eixo do SP Produz (texto livre — documento não define uma lista fechada de eixos), responsável (`Pessoa`) e vínculo a `ObjetivoEstrategico` do planejamento estratégico. `GET/POST /api/projetos/cpls/{id}/projetos`, `PATCH /api/projetos/{id}`, UI em `/painel/projetos`. Plano de trabalho (RF-033), RF-034 completo, RF-035 completo, financeiro (RF-036 a RF-038), execução (RF-039/040) e prestação de contas (RF-041) também implementados — módulo de Projetos completo (RF-029 a RF-041) |

### Plano de trabalho

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-033 | Estruturar informações básicas, introdução, objeto, objetivos, justificativa e impactos do projeto. | M | ✅ Implementado — campos novos direto em `Projeto` (`introducao`, `objeto`, `objetivos`, `justificativa`, `impactos`; "informações básicas" já cobertas por `titulo`/`descricao`/`eixo_sp_produz` do RF-032) — 1:1 com o projeto, sem entidade `PlanoDeTrabalho` separada. `POST /painel/projetos/{id}/plano-de-trabalho` (web) e `PATCH /api/projetos/{id}` (API, mesmo endpoint do portfólio). RF-034 e RF-035 completos também implementados — ver linhas próprias |
| RF-034 | Estruturar etapas, atividades, cronograma, metas quantitativas e qualitativas, resultados, indicadores, riscos e impactos socioambientais. | M | ✅ Implementado — **etapas/atividades/cronograma**: `EtapaProjeto`, etapa e atividade tratadas como o mesmo nível (mesma simplificação de `TarefaGovernanca`, sem sub-tarefas), `data_inicio`/`data_fim` previstos, `ordem` (auto-incrementada) e status (`StatusTarefa`, reaproveitado). **Metas** quantitativas/qualitativas: `MetaProjeto` (`TipoMeta`), `valor_alvo`/`valor_alcancado` (só valor mais recente, sem série histórica), prazo, responsável, status. **Indicadores**: `IndicadorProjeto`, versão mais simples do que `IndicadorEstrategico` (RF-044), sem série histórica própria. **Riscos**: `RiscoProjeto` — probabilidade (`ProbabilidadeRisco`), impacto (`ImpactoRisco`), resposta/mitigação, status (`StatusRisco`); estendido pelo RF-040 com `evidencia_documento_id` — ver linha própria. **Impactos socioambientais**: campo `Text` a mais em `Projeto` (1:1, mesmo padrão do RF-033), distinto do campo "impactos" geral do RF-033. `POST/GET /api/projetos/{id}/{etapas,metas,indicadores,riscos}`, `PATCH /api/projetos/{etapas,metas,indicadores,riscos}/{id}`, UI em `/painel/projetos/{id}` |
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
| RF-039 | Acompanhar execução física e financeira, entregas, marcos, alterações de plano e aprovações. | M | ✅ Implementado — execução física/financeira já coberta desde o RF-035/038 (`EtapaProjeto` status/valores, `DesembolsoProjeto`). **Marcos**: não é entidade nova — `marco: Boolean` a mais em `EtapaProjeto`, mesmo padrão de não duplicar já usado pro cronograma físico-financeiro. **Entregas**: `EntregaProjeto` — título, etapa opcional, datas prevista/entrega, documento opcional, aprovação (`aprovado`/`aprovado_por_id`/`data_aprovacao`, mesmo padrão que `Documento` já usa). **Alterações de plano**: `AlteracaoPlanoProjeto` — tipo (texto livre), descrição/justificativa, solicitação e decisão, reaproveitando `StatusRecurso` e o mesmo formato de `RecursoSubmissaoProjeto` (RF-030), mas decisão é `PAPEIS_GESTAO` (governança interna), não `PAPEIS_EDITAL_GESTAO` (autoridade do edital externo) — aprovação de entrega usa a mesma autoridade. `POST/GET /api/projetos/{id}/{entregas,alteracoes-plano}`, `POST /api/projetos/entregas/{id}/aprovar`, `POST /api/projetos/alteracoes-plano/{id}/decidir`, UI em `/painel/projetos/{id}` |
| RF-040 | Gerenciar riscos com probabilidade, impacto, resposta, responsável e evidência de mitigação. | M | ✅ Implementado — extensão mais barata do módulo: 4 dos 5 campos (probabilidade, impacto, resposta, responsável) já existiam em `RiscoProjeto` desde o RF-034; só faltou `evidencia_documento_id` (Documentos/RF-042, mesmo padrão de `AvaliacaoCriterio.evidencia_documento_id`), exatamente como a docstring original do modelo já previa |

### Prestação de contas

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-041 | Gerar relatório de execução do objeto, relatório financeiro e dossiê de evidências. | S | ✅ Implementado — três funções de agregação novas em `app/services/projeto.py` (`resumo_execucao_projeto`, `resumo_financeiro_projeto`, `dossie_evidencias_projeto`) escopadas a um único `Projeto` (mesmo padrão de `resumo_orgao`/relatório de comissão do RF-048), sem entidade nova. **Execução**: cronograma (etapas concluídas/marcos), metas, indicadores, entregas (realizadas/aprovadas), riscos por status e alterações de plano pendentes. **Financeiro**: origens de recursos com saldo calculado (não armazenado), aquisições com valor estimado total, desembolsos com total/conciliados. **Dossiê de evidências**: agrega, sem criar vínculo novo, os quatro pontos onde o módulo já linka Documentos — cotação, comprovante de desembolso, evidência de mitigação de risco e documento de entrega. `POST /api/projetos/{id}/relatorio-execucao`, `/relatorio-financeiro`, `/relatorio-dossie-evidencias` (e botões em `/painel/projetos/{id}`), RBAC `PAPEIS_GESTAO` (mesma convenção de todo relatório do sistema), PDF salvo no repositório de Documentos. Fecha também o tipo "de projeto" do RF-048 |

### Documentos

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-042 | Manter repositório com classificação, metadados, versão, validade, assinatura, aprovação e retenção. | M | ✅ Implementado (`Documento` — categoria, confidencialidade, versionamento por `documento_anterior_id`, validade, aprovado/assinado, retenção; arquivo em disco via `app/services/armazenamento.py`). **Código do documento, busca e visualização de aprovações/assinaturas exigidas** (pedidos explícitos): `codigo` (ex.: `DOC-000123`) gerado pelo próprio Postgres via `nextval()` de uma sequência dedicada (`server_default`, sem precisar tocar nos ~20 pontos do código que criam um `Documento`); busca por nome ou código em `/painel/documentos/cpls/{id}?q=...`. Novo modelo `AprovacaoDocumento` (pessoa + tipo `aprovacao`/`assinatura` + concluído/data) registra quantas e quais aprovações/assinaturas um documento específico exige, além do `aprovado`/`assinado` booleano simples que já existia (os dois convivem); nova tela `/painel/documentos/{id}` mostra "X de Y concluídas" e permite adicionar exigências e marcá-las concluídas |
| RF-043 | Gerar documentos padronizados em PDF/DOCX e pacotes de submissão com índice e checklist. | M | ✅ Implementado — exportação de ata de reunião em PDF (`gerar_pdf_ata`) e pacote de submissão com índice e checklist (`gerar_pdf_pacote_submissao`), este último reunindo o checklist de habilitação jurídica (RF-027, contra o template de documentos exigidos do RF-003 — a marcação anterior de "depende do módulo de Editais/Reconhecimento" estava desatualizada, o módulo existe desde o RF-024) e a avaliação de maturidade mais recente de uma CPL perante um edital. `POST /api/maturidade/cpls/{id}/pacote-submissao`. DOCX segue fora de escopo — PDF cobre o mesmo caso de uso e é o formato já usado em todos os outros relatórios do sistema (RF-048) |

### Indicadores

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-044 | Manter catálogo de indicadores com fórmula, fonte, periodicidade, responsável, meta e série histórica. | M | ✅ Implementado — `IndicadorEstrategico` ganhou `fonte` e `responsavel_id`; `IndicadorValorHistorico` guarda a série (cada aferição, não só o valor atual). Catálogo consolidado (através de todos os ciclos de planejamento de uma CPL) em `/painel/indicadores` e `GET /api/indicadores/cpls/{id}/catalogo`. **Descrição de como montar o valor ao registrar** (pedido explícito): o mini-formulário inline de "valor atual" (`/painel/planejamento/objetivos/{id}`) ganhou uma linha de ajuda logo abaixo, combinando a fórmula/unidade/fonte já cadastradas do indicador numa frase só ("siga a fórmula X, expresso em Y, fonte Z") e lembrando que cada valor salvo vira um novo ponto da série histórica, não sobrescreve o anterior |
| RF-045 | Disponibilizar painéis de governança, maturidade, projetos, finanças e impacto territorial. | M | ✅ Implementado — painel de governança (`/painel`) + painel consolidado de governança/planejamento/cadastro/projetos/finanças/**maturidade** por CPL (`/painel/indicadores/cpls/{id}`). Card "Projetos" agrega todo o portfólio da CPL (não um projeto só, já coberto pelos relatórios do RF-041): contagem por estágio/prioridade, financeiro (previsto/desembolsado/saldo somados de todas as origens de recurso e desembolsos) e execução (etapas/marcos/entregas/metas/riscos agregados) — `resumo_projetos_cpl()` em `app/services/projeto.py`. Card "Maturidade" reaproveita `resumo_recadastramento()` (já existia desde o RF-048, sem nenhuma agregação nova): nível vigente, validade do reconhecimento com alerta de vencimento, contagem de avaliações e lacunas da avaliação vigente. Todos os módulos mantêm também sua tela de portfólio/detalhe individual (`/painel/projetos/cpls/{id}`, `/painel/maturidade/cpls/{id}`) |
| RF-046 | Monitorar empresas participantes, empregos diretos/indiretos, novos empregos, faturamento por faixa, inovação, qualificação e cooperação. | M | ✅ Implementado — `resumo_cadastral()` agrega empresas vinculadas, empregos diretos/indiretos, faturamento por faixa e % de inovação/associativismo a partir do `DiagnosticoCadastral`. "Novos empregos" (variação no tempo) agora é calculável via `DiagnosticoCadastralHistorico` (snapshot de empregos a cada atualização de diagnóstico — API, formulário público de campanha e importação); "qualificação" ganhou campo próprio (`oferece_qualificacao_colaboradores`/`descricao_qualificacao`) |
| RF-047 | Monitorar ODS, sustentabilidade, exportação, contatos internacionais, certificações e digitalização. | S | ✅ Implementado — ODS mais citados e % de exportação já cobertos; sustentabilidade, contatos internacionais, certificações (com lista dos mais citados, mesmo padrão de ODS) e nível de digitalização ganharam campo próprio em `DiagnosticoCadastral` e passaram a ser coletados pelos 3 pontos de escrita (API, formulário público, importação de planilha) |

### Relatórios

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-048 | Gerar relatórios executivo, anual, de recadastramento, de comissão, de projeto e de impacto. | M | ✅ Implementado, todos os seis tipos — **executivo** (acumulado desde sempre), **de recadastramento** (nível de maturidade vigente, validade, lacunas, histórico de avaliações), **anual** (mesma base do executivo, recortada a um ano-calendário), **de comissão** (`POST /api/governanca/orgaos/{id}/relatorio-comissao` — escopado a um único órgão de governança em vez de toda a CPL: membros ativos, reuniões, deliberações e tarefas daquele órgão específico; serve qualquer `TipoOrgao`, não só comissão temática), **de impacto** (`POST /api/indicadores/cpls/{id}/relatorio-impacto` — recorte do resumo cadastral do RF-046/047 focado em sustentabilidade/ODS/exportação/certificações/empregos/inovação, sem consolidar governança/planejamento como o executivo; reaproveita `resumo_cadastral()` sem nenhuma agregação nova) e **de projeto** (RF-041 — três relatórios escopados a um único `Projeto`: execução, financeiro e dossiê de evidências, `POST /api/projetos/{id}/relatorio-{execucao,financeiro,dossie-evidencias}`) construídos, todos salvos no repositório de Documentos. O requisito não descreve um formato próprio pra "de projeto" além do que RF-041 já pede, então não há um sétimo tipo separado |

### Comunicação

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-049 | Enviar notificações de prazos, pendências, reuniões, tarefas, validade documental e metas. | M | ✅ Implementado — `Notificacao` (`app/models/notificacao.py`) + `app/services/notificacoes.py::gerar_notificacoes()`, cobrindo as 5 fontes citadas: reunião agendada nos próximos 7 dias (aos membros ativos do órgão), tarefa/meta com prazo vencendo ou vencido (ao responsável), documento perdendo validade (a quem criou), e recadastramento de CPL vencendo em até 90 dias — RN-005 (aos administradores da plataforma). "Enviar" é dentro do próprio sistema (`/painel/notificacoes`, `GET /api/notificacoes`), não e-mail/push — não há esse canal hoje. Sem agendador/worker (sem Celery/cron neste stack): a varredura roda sob demanda, sempre que a tela/endpoint é acessado, idempotente (nunca duplica o mesmo aviso) |
| RF-050 | Gerenciar eventos, capacitações, mentorias, missões técnicas, inscrições, presença e avaliação. | S | ✅ Implementado — `Evento` (capacitação/mentoria/missão técnica/outro), mesmo raciocínio de `Edital` (RN-006): `cpl_id` nulo é aberto a todas as CPLs, gerido pela plataforma (`PAPEIS_EDITAL_GESTAO`); `cpl_id` preenchido é local de uma CPL, gerida por `PAPEIS_GESTAO` dela. Inscrição, presença e avaliação ficam num único registro por pessoa+evento (`InscricaoEvento`) em vez de três tabelas — são estados sucessivos do mesmo vínculo, não entidades independentes. Limite de vagas respeitado na inscrição. `/painel/eventos`, `POST/GET /api/eventos`, `POST /api/eventos/{id}/inscricoes`, `PATCH /api/eventos/inscricoes/{id}` |

### Conhecimento

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-051 | Manter biblioteca de modelos, atas, estudos, boas práticas, editais, oportunidades e conteúdos técnicos. | S | ✅ Implementado — `RecursoBiblioteca`, conteúdo compartilhado entre todas as CPLs (sem `cpl_id`, diferente do repositório de documentos operacionais do RF-042, sempre preso a uma CPL), gerido por `PAPEIS_EDITAL_GESTAO`. Seis tipos (`modelo`, `estudo`, `boa_pratica`, `edital`, `oportunidade`, `conteudo_tecnico`) — "atas" não virou um sétimo tipo porque já é `Documento`/RF-042, duplicar seria o mesmo conteúdo em dois lugares. Cada recurso pode ser um arquivo enviado, um link externo ou só texto (ao menos um dos três é exigido); `publicado` controla rascunho vs. visível a todos. `/painel/biblioteca`, `POST/GET /api/biblioteca`, `GET /api/biblioteca/{id}/arquivo` |

### Ecossistema

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-052 | Realizar matchmaking entre demandas das empresas e competências de universidades, ICTs, fornecedores, startups e ambientes SPAI. | C | ✅ Implementado — `MatchInovacao` pareia uma `DemandaProjeto` (RF-031, `origem_tipo=empresa` já é "demanda das empresas") com uma `Entidade` candidata (universidade/ICT/prestador/ambiente de inovação), citando opcionalmente qual `OfertaEntidade` (RF-010, "competência") motivou a sugestão. Busca por nome/competência com filtro de tipo (`buscar_competencias`) ajuda a achar candidatos, mas a sugestão e a decisão de status (sugerido → em conversa → firmado/descartado) são sempre de uma pessoa — RN-016. Fecha o meio do fluxo F09; a ponta final (demanda → projeto) já existia via `POST /api/projetos/demandas/{id}/converter` (RF-031/032). `/painel/inovacao/demandas/{id}`, `POST/GET /api/inovacao/demandas/{id}/matches`, `GET /api/inovacao/competencias` |

### Integrações

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-053 | Disponibilizar API e importação/exportação em XLSX, CSV, PDF e formatos interoperáveis. | M | ⚠️ Parcial — API REST/JSON completa; importação XLSX/CSV existe desde o RF-013 (`app/services/importacao_entidades.py`); PDF existe pros seis tipos de relatório do RF-048; **exportação** XLSX/CSV de entidades + diagnóstico cadastral por CPL implementada nesta fatia (`GET /api/cadastro/cpls/{id}/exportar-entidades?formato=xlsx|csv`, botões em `/painel/cadastro/cpls/{id}`) — simétrica à importação (mesmo cabeçalho de `CAMPOS_CONHECIDOS`, então o arquivo exportado pode ser reimportado sem remapeamento manual, testado ponta a ponta). Exportação fica restrita a entidades/cadastro — outras listagens do sistema (projetos, documentos, auditoria etc.) não ganharam exportação própria nesta fatia |
| RF-054 | Integrar, quando autorizado e tecnicamente disponível, com assinatura eletrônica, dados cadastrais públicos, BI e sistemas institucionais. | S | ⚠️ Parcial, por design — duas das quatro integrações citadas foram implementadas de verdade porque são "tecnicamente disponíveis" sem depender de contrato com terceiro: **dados cadastrais públicos** (consulta de CNPJ via BrasilAPI, pública e gratuita — `GET /api/entidades/{id}/cnpj-publico`, tela de conferência em `/painel/cadastro/entidades/{id}`, botão "usar dados da base pública" aplica os campos com correspondência direta no cadastro) e **BI** (`GET /api/indicadores/bi-feed?formato=json\|csv`, uma linha por CPL com KPIs cadastrais escalares, pronta pra conector de URL de qualquer ferramenta de BI). **Assinatura eletrônica** e **"sistemas institucionais"** seguem pendentes de propósito — não há provedor público/gratuito equivalente (diferem de dados cadastrais e BI, que não dependem de contrato), então integrá-los de verdade exigiria escolher e contratar um provedor específico (ex.: gov.br assinatura, Clicksign, DocuSign) — decisão de negócio que só o programa pode tomar, mesma natureza que a pendência de SMTP em produção tinha antes de ser resolvida (RF-004, hoje configurado com o Titan Mail do Hostinger) |

### Transparência

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-055 | Publicar informações agregadas, governança, agenda, resultados e projetos autorizados, sem exposição de dados pessoais ou sigilosos. | S | ✅ Implementado — portal de transparência público (`/cpls`, lista de CPLs ativas; `/cpls/{id}`, página por CPL), sem autenticação. **Governança**: `resumo_governanca()` (contagens agregadas) + estrutura dos órgãos (nome/tipo/periodicidade/quantidade de membros ativos) — nunca nome de pessoa. **Agenda**: reuniões futuras (só data/título/local, sem pauta) e eventos abertos (RF-050). **Resultados**: `resumo_cadastral()` (dados cadastrais agregados, RF-046/047, já anonimizado). **Projetos autorizados**: só estágios `aprovado`/`em_execucao`/`concluido` (`demanda`/`em_elaboração`/`submetido` ainda não são resultado decidido; `rejeitado`/`cancelado` não é resultado a divulgar), só campos textuais (título/descrição/eixo), sem valor financeiro nem responsável. Testado (pytest, inclusive verificação explícita de que nome de pessoa não aparece na página) e via Playwright, zero autenticação exigida |

### Administração

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-056 | Disponibilizar trilha de auditoria, logs, gestão de parâmetros, tabelas auxiliares, perfis e retenção. | M | ✅ Implementado — `RegistroAuditoria` (`app/models/auditoria.py`), captura automática de criação/atualização/exclusão via listener SQLAlchemy (`app/services/auditoria.py`) + registro explícito de login e download; leitura em `/api/auditoria` e `/painel/auditoria`, com paginação real (offset/limite, `X-Total-Count` na API; página anterior/próxima na web) e visão global (`/api/auditoria/global`, `/painel/auditoria/global`) para eventos sem CPL resolvível (login, criação de `Usuario`/`Pessoa`/CPL), restrita ao administrador da plataforma. "Gestão de parâmetros/tabelas auxiliares/perfis" não tem tela dedicada própria (fica coberto indiretamente pela trilha de qualquer alteração nos modelos existentes, incl. `UsuarioPapel`) |

### Assistência inteligente

| ID | Requisito macro | Pri. | Status no repo |
|---|---|---|---|
| RF-057 | Oferecer, em evolução futura, apoio de IA para síntese, verificação de consistência e sugestão de lacunas, com revisão humana obrigatória. | C | ✅ Implementado — botão "Assistente de IA" no dashboard de indicadores de uma CPL (`/painel/indicadores/cpls/{id}`, `PAPEIS_GESTAO`), usando a API da Anthropic (Claude) sobre os mesmos agregados já mostrados no painel (cadastral, governança, planejamento, projetos, maturidade — nunca dado de pessoa). Devolve síntese em texto, lista de pontos de atenção (verificação de consistência) e lista de lacunas sugeridas, sempre rotulado "revisão humana obrigatória" e nunca persistido/aplicado automaticamente a nada. Sem `ANTHROPIC_API_KEY` configurada, a função degrada graciosamente (botão desabilitado + aviso), mesmo padrão do SMTP (RF-004). **Configurado e testado em produção** — extended thinking desligado (`thinking={"type": "disabled"}`, evita gastar o orçamento de tokens "pensando" em vez de responder, causa real de um 500 na primeira chamada real) e resposta limpa de cerca de código markdown antes do `json.loads` (modelo às vezes envolve o JSON em ```` ```json ```` mesmo instruído a não fazer isso) |

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
| Pessoa e vínculo | Representante, papel, mandato, contato, consentimento e relação com entidades/CPL. | ⚠️ `Pessoa`, `PessoaVinculo` cobrem representante/papel/mandato/contato/relação; "consentimento" em si só existe no fluxo de adesão (F01, `SolicitacaoAdesao.consentimento_lgpd`/`consentimento_em`), não como campo genérico de `Pessoa`/`PessoaVinculo` — RNF-002 (privacidade) segue majoritariamente pendente |
| Elo e oferta | Elo da cadeia, produto, serviço, tecnologia, competência, certificação e capacidade. | ✅ Completo — Elo (`EntidadeElo`), produto/serviço/tecnologia (`OfertaEntidade`, RF-010), certificação e capacidade (`DiagnosticoCadastral`). "Competência" não tem campo próprio — não é um conceito claramente distinto de "serviço/tecnologia" no documento de requisitos |
| Governança | Órgão, comissão, mandato, reunião, presença, votação, decisão e tarefa. | ✅ Completo (módulo Governança) |
| Planejamento | Diagnóstico, objetivo, meta, iniciativa, indicador e risco. | ⚠️ Completo exceto "risco" (não modelado ainda) |
| Maturidade | Edital, critério, peso, evidência, avaliação, nota, parecer e nível. | ✅ `Edital`, `CriterioMaturidade`, `Avaliacao`, `AvaliacaoCriterio`, `RecursoAvaliacao`, `ItemHabilitacaoJuridica` (RF-027) |
| Projeto | Demanda, proposta, eixo, plano de trabalho, equipe, etapa, atividade, entrega e resultado. | ✅ Completo — `DemandaProjeto`, `Projeto`, `EtapaProjeto` (demanda/proposta, eixo, portfólio, plano de trabalho, etapa/atividade com cronograma e marcos), `EquipeProjeto`, `EntregaProjeto` (com aprovação); "resultado" coberto por `MetaProjeto`/`IndicadorProjeto` |
| Financeiro do projeto | Item, cotação, fornecedor, fonte, contrapartida, desembolso, comprovante e saldo. | ✅ Completo — `AquisicaoProjeto` (item/contrapartida), `CotacaoAquisicao` (fornecedor), `OrigemRecursoProjeto` (fonte), `DesembolsoProjeto` (comprovante via Documentos); saldo calculado, não armazenado |
| Documento | Tipo, arquivo, metadados, validade, versão, aprovação, assinatura e confidencialidade. | ✅ `Documento` |
| Evento e comunicação | Evento, inscrição, presença, notícia, aviso, notificação e campanha. | ⚠️ Evento/inscrição/presença (RF-050), notificação (RF-049) e campanha (RF-012) implementados; portal público (RF-055) publica eventos abertos como agenda — "notícia"/"aviso" como conteúdo editorial próprio (texto livre, não vinculado a evento/reunião) ainda não tem modelo dedicado |
| Auditoria | Evento de sistema, usuário, data, objeto, ação, valor anterior e valor posterior. | ✅ `RegistroAuditoria` |

## 11. Fluxos de negócio prioritários

| Fluxo | Etapas principais | Status no repo |
|---|---|---|
| F01 – Adesão de membro | Convite/solicitação → cadastro → consentimento → validação → vínculo à CPL → classificação de elo → ativação. | ✅ Implementado — formulário público `/cpls/{id}/solicitar-adesao` (sem login, linkado a partir do portal de transparência, RF-055) cobre cadastro + consentimento (LGPD, obrigatório, com carimbo de data/hora); cria só um registro `SolicitacaoAdesao` (`PENDENTE`), nunca `Entidade`/vínculo direto. Validação é tela de gestão (`/painel/cadastro/cpls/{id}/solicitacoes-adesao`, `PAPEIS_GESTAO`) — aprovar cria (ou reaproveita por CNPJ/CPF já existente, RN-003) a `Entidade`, o vínculo à CPL (`EntidadeCPL`) e a classificação de elo (`EntidadeElo`, RF-009 — primeira vez que esse modelo ganha uma rota de escrita) e ainda registra o contato como `PessoaVinculo` (primeira vez que esse modelo também é escrito por algum fluxo do sistema). "Convite" não ganhou infraestrutura própria (token/e-mail) — a gestão simplesmente compartilha o link público, decisão documentada no código. **Município/UF viraram listbox** (pedido explícito, mesmo padrão do RF-001 — ver `app/services/localidades.py`): Estado antes de Município, Município filtrado pelo Estado via HTMX (`GET /cpls/{id}/solicitar-adesao/municipios-fragment`, público, sem exigir login). **Telefone** ganhou máscara `(99) 99999-9999` — único trecho de JavaScript escrito à mão no projeto até aqui (formata em `input`, progressive enhancement; a validação de verdade é sempre no servidor, `telefone_valido()` em `app/services/validadores.py`, contagem de 10 ou 11 dígitos). **E-mail** já era validado no servidor por `EmailStr` (Pydantic) desde a criação deste fluxo; ganhou reforço de `pattern`/`title` no HTML pra dar feedback imediato no navegador |
| F02 – Atualização diagnóstica | Criação de campanha → envio de formulário → resposta → validação → consolidação → indicadores. | ✅ **Implementado ponta a ponta** — campanha → convite (link/token) → resposta pública → consolidação em `resumo_cadastral()` (RF-046/047), exibida em `/painel/indicadores` |
| F03 – Reunião e decisão | Convocação → pauta → presença/quórum → deliberação → ata → tarefas → acompanhamento. | ✅ **Implementado ponta a ponta** (API + UI HTMX) |
| F04 – Planejamento estratégico | Diagnóstico → priorização → objetivos → metas → indicadores → aprovação → monitoramento. | ✅ **Implementado ponta a ponta** (API + UI HTMX) |
| F05 – Reconhecimento/recadastro | Edital → habilitação → PEN → evidências de maturidade → avaliação → submissão → resultado → recurso. | ⚠️ Parcial — edital → **habilitação** (`ItemHabilitacaoJuridica`, RF-027) → PEN (já existe) → evidências → avaliação → resultado (sugerido + decidido) → recurso todos implementados; só "submissão" formal (protocolo/prazo perante o órgão do edital, distinto do recurso de submissão de projetos que já existe em RF-030) não tem etapa própria no fluxo ainda |
| F06 – Projeto de fomento | Oportunidade → priorização → plano de trabalho → orçamento/cotações → aprovação → submissão → parceria. | ✅ Implementado ponta a ponta — demanda (oportunidade) → conversão em projeto (priorização) → plano de trabalho → orçamento/cotações (`AquisicaoProjeto`/`CotacaoAquisicao`, com validação de mínimo de fornecedores) → submissão a edital de fomento (`POST /api/projetos/{id}/submeter`); "aprovação"/"parceria" formais não têm etapa própria além da decisão de recurso de submissão |
| F07 – Execução do projeto | Kickoff → atividades → desembolsos → entregas → metas/indicadores → riscos → relatórios → encerramento. | ✅ Implementado ponta a ponta — etapas/atividades com marcos, `DesembolsoProjeto`, `EntregaProjeto` com aprovação, `MetaProjeto`/`IndicadorProjeto`, `RiscoProjeto` com evidência, relatório de execução em PDF (RF-041); "kickoff"/"encerramento" formais não têm etapa própria, cobertos pelo `EstagioProjeto` do portfólio |
| F08 – Prestação de contas | Consolidação física → consolidação financeira → validação → relatório → aprovação → protocolo → diligências. | ✅ Implementado — consolidação física (relatório de execução) e financeira (relatório financeiro, saldos/conciliação) via RF-041, dossiê de evidências como validação documental; "aprovação"/"protocolo"/"diligências" formais de prestação de contas (perante o órgão do edital, distinto da governança interna já coberta por `AlteracaoPlanoProjeto`) não têm etapa própria |
| F09 – Oportunidade de inovação | Demanda empresarial → busca de competência → matchmaking → projeto de P&D → instrumento jurídico → acompanhamento. | ✅ Implementado — demanda empresarial (`DemandaProjeto`, origem empresa) → busca de competência + matchmaking (`MatchInovacao`/RF-052) → projeto de P&D (conversão pra `Projeto` já existente, RF-031/032) → acompanhamento (portfólio de projetos já existente). "Instrumento jurídico" não tem modelo próprio — cai no repositório de Documentos (RF-042) como qualquer outro contrato, mesmo raciocínio já usado pra outras peças formais do sistema |

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
| RNF-010 – Interoperabilidade | APIs REST/JSON, webhooks quando cabíveis e exportação em formatos abertos. | ⚠️ REST/JSON ok; exportação de entidades em XLSX/CSV (RF-053) e feed de BI em JSON/CSV (RF-054) implementados; webhooks e exportação de outras listagens pendentes |
| RNF-011 – Manutenibilidade | Código versionado, testes automatizados, documentação técnica, modularidade e pipeline de implantação. | ✅ Implementado — código versionado no GitHub; 43 testes automatizados (`tests/`, pytest, banco Postgres de teste isolado por SAVEPOINT, 49% de cobertura de statements) cobrindo autenticação, cadastro/RBAC, geocodificação (RF-011), governança, maturidade, projetos/matchmaking (RF-052) e observabilidade (RNF-012); lint com ruff (`ruff check .` limpo); pipeline de CI (`.github/workflows/ci.yml`, GitHub Actions) rodando lint + testes a cada push/PR contra `master` com serviço Postgres efêmero; documentação técnica em README/HANDOFF/`docs/requisitos_macros.md`; modularidade já existente (camadas `models`/`schemas`/`services`/`api`/`web`). Pipeline de implantação em produção segue manual via `deploy.sh` sobre SSH — automatizar isso é passo futuro, não coberto aqui |
| RNF-012 – Observabilidade | Logs centralizados, métricas, alertas, rastreamento de falhas e painel de saúde. | ✅ Implementado — logs estruturados em JSON por requisição (`app/core/logging_config.py`, um `request_id` por requisição, devolvido também em `X-Request-ID`); métricas em memória desde o último deploy (total de requisições, por classe de status, latência média); rastreamento de falhas persistido em `RegistroFalha` (uma linha por exceção não tratada, com traceback); alerta por limiar (padrão: 5 falhas em 15 min) com banner no painel e e-mail best-effort aos administradores; painel de saúde em `/painel/administracao/saude` (admin) e `GET /api/metricas`; `/api/saude` passou a checar conectividade real com o banco. Sem infraestrutura externa nova (Prometheus/Grafana/Sentry) — tudo no próprio Postgres/processo |
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
| Identidade e segurança | IAM, MFA, RBAC/ABAC, criptografia, consentimento e auditoria. | JWT + bcrypt + RBAC (`app/core/security.py`, `app/core/rbac.py`) + MFA opcional via TOTP (`app/services/mfa.py`, RF-004) + trilha de auditoria (`app/models/auditoria.py`, `app/services/auditoria.py`); consentimento só no fluxo de adesão (F01), não um mecanismo genérico ainda |
| Integração | API gateway, conectores, importação/exportação e filas de processamento. | FastAPI expõe REST direto; sem gateway, filas ou conectores externos |
| Analytics | ETL, indicadores, dashboards, georreferenciamento e relatórios. | KPIs simples no `/painel`; sem ETL, geo ou relatórios |
| Operação | Ambientes separados, CI/CD, monitoramento, backup, suporte e gestão de incidentes. | Só ambiente de desenvolvimento local (`docker-compose.yml` com Postgres); sem CI/CD nem monitoramento |

## 17. Priorização sugerida e roadmap

| Fase | Entregas principais | Status no repo |
|---|---|---|
| Fase 0 – Descoberta (4–6 semanas) | Validação de processos, matriz de perfis, dicionário de dados, protótipos, integração da planilha atual e backlog detalhado. | Pulado — este projeto começou direto na construção técnica |
| Fase 1 – MVP (3–4 meses) | Identidade, cadastro, cadeia, formulários, governança, planejamento, documentos, tarefas, indicadores básicos, relatórios e auditoria. | ✅ **Completa** (com recortes de escopo documentados por requisito). Feito: identidade, cadastro (parcial) + campanhas/importação, governança, planejamento, documentos (repositório + ata em PDF), tarefas (dentro de governança), catálogo de indicadores com série histórica (RF-044), painéis consolidados (RF-045, completo), resumo cadastral (RF-046/047, parcial), os seis tipos de relatório em PDF (RF-048, completo), trilha de auditoria (RF-056). |
| Fase 2 – Conformidade SP Produz (2–3 meses) | Maturidade, reconhecimento/recadastro, editais, plano de trabalho, orçamento, cotações, submissões e alertas. | ✅ **Completa** (módulo de Projetos). Feito: maturidade, editais/critérios, avaliação com nota/evidência/lacunas, decisão de nível (RN-016), recadastro bienal com alertas (RF-024 a RF-028); módulo de Projetos — edital de fomento com submissão e recursos/contrarrazões/diligências, demandas, portfólio, plano de trabalho completo, financeiro completo (itens de despesa, cotações, desembolsos), execução completa (marcos, entregas com aprovação, alterações de plano com decisão, riscos com evidência de mitigação) e prestação de contas (relatório de execução, relatório financeiro e dossiê de evidências em PDF) — RF-029 a RF-041, módulo inteiro completo. |
| Fase 3 – Execução e fomento (2–3 meses) | Execução física/financeira, prestação de contas, riscos, bens, relatórios e portal de transparência. | ⚠️ **Quase completa** — execução física/financeira, prestação de contas, riscos (com evidência) e relatórios (RF-041, ver Fase 2) foram construídos junto com o resto do módulo de Projetos, em vez de esperar uma fase separada; portal de transparência feito (RF-055, `/cpls`); "bens" tem só `bem_adquirido` (texto livre em `DesembolsoProjeto`), sem controle patrimonial próprio — única lacuna restante da fase |
| Fase 4 – Ecossistema e inovação | Matchmaking, catálogo de competências, integração SPAI/ICTs, mapas de rede, IA assistiva e análises avançadas. | ✅ **Completa** — matchmaking e "catálogo de competências" feitos (RF-052, `MatchInovacao` + `buscar_competencias()` sobre `OfertaEntidade` de universidades/ICTs/ambientes de inovação — cobre a integração com o ecossistema SPAI/ICTs citada aqui); análises avançadas ganharam o feed de BI (RF-054); mapas de rede/georreferenciamento feito (RF-011, mapa Leaflet por CPL); IA assistiva feita (RF-057, síntese/verificação de consistência/lacunas via Anthropic, com revisão humana obrigatória) |

## 18. Critérios macros de aceite

1. Usuários conseguem cadastrar uma entidade e vinculá-la corretamente à CPL e a um ou mais elos. ✅
2. A entidade gestora consegue criar uma reunião, registrar ata, decisão, responsável e acompanhar a execução. ✅
3. O sistema consegue representar o planejamento estratégico, metas, indicadores e projetos vinculados. ✅ (módulo de Projetos completo desde RF-029 a RF-041, ver seção 17 — item desatualizado corrigido em 2026-08-06)
4. A matriz de maturidade pode ser configurada por edital e recebe evidências, notas, justificativas e pareceres. ✅ (RF-024 a RF-028, critérios/pesos/notas de corte por edital, evidência por critério via `Documento`)
5. O sistema gera checklist de reconhecimento/recadastro e identifica pendências de prazo, documento e evidência. ✅ (checklist de habilitação — RF-027/RF-003 — e recadastro bienal com alerta de vencimento — RF-028)
6. Um plano de trabalho completo pode ser preenchido, versionado, aprovado e exportado. ✅ (plano de trabalho do módulo de Projetos + exportação em PDF, RF-048)
7. O orçamento aceita cotações, contrapartidas e cronograma físico-financeiro, mantendo rastreabilidade. ✅ (RF-036 a RF-038)
8. Dashboards apresentam indicadores consolidados sem expor dados pessoais indevidamente. ⚠️ (dashboard existe — RF-044/045 — mas não foi auditado formalmente quanto a exposição de dados pessoais, ver RNF-002)
9. Logs permitem reconstruir as principais alterações, avaliações, aprovações e submissões. ✅ (trilha de auditoria automática, RF-056, mais rastreamento de falhas do sistema em si, RNF-012)
10. Importação da planilha atual produz registros consistentes, relatório de inconsistências e controle de duplicidade. ✅ (RF-013, com remapeamento manual de colunas e relatório de erro por linha)

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
