from fastapi import FastAPI

app = FastAPI(title="Preço de Máquinas Públicas", version="0.1.0")


@app.get("/")
def home():
    return {
        "projeto": "Preço de Máquinas Públicas",
        "status": "online",
        "dados_exemplo": [
            {
                "item": "Caminhão Basculante",
                "municipio": "Ibiporã",
                "valor": 480000
            },
            {
                "item": "Retroescavadeira",
                "municipio": "Londrina",
                "valor": 320000
            }
        ]
    }


@app.get("/health")
def health():
    return {"status": "ok"}
