import uuid
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_optional
from app.core.rbac import PAPEIS_GOVERNANCA_LEITURA, cpl_ids_visiveis, verificar_papel
from app.core.security import hash_password
from app.db.session import get_db
from app.models.cpl import CPL
from app.models.entidade import Entidade
from app.models.enums import Papel, TipoEntidade
from app.models.pessoa import Pessoa, PessoaVinculo
from app.models.usuario import Usuario, UsuarioPapel
from app.services.localidades import estados, municipios_do_estado
from app.services.validadores import cnpj_valido, cpf_valido, normalizar_cnpj, normalizar_cpf, uf_valida
from app.web.templates import templates

router = APIRouter(prefix="/painel/cpls", tags=["Área restrita — CPLs"])

_PAPEIS_RESPONSAVEL_ENTIDADE_GESTORA = {Papel.ENTIDADE_GESTORA, Papel.DIRIGENTE_ENTIDADE_GESTORA}


def _exigir_login(usuario: Usuario | None) -> RedirectResponse | None:
    if not usuario:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    return None


def _e_administrador(db: Session, usuario: Usuario) -> bool:
    return cpl_ids_visiveis(db, usuario) is None


def _opt_uuid(valor: str | None) -> uuid.UUID | None:
    return uuid.UUID(valor) if valor else None


def _setores_cadastrados(db: Session) -> list[str]:
    """Setor virou listbox restrita aos valores já usados por alguma CPL
    (pedido explícito) — sem tabela nova, só `DISTINCT` no que já existe.
    Ver `setor_outro` em `criar`/`atualizar` pra como um setor novo (ex.:
    a primeiríssima CPL do sistema, sem nenhum setor cadastrado ainda)
    consegue entrar na lista sem ficar num beco sem saída."""

    linhas = (
        db.query(CPL.setor).filter(CPL.setor.is_not(None)).distinct().order_by(CPL.setor).all()
    )
    return [linha[0] for linha in linhas]


def _setor_final(setor: str | None, setor_outro: str | None) -> str | None:
    return (setor_outro or "").strip() or (setor or None)


@router.get("")
def listar(request: Request, db: Session = Depends(get_db), usuario=Depends(get_current_user_optional)):
    if redir := _exigir_login(usuario):
        return redir
    ids = cpl_ids_visiveis(db, usuario)
    if ids is None:
        cpls = db.query(CPL).order_by(CPL.nome).all()
    elif ids:
        cpls = db.query(CPL).filter(CPL.id.in_(ids)).order_by(CPL.nome).all()
    else:
        cpls = []
    return templates.TemplateResponse(
        request,
        "restrito/cpls/lista.html",
        {
            "cpls": cpls,
            "e_administrador": _e_administrador(db, usuario),
            "estados": estados(),
            "setores": _setores_cadastrados(db),
            "municipios": [],
            "municipio_selecionado": None,
            "usuario": usuario,
            "pagina_ativa": "cpls",
        },
    )


@router.get("/municipios-fragment")
def municipios_fragment(
    request: Request,
    uf: str = "",
    municipio_selecionado: str = "",
    usuario=Depends(get_current_user_optional),
):
    """Fragmento HTMX — o `<select>` de Estado dispara isto no `change`
    (`hx-get`/`hx-trigger`/`hx-target`, sem JavaScript escrito à mão,
    mesmo padrão de fragmento já usado em Cadastro/Campanhas) e troca o
    conteúdo do `<select>` de Município pelos municípios da UF escolhida.
    **Precisa vir registrada antes de `GET /{cpl_id}` no router** — senão
    `/municipios-fragment` seria capturado pelo `{cpl_id}` (tentativa de
    conversão pra UUID, 422) antes de chegar aqui."""

    if redir := _exigir_login(usuario):
        return redir
    return templates.TemplateResponse(
        request,
        "restrito/cpls/fragments/municipio_select.html",
        {
            "municipios": municipios_do_estado(uf) if uf else [],
            "municipio_selecionado": municipio_selecionado or None,
        },
    )


