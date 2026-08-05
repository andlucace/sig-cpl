"""RF-043/RF-048: geração de documentos padronizados em PDF. Nove peças:
exportar a ata de uma reunião de governança (usa o campo `Reuniao.ata`
que já existe), o relatório executivo consolidado (acumulado desde
sempre), o relatório de recadastramento, o relatório anual (recortado a
um ano-calendário), o relatório de comissão (escopado a um único órgão
de governança) e o relatório de impacto (reaproveita o resumo cadastral
do RF-046/047, sem consolidar governança/planejamento) de uma CPL, mais
os três relatórios "de projeto" do RF-041 (execução, financeiro e
dossiê de evidências) — escopados a um único `Projeto`, não a uma CPL
inteira. Com estes três, os seis tipos de relatório citados no RF-048
estão completos (o tipo "de projeto" dependia do módulo de Projetos
existir, ver README/HANDOFF).
"""

from pathlib import Path

from fpdf import FPDF

from app.models.cpl import CPL
from app.models.governanca import OrgaoGovernanca, Reuniao
from app.models.planejamento import IndicadorEstrategico
from app.models.projeto import Projeto

# A fonte core "Helvetica" do fpdf2 só cobre latin-1 e não tem travessão
# (—), então acentuação e travessão saem trocados por "?" se usada direto.
# Se alguma destas fontes TrueType existir, usamos Unicode de verdade; senão
# caímos para Helvetica + normalização "lossy" (ver `_texto_seguro`). Para
# rodar isso numa VPS Linux, o caminho mais simples é colocar um
# DejaVuSans.ttf (licença permissiva, comum em `fonts-dejavu-core`) em
# `app/static/fonts/` — passa a ser detectado automaticamente, sem mudar
# código.
_FONTES_REGULAR = [
    Path(__file__).resolve().parent.parent / "static" / "fonts" / "DejaVuSans.ttf",
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("C:/Windows/Fonts/arial.ttf"),
]
_FONTES_NEGRITO = [
    Path(__file__).resolve().parent.parent / "static" / "fonts" / "DejaVuSans-Bold.ttf",
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("C:/Windows/Fonts/arialbd.ttf"),
]


def _texto_seguro(texto: str | None) -> str:
    """Usado só quando não há fonte Unicode disponível — normaliza para
    latin-1 substituindo o que não for suportado, em vez de quebrar."""

    if not texto:
        return ""
    return texto.encode("latin-1", errors="replace").decode("latin-1")


class _GeradorPDF:
    def __init__(self) -> None:
        self.pdf = FPDF()
        self.pdf.add_page()
        self.unicode_ok = self._registrar_fontes()

    def _registrar_fontes(self) -> bool:
        regular = next((f for f in _FONTES_REGULAR if f.exists()), None)
        if regular is None:
            return False
        self.pdf.add_font("Documento", "", str(regular))
        negrito = next((f for f in _FONTES_NEGRITO if f.exists()), regular)
        self.pdf.add_font("Documento", "B", str(negrito))
        return True

    def linha(self, texto: str, altura: int = 7, negrito: bool = False, tamanho: int = 11) -> None:
        familia = "Documento" if self.unicode_ok else "Helvetica"
        estilo = "B" if negrito else ""
        conteudo = texto if self.unicode_ok else _texto_seguro(texto)
        self.pdf.set_font(familia, estilo, tamanho)
        # `multi_cell` calcula a largura disponível a partir do X atual;
        # sem resetar pra margem esquerda antes de cada chamada, uma quebra
        # de linha anterior pode deixar o X perto da borda e estourar
        # "Not enough horizontal space to render a single character".
        self.pdf.set_x(self.pdf.l_margin)
        self.pdf.multi_cell(0, altura, conteudo, new_x="LMARGIN", new_y="NEXT")

    def espaco(self, altura: int = 4) -> None:
        self.pdf.ln(altura)

    def bytes(self) -> bytes:
        return bytes(self.pdf.output())


