from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.cadastro_dinamico import CampanhaConvite, DiagnosticoCadastral
from app.models.entidade import Entidade, EntidadeElo
from app.models.enums import Elo
from app.services.campanhas import sincronizar_elos, vincular_responsavel
from app.services.indicadores import registrar_snapshot_diagnostico
from app.services.validadores import uf_valida
from app.web.templates import templates

router = APIRouter(prefix="/atualizacao", tags=["Autopreenchimento público"])

# RF-012: os 17 Objetivos de Desenvolvimento Sustentável da Agenda 2030
# (títulos oficiais da tradução da ONU Brasil), pra listbox de seleção
# múltipla — texto e valor são a mesma string, guardada em
# `DiagnosticoCadastral.ods_relacionados` separada por "; " (não vírgula:
# vários títulos já têm vírgula, ver comentário no model/indicadores.py).
ODS_OPCOES = [
    "ODS 1 — Erradicação da pobreza",
    "ODS 2 — Fome zero e agricultura sustentável",
    "ODS 3 — Saúde e bem-estar",
    "ODS 4 — Educação de qualidade",
    "ODS 5 — Igualdade de gênero",
    "ODS 6 — Água potável e saneamento",
    "ODS 7 — Energia limpa e acessível",
    "ODS 8 — Trabalho decente e crescimento econômico",
    "ODS 9 — Indústria, inovação e infraestrutura",
    "ODS 10 — Redução das desigualdades",
    "ODS 11 — Cidades e comunidades sustentáveis",
    "ODS 12 — Consumo e produção responsáveis",
    "ODS 13 — Ação contra a mudança global do clima",
    "ODS 14 — Vida na água",
    "ODS 15 — Vida terrestre",
    "ODS 16 — Paz, justiça e instituições eficazes",
    "ODS 17 — Parcerias e meios de implementação",
]


def _elos_ativos(db: Session, entidade_id, cpl_id) -> set[Elo]:
    return {
        e.elo
        for e in db.query(EntidadeElo)
        .filter(EntidadeElo.entidade_id == entidade_id, EntidadeElo.cpl_id == cpl_id, EntidadeElo.ativo.is_(True))
        .all()
    }


