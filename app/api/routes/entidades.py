import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rbac import PAPEIS_GESTAO, PAPEIS_GOVERNANCA_LEITURA, cpl_ids_visiveis, verificar_papel
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.entidade import Entidade, EntidadeCPL, OfertaEntidade
from app.models.usuario import Usuario
from app.schemas.entidade import (
    CanaisDigitaisUpdate,
    EntidadeCPLRead,
    EntidadeCreate,
    EntidadeRead,
    OfertaEntidadeCreate,
    OfertaEntidadeRead,
)
from app.services.validadores import cnpj_valido, cpf_valido, normalizar_cnpj, normalizar_cpf, uf_valida

router = APIRouter(prefix="/entidades", tags=["Cadastro e cadeia"])
cpl_router = APIRouter(prefix="/cpls", tags=["Cadastro e cadeia"])


def _validar_mascaras(cnpj: str | None, cpf: str | None, uf: str | None) -> None:
    """RF-014: "máscara" = validação de formato de verdade (dígito
    verificador, não só contagem de dígitos) — só valida quando o campo
    vem preenchido, nenhum é obrigatório em si."""

    if cnpj and not cnpj_valido(cnpj):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "CNPJ inválido.")
    if cpf and not cpf_valido(cpf):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "CPF inválido.")
    if uf and not uf_valida(uf):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "UF inválida.")


def _get_entidade_visivel_or_404(db: Session, usuario: Usuario, entidade_id: uuid.UUID) -> Entidade:
    """Mesma checagem de `obter_entidade` — reaproveitada pelas rotas de
    ofertas/canais digitais, que também são escopadas por entidade, não
    por CPL na URL."""

    entidade = db.get(Entidade, entidade_id)
    if entidade is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entidade não encontrada.")
    ids_visiveis = cpl_ids_visiveis(db, usuario)
    if ids_visiveis is not None:
        vinculada = (
            db.query(EntidadeCPL)
            .filter(EntidadeCPL.entidade_id == entidade_id, EntidadeCPL.cpl_id.in_(ids_visiveis))
            .first()
        )
        if vinculada is None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não tem acesso a esta entidade.")
    return entidade


