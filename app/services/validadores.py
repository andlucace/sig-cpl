"""RF-014: regras de qualidade de dados — "máscara" aqui significa
validação de formato de verdade (dígito verificador oficial de CNPJ/CPF,
não só contar dígitos; UF contra a lista fechada de 27 unidades da
federação), reaproveitada nos três pontos de escrita já estabelecidos
para dado cadastral (criação direta via API, importação de planilha —
RF-013 — e formulário público de campanha — RF-012), pra nunca ficar
divergente entre eles.

Só valida quando o campo vem preenchido — nenhum destes campos é
obrigatório em si (uma entidade estrangeira pode não ter CNPJ/CPF
brasileiro), então ausência não é erro; valor presente e mal formado é."""

_UFS_VALIDAS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO",
}


def normalizar_cnpj(valor: str) -> str:
    return "".join(c for c in valor if c.isdigit())


def normalizar_cpf(valor: str) -> str:
    return "".join(c for c in valor if c.isdigit())


def _digito_verificador(base: str, pesos: list[int]) -> str:
    soma = sum(int(digito) * peso for digito, peso in zip(base, pesos))
    resto = soma % 11
    return "0" if resto < 2 else str(11 - resto)


def cnpj_valido(valor: str) -> bool:
    """Dígito verificador oficial (módulo 11) — pega erro de digitação
    que só checar 14 dígitos não pegaria (ex.: dígitos trocados de
    lugar)."""

    cnpj = normalizar_cnpj(valor)
    if len(cnpj) != 14 or len(set(cnpj)) == 1:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    d1 = _digito_verificador(cnpj[:12], pesos1)
    d2 = _digito_verificador(cnpj[:12] + d1, pesos2)
    return cnpj[-2:] == d1 + d2


def cpf_valido(valor: str) -> bool:
    cpf = normalizar_cpf(valor)
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
    pesos1 = list(range(10, 1, -1))
    pesos2 = list(range(11, 1, -1))
    d1 = _digito_verificador(cpf[:9], pesos1)
    d2 = _digito_verificador(cpf[:9] + d1, pesos2)
    return cpf[-2:] == d1 + d2


def uf_valida(valor: str) -> bool:
    return valor.strip().upper() in _UFS_VALIDAS
