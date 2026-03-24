"""Adaptador PNCP.

Mantém a chamada isolada para a API pública de consulta do PNCP.
Se o endpoint ou o nome do parâmetro de busca mudar, ajuste por variável
ambiente sem reescrever o coletor.
"""
from __future__ import annotations

from typing import Any, Iterable
import os

import requests

PNCP_BASE_URL = os.getenv("PNCP_BASE_URL", "https://pncp.gov.br/api/consulta")
TIMEOUT = int(os.getenv("PNCP_TIMEOUT", "60"))
PNCP_SEARCH_ENDPOINT = os.getenv("PNCP_SEARCH_ENDPOINT", "/v1/contratacoes/publicacao")
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

    nested = payload.get("data")
    if isinstance(nested, dict):
        for value in nested.values():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        yield item
