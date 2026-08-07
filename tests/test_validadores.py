"""RF-014: validadores de CNPJ/CPF/UF — funções puras, sem banco."""

from app.services.validadores import cnpj_valido, cpf_valido, normalizar_cnpj, normalizar_cpf, uf_valida


def test_cnpj_valido_aceita_cnpj_correto():
    assert cnpj_valido("11222333000181") is True


def test_cnpj_valido_rejeita_digito_verificador_errado():
    assert cnpj_valido("11222333000144") is False


def test_cnpj_valido_rejeita_todos_digitos_iguais():
    assert cnpj_valido("11111111111111") is False


def test_cnpj_valido_aceita_com_mascara():
    assert cnpj_valido("11.222.333/0001-81") is True


def test_cpf_valido_aceita_cpf_correto():
    assert cpf_valido("11144477735") is True


def test_cpf_valido_rejeita_digito_verificador_errado():
    assert cpf_valido("12345678900") is False


def test_normalizar_cnpj_remove_pontuacao():
    assert normalizar_cnpj("11.222.333/0001-81") == "11222333000181"


def test_normalizar_cpf_remove_pontuacao():
    assert normalizar_cpf("111.444.777-35") == "11144477735"


def test_uf_valida_aceita_uf_conhecida():
    assert uf_valida("sp") is True
    assert uf_valida("SP") is True


def test_uf_valida_rejeita_uf_inexistente():
    assert uf_valida("XX") is False
