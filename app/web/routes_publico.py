import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.cpl import CPL
from app.services.indicadores import (
    agenda_publica,
    estrutura_governanca_publica,
    resumo_cadastral,
    resumo_governanca,
)
from app.services.projeto import projetos_autorizados
from app.web.templates import templates

router = APIRouter(tags=["Portal público"])


@router.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    """RF-002/RF-055: portal público institucional, com link pro portal de
    transparência (`/cpls`) — a contagem de CPLs ativas dá um preview do
    que existe sem exigir clicar adiante."""

    total_cpls = db.query(CPL).filter(CPL.ativo.is_(True)).count()
    return templates.TemplateResponse(request, "publico/home.html", {"total_cpls": total_cpls})


@router.get("/cpls")
def lista_cpls_publica(request: Request, db: Session = Depends(get_db)):
    """RF-055: portal de transparência — lista de todas as CPLs ativas do
    programa, sem autenticação nenhuma (é o ponto de entrada do
    requisito de "publicar informações agregadas... sem exposição de
    dados pessoais ou sigilosos")."""

    cpls = db.query(CPL).filter(CPL.ativo.is_(True)).order_by(CPL.nome).all()
    return templates.TemplateResponse(request, "publico/cpls_lista.html", {"cpls": cpls})


@router.get("/cpls/{cpl_id}")
def detalhe_cpl_publica(cpl_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    """RF-055: página pública de uma CPL — identificação, governança
    (estrutura + contagens agregadas, nunca nomes de pessoas), agenda,
    resultados (dados cadastrais agregados, RF-046/047) e projetos
    autorizados. Todas as funções chamadas aqui já filtram/agregam pra
    excluir dado pessoal ou ainda não decidido — ver
    `app/services/indicadores.py` e `app/services/projeto.py`."""

    cpl = db.query(CPL).filter(CPL.id == cpl_id, CPL.ativo.is_(True)).first()
    if cpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")

    return templates.TemplateResponse(
        request,
        "publico/cpl_detalhe.html",
        {
            "cpl": cpl,
            "governanca": resumo_governanca(db, cpl_id),
            "orgaos": estrutura_governanca_publica(db, cpl_id),
            "resultados": resumo_cadastral(db, cpl_id),
            "agenda": agenda_publica(db, cpl_id),
            "projetos": projetos_autorizados(db, cpl_id),
        },
    )