def gerar_pdf_ata(reuniao: Reuniao) -> bytes:
    doc = _GeradorPDF()

    doc.linha(f"Ata — {reuniao.titulo}", altura=10, negrito=True, tamanho=16)
    doc.espaco(2)

    doc.linha(f"Órgão: {reuniao.orgao.nome}")
    doc.linha(f"Data/hora: {reuniao.data_hora.strftime('%d/%m/%Y %H:%M')}")
    if reuniao.local:
        doc.linha(f"Local: {reuniao.local}")
    doc.linha(f"Status: {reuniao.status.value}")

    if reuniao.pauta:
        doc.espaco()
        doc.linha("Pauta", negrito=True, tamanho=12)
        doc.linha(reuniao.pauta)

    doc.espaco()
    doc.linha("Presenças", negrito=True, tamanho=12)
    if reuniao.presencas:
        for presenca in reuniao.presencas:
            situacao = "presente" if presenca.presente else "ausente"
            doc.linha(f"- {presenca.pessoa.nome}: {situacao}")
    else:
        doc.linha("Nenhuma presença registrada.")

    if reuniao.deliberacoes:
        doc.espaco()
        doc.linha("Deliberações", negrito=True, tamanho=12)
        for deliberacao in reuniao.deliberacoes:
            doc.linha(f"- {deliberacao.descricao} ({deliberacao.resultado.value})")

    doc.espaco()
    doc.linha("Ata", negrito=True, tamanho=12)
    doc.linha(reuniao.ata or "(ata ainda não registrada)")

    return doc.bytes()


def gerar_pdf_relatorio_executivo(
    cpl: CPL,
    resumo_governanca: dict,
    resumo_planejamento: dict,
    resumo_cadastral: dict,
    indicadores: list[IndicadorEstrategico],
) -> bytes:
    """RF-048: relatório executivo — consolida em um único PDF o que RF-045
    a RF-047 pedem como painéis separados. Dados vêm prontos de
    `app/services/indicadores.py`; esta função só formata."""

    doc = _GeradorPDF()

    doc.linha(f"Relatório Executivo — {cpl.nome}", altura=10, negrito=True, tamanho=16)
    doc.linha(f"Sigla: {cpl.sigla} — Elo/setor: {cpl.setor or '—'}")
    doc.espaco(2)

    doc.linha("Governança", negrito=True, tamanho=12)
    doc.linha(f"Órgãos ativos: {resumo_governanca['total_orgaos']}")
    doc.linha(f"Reuniões realizadas: {resumo_governanca['reunioes_realizadas']}")
    doc.linha(f"Deliberações aprovadas: {resumo_governanca['deliberacoes_aprovadas']}")
    doc.linha(
        f"Tarefas: {resumo_governanca['tarefas_concluidas']} concluídas, "
        f"{resumo_governanca['tarefas_pendentes']} pendentes"
    )

    doc.espaco()
    doc.linha("Planejamento estratégico", negrito=True, tamanho=12)
    doc.linha(f"Ciclos de planejamento: {resumo_planejamento['total_ciclos']}")
    doc.linha(
        f"Objetivos: {resumo_planejamento['objetivos_concluidos']} concluídos de "
        f"{resumo_planejamento['total_objetivos']}"
    )
    doc.linha(
        f"Metas: {resumo_planejamento['metas_concluidas']} concluídas de "
        f"{resumo_planejamento['total_metas']}"
    )

    doc.espaco()
    doc.linha("Cadastro e cadeia", negrito=True, tamanho=12)
    doc.linha(f"Empresas vinculadas: {resumo_cadastral['total_empresas']}")
    doc.linha(f"Com diagnóstico cadastral respondido: {resumo_cadastral['total_com_diagnostico']}")
    doc.linha(
        f"Empregos diretos: {resumo_cadastral['soma_empregos_diretos']} — "
        f"indiretos: {resumo_cadastral['soma_empregos_indiretos']}"
    )
    if resumo_cadastral["novos_empregos_diretos_12_meses"]:
        doc.linha(f"Novos empregos diretos (últimos 12 meses): {resumo_cadastral['novos_empregos_diretos_12_meses']}")
    if resumo_cadastral["percentual_inovacao"] is not None:
        doc.linha(f"Realizam inovação: {resumo_cadastral['percentual_inovacao']}%")
    if resumo_cadastral["percentual_exportacao"] is not None:
        doc.linha(f"Exportam: {resumo_cadastral['percentual_exportacao']}%")
    if resumo_cadastral["percentual_qualificacao"] is not None:
        doc.linha(f"Oferecem qualificação a colaboradores: {resumo_cadastral['percentual_qualificacao']}%")
    if resumo_cadastral["percentual_sustentabilidade"] is not None:
        doc.linha(f"Adotam práticas de sustentabilidade: {resumo_cadastral['percentual_sustentabilidade']}%")
    if resumo_cadastral["percentual_contatos_internacionais"] is not None:
        doc.linha(f"Possuem contatos internacionais: {resumo_cadastral['percentual_contatos_internacionais']}%")
    if resumo_cadastral["percentual_certificacoes"] is not None:
        doc.linha(f"Possuem certificações: {resumo_cadastral['percentual_certificacoes']}%")
    if resumo_cadastral["distribuicao_faturamento"]:
        doc.linha("Faturamento por faixa:")
        for faixa, quantidade in resumo_cadastral["distribuicao_faturamento"].items():
            doc.linha(f"- {faixa}: {quantidade}")
    if resumo_cadastral["distribuicao_digitalizacao"]:
        doc.linha("Nível de digitalização:")
        for nivel, quantidade in resumo_cadastral["distribuicao_digitalizacao"].items():
            doc.linha(f"- {nivel}: {quantidade}")
    if resumo_cadastral["ods_mais_citados"]:
        ods_texto = ", ".join(f"{nome} ({qtd})" for nome, qtd in resumo_cadastral["ods_mais_citados"])
        doc.linha(f"ODS mais citados: {ods_texto}")
    if resumo_cadastral["certificacoes_mais_citadas"]:
        cert_texto = ", ".join(f"{nome} ({qtd})" for nome, qtd in resumo_cadastral["certificacoes_mais_citadas"])
        doc.linha(f"Certificações mais citadas: {cert_texto}")

    doc.espaco()
    doc.linha("Catálogo de indicadores", negrito=True, tamanho=12)
    if indicadores:
        for indicador in indicadores:
            valor = indicador.valor_atual or "sem valor registrado"
            meta = f" (meta: {indicador.meta_valor})" if indicador.meta_valor else ""
            doc.linha(f"- {indicador.nome}: {valor}{meta}")
    else:
        doc.linha("Nenhum indicador cadastrado ainda.")

    return doc.bytes()


