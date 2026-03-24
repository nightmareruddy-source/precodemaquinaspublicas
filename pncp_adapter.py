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


def search_pncp(keyword: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
    url = "https://pncp.gov.br/pncp-api/v1/orgaos/consulta"

    params = {
        "pagina": page,
        "tamanhoPagina": page_size,
        "palavraChave": keyword,
    }

    response = requests.get(url, params=params, timeout=TIMEOUT)
    response.raise_for_status()

    payload = response.json()

    print("URL usada:", response.url)
    print("Tipo do payload:", type(payload).__name__)

    if isinstance(payload, dict):
        print("Chaves do payload:", list(payload.keys())[:20])

    return payload if isinstance(payload, dict) else {"data": []}


def iter_results(payload: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for key in ("data", "items", "resultado", "resultados"):
        value = payload.get(key)
        if isinstance(value, list):
            print(f"Lista encontrada em '{key}' com", len(value), "itens")
            for item in value:
                if isinstance(item, dict):
                    yield item
            return

    if isinstance(payload.get("data"), dict):
        for chave, value in payload["data"].items():
            if isinstance(value, list):
                print(f"Lista encontrada em 'data[{chave}]' com", len(value), "itens")
                for item in value:
                    if isinstance(item, dict):
                        yield item
                return

    print("Nenhuma lista de resultados encontrada.")