@router.post("")
def criar(
    request: Request,
    nome: str = Form(...),
    sigla: str = Form(...),
    setor: str | None = Form(None),
    setor_outro: str | None = Form(None),
    municipio: str | None = Form(None),
    uf: str | None = Form(None),
    entidade_gestora_id: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    verificar_papel(db, usuario, {Papel.ADMINISTRADOR_PLATAFORMA})
    if db.query(CPL).filter(CPL.sigla == sigla).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Sigla já utilizada por outra CPL.")
    _validar_mascaras(None, None, uf)
    cpl = CPL(
        nome=nome,
        sigla=sigla,
        setor=_setor_final(setor, setor_outro),
        municipio=municipio or None,
        uf=uf.strip().upper() if uf else None,
        entidade_gestora_id=_opt_uuid(entidade_gestora_id),
    )
    db.add(cpl)
    db.commit()
    db.refresh(cpl)
    return RedirectResponse(f"/painel/cpls/{cpl.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{cpl_id}")
def detalhe(
    request: Request,
    cpl_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        return RedirectResponse("/painel/cpls", status_code=status.HTTP_303_SEE_OTHER)
    verificar_papel(db, usuario, PAPEIS_GOVERNANCA_LEITURA, cpl_id=cpl_id)
    entidades = db.query(Entidade).order_by(Entidade.razao_social).all()
    responsaveis = (
        db.query(UsuarioPapel)
        .filter(
            UsuarioPapel.cpl_id == cpl_id,
            UsuarioPapel.papel.in_(_PAPEIS_RESPONSAVEL_ENTIDADE_GESTORA),
        )
        .all()
    )
    return templates.TemplateResponse(
        request,
        "restrito/cpls/detail.html",
        {
            "cpl": cpl,
            "entidades": entidades,
            "tipos_entidade": list(TipoEntidade),
            "responsaveis": responsaveis,
            "papeis_responsavel": list(_PAPEIS_RESPONSAVEL_ENTIDADE_GESTORA),
            "e_administrador": _e_administrador(db, usuario),
            "estados": estados(),
            "setores": _setores_cadastrados(db),
            "municipios": municipios_do_estado(cpl.uf) if cpl.uf else [],
            "municipio_selecionado": cpl.municipio,
            "usuario": usuario,
            "pagina_ativa": "cpls",
        },
    )


def _validar_mascaras(cnpj: str | None, cpf: str | None, uf: str | None) -> None:
    """RF-014: mesma validação de formato já usada em
    `app/api/routes/entidades.py`/`app/web/routes_cadastro.py`."""

    if cnpj and not cnpj_valido(cnpj):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "CNPJ inválido.")
    if cpf and not cpf_valido(cpf):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "CPF inválido.")
    if uf and not uf_valida(uf):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "UF inválida.")


@router.post("/{cpl_id}/entidade-gestora")
def criar_entidade_gestora(
    cpl_id: uuid.UUID,
    tipo: TipoEntidade = Form(...),
    razao_social: str = Form(...),
    cnpj: str | None = Form(None),
    cpf: str | None = Form(None),
    municipio: str | None = Form(None),
    uf: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """Cadastra uma `Entidade` nova e já a designa como
    `CPL.entidade_gestora_id` num passo só — antes disso, o formulário de
    edição da CPL só deixava *escolher* entre entidades já existentes
    (`<select>` cru), sem jeito de cadastrar a entidade gestora na hora.
    Só administrador (mesma restrição de sempre pra editar dados
    cadastrais da CPL, não ampliada pra `PAPEIS_GESTAO` porque o pedido
    foi especificamente "permitir que o administrador possa cadastrar
    entidades gestoras")."""

    if redir := _exigir_login(usuario):
        return redir
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario, {Papel.ADMINISTRADOR_PLATAFORMA})
    _validar_mascaras(cnpj, cpf, uf)

    entidade = Entidade(
        tipo=tipo,
        razao_social=razao_social,
        cnpj=normalizar_cnpj(cnpj) if cnpj else None,
        cpf=normalizar_cpf(cpf) if cpf else None,
        municipio=municipio or None,
        uf=uf.strip().upper() if uf else None,
    )
    db.add(entidade)
    db.flush()
    cpl.entidade_gestora_id = entidade.id
    db.commit()
    return RedirectResponse(f"/painel/cpls/{cpl_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{cpl_id}/usuario-responsavel")