def gerar_pdf_relatorio_recadastramento(cpl: CPL, resumo: dict) -> bytes:
    """RF-048: dossiê de recadastramento — nível de maturidade vigente,
    validade do reconhecimento (RN-005) e histórico de avaliações/decisões.
    Dados vêm prontos de `app/services/maturidade.py::resumo_recadastramento`;
    esta função só formata."""

    doc = _GeradorPDF()

    doc.linha(f"Relatório de Recadastramento — {cpl.nome}", altura=10, negrito=True, tamanho=16)
    doc.linha(f"Sigla: {cpl.sigla} — Elo/setor: {cpl.setor or '—'}")
    doc.espaco(2)

    doc.linha("Situação atual", negrito=True, tamanho=12)
    nivel = resumo["nivel_maturidade_atual"]
    doc.linha(f"Nível de maturidade: {nivel.value.replace('_', ' ') if nivel else 'não reconhecido ainda'}")
    if resumo["data_reconhecimento"]:
        doc.linha(f"Reconhecido em: {resumo['data_reconhecimento'].strftime('%d/%m/%Y')}")
    if resumo["data_validade_reconhecimento"]:
        doc.linha(f"Válido até: {resumo['data_validade_reconhecimento'].strftime('%d/%m/%Y')}")
        if resumo["dias_para_vencer"] is not None:
            if resumo["dias_para_vencer"] < 0:
                doc.linha(f"Reconhecimento vencido há {-resumo['dias_para_vencer']} dia(s) — recadastramento necessário.")
            elif resumo["vencimento_proximo_ou_vencido"]:
                doc.linha(f"Vence em {resumo['dias_para_vencer']} dia(s) — recadastramento recomendado.")
    else:
        doc.linha("Sem reconhecimento formal registrado ainda.")

    if resumo["lacunas_avaliacao_vigente"]:
        doc.espaco()
        doc.linha("Lacunas identificadas na avaliação vigente", negrito=True, tamanho=12)
        for nota in resumo["lacunas_avaliacao_vigente"]:
            doc.linha(f"- {nota.criterio.nome}: nota {nota.nota} (corte: {nota.criterio.nota_corte})")

    doc.espaco()
    doc.linha("Histórico de avaliações", negrito=True, tamanho=12)
    if resumo["avaliacoes"]:
        for avaliacao in resumo["avaliacoes"]:
            linha = (
                f"- {avaliacao.data_avaliacao.strftime('%d/%m/%Y')} "
                f"(edital {avaliacao.edital.ciclo}): status {avaliacao.status.value}"
            )
            if avaliacao.pontuacao_calculada is not None:
                linha += f", pontuação {avaliacao.pontuacao_calculada}"
            if avaliacao.nivel_sugerido is not None:
                linha += f", sugerido {avaliacao.nivel_sugerido.value.replace('_', ' ')}"
            if avaliacao.nivel_decidido is not None:
                linha += f", decidido {avaliacao.nivel_decidido.value.replace('_', ' ')}"
            doc.linha(linha)
            if avaliacao.parecer:
                doc.linha(f"  Parecer: {avaliacao.parecer}")
    else:
        doc.linha("Nenhuma avaliação registrada ainda.")

    return doc.bytes()


