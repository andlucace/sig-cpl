from pydantic import BaseModel


class ResumoCadastralRead(BaseModel):
    """RF-046/047: agregado do que já é coletado via campanha cadastral —
    ver `app/services/indicadores.py::resumo_cadastral` para o que cada
    campo mede e o que ainda não é capturado no cadastro atual."""

    total_empresas: int
    total_com_diagnostico: int
    soma_empregos_diretos: int
    soma_empregos_indiretos: int
    distribuicao_faturamento: dict[str, int]
    percentual_inovacao: float | None
    percentual_pd: float | None
    percentual_exportacao: float | None
    percentual_associativismo: float | None
    ods_mais_citados: list[tuple[str, int]]