def criar_usuario_responsavel(
    cpl_id: uuid.UUID,
    nome: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),
    papel: Papel = Form(Papel.ENTIDADE_GESTORA),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    """Cria o login (`Usuario`) responsável pela entidade gestora da CPL —
    peça que faltava por completo: até aqui, criar um `Usuario` só existia
    via `POST /api/auth/registrar` (cru, sem escopo de CPL/entidade
    nenhum) seguido de `POST /api/usuarios/{id}/papeis` à parte, nada
    disso exposto na área restrita. Cria também `Pessoa`/`PessoaVinculo`
    (mesmo padrão já usado em F01 — identidade completa, não só a conta
    de acesso) escopados à entidade gestora e à CPL. Exige que a CPL já
    tenha uma entidade gestora definida (`criar_entidade_gestora` acima,
    ou o `<select>` do formulário de edição da CPL) — não faz sentido
    "responsável pela entidade gestora" sem entidade gestora nenhuma."""

    if redir := _exigir_login(usuario):
        return redir
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario, {Papel.ADMINISTRADOR_PLATAFORMA})
    if cpl.entidade_gestora_id is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Defina a entidade gestora desta CPL antes de cadastrar o usuário responsável.",
        )
    if papel not in _PAPEIS_RESPONSAVEL_ENTIDADE_GESTORA:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Papel inválido para usuário responsável.")
    if db.query(Usuario).filter(Usuario.email == email).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "E-mail já cadastrado.")

    pessoa = Pessoa(nome=nome, email=email)
    db.add(pessoa)
    db.flush()

    novo_usuario = Usuario(email=email, hashed_password=hash_password(password), pessoa_id=pessoa.id)
    db.add(novo_usuario)
    db.flush()

    db.add(
        UsuarioPapel(
            usuario_id=novo_usuario.id, papel=papel, cpl_id=cpl_id, entidade_id=cpl.entidade_gestora_id
        )
    )
    db.add(
        PessoaVinculo(
            pessoa_id=pessoa.id,
            entidade_id=cpl.entidade_gestora_id,
            cpl_id=cpl_id,
            papel=papel,
            cargo="Responsável pela entidade gestora",
            data_inicio=date.today(),
        )
    )
    db.commit()
    return RedirectResponse(f"/painel/cpls/{cpl_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{cpl_id}")
def atualizar(
    cpl_id: uuid.UUID,
    nome: str | None = Form(None),
    sigla: str | None = Form(None),
    setor: str | None = Form(None),
    setor_outro: str | None = Form(None),
    municipio: str | None = Form(None),
    uf: str | None = Form(None),
    entidade_gestora_id: str | None = Form(None),
    ativo: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user_optional),
):
    if redir := _exigir_login(usuario):
        return redir
    cpl = db.get(CPL, cpl_id)
    if cpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CPL não encontrada.")
    verificar_papel(db, usuario, {Papel.ADMINISTRADOR_PLATAFORMA})
    _validar_mascaras(None, None, uf)

    if sigla and sigla != cpl.sigla:
        if db.query(CPL).filter(CPL.sigla == sigla, CPL.id != cpl_id).first():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Sigla já utilizada por outra CPL.")
        cpl.sigla = sigla
    if nome:
        cpl.nome = nome
    cpl.setor = _setor_final(setor, setor_outro)
    cpl.municipio = municipio or None
    cpl.uf = uf.strip().upper() if uf else None
    cpl.entidade_gestora_id = _opt_uuid(entidade_gestora_id)
    cpl.ativo = ativo == "on"
    db.commit()
    return RedirectResponse(f"/painel/cpls/{cpl_id}", status_code=status.HTTP_303_SEE_OTHER)
