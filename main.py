from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"ok": True}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/maquinas")
def maquinas():
    return [
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