def gerar_pdf_relatorio_anual(cpl: CPL, resumo: dict) -> bytes:
    """RF-048: relatório anual — o que aconteceu na CPL num ano-calendário
    específico (o executivo é o acumulado desde sempre). Dados vêm
    prontos de `app/services/indicadores.py::resumo_anual`; esta função
    só formata."""

    doc = _GeradorPDF()

    doc.linha(f"Relatório Anual {resumo['ano']} — {cpl.nome}", altura=10, negrito=True, tamanho=16)
    doc.linha(f"Sigla: {cpl.sigla} — Elo/setor: {cpl.setor or '—'}")
    doc.espaco(2)

    doc.linha("Governança", negrito=True, tamanho=12)
    doc.linha(f"Reuniões realizadas no ano: {resumo['reunioes_realizadas_no_ano']}")
    doc.linha(f"Deliberações aprovadas no ano: {resumo['deliberacoes_aprovadas_no_ano']}")
    doc.linha(f"Tarefas concluídas no ano: {resumo['tarefas_concluidas_no_ano']}")

    doc.espaco()
    doc.linha("Planejamento estratégico", negrito=True, tamanho=12)
    doc.linha(f"Metas concluídas no ano: {resumo['metas_concluidas_no_ano']}")
    doc.linha(f"Indicadores atualizados no ano: {resumo['indicadores_atualizados_no_ano']}")

    doc.espaco()
    doc.linha("Cadastro e cadeia", negrito=True, tamanho=12)
    doc.linha(f"Novos empregos diretos no ano: {resumo['novos_empregos_diretos_no_ano']}")

    doc.espaco()
    doc.linha("Documentos", negrito=True, tamanho=12)
    doc.linha(f"Documentos gerados/anexados no ano: {resumo['documentos_gerados_no_ano']}")

    return doc.bytes()


def gerar_pdf_relatorio_comissao(orgao: OrgaoGovernanca, resumo: dict) -> bytes:
    """RF-048: relatório de comissão — escopado a um único órgão de
    governança (qualquer `TipoOrgao`, não só comissão temática), em vez
    de toda a CPL como o executivo. Dados vêm prontos de
    `app/services/indicadores.py::resumo_orgao`; esta função só formata."""

    doc = _GeradorPDF()

    doc.linha(f"Relatório de Comissão — {orgao.nome}", altura=10, negrito=True, tamanho=16)
    doc.linha(f"Tipo: {orgao.tipo.value.replace('_', ' ')}")
    doc.espaco(2)

    doc.linha("Resumo", negrito=True, tamanho=12)
    doc.linha(f"Membros ativos: {len(resumo['membros_ativos'])}")
    doc.linha(f"Reuniões realizadas: {resumo['reunioes_realizadas']}")
    doc.linha(f"Deliberações aprovadas: {resumo['deliberacoes_aprovadas']}")
    doc.linha(
        f"Tarefas: {resumo['tarefas_concluidas']} concluídas, "
        f"{resumo['tarefas_pendentes']} pendentes"
    )

    doc.espaco()
    doc.linha("Membros", negrito=True, tamanho=12)
    if resumo["membros_ativos"]:
        for membro in resumo["membros_ativos"]:
            doc.linha(f"- {membro.pessoa.nome} ({membro.funcao})")
    else:
        doc.linha("Nenhum membro ativo cadastrado.")

    doc.espaco()
    doc.linha("Reuniões", negrito=True, tamanho=12)
    if resumo["reunioes"]:
        for reuniao in resumo["reunioes"]:
            doc.linha(f"- {reuniao.data_hora.strftime('%d/%m/%Y %H:%M')}: {reuniao.titulo} ({reuniao.status.value})")
    else:
        doc.linha("Nenhuma reunião registrada ainda.")

    doc.espaco()
    doc.linha("Deliberações", negrito=True, tamanho=12)
    if resumo["deliberacoes"]:
        for deliberacao in resumo["deliberacoes"]:
            doc.linha(f"- {deliberacao.descricao} ({deliberacao.resultado.value})")
    else:
        doc.linha("Nenhuma deliberação registrada ainda.")

    return doc.bytes()


