"""RF-043/RF-048: geração de documentos padronizados em PDF. Três peças:
exportar a ata de uma reunião de governança (usa o campo `Reuniao.ata` que
já existe), o relatório executivo consolidado de uma CPL e o relatório de
recadastramento (RF-048 — dos seis tipos de relatório citados no
requisito, só estes dois foram construídos; anual/comissão/projeto/
impacto ainda não têm formato definido ou dependem de módulos que não
existem, ver README).
"""

from pathlib import Path

from fpdf import FPDF

from app.models.cpl import CPL
from app.models.governanca import Reuniao
from app.models.planejamento import IndicadorEstrategico

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
