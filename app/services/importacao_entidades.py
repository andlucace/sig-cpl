"""RF-013/RF-014: importação de planilha (CSV/XLSX) para o cadastro de
Entidade + DiagnosticoCadastral, com mapeamento automático de colunas por
nome (ver `_ALIASES_CAMPO`), remapeamento manual quando a sugestão erra ou
deixa campo sem coluna, deduplicação por CNPJ, validação e relatório por
linha.

Fluxo em dois passos (RF-013 — "remapeamento manual"):
1. `preparar_importacao()` salva o arquivo em staging (mesmo mecanismo de
   `app/services/armazenamento.py`) e devolve os cabeçalhos + o
   mapeamento *sugerido*, sem processar nenhuma linha ainda.
2. `confirmar_importacao()` recebe o mapeamento que o usuário confirmou
   (igual à sugestão) ou ajustou manualmente, e só então processa as
   linhas de verdade.

`processar_planilha()` continua existindo como atalho de 1 passo só
mapeamento automático — não quebra quem já chamava a API assim.

A planilha real "CPLS - FORMS.xlsx" citada no documento de requisitos
nunca foi anexada ao projeto, então o dicionário de aliases é uma
aproximação razoável dos nomes de campo mencionados na seção 3 do
documento — ajuste `_ALIASES_CAMPO` se a planilha real usar cabeçalhos
diferentes (o remapeamento manual cobre o caso de ela não bater de
primeira, mas calibrar os aliases continua reduzindo o trabalho manual).
"""

import csv
import io
import unicodedata
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.cadastro_dinamico import DiagnosticoCadastral, ImportacaoLinha, ImportacaoLote
from app.models.entidade import Entidade, EntidadeCPL
from app.models.enums import StatusLinhaImportacao, StatusLoteImportacao, TipoEntidade
from app.services.armazenamento import caminho_absoluto, salvar_arquivo

_ALIASES_CAMPO: dict[str, list[str]] = {
    "razao_social": ["razao social", "nome", "nome da empresa", "empresa", "organizacao"],
    "nome_fantasia": ["nome fantasia", "fantasia"],
    "cnpj": ["cnpj"],
    "cpf": ["cpf"],
    "cnae": ["cnae"],
    "porte": ["porte"],
    "municipio": ["municipio", "cidade"],
    "uf": ["uf", "estado"],
    "endereco": ["endereco"],
    "tipo": ["tipo", "tipo de entidade", "tipo de organizacao"],
    "atividades_produtos": ["atividades", "produtos", "atividades e produtos"],
    "diferenciais_competitivos": ["diferenciais", "diferenciais competitivos"],
    "faturamento_faixa": ["faturamento", "faixa de faturamento"],
    "empregos_diretos": ["empregos diretos"],
    "empregos_indiretos": ["empregos indiretos"],
    "participacao_associativa": ["participacao associativa"],
    "entidades_associativas": ["entidades associativas", "associacoes"],
    "compartilha_recursos": ["compartilhamento de recursos", "compartilha recursos"],
    "recursos_compartilhados": ["recursos compartilhados"],
    "realiza_inovacao": ["inovacao"],
    "descricao_inovacao": ["descricao da inovacao", "descricao inovacao"],
    "realiza_pd": ["p&d", "pd", "pesquisa e desenvolvimento"],
    "ods_relacionados": ["ods"],
    "exporta": ["exportacao", "exporta"],
    "mercados_exportacao": ["mercados de exportacao", "mercados-alvo"],
    "interesse_comissoes": ["comissoes", "interesse em comissoes", "comissoes tematicas"],
}

_CAMPOS_BOOLEANOS = {
    "participacao_associativa",
    "compartilha_recursos",
    "realiza_inovacao",
    "realiza_pd",
    "exporta",
}
_CAMPOS_INTEIROS = {"empregos_diretos", "empregos_indiretos"}
_CAMPOS_DIAGNOSTICO = set(_ALIASES_CAMPO) - {
    "razao_social", "nome_fantasia", "cnpj", "cpf", "cnae", "porte", "municipio", "uf", "endereco", "tipo",
}

CAMPOS_CONHECIDOS = list(_ALIASES_CAMPO.keys())
"""Campos que o mapeamento (automático ou manual) pode preencher — usado
pra renderizar o formulário de remapeamento com todos os campos, mesmo os
que a sugestão automática não bateu com nenhuma coluna."""

_VALORES_VERDADEIROS = {"sim", "s", "yes", "y", "true", "verdadeiro", "1"}
_VALORES_FALSOS = {"nao", "não", "n", "no", "false", "falso", "0"}