def gerar_pdf_relatorio_impacto(cpl: CPL, resumo_cadastral: dict) -> bytes:
    """RF-048/RF-047: relatório de impacto — recorte do resumo cadastral
    focado em sustentabilidade, inovação, ODS, exportação, certificações
    e empregos, sem as seções de governança/planejamento do executivo.
    Reaproveita o mesmo `resumo_cadastral()` do RF-046/047 — não introduz
    nenhuma coleta ou agregação nova, só uma apresentação diferente do
    que já existe."""

    doc = _GeradorPDF()

    doc.linha(f"Relatório de Impacto — {cpl.nome}", altura=10, negrito=True, tamanho=16)
    doc.linha(f"Sigla: {cpl.sigla} — Elo/setor: {cpl.setor or '—'}")
    doc.espaco(2)

    doc.linha("Impacto socioeconômico", negrito=True, tamanho=12)
    doc.linha(f"Empresas vinculadas: {resumo_cadastral['total_empresas']}")
    doc.linha(
        f"Empregos diretos: {resumo_cadastral['soma_empregos_diretos']} — "
        f"indiretos: {resumo_cadastral['soma_empregos_indiretos']}"
    )
    if resumo_cadastral["novos_empregos_diretos_12_meses"]:
        doc.linha(f"Novos empregos diretos (últimos 12 meses): {resumo_cadastral['novos_empregos_diretos_12_meses']}")
    if resumo_cadastral["percentual_exportacao"] is not None:
        doc.linha(f"Exportam: {resumo_cadastral['percentual_exportacao']}%")
    if resumo_cadastral["percentual_qualificacao"] is not None:
        doc.linha(f"Oferecem qualificação a colaboradores: {resumo_cadastral['percentual_qualificacao']}%")

    doc.espaco()
    doc.linha("Impacto socioambiental", negrito=True, tamanho=12)
    if resumo_cadastral["percentual_sustentabilidade"] is not None:
        doc.linha(f"Adotam práticas de sustentabilidade: {resumo_cadastral['percentual_sustentabilidade']}%")
    if resumo_cadastral["ods_mais_citados"]:
        ods_texto = ", ".join(f"{nome} ({qtd})" for nome, qtd in resumo_cadastral["ods_mais_citados"])
        doc.linha(f"ODS mais citados: {ods_texto}")

    doc.espaco()
    doc.linha("Inovação e competitividade", negrito=True, tamanho=12)
    if resumo_cadastral["percentual_inovacao"] is not None:
        doc.linha(f"Realizam inovação: {resumo_cadastral['percentual_inovacao']}%")
    if resumo_cadastral["percentual_pd"] is not None:
        doc.linha(f"Realizam P&D: {resumo_cadastral['percentual_pd']}%")
    if resumo_cadastral["percentual_certificacoes"] is not None:
        doc.linha(f"Possuem certificações: {resumo_cadastral['percentual_certificacoes']}%")
    if resumo_cadastral["certificacoes_mais_citadas"]:
        cert_texto = ", ".join(f"{nome} ({qtd})" for nome, qtd in resumo_cadastral["certificacoes_mais_citadas"])
        doc.linha(f"Certificações mais citadas: {cert_texto}")
    if resumo_cadastral["percentual_contatos_internacionais"] is not None:
        doc.linha(f"Possuem contatos internacionais: {resumo_cadastral['percentual_contatos_internacionais']}%")
    if resumo_cadastral["distribuicao_digitalizacao"]:
        doc.linha("Nível de digitalização:")
        for nivel, quantidade in resumo_cadastral["distribuicao_digitalizacao"].items():
            doc.linha(f"- {nivel}: {quantidade}")

    return doc.bytes()


