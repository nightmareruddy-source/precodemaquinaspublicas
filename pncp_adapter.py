"""Adaptador inicial para o PNCP.

Este módulo existe para você ligar o robô ao PNCP usando a API pública de consulta.
O portal mantém documentação Swagger e manual de integração para consultas públicas.
Veja docs/NOTAS.md antes de ativar em produção.
"""
from __future__ import annotations
from typing import Any, Iterable
import os
import requests

PNCP_BASE_URL = os.getenv("PNCP_BASE_URL", "https://pncp.gov.br/api/consulta")
TIMEOUT = int(os.getenv("PNCP_TIMEOUT", "30"))

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


def search_pncp(keyword: str, page: int = 1) -> dict[str, Any]:
    """Chamada genérica e conservadora.

    Ajuste o endpoint exato com base no Swagger atual do PNCP.
    Este código não assume um schema fechado para não quebrar quando o portal mudar.
    """
    endpoint = os.getenv("PNCP_SEARCH_ENDPOINT", "/v1/contratacoes/publicacao")
    url = f"{PNCP_BASE_URL.rstrip('/')}{endpoint}"
    params = {"pagina": page, "q": keyword}
    response = requests.get(url, params=params, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def iter_results(payload: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for key in ("data", "items", "resultado", "resultados"):
        value = payload.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    yield item