def _normalizar(texto: str) -> str:
    texto = texto.strip().lower()
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def _parse_bool(valor: str) -> bool | None:
    v = _normalizar(valor)
    if v in _VALORES_VERDADEIROS:
        return True
    if v in _VALORES_FALSOS:
        return False
    return None


def mapear_colunas(cabecalhos: list[str]) -> dict[str, int]:
    normalizados = [_normalizar(h) for h in cabecalhos]
    mapa: dict[str, int] = {}
    for campo, aliases in _ALIASES_CAMPO.items():
        aliases_norm = {_normalizar(a) for a in aliases} | {campo}
        for indice, cabecalho in enumerate(normalizados):
            if cabecalho in aliases_norm:
                mapa[campo] = indice
                break
    return mapa


def ler_planilha(nome_arquivo: str, conteudo: bytes) -> tuple[list[str], list[list[str]]]:
    if nome_arquivo.lower().endswith((".xlsx", ".xlsm")):
        import openpyxl

        pasta = openpyxl.load_workbook(io.BytesIO(conteudo), data_only=True, read_only=True)
        planilha = pasta.worksheets[0]
        linhas_brutas = list(planilha.iter_rows(values_only=True))
        if not linhas_brutas:
            return [], []
        cabecalhos = [str(c).strip() if c is not None else "" for c in linhas_brutas[0]]
        linhas = [
            [str(c).strip() if c is not None else "" for c in linha] for linha in linhas_brutas[1:]
        ]
        return cabecalhos, linhas

    for encoding in ("utf-8-sig", "latin-1"):
        try:
            texto = conteudo.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        texto = conteudo.decode("utf-8", errors="replace")

    leitor = csv.reader(io.StringIO(texto), delimiter=";" if ";" in texto.splitlines()[0] else ",")
    todas_linhas = list(leitor)
    if not todas_linhas:
        return [], []
    return todas_linhas[0], todas_linhas[1:]


def _processar_linhas(
    db: Session,
    lote: ImportacaoLote,
    cpl_id: uuid.UUID,
    mapa: dict[str, int],
    linhas_dados: list[list[str]],
) -> None:
    """Preenche `ImportacaoLinha` + `Entidade`/`DiagnosticoCadastral` para
    um lote já existente, usando o mapeamento (sugerido ou confirmado à
    mão) informado, e atualiza os totais/status nele."""

    total_criadas = total_atualizadas = total_erros = 0

    for indice, linha in enumerate(linhas_dados, start=2):  # linha 1 = cabeçalho
        valores = {
            campo: (linha[coluna].strip() if coluna < len(linha) else "")
            for campo, coluna in mapa.items()
        }

        razao_social = valores.get("razao_social", "")
        if not razao_social:
            db.add(
                ImportacaoLinha(
                    lote_id=lote.id,
                    numero_linha=indice,
                    status=StatusLinhaImportacao.ERRO,
                    mensagem="Campo obrigatório 'razão social' ausente ou não reconhecido no cabeçalho.",
                )
            )
            total_erros += 1
            continue

        cnpj_bruto = valores.get("cnpj", "")
        cnpj_normalizado = "".join(c for c in cnpj_bruto if c.isdigit()) or None

        entidade = None
        if cnpj_normalizado:
            entidade = db.query(Entidade).filter(Entidade.cnpj == cnpj_normalizado).first()

        tipo_valor = _normalizar(valores.get("tipo", "")) or "empresa"
        tipo_map = {t.value: t for t in TipoEntidade}
        tipo = tipo_map.get(tipo_valor, TipoEntidade.EMPRESA)

        criando = entidade is None
        if criando:
            entidade = Entidade(tipo=tipo, razao_social=razao_social)
            db.add(entidade)

        entidade.razao_social = razao_social
        if valores.get("nome_fantasia"):
            entidade.nome_fantasia = valores["nome_fantasia"]
        if cnpj_normalizado:
            entidade.cnpj = cnpj_normalizado
        if valores.get("cpf"):
            entidade.cpf = "".join(c for c in valores["cpf"] if c.isdigit())
        if valores.get("cnae"):
            entidade.cnae = valores["cnae"]
        if valores.get("porte"):
            entidade.porte = valores["porte"]
        if valores.get("municipio"):
            entidade.municipio = valores["municipio"]
        if valores.get("uf"):
            entidade.uf = valores["uf"].upper()[:2]
        if valores.get("endereco"):
            entidade.endereco = valores["endereco"]

        db.flush()

        if not db.query(EntidadeCPL).filter(
            EntidadeCPL.cpl_id == cpl_id, EntidadeCPL.entidade_id == entidade.id
        ).first():
            db.add(EntidadeCPL(cpl_id=cpl_id, entidade_id=entidade.id, data_vinculo=date.today()))

        if any(valores.get(campo) for campo in _CAMPOS_DIAGNOSTICO):
            diagnostico = (
                db.query(DiagnosticoCadastral)
                .filter(DiagnosticoCadastral.entidade_id == entidade.id)
                .first()
            )
            if diagnostico is None:
                diagnostico = DiagnosticoCadastral(entidade_id=entidade.id)
                db.add(diagnostico)
            for campo in _CAMPOS_DIAGNOSTICO:
                valor = valores.get(campo)
                if not valor:
                    continue
                if campo in _CAMPOS_BOOLEANOS:
                    parsed = _parse_bool(valor)
                    if parsed is not None:
                        setattr(diagnostico, campo, parsed)
                elif campo in _CAMPOS_INTEIROS:
                    try:
                        setattr(diagnostico, campo, int(float(valor.replace(",", "."))))
                    except ValueError:
                        pass
                else:
                    setattr(diagnostico, campo, valor)

        status_linha = StatusLinhaImportacao.CRIADA if criando else StatusLinhaImportacao.ATUALIZADA
        db.add(
            ImportacaoLinha(
                lote_id=lote.id,
                numero_linha=indice,
                status=status_linha,
                entidade_id=entidade.id,
                mensagem=None,
            )
        )
        if criando:
            total_criadas += 1
        else:
            total_atualizadas += 1

    lote.total_linhas = len(linhas_dados)
    lote.total_criadas = total_criadas
    lote.total_atualizadas = total_atualizadas
    lote.total_erros = total_erros
    lote.mapeamento_colunas = dict(mapa)
    lote.status = StatusLoteImportacao.CONCLUIDO