def gerar_pdf_relatorio_execucao_projeto(projeto: Projeto, resumo: dict) -> bytes:
    """RF-041: relatório de execução do objeto — cronograma (etapas e
    marcos), metas, indicadores, entregas e riscos. Dados vêm prontos de
    `app/services/projeto.py::resumo_execucao_projeto`; esta função só
    formata."""

    doc = _GeradorPDF()

    doc.linha(f"Relatório de Execução — {projeto.titulo}", altura=10, negrito=True, tamanho=16)
    doc.linha(f"Estágio: {projeto.estagio.value.replace('_', ' ')}")
    doc.espaco(2)

    doc.linha("Cronograma", negrito=True, tamanho=12)
    doc.linha(f"Etapas: {resumo['etapas_concluidas']} concluídas de {resumo['total_etapas']}")
    if resumo["marcos"]:
        doc.linha("Marcos:")
        for marco in resumo["marcos"]:
            doc.linha(f"- {marco.titulo} ({marco.status.value.replace('_', ' ')})")
    else:
        doc.linha("Nenhum marco cadastrado.")

    doc.espaco()
    doc.linha("Metas e indicadores", negrito=True, tamanho=12)
    doc.linha(f"Metas: {resumo['metas_concluidas']} concluídas de {resumo['total_metas']}")
    if resumo["indicadores"]:
        for indicador in resumo["indicadores"]:
            valor = indicador.valor_atual or "sem valor registrado"
            meta = f" (meta: {indicador.meta_valor})" if indicador.meta_valor else ""
            doc.linha(f"- {indicador.nome}: {valor}{meta}")
    else:
        doc.linha("Nenhum indicador cadastrado.")

    doc.espaco()
    doc.linha("Entregas", negrito=True, tamanho=12)
    doc.linha(
        f"Total: {resumo['total_entregas']} — realizadas: {resumo['entregas_realizadas']} — "
        f"aprovadas: {resumo['entregas_aprovadas']}"
    )
    for entrega in resumo["entregas"]:
        situacao = "aprovada" if entrega.aprovado else ("entregue" if entrega.data_entrega else "pendente")
        doc.linha(f"- {entrega.titulo} ({situacao})")

    doc.espaco()
    doc.linha("Riscos", negrito=True, tamanho=12)
    doc.linha(
        f"Ativos: {resumo['riscos_ativos']} — mitigados: {resumo['riscos_mitigados']} — "
        f"materializados: {resumo['riscos_materializados']}"
    )
    for risco in resumo["riscos"]:
        doc.linha(f"- {risco.descricao} ({risco.status.value})")

    if resumo["alteracoes_plano"]:
        doc.espaco()
        doc.linha("Alterações de plano", negrito=True, tamanho=12)
        doc.linha(f"Pendentes de decisão: {resumo['alteracoes_plano_pendentes']}")
        for alteracao in resumo["alteracoes_plano"]:
            doc.linha(f"- {alteracao.tipo}: {alteracao.descricao} ({alteracao.status.value})")

    return doc.bytes()