def _ods_selecionados(diagnostico: DiagnosticoCadastral | None) -> set[str]:
    if diagnostico is None or not diagnostico.ods_relacionados:
        return set()
    return {o.strip() for o in diagnostico.ods_relacionados.split(";")} & set(ODS_OPCOES)


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
            "elos": Elo,
            "elos_ativos": _elos_ativos(db, convite.entidade_id, convite.campanha.cpl_id),
            "ods_opcoes": ODS_OPCOES,
            "ods_selecionados": _ods_selecionados(diagnostico),
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
    ods_relacionados: list[str] = Form([]),
    oferece_qualificacao_colaboradores: str | None = Form(None),
    descricao_qualificacao: str | None = Form(None),
    adota_praticas_sustentabilidade: str | None = Form(None),
    descricao_sustentabilidade: str | None = Form(None),
    possui_contatos_internacionais: str | None = Form(None),
    descricao_contatos_internacionais: str | None = Form(None),
    possui_certificacoes: str | None = Form(None),
    certificacoes: str | None = Form(None),
    nivel_digitalizacao: str | None = Form(None),
    cep: str | None = Form(None),
    numero: str | None = Form(None),
    complemento: str | None = Form(None),
    bairro: str | None = Form(None),
    possui_filiais: str | None = Form(None),
    situacao_vinculo_cpl: str | None = Form(None),
    elos: list[str] = Form([]),
    materia_prima_principal: str | None = Form(None),
    produto_principal: str | None = Form(None),
    compra_de: str | None = Form(None),
    vende_para: str | None = Form(None),
    parcerias_instituicoes: str | None = Form(None),
    funcionarios_clt: str | None = Form(None),
    terceirizados: str | None = Form(None),
    aprendizes: str | None = Form(None),
    colaboradores_pcd: str | None = Form(None),
    investimentos_recentes: str | None = Form(None),
    pretende_investir: str | None = Form(None),
    areas_investimento: str | None = Form(None),
    tecnologias_utilizadas: str | None = Form(None),
    desenvolve_novos_produtos: str | None = Form(None),
    desenvolve_novos_processos: str | None = Form(None),
    possui_setor_pd: str | None = Form(None),
    possui_projetos_inovacao: str | None = Form(None),
    possui_patente: str | None = Form(None),
    possui_registro_software: str | None = Form(None),
    possui_marca_registrada: str | None = Form(None),
    recebeu_recursos_publicos_inovacao: str | None = Form(None),
    praticas_ambientais: str | None = Form(None),
    importa: str | None = Form(None),
    possui_clientes_internacionais: str | None = Form(None),
    participa_feiras_internacionais: str | None = Form(None),
    interesse_exportar: str | None = Form(None),
    necessidades_empresa: str | None = Form(None),
    outras_demandas: str | None = Form(None),
    responsavel_nome: str | None = Form(None),
    responsavel_cargo: str | None = Form(None),
    responsavel_telefone: str | None = Form(None),
    responsavel_whatsapp: str | None = Form(None),
    responsavel_email: str | None = Form(None),
    consentimento_lgpd: str | None = Form(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    convite = db.query(CampanhaConvite).filter(CampanhaConvite.token == token).first()
    if convite is None:
        return templates.TemplateResponse(
            request, "publico/atualizacao_invalida.html", {}, status_code=404
        )

    def _erro(mensagem: str) -> HTMLResponse:
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
                "elos": Elo,
                "elos_ativos": _elos_ativos(db, convite.entidade_id, convite.campanha.cpl_id),
                "ods_opcoes": ODS_OPCOES,
                "ods_selecionados": _ods_selecionados(diagnostico),
                "erro": mensagem,
            },
            status_code=400,
        )

    if uf and not uf_valida(uf):
        return _erro(f"UF {uf!r} não é uma unidade da federação válida.")
    if not consentimento_lgpd:
        return _erro("É necessário consentir com o tratamento de dados para enviar a atualização.")

    entidade: Entidade = convite.entidade
    entidade.razao_social = razao_social
    entidade.nome_fantasia = nome_fantasia or None
    entidade.municipio = municipio or None
    entidade.uf = (uf or "").upper()[:2] or None
    entidade.endereco = endereco or None
    entidade.cep = cep or None
    entidade.numero = numero or None
    entidade.complemento = complemento or None
    entidade.bairro = bairro or None
    entidade.possui_filiais = possui_filiais == "sim"

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
    ods_validos = [o for o in ods_relacionados if o in ODS_OPCOES]
    diagnostico.ods_relacionados = "; ".join(ods_validos) or None
    diagnostico.oferece_qualificacao_colaboradores = oferece_qualificacao_colaboradores == "sim"
    diagnostico.descricao_qualificacao = descricao_qualificacao or None
    diagnostico.adota_praticas_sustentabilidade = adota_praticas_sustentabilidade == "sim"
    diagnostico.descricao_sustentabilidade = descricao_sustentabilidade or None
    diagnostico.possui_contatos_internacionais = possui_contatos_internacionais == "sim"
    diagnostico.descricao_contatos_internacionais = descricao_contatos_internacionais or None
    diagnostico.possui_certificacoes = possui_certificacoes == "sim"
    diagnostico.certificacoes = certificacoes or None
    diagnostico.nivel_digitalizacao = nivel_digitalizacao or None
    diagnostico.situacao_vinculo_cpl = situacao_vinculo_cpl or None
    diagnostico.materia_prima_principal = materia_prima_principal or None
    diagnostico.produto_principal = produto_principal or None
    diagnostico.compra_de = compra_de or None
    diagnostico.vende_para = vende_para or None
    diagnostico.parcerias_instituicoes = parcerias_instituicoes or None
    diagnostico.funcionarios_clt = int(funcionarios_clt) if funcionarios_clt else None
    diagnostico.terceirizados = int(terceirizados) if terceirizados else None
    diagnostico.aprendizes = int(aprendizes) if aprendizes else None
    diagnostico.colaboradores_pcd = int(colaboradores_pcd) if colaboradores_pcd else None
    diagnostico.investimentos_recentes = investimentos_recentes or None
    diagnostico.pretende_investir = pretende_investir == "sim"
    diagnostico.areas_investimento = areas_investimento or None
    diagnostico.tecnologias_utilizadas = tecnologias_utilizadas or None
    diagnostico.desenvolve_novos_produtos = desenvolve_novos_produtos == "sim"
    diagnostico.desenvolve_novos_processos = desenvolve_novos_processos == "sim"
    diagnostico.possui_setor_pd = possui_setor_pd == "sim"
    diagnostico.possui_projetos_inovacao = possui_projetos_inovacao == "sim"
    diagnostico.possui_patente = possui_patente == "sim"
    diagnostico.possui_registro_software = possui_registro_software == "sim"
    diagnostico.possui_marca_registrada = possui_marca_registrada == "sim"
    diagnostico.recebeu_recursos_publicos_inovacao = recebeu_recursos_publicos_inovacao == "sim"
    diagnostico.praticas_ambientais = praticas_ambientais or None
    diagnostico.importa = importa == "sim"
    diagnostico.possui_clientes_internacionais = possui_clientes_internacionais == "sim"
    diagnostico.participa_feiras_internacionais = participa_feiras_internacionais == "sim"
    diagnostico.interesse_exportar = interesse_exportar == "sim"
    diagnostico.necessidades_empresa = necessidades_empresa or None
    diagnostico.outras_demandas = outras_demandas or None

    elos_validos = {Elo(v) for v in elos if v in {e.value for e in Elo}}
    sincronizar_elos(db, entidade, convite.campanha.cpl_id, list(elos_validos))
    vincular_responsavel(
        db,
        entidade,
        convite.campanha.cpl_id,
        responsavel_nome,
        responsavel_cargo,
        responsavel_telefone,
        responsavel_whatsapp,
        responsavel_email,
    )

    convite.respondido = True
    convite.respondido_em = datetime.now()
    convite.consentimento_lgpd = True
    convite.consentimento_em = datetime.now(UTC)
    db.flush()
    registrar_snapshot_diagnostico(db, diagnostico)
    db.commit()

    return templates.TemplateResponse(request, "publico/atualizacao_obrigado.html", {"entidade": entidade})
