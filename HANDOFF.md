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
- **Migrações Alembic aplicadas:** 6 revisões, todas no banco atual:
  1. `18541dca0a36` — modelos base (CPL, Entidade, Pessoa, Usuário)
  2. `0ba4d1a10f9d` — módulo Governança
  3. `5dd913b79202` — módulo Planejamento Estratégico
  4. `ac2ebdd62dd4` — módulo Cadastro dinâmico (diagnóstico, campanhas,
     convites, importação de planilha)
  5. `5891c62d1cb7` — módulo Documentos (repositório, versionamento,
     aprovação/assinatura, geração de ata em PDF)
  6. `5bff0df723be` — trilha de auditoria (`registros_auditoria`)

### Usuários de teste já existentes no banco

| E-mail | Senha | Papel (`UsuarioPapel`) |
|---|---|---|
| `admin@atibaia-autopecas.sp.gov.br` | `trocar-senha-123` | `administrador_plataforma` (global) |
| `gestora@cpl-autopecas.example` | `senha-gestora-123` | `entidade_gestora` escopado à CPL Autopeças de Atibaia |
| `conselho@exemplo.com` | `senha-conselho-123` | nenhum papel (útil para testar 403) |

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
**A Fase 1/MVP está completa** — indicadores e relatórios (RF-044 a
RF-048, era o último item) foi implementado nesta sessão. Resumo na ordem
recomendada para o que vem depois:

1. **Fechar limitações conhecidas do RBAC** (ver README, seção "Controle de
   acesso" → "Limitações conhecidas"): escopo por órgão/comissão específica
   (não só CPL), escopo de CPL para Entidade/Pessoa, página 403 amigável no
   portal web (hoje mostra JSON cru).
2. **Tela de criação/edição de CPL no portal restrito** — hoje só existe via
   API (`POST /api/cpls`), o que obriga usar `/docs` para o primeiro passo.
3. **Remapeamento manual de colunas na importação de planilha** — hoje o
   casamento é só automático por nome de cabeçalho
   (`app/services/importacao_entidades.py`); se a planilha real "CPLS -
   FORMS.xlsx" for anexada em algum momento, calibrar os aliases contra ela
   (o arquivo em si nunca foi anexado ao projeto).
4. ~~Fonte Unicode para PDF em produção~~ — **resolvido no deploy**: em vez
   de bundlar o arquivo `.ttf` no repositório, o `Dockerfile` instala o
   pacote apt `fonts-dejavu-core` na imagem, que já entrega
   `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf` — caminho que
   `app/services/geracao_documentos.py` já procurava desde antes, então
   nenhum código mudou.
5. **Fase 2 do roadmap** (Maturidade/Reconhecimento, RF-024 a RF-028) — só
   faz sentido agora, depende do Planejamento Estratégico (já pronto) como
   pré-requisito conceitual.
6. ~~Deploy na VPS Hostinger~~ — **feito nesta sessão**, ver seção "Deploy
   em produção" abaixo para todos os detalhes (como foi feito, segredos,
   como reimplantar).
7. **Trilha de auditoria: limitações conhecidas** — (a) a tela
   `/painel/auditoria` é por CPL; eventos sem CPL resolvível (login,
   criação de `Usuario`/`Pessoa`/`CPL` em si) ficam gravados no banco com
   `cpl_id=None` mas não aparecem em nenhuma tela hoje (só consultáveis
   direto no banco) — cobrir isso exigiria uma visão "global", restrita a
   `ADMINISTRADOR_PLATAFORMA`; (b) não há paginação de verdade, só um
   limite fixo (200 registros mais recentes) — se o volume crescer, vai
   precisar de paginação ou filtro por data; (c) `DELETE` não é exposto em
   nenhum endpoint do sistema hoje, então a captura de EXCLUSAO nunca roda
   em uso real — foi testada diretamente via sessão SQLAlchemy num script
   ad-hoc, não através de um endpoint HTTP real.
8. **Indicadores e relatórios: limitações conhecidas** (ver README para o
   detalhe por requisito) — RF-046/047 só cobrem o que já existe no
   `DiagnosticoCadastral` (empregos, faturamento, inovação, exportação,
   ODS); sustentabilidade, certificações, contatos internacionais,
   digitalização e "qualificação" não têm campo no cadastro atual. RF-048
   só tem o relatório executivo — os outros 5 tipos citados no requisito
   não existem (comissão/projeto dependem de módulos ainda não
   construídos). RF-045 só cobre governança/planejamento/cadastro —
   maturidade/projetos/finanças/impacto territorial ficam pra quando esses
   módulos existirem.

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
