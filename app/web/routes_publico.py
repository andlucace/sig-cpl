import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.cpl import CPL
from app.models.enums import Elo, TipoEntidade
from app.schemas.adesao import SolicitacaoAdesaoCreate
from app.services.adesao import SolicitacaoInvalida, criar_solicitacao
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


def _cpl_ativa_ou_404(db: Session, cpl_id: uuid.UUID) -> CPL:
    cpl = db.query(CPL).filter(CPL.id == cpl_id, CPL.ativo.is_(True)).first()
    if cpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    return cpl


@router.get("/cpls/{cpl_id}/solicitar-adesao")
def solicitar_adesao_form(cpl_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    """F01: formulário público de solicitação de adesão — nenhum vínculo
    é criado aqui, só o pedido (ver `criar_solicitacao`); "cadastro" e
    "consentimento" do fluxo acontecem nesta tela, "validação" fica para
    quem tem papel de gestão analisar depois."""

    cpl = _cpl_ativa_ou_404(db, cpl_id)
    return templates.TemplateResponse(
        request,
        "publico/solicitar_adesao.html",
        {"cpl": cpl, "tipos": list(TipoEntidade), "elos": list(Elo), "erro": None, "dados": {}},
    )


@router.post("/cpls/{cpl_id}/solicitar-adesao")
def solicitar_adesao_submit(
    cpl_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    tipo: TipoEntidade = Form(...),
    razao_social: str = Form(...),
    cnpj: str = Form(""),
    cpf: str = Form(""),
    municipio: str = Form(""),
    uf: str = Form(""),
    elo_pretendido: Elo = Form(...),
    mensagem: str = Form(""),
    contato_nome: str = Form(...),
    contato_email: str = Form(...),
    contato_telefone: str = Form(""),
    consentimento_lgpd: bool = Form(False),
):
    cpl = _cpl_ativa_ou_404(db, cpl_id)
    dados_form = {
        "tipo": tipo.value,
        "razao_social": razao_social,
        "cnpj": cnpj,
        "cpf": cpf,
        "municipio": municipio,
        "uf": uf,
        "elo_pretendido": elo_pretendido.value,
        "mensagem": mensagem,
        "contato_nome": contato_nome,
        "contato_email": contato_email,
        "contato_telefone": contato_telefone,
    }
    try:
        payload = SolicitacaoAdesaoCreate(
            tipo=tipo,
            razao_social=razao_social,
            cnpj=cnpj or None,
            cpf=cpf or None,
            municipio=municipio or None,
            uf=uf or None,
            elo_pretendido=elo_pretendido,
            mensagem=mensagem or None,
            contato_nome=contato_nome,
            contato_email=contato_email,
            contato_telefone=contato_telefone or None,
            consentimento_lgpd=consentimento_lgpd,
        )
        criar_solicitacao(db, cpl_id, payload)
    except ValidationError:
        erro = "E-mail de contato inválido."
    except SolicitacaoInvalida as exc:
        erro = str(exc)
    else:
        erro = None

    if erro is not None:
        return templates.TemplateResponse(
            request,
            "publico/solicitar_adesao.html",
            {
                "cpl": cpl,
                "tipos": list(TipoEntidade),
                "elos": list(Elo),
                "erro": erro,
                "dados": dados_form,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return templates.TemplateResponse(
        request, "publico/solicitacao_adesao_obrigado.html", {"cpl": cpl}
    )
