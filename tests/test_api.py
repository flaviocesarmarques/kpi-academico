"""Testes de API (componente): exercitam rotas, validação, segurança e banco.

Cobrem os caminhos felizes E os de erro — boa prática que costuma ser
esquecida: autenticação negada, duplicidade, dado inválido, recurso inexistente.
"""

import pytest
from fastapi.testclient import TestClient

from conftest import CABECALHO
from kpi_academico.config import Ambiente, Settings, get_settings


def test_health(cliente: TestClient) -> None:
    assert cliente.get("/health/live").json()["status"] == "ok"
    assert cliente.get("/health/ready").status_code == 200


def test_metricas_expostas(cliente: TestClient) -> None:
    corpo = cliente.get("/metrics").text
    assert "kpi_build_info" in corpo


def test_dimensoes(cliente: TestClient) -> None:
    assert len(cliente.get("/api/v1/dimensoes").json()) == 4


def test_escrita_exige_chave(cliente: TestClient) -> None:
    resposta = cliente.post("/api/v1/indicadores", json={}, headers={"X-API-Key": "errada"})
    assert resposta.status_code == 401


def test_indicador_duplicado(cliente: TestClient, indicador_evasao: dict[str, object]) -> None:
    dados = {k: v for k, v in indicador_evasao.items() if k != "id"}
    assert cliente.post("/api/v1/indicadores", json=dados, headers=CABECALHO).status_code == 409


def test_filtrar_por_dimensao(cliente: TestClient, indicador_evasao: dict[str, object]) -> None:
    filtro = "/api/v1/indicadores?dimensao="
    assert len(cliente.get(filtro + "trajetoria_estudante").json()) == 1
    assert cliente.get(filtro + "qualidade_gestao").json() == []


@pytest.mark.parametrize(
    ("campo", "valor"), [("curso", "XYZ"), ("periodo", "2026.9"), ("valor", -1)]
)
def test_medicao_invalida(
    cliente: TestClient, indicador_evasao: dict[str, object], campo: str, valor: object
) -> None:
    dados = {"codigo_indicador": "EST-01", "curso": "CC", "periodo": "2026.1", "valor": 10}
    dados[campo] = valor
    assert cliente.post("/api/v1/medicoes", json=dados, headers=CABECALHO).status_code == 422


def test_medicao_indicador_inexistente(cliente: TestClient) -> None:
    dados = {"codigo_indicador": "NAO-EXISTE", "curso": "CC", "periodo": "2026.1", "valor": 1}
    assert cliente.post("/api/v1/medicoes", json=dados, headers=CABECALHO).status_code == 404


def _medir(cliente: TestClient, periodo: str, valor: float) -> int:
    dados = {"codigo_indicador": "EST-01", "curso": "cc", "periodo": periodo, "valor": valor}
    return cliente.post("/api/v1/medicoes", json=dados, headers=CABECALHO).status_code


def test_painel_semaforo(cliente: TestClient, indicador_evasao: dict[str, object]) -> None:
    assert _medir(cliente, "2026.1", 8) == 201
    assert _medir(cliente, "2026.1", 9) == 409  # mesma medição duas vezes

    painel = cliente.get("/api/v1/cursos/CC/painel?periodo=2026.1").json()
    item = painel["itens"][0]
    assert item["atingimento"] == 150.0
    assert item["status"] == "verde"
    assert item["variacao"] is None  # flag desligada por padrão
    assert painel["resumo"]["verde"] == 1

    vazio = cliente.get("/api/v1/cursos/ADS/painel?periodo=2026.1").json()
    assert vazio["resumo"]["sem_dado"] == 1


def test_painel_curso_inexistente(cliente: TestClient) -> None:
    assert cliente.get("/api/v1/cursos/XX/painel?periodo=2026.1").status_code == 404
    assert cliente.get("/api/v1/cursos/CC/painel?periodo=2026").status_code == 422


def test_painel_com_flag_de_tendencia(
    cliente: TestClient, indicador_evasao: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "flag_painel_tendencia", True)
    _medir(cliente, "2025.2", 14)
    _medir(cliente, "2026.1", 10)
    item = cliente.get("/api/v1/cursos/CC/painel?periodo=2026.1").json()["itens"][0]
    assert item["variacao"] == -4.0


def test_producao_recusa_chave_de_exemplo() -> None:
    with pytest.raises(ValueError, match="produção"):
        Settings(ambiente=Ambiente.PRODUCAO, api_key="troque-esta-chave")


def test_limiares_incoerentes() -> None:
    with pytest.raises(ValueError, match="limite_amarelo"):
        Settings(limite_verde=80, limite_amarelo=90)


def test_indicador_com_fonte_de_dados(cliente: TestClient) -> None:
    dados = {
        "codigo": "EST-09",
        "nome": "Taxa de diplomação",
        "dimensao": "trajetoria_estudante",
        "unidade": "%",
        "meta": 60,
        "polaridade": "maior_melhor",
        "fonte_dados": "Censo da Educação Superior",
    }
    resposta = cliente.post("/api/v1/indicadores", json=dados, headers=CABECALHO)
    assert resposta.status_code == 201
    assert resposta.json()["fonte_dados"] == "Censo da Educação Superior"
