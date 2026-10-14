"""KPI Acadêmico — API de indicadores acadêmicos para cursos de graduação.

A versão é lida dos metadados do pacote instalado (definida no pyproject.toml
e atualizada automaticamente pelo release-please). Assim existe uma ÚNICA
fonte da verdade para a versão, exposta em /health e nas métricas.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("kpi-academico")
except PackageNotFoundError:  # pragma: no cover - só ocorre sem instalação
    __version__ = "0.2.0"
