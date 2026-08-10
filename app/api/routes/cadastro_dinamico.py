import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rbac import PAPEIS_GESTAO, PAPEIS_GOVERNANCA_LEITURA, verificar_papel
from app.db.session import get_db
from app.models.cadastro_dinamico import (
    CampanhaCadastral,
    CampanhaConvite,
    DiagnosticoCadastral,
    ImportacaoLote,
)
from app.models.cpl import CPL
from app.models.entidade import Entidade
from app.models.enums import StatusLoteImportacao
from app.models.usuario import Usuario
from app.schemas.cadastro_dinamico import (
    CampanhaCadastralCreate,
    CampanhaCadastralRead,
    CampanhaConviteCreate,
    CampanhaConviteRead,
    ConfirmarMapeamentoCreate,
    DiagnosticoCadastralRead,
    DiagnosticoCadastralUpdate,
    ImportacaoLoteRead,
    PrepararImportacaoRead,
)
from app.services.importacao_entidades import (
    CAMPOS_CONHECIDOS,
    confirmar_importacao,
    exportar_entidades,
    gerar_csv_entidades,
    gerar_xlsx_entidades,
    preparar_importacao,
)
from app.services.indicadores import registrar_snapshot_diagnostico

router = APIRouter(prefix="/cadastro", tags=["Formulários e dados"])