def processar_planilha(
    db: Session,
    cpl_id: uuid.UUID,
    usuario_id: uuid.UUID,
    nome_arquivo: str,
    conteudo: bytes,
) -> ImportacaoLote:
    """RF-013/RF-014: atalho de 1 passo, só com mapeamento automático —
    usado por quem chama a importação sem passar pelo fluxo de
    remapeamento manual (`preparar_importacao`/`confirmar_importacao`)."""

    cabecalhos, linhas_dados = ler_planilha(nome_arquivo, conteudo)
    mapa = mapear_colunas(cabecalhos)

    lote = ImportacaoLote(cpl_id=cpl_id, usuario_id=usuario_id, nome_arquivo=nome_arquivo)
    db.add(lote)
    db.flush()

    _processar_linhas(db, lote, cpl_id, mapa, linhas_dados)
    db.commit()
    db.refresh(lote)
    return lote


def preparar_importacao(
    db: Session,
    cpl_id: uuid.UUID,
    usuario_id: uuid.UUID,
    nome_arquivo: str,
    conteudo: bytes,
) -> tuple[ImportacaoLote, list[str], dict[str, int]]:
    """RF-013 (remapeamento manual), passo 1: salva o arquivo em staging e
    devolve o lote (status `pendente_mapeamento`), os cabeçalhos lidos e o
    mapeamento sugerido — sem processar nenhuma linha ainda."""

    caminho = salvar_arquivo(cpl_id, nome_arquivo, conteudo)
    cabecalhos, linhas_dados = ler_planilha(nome_arquivo, conteudo)
    mapa_sugerido = mapear_colunas(cabecalhos)

    lote = ImportacaoLote(
        cpl_id=cpl_id,
        usuario_id=usuario_id,
        nome_arquivo=nome_arquivo,
        status=StatusLoteImportacao.PENDENTE_MAPEAMENTO,
        arquivo_path=caminho,
        total_linhas=len(linhas_dados),
    )
    db.add(lote)
    db.commit()
    db.refresh(lote)
    return lote, cabecalhos, mapa_sugerido


def confirmar_importacao(
    db: Session, lote: ImportacaoLote, mapeamento: dict[str, int]
) -> ImportacaoLote:
    """RF-013 (remapeamento manual), passo 2: processa as linhas de
    verdade com o mapeamento que o usuário confirmou (igual à sugestão
    original ou ajustado à mão)."""

    conteudo = caminho_absoluto(lote.arquivo_path).read_bytes()
    _, linhas_dados = ler_planilha(lote.nome_arquivo, conteudo)
    _processar_linhas(db, lote, lote.cpl_id, mapeamento, linhas_dados)
    db.commit()
    db.refresh(lote)
    return lote
