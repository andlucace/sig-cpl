"""RF-043: geração de documentos padronizados. Escopo desta etapa: exportar
a ata de uma reunião de governança em PDF — usa o campo `Reuniao.ata` que já
existe, sem depender de módulos ainda não construídos (Editais/Reconhecimento,
Fase 2, é quem pediria o "pacote de submissão com índice e checklist").
"""

from pathlib import Path

from fpdf import FPDF

from app.models.governanca import Reuniao

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


class _GeradorAta:
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
    doc = _GeradorAta()

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
