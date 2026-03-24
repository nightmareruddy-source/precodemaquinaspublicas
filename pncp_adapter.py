from __future__ import annotations

from typing import Any, Iterable
import requests

TIMEOUT = 60

# Busca por janela de vigência, como a API oficial exige
DEFAULT_DATA_INICIAL = "2025-01-01"
DEFAULT_DATA_FINAL = "2026-12-31"


def search_atas(page: int = 1, page_size: int = 50) -> dict[str, Any]:
    url = "https://dadosabertos.compras.gov.br/modulo-arp/1_consultarARP"

    params = {
        "pagina": page,
        "tamanhoPagina": page_size,
        "dataVigenciaInicialMin": DEFAULT_DATA_INICIAL,
        "dataVigenciaInicialMax": DEFAULT_DATA_FINAL,
    }

    response = requests.get(url, params=params, timeout=TIMEOUT)
    response.raise_for_status()
    payload = response.json()

    if not isinstance(payload, dict):
        return {"resultado": []}

    return payload


def iter_results(payload: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for key in ("resultado", "data", "items", "resultados"):
        value = payload.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    yield item
            return
