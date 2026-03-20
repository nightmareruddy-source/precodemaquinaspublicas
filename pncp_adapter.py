"""Adaptador PNCP mais conservador.

Observação importante:
- A API pública de consulta do PNCP documenta consultas por data/período.
- A busca por palavra-chave usada pela interface do portal é menos estável.
- Por isso este adapter deixa endpoint e nomes de parâmetros configuráveis por ambiente.
"""
from __future__ import annotations

from typing import Any, Iterable
import os
import requests

PNCP_BASE_URL = os.getenv("PNCP_BASE_URL", "https://pncp.gov.br/api/consulta")
TIMEOUT = int(os.getenv("PNCP_TIMEOUT", "60"))

# Deixe configurável para não travar o projeto em um único endpoint
PNCP_SEARCH_ENDPOINT = os.getenv(
    "PNCP_SEARCH_ENDPOINT",
    "/v1/contratacoes/publicacao",
)

# Nome do parâmetro de busca: ajuste fácil sem reescrever código
PNCP_QUERY_PARAM = os.getenv("PNCP_QUERY_PARAM", "palavraChave")

KEYWORDS = [
    "escavadeira hidráulica",
    "pá carregadeira",
    "motoniveladora",
    "retroescavadeira",
    "rolo compactador",
    "caminhão caçamba",
    "caminhão pipa",
    "caminhão coletor de lixo",
    "caminhão chassi",
    "caminhão carroceria",
    "caminhão toco",
]


def search_pncp(keyword: str, page: int = 1, page_size: int = 50) -> dict[str, Any]:
    url = f"{PNCP_BASE_URL.rstrip('/')}{PNCP_SEARCH_ENDPOINT}"

    params: dict[str, Any] = {
        "pagina": page,
        "tamanhoPagina": page_size,
        PNCP_QUERY_PARAM: keyword,
    }

    response = requests.get(url, params=params, timeout=TIMEOUT)
    response.raise_for_status()

    payload = response.json()

    # debug mínimo para diagnóstico
    if not isinstance(payload, dict):
        return {"data": []}

    return payload


def iter_results(payload: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for key in ("data", "items", "resultado", "resultados"):
        value = payload.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    yield item
            return

    # fallback defensivo
    if isinstance(payload.get("data"), dict):
        for _, value in payload["data"].items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        yield item
