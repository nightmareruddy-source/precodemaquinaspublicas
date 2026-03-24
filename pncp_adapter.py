from __future__ import annotations

from typing import Any, Iterable
import requests

TIMEOUT = 60

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
    url = "https://pncp.gov.br/pncp-api/v1/orgaos/consulta"

    params = {
        "pagina": page,
        "tamanhoPagina": page_size,
        "palavraChave": keyword,
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

    if isinstance(payload.get("data"), dict):
        for _, value in payload["data"].items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        yield item