_MEDIA_TYPES_EXPORTACAO = {
    "csv": "text/csv",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def _get_cpl_or_404(db: Session, cpl_id: uuid.UUID) -> CPL:
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    return cpl


def _get_campanha_or_404(db: Session, campanha_id: uuid.UUID) -> CampanhaCadastral:
    campanha = db.get(CampanhaCadastral, campanha_id)
    if campanha is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campanha não encontrada.")
    return campanha


# --- Campanhas de atualização cadastral (RF-012) ----------------------------


@router.post(
    "/cpls/{cpl_id}/campanhas", response_model=CampanhaCadastralRead, status_code=status.HTTP_201_CREATED
)
def criar_campanha(
    cpl_id: uuid.UUID,
    dados: CampanhaCadastralCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> CampanhaCadastral:
    _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=cpl_id)
    campanha = CampanhaCadastral(cpl_id=cpl_id, **dados.model_dump())
    db.add(campanha)
    db.commit()
    db.refresh(campanha)
    return campanha


@router.get("/cpls/{cpl_id}/campanhas", response_model=list[CampanhaCadastralRead])
def listar_campanhas(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[CampanhaCadastral]:
    _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)
    return db.query(CampanhaCadastral).filter(CampanhaCadastral.cpl_id == cpl_id).all()


@router.get("/campanhas/{campanha_id}", response_model=CampanhaCadastralRead)
def obter_campanha(
    campanha_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> CampanhaCadastral:
    campanha = _get_campanha_or_404(db, campanha_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=campanha.cpl_id)
    return campanha


@router.post(
    "/campanhas/{campanha_id}/convites",
    response_model=CampanhaConviteRead,
    status_code=status.HTTP_201_CREATED,
)
def convidar_entidade(
    campanha_id: uuid.UUID,
    dados: CampanhaConviteCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> CampanhaConvite:
    campanha = _get_campanha_or_404(db, campanha_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=campanha.cpl_id)
    if db.get(Entidade, dados.entidade_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entidade não encontrada.")
    convite = CampanhaConvite(
        campanha_id=campanha_id,
        entidade_id=dados.entidade_id,
        token=secrets.token_urlsafe(24),
    )
    db.add(convite)
    db.commit()
    db.refresh(convite)
    return convite


@router.get("/campanhas/{campanha_id}/convites", response_model=list[CampanhaConviteRead])
def listar_convites(
    campanha_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[CampanhaConvite]:
    campanha = _get_campanha_or_404(db, campanha_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=campanha.cpl_id)
    return db.query(CampanhaConvite).filter(CampanhaConvite.campanha_id == campanha_id).all()


# --- Diagnóstico cadastral (RF-012) ------------------------------------------


@router.get("/entidades/{entidade_id}/diagnostico", response_model=DiagnosticoCadastralRead)
def obter_diagnostico(
    entidade_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> DiagnosticoCadastral:
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA)
    diagnostico = db.query(DiagnosticoCadastral).filter(
        DiagnosticoCadastral.entidade_id == entidade_id
    ).first()
    if diagnostico is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Diagnóstico não encontrado para esta entidade.")
    return diagnostico


@router.put("/entidades/{entidade_id}/diagnostico", response_model=DiagnosticoCadastralRead)
def atualizar_diagnostico(
    entidade_id: uuid.UUID,
    dados: DiagnosticoCadastralUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> DiagnosticoCadastral:
    if db.get(Entidade, entidade_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entidade não encontrada.")
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO)
    diagnostico = db.query(DiagnosticoCadastral).filter(
        DiagnosticoCadastral.entidade_id == entidade_id
    ).first()
    if diagnostico is None:
        diagnostico = DiagnosticoCadastral(entidade_id=entidade_id)
        db.add(diagnostico)
    for campo, valor in dados.model_dump().items():
        setattr(diagnostico, campo, valor)
    db.flush()
    registrar_snapshot_diagnostico(db, diagnostico)
    db.commit()
    db.refresh(diagnostico)
    return diagnostico


# --- Importação de planilha (RF-013/RF-014) ---------------------------------


@router.post(
    "/cpls/{cpl_id}/importacoes",
    response_model=PrepararImportacaoRead,
    status_code=status.HTTP_201_CREATED,
)
async def preparar_importacao_planilha(
    cpl_id: uuid.UUID,
    arquivo: UploadFile,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> dict:
    """RF-013 (remapeamento manual), passo 1: salva o arquivo e devolve o
    mapeamento sugerido — não processa nenhuma linha ainda. Confirme (ou
    ajuste) via `POST /importacoes/{lote_id}/confirmar-mapeamento`."""

    _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=cpl_id)
    if not arquivo.filename or not arquivo.filename.lower().endswith((".csv", ".xlsx", ".xlsm")):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Envie um arquivo .csv, .xlsx ou .xlsm.")
    conteudo = await arquivo.read()
    lote, cabecalhos, mapeamento_sugerido = preparar_importacao(
        db, cpl_id, usuario_atual.id, arquivo.filename, conteudo
    )
    return {
        "lote": lote,
        "cabecalhos": cabecalhos,
        "mapeamento_sugerido": mapeamento_sugerido,
        "campos_conhecidos": CAMPOS_CONHECIDOS,
    }


@router.post("/importacoes/{lote_id}/confirmar-mapeamento", response_model=ImportacaoLoteRead)
def confirmar_mapeamento_importacao(
    lote_id: uuid.UUID,
    dados: ConfirmarMapeamentoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> ImportacaoLote:
    """RF-013 (remapeamento manual), passo 2: processa as linhas com o
    mapeamento confirmado (igual à sugestão ou ajustado à mão)."""

    lote = db.get(ImportacaoLote, lote_id)
    if lote is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lote de importação não encontrado.")
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=lote.cpl_id)
    if lote.status != StatusLoteImportacao.PENDENTE_MAPEAMENTO:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Este lote já foi processado.")
    return confirmar_importacao(db, lote, dados.mapeamento)


@router.get("/cpls/{cpl_id}/importacoes", response_model=list[ImportacaoLoteRead])
def listar_importacoes(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[ImportacaoLote]:
    _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)
    return db.query(ImportacaoLote).filter(ImportacaoLote.cpl_id == cpl_id).all()


@router.get("/importacoes/{lote_id}", response_model=ImportacaoLoteRead)
def obter_importacao(
    lote_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> ImportacaoLote:
    lote = db.get(ImportacaoLote, lote_id)
    if lote is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lote de importação não encontrado.")
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=lote.cpl_id)
    return lote


@router.get("/modelo-planilha")
def modelo_planilha(
    formato: str = "xlsx",
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Response:
    """Planilha-modelo (cabeçalho de `CAMPOS_CONHECIDOS`, sem linha de
    dado nenhuma) pra ajudar quem vai importar — não escopada por CPL,
    o cabeçalho é sempre o mesmo."""

    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=None)
    if formato not in _MEDIA_TYPES_EXPORTACAO:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Formato precisa ser 'xlsx' ou 'csv'.")

    conteudo = gerar_xlsx_entidades([]) if formato == "xlsx" else gerar_csv_entidades([])
    return Response(
        content=conteudo,
        media_type=_MEDIA_TYPES_EXPORTACAO[formato],
        headers={"Content-Disposition": f'attachment; filename="modelo-entidades.{formato}"'},
    )


# --- Exportação de entidades (RF-053) ----------------------------------------


@router.get("/cpls/{cpl_id}/exportar-entidades")
def exportar_entidades_cpl(
    cpl_id: uuid.UUID,
    formato: str = "xlsx",
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Response:
    """RF-053: exportação de entidades + diagnóstico cadastral de uma CPL em
    XLSX ou CSV — simétrica à importação (RF-013/014): mesmo cabeçalho de
    `CAMPOS_CONHECIDOS`, então o arquivo devolvido aqui pode ser reimportado
    sem remapeamento manual."""

    _get_cpl_or_404(db, cpl_id)
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)
    if formato not in _MEDIA_TYPES_EXPORTACAO:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Formato precisa ser 'xlsx' ou 'csv'.")

    linhas = exportar_entidades(db, cpl_id)
    conteudo = gerar_xlsx_entidades(linhas) if formato == "xlsx" else gerar_csv_entidades(linhas)
    return Response(
        content=conteudo,
        media_type=_MEDIA_TYPES_EXPORTACAO[formato],
        headers={"Content-Disposition": f'attachment; filename="entidades.{formato}"'},
    )
