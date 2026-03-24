import requests

TIMEOUT = 60

def search_atas(page: int = 1, page_size: int = 20):
    url = "https://dadosabertos.compras.gov.br/modulo-arp/1_consultarARP"

    params = {
        "pagina": page,
        "tamanhoPagina": page_size,
    }

    response = requests.get(url, params=params, timeout=TIMEOUT)
    response.raise_for_status()

    return response.json()


def iter_results(payload):
    if isinstance(payload, dict):
        for key in ("resultado", "data"):
            if key in payload and isinstance(payload[key], list):
                for item in payload[key]:
                    yield item
