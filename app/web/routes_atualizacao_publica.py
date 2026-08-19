from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.cadastro_dinamico import CampanhaConvite, DiagnosticoCadastral
from app.models.entidade import Entidade
from app.services.indicadores import registrar_snapshot_diagnostico
from app.services.validadores import uf_valida
from app.web.templates import templates

router = APIRouter(prefix="/atualizacao", tags=["Autopreenchimento público"])


@router.get("/{token}")
def form_atualizacao(request: Request, token: str, db: Session = Depends(get_db)):
    """RF-012: acesso público (sem login) para a entidade convidada
    autoatualizar seu cadastro e responder ao diagnóstico da campanha."""

    convite = db.query(CampanhaConvite).filter(CampanhaConvite.token == token).first()
    if convite is None:
        return templates.TemplateResponse(
            request, "publico/atualizacao_invalida.html", {}, status_code=404
        )
    diagnostico = (
        db.query(DiagnosticoCadastral)
        .filter(DiagnosticoCadastral.entidade_id == convite.entidade_id)
        .first()
    )
    return templates.TemplateResponse(
        request,
        "publico/atualizacao_form.html",
        {
            "convite": convite,
            "entidade": convite.entidade,
            "campanha": convite.campanha,
            "diagnostico": diagnostico,
        },
    )


@router.post("/{token}")
def processar_atualizacao(
    request: Request,
    token: str,
    razao_social: str = Form(...),
    nome_fantasia: str | None = Form(None),
    municipio: str | None = Form(None),
    uf: str | None = Form(None),
    endereco: str | None = Form(None),
    atividades_produtos: str | None = Form(None),
    diferenciais_competitivos: str | None = Form(None),
    capacidade_produtiva: str | None = Form(None),
    faturamento_faixa: str | None = Form(None),
    empregos_diretos: str | None = Form(None),
    empregos_indiretos: str | None = Form(None),
    realiza_inovacao: str | None = Form(None),
    descricao_inovacao: str | None = Form(None),
    realiza_pd: str | None = Form(None),
    exporta: str | None = Form(None),
    mercados_exportacao: str | None = Form(None),
    interesse_comissoes: str | None = Form(None),
    participacao_associativa: str | None = Form(None),
    entidades_associativas: str | None = Form(None),
    compartilha_recursos: str | None = Form(None),
    recursos_compartilhados: str | None = Form(None),
    ods_relacionados: str | None = Form(None),
    oferece_qualificacao_colaboradores: str | None = Form(None),
    descricao_qualificacao: str | None = Form(None),
    adota_praticas_sustentabilidade: str | None = Form(None),
    descricao_sustentabilidade: str | None = Form(None),
    possui_contatos_internacionais: str | None = Form(None),
    descricao_contatos_internacionais: str | None = Form(None),
    possui_certificacoes: str | None = Form(None),
    certificacoes: str | None = Form(None),
    nivel_digitalizacao: str | None = Form(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    convite = db.query(CampanhaConvite).filter(CampanhaConvite.token == token).first()
    if convite is None:
        return templates.TemplateResponse(
            request, "publico/atualizacao_invalida.html", {}, status_code=404
        )

    if uf and not uf_valida(uf):
        diagnostico = (
            db.query(DiagnosticoCadastral)
            .filter(DiagnosticoCadastral.entidade_id == convite.entidade_id)
            .first()
        )
        return templates.TemplateResponse(
            request,
            "publico/atualizacao_form.html",
            {
                "convite": convite,
                "entidade": convite.entidade,
                "campanha": convite.campanha,
                "diagnostico": diagnostico,
                "erro": f"UF {uf!r} não é uma unidade da federação válida.",
            },
            status_code=400,
        )

    entidade: Entidade = convite.entidade
    entidade.razao_social = razao_social
    entidade.nome_fantasia = nome_fantasia or None
    entidade.municipio = municipio or None
    entidade.uf = (uf or "").upper()[:2] or None
    entidade.endereco = endereco or None

    diagnostico = (
        db.query(DiagnosticoCadastral).filter(DiagnosticoCadastral.entidade_id == entidade.id).first()
    )
    if diagnostico is None:
        diagnostico = DiagnosticoCadastral(entidade_id=entidade.id)
        db.add(diagnostico)
    diagnostico.atividades_produtos = atividades_produtos or None
    diagnostico.diferenciais_competitivos = diferenciais_competitivos or None
    diagnostico.capacidade_produtiva = capacidade_produtiva or None
    diagnostico.faturamento_faixa = faturamento_faixa or None
    diagnostico.empregos_diretos = int(empregos_diretos) if empregos_diretos else None
    diagnostico.empregos_indiretos = int(empregos_indiretos) if empregos_indiretos else None
    diagnostico.realiza_inovacao = realiza_inovacao == "sim"
    diagnostico.descricao_inovacao = descricao_inovacao or None
    diagnostico.realiza_pd = realiza_pd == "sim"
    diagnostico.exporta = exporta == "sim"
    diagnostico.mercados_exportacao = mercados_exportacao or None
    diagnostico.interesse_comissoes = interesse_comissoes or None
    diagnostico.participacao_associativa = participacao_associativa == "sim"
    diagnostico.entidades_associativas = entidades_associativas or None
    diagnostico.compartilha_recursos = compartilha_recursos == "sim"
    diagnostico.recursos_compartilhados = recursos_compartilhados or None
    diagnostico.ods_relacionados = ods_relacionados or None
    diagnostico.oferece_qualificacao_colaboradores = oferece_qualificacao_colaboradores == "sim"
    diagnostico.descricao_qualificacao = descricao_qualificacao or None
    diagnostico.adota_praticas_sustentabilidade = adota_praticas_sustentabilidade == "sim"
    diagnostico.descricao_sustentabilidade = descricao_sustentabilidade or None
    diagnostico.possui_contatos_internacionais = possui_contatos_internacionais == "sim"
    diagnostico.descricao_contatos_internacionais = descricao_contatos_internacionais or None
    diagnostico.possui_certificacoes = possui_certificacoes == "sim"
    diagnostico.certificacoes = certificacoes or None
    diagnostico.nivel_digitalizacao = nivel_digitalizacao or None

    convite.respondido = True
    convite.respondido_em = datetime.now()
    db.flush()
    registrar_snapshot_diagnostico(db, diagnostico)
    db.commit()

    return templates.TemplateResponse(request, "publico/atualizacao_obrigado.html", {"entidade": entidade})
