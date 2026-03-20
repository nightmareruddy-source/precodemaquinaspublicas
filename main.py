from fastapi import FastAPI, Query
from sqlmodel import Session, select

from database import engine, create_db_and_tables
from models import MachineRecord

app = FastAPI()

create_db_and_tables()


@app.get("/")
def home():
    return {"ok": True}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/maquinas")
def maquinas(tipo: str = Query(default=None)):
    with Session(engine) as session:
        registros = session.exec(select(MachineRecord)).all()

        resultado = []
        termo = (tipo or "").lower().strip()

        for r in registros:
            item_name = (r.item_name or "")
            item_category = (r.item_category or "")
            municipality = (r.municipality or "")
            organ_name = (r.organ_name or "")

            if termo:
                texto_busca = " | ".join([
                    item_name.lower(),
                    item_category.lower(),
                    municipality.lower(),
                    organ_name.lower(),
                ])
                if termo not in texto_busca:
                    continue

            resultado.append({
                "id": r.id,
                "item": item_name,
                "categoria": item_category,
                "municipio": municipality,
                "orgao": organ_name,
                "valor": r.amount_brl,
                "ano": r.purchase_year,
                "status": r.status,
                "fonte": r.source,
                "link": r.source_url,
            })

        return resultado
