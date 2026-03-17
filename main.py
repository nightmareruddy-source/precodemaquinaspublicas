from fastapi import FastAPI

app = FastAPI(title="Preço de Máquinas Públicas", version="0.1.0")


@app.get("/")
def home():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}