def gerar_pdf_relatorio_financeiro_projeto(projeto: Projeto, resumo: dict) -> bytes:
    """RF-041: relatório financeiro do projeto — origens de recursos e
    saldos, aquisições e desembolsos/conciliação. Dados vêm prontos de
    `app/services/projeto.py::resumo_financeiro_projeto`; esta função só
    formata."""

    doc = _GeradorPDF()

    doc.linha(f"Relatório Financeiro — {projeto.titulo}", altura=10, negrito=True, tamanho=16)
    doc.espaco(2)

    doc.linha("Origens de recursos", negrito=True, tamanho=12)
    doc.linha(f"Total previsto: R$ {resumo['total_previsto']}")
    doc.linha(f"Total desembolsado: R$ {resumo['total_desembolsado']}")
    doc.linha(f"Saldo total: R$ {resumo['saldo_total']}")
    for origem in resumo["origens"]:
        contrapartida = " (contrapartida)" if origem.contrapartida else ""
        saldo = resumo["saldos_por_origem"][origem.id]
        doc.linha(f"- {origem.fonte}{contrapartida}: previsto R$ {origem.valor}, saldo R$ {saldo}")

    doc.espaco()
    doc.linha("Aquisições", negrito=True, tamanho=12)
    doc.linha(
        f"Total: {resumo['total_aquisicoes']} — valor estimado: R$ {resumo['total_estimado_aquisicoes']}"
    )
    for aquisicao in resumo["aquisicoes"]:
        etapa = f" — etapa: {aquisicao.etapa.titulo}" if aquisicao.etapa else ""
        valor = f"R$ {aquisicao.valor_estimado}" if aquisicao.valor_estimado is not None else "sem valor"
        doc.linha(f"- {aquisicao.item}: {valor} ({aquisicao.status.value}){etapa}")
        if aquisicao.justificativa_excecao:
            doc.linha(f"  Justificativa (exceção de cotações): {aquisicao.justificativa_excecao}")

    doc.espaco()
    doc.linha("Desembolsos e conciliação", negrito=True, tamanho=12)
    doc.linha(
        f"Conciliados: {resumo['desembolsos_conciliados']} — "
        f"pendentes: {resumo['desembolsos_pendentes_conciliacao']}"
    )
    for desembolso in resumo["desembolsos"]:
        conciliado = "conciliado" if desembolso.conciliado else "não conciliado"
        bem = f" — bem adquirido: {desembolso.bem_adquirido}" if desembolso.bem_adquirido else ""
        doc.linha(
            f"- {desembolso.data.strftime('%d/%m/%Y')}: R$ {desembolso.valor} ({conciliado}){bem}"
        )

    return doc.bytes()


def gerar_pdf_dossie_evidencias_projeto(projeto: Projeto, resumo: dict) -> bytes:
    """RF-041: dossiê de evidências — lista, com referência ao documento
    do repositório (RF-042), tudo que já foi anexado como comprovação em
    fatias anteriores do módulo (cotações, comprovantes de desembolso,
    evidência de mitigação de risco, documento de entrega). Dados vêm
    prontos de `app/services/projeto.py::dossie_evidencias_projeto`; esta
    função só formata."""

    doc = _GeradorPDF()

    doc.linha(f"Dossiê de Evidências — {projeto.titulo}", altura=10, negrito=True, tamanho=16)
    doc.linha(f"Total de evidências: {resumo['total_evidencias']}")
    doc.espaco(2)

    doc.linha("Cotações de aquisição", negrito=True, tamanho=12)
    if resumo["cotacoes"]:
        for cotacao in resumo["cotacoes"]:
            doc.linha(
                f"- {cotacao.aquisicao.item}: cotação de {cotacao.fornecedor} — "
                f"{cotacao.documento.titulo}"
            )
    else:
        doc.linha("Nenhuma cotação com documento anexado.")

    doc.espaco()
    doc.linha("Comprovantes de desembolso", negrito=True, tamanho=12)
    if resumo["desembolsos"]:
        for desembolso in resumo["desembolsos"]:
            doc.linha(
                f"- {desembolso.data.strftime('%d/%m/%Y')} (R$ {desembolso.valor}): "
                f"{desembolso.documento_comprovante.titulo}"
            )
    else:
        doc.linha("Nenhum desembolso com comprovante anexado.")

    doc.espaco()
    doc.linha("Evidências de mitigação de risco", negrito=True, tamanho=12)
    if resumo["riscos"]:
        for risco in resumo["riscos"]:
            doc.linha(f"- {risco.descricao}: {risco.evidencia_documento.titulo}")
    else:
        doc.linha("Nenhum risco com evidência anexada.")

    doc.espaco()
    doc.linha("Documentos de entrega", negrito=True, tamanho=12)
    if resumo["entregas"]:
        for entrega in resumo["entregas"]:
            doc.linha(f"- {entrega.titulo}: {entrega.documento.titulo}")
    else:
        doc.linha("Nenhuma entrega com documento anexado.")

    return doc.bytes()
