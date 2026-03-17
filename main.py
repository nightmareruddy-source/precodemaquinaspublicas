from datetime import datetime, date
from typing import Optional
from sqlmodel import SQLModel, Field


class MachineRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source: str = Field(index=True)
    source_url: Optional[str] = None
    source_document_url: Optional[str] = None
    item_category: str = Field(index=True)
    item_name: str = Field(index=True)
    organ_name: str = Field(index=True)
    municipality: Optional[str] = Field(default=None, index=True)
    supplier_name: Optional[str] = None
    contract_type: str = Field(index=True)  # "ata" ou "compra"
    process_number: Optional[str] = None
    ata_number: Optional[str] = None
    purchase_year: Optional[int] = Field(default=None, index=True)
    amount_brl: Optional[float] = None
    validity_start: Optional[date] = None
    validity_end: Optional[date] = None
    status: str = Field(default="desconhecido", index=True)
    raw_excerpt: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Optional

from fastapi import FastAPI, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from database import create_db_and_tables, get_session
from models import MachineRecord

app = FastAPI(title="Preço de Máquinas Públicas", version="0.1.0")

# Como seu index.html está na raiz do repositório:
templates = Jinja2Templates(directory=".")

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


@app.get("/", response_class=HTMLResponse)
def home(request: Request, session: Session = Depends(get_session)):
    rows = session.exec(select(MachineRecord)).all()
    top = rows[:50]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "rows": top,
            "title": "Preço de Máquinas Públicas",
        },
    )