@router.post("", response_model=EntidadeRead, status_code=status.HTTP_201_CREATED)
def criar_entidade(
    dados: EntidadeCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Entidade:
    """RF-006/RF-008: cadastra empresa, órgão, universidade, ICT, associação,
    prestador ou ambiente de inovação.

    Nota de escopo do RBAC: criar uma Entidade continua sem escopo de CPL
    de propósito — o registro pode não ter nenhum vínculo ainda (o vínculo
    é feito à parte via `EntidadeCPL`, `POST /cpls/{cpl_id}/entidades/
    {entidade_id}/vinculo`, que já é escopado). Qualquer usuário com papel
    de gestão em alguma CPL pode cadastrar dado mestre; leitura (`GET`,
    abaixo) é que é restrita às CPLs onde a entidade está de fato
    vinculada."""

    verificar_papel(db, usuario_atual, PAPEIS_GESTAO)
    _validar_mascaras(dados.cnpj, dados.cpf, dados.uf)

    valores = dados.model_dump()
    if valores.get("cnpj"):
        valores["cnpj"] = normalizar_cnpj(valores["cnpj"])
    if valores.get("cpf"):
        valores["cpf"] = normalizar_cpf(valores["cpf"])
    if valores.get("uf"):
        valores["uf"] = valores["uf"].strip().upper()

    entidade = Entidade(**valores)
    db.add(entidade)
    db.commit()
    db.refresh(entidade)
    return entidade


@router.get("", response_model=list[EntidadeRead])
def listar_entidades(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[Entidade]:
    """Escopo do RBAC (RN-003): uma entidade pode estar em várias CPLs, então
    "escopar por CPL" aqui significa "está vinculada a pelo menos uma CPL
    que o usuário pode ver" — não uma CPL única. Administrador (
    `cpl_ids_visiveis` retorna None) continua vendo todas."""

    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA)
    query = db.query(Entidade)
    ids_visiveis = cpl_ids_visiveis(db, usuario_atual)
    if ids_visiveis is not None:
        query = (
            query.join(EntidadeCPL, EntidadeCPL.entidade_id == Entidade.id)
            .filter(EntidadeCPL.cpl_id.in_(ids_visiveis))
            .distinct()
        )
    return query.order_by(Entidade.razao_social).all()


@router.get("/{entidade_id}", response_model=EntidadeRead)
def obter_entidade(
    entidade_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Entidade:
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA)
    return _get_entidade_visivel_or_404(db, usuario_atual, entidade_id)


# --- Canais digitais e ofertas (RF-010) --------------------------------------


@router.patch("/{entidade_id}/canais-digitais", response_model=EntidadeRead)
def atualizar_canais_digitais(
    entidade_id: uuid.UUID,
    dados: CanaisDigitaisUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> Entidade:
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO)
    entidade = db.get(Entidade, entidade_id)
    if entidade is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entidade não encontrada.")
    entidade.canais_digitais = dados.canais_digitais or None
    db.commit()
    db.refresh(entidade)
    return entidade


@router.post(
    "/{entidade_id}/ofertas", response_model=OfertaEntidadeRead, status_code=status.HTTP_201_CREATED
)
def criar_oferta(
    entidade_id: uuid.UUID,
    dados: OfertaEntidadeCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> OfertaEntidade:
    """RF-010: produto, serviço ou tecnologia ofertado pela entidade."""

    verificar_papel(db, usuario_atual, PAPEIS_GESTAO)
    if db.get(Entidade, entidade_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entidade não encontrada.")
    oferta = OfertaEntidade(entidade_id=entidade_id, **dados.model_dump())
    db.add(oferta)
    db.commit()
    db.refresh(oferta)
    return oferta


@router.get("/{entidade_id}/ofertas", response_model=list[OfertaEntidadeRead])
def listar_ofertas(
    entidade_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[OfertaEntidade]:
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA)
    _get_entidade_visivel_or_404(db, usuario_atual, entidade_id)
    return (
        db.query(OfertaEntidade)
        .filter(OfertaEntidade.entidade_id == entidade_id)
        .order_by(OfertaEntidade.tipo, OfertaEntidade.nome)
        .all()
    )


@router.post("/ofertas/{oferta_id}/desativar", response_model=OfertaEntidadeRead)
def desativar_oferta(
    oferta_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> OfertaEntidade:
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO)
    oferta = db.get(OfertaEntidade, oferta_id)
    if oferta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Oferta não encontrada.")
    oferta.ativo = False
    db.commit()
    db.refresh(oferta)
    return oferta


# --- Vínculo Entidade <-> CPL (RN-003) --------------------------------------


@cpl_router.post(
    "/{cpl_id}/entidades/{entidade_id}/vinculo",
    response_model=EntidadeCPLRead,
    status_code=status.HTTP_201_CREATED,
)
def vincular_entidade_a_cpl(
    cpl_id: uuid.UUID,
    entidade_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> EntidadeCPL:
    """RN-003: uma organização pode participar de mais de uma CPL; o
    vínculo (não a entidade em si) é escopado por CPL no RBAC."""

    if db.get(CPL, cpl_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    if db.get(Entidade, entidade_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entidade não encontrada.")
    verificar_papel(db, usuario_atual, PAPEIS_GESTAO, cpl_id=cpl_id)

    vinculo = (
        db.query(EntidadeCPL)
        .filter(EntidadeCPL.cpl_id == cpl_id, EntidadeCPL.entidade_id == entidade_id)
        .first()
    )
    if vinculo is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Entidade já vinculada a esta CPL.")

    vinculo = EntidadeCPL(cpl_id=cpl_id, entidade_id=entidade_id, data_vinculo=date.today())
    db.add(vinculo)
    db.commit()
    db.refresh(vinculo)
    return vinculo


@cpl_router.get("/{cpl_id}/entidades", response_model=list[EntidadeCPLRead])
def listar_entidades_da_cpl(
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
) -> list[EntidadeCPL]:
    if db.get(CPL, cpl_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario_atual, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)
    return (
        db.query(EntidadeCPL)
        .filter(EntidadeCPL.cpl_id == cpl_id, EntidadeCPL.ativo.is_(True))
        .all()
    )
