from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Optional

from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from database import create_db_and_tables, get_session
from models import MachineRecord

app = FastAPI(title="Preço de Máquinas Públicas", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/search")
def search_records(
    q: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    contract_type: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
):
    stmt = select(MachineRecord)
    rows = session.exec(stmt).all()
    result = []

    for row in rows:
        hay = " ".join(
            filter(
                None,
                [
                    row.item_name,
                    row.item_category,
                    row.organ_name,
                    row.municipality,
                    row.supplier_name,
                    row.raw_excerpt,
                ],
            )
        )

        if q and q.lower() not in hay.lower():
            continue
        if category and row.item_category != category:
            continue
        if contract_type and row.contract_type != contract_type:
            continue
        if status and row.status != status:
            continue

        result.append(row)

    return result


@app.get("/api/stats")
def stats(session: Session = Depends(get_session)):
    rows = session.exec(select(MachineRecord)).all()
    counts = defaultdict(int)
    prices = defaultdict(list)

    for row in rows:
        counts[row.item_category] += 1
        if row.amount_brl is not None:
            prices[row.item_category].append(row.amount_brl)

    averages = {k: round(mean(v), 2) for k, v in prices.items() if v}
    return {"counts": counts, "average_prices": averages}


@app.get("/")
def home():
    return {"status": "ok"}
