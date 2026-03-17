from __future__ import annotations
from datetime import datetime, date
from typing import Optional
import re
from sqlmodel import Session, select
from database import engine, create_db_and_tables
from models import MachineRecord
from pncp_adapter import search_pncp, iter_results, KEYWORDS

CATEGORY_PATTERNS = [
    ("escavadeira hidráulica", [r"escavadeira"]),
    ("pá carregadeira", [r"pá\s+carregadeira", r"pa\s+carregadeira"]),
    ("motoniveladora", [r"motoniveladora"]),
    ("retroescavadeira", [r"retroescavadeira"]),
    ("rolo compactador", [r"rolo\s+compactador"]),
    ("caminhão caçamba", [r"caminh[aã]o\s+ca[cç]amba", r"basculante"]),
    ("caminhão pipa", [r"caminh[aã]o\s+pipa"]),
    ("caminhão coletor de lixo", [r"coletor\s+de\s+lixo"]),
    ("caminhão chassi", [r"caminh[aã]o\s+chassi"]),
    ("caminhão carroceria", [r"caminh[aã]o\s+carroceria"]),
    ("caminhão toco", [r"caminh[aã]o\s+toco"]),
]


def normalize_category(text: str) -> Optional[str]:
    low = text.lower()
    for category, patterns in CATEGORY_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, low):
                return category
    return None


def extract_amount(text: str) -> Optional[float]:
    match = re.search(r"R\$\s*([\d\.]+,\d{2})", text)
    if not match:
        return None
    raw = match.group(1).replace(".", "").replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def upsert_record(session: Session, record: MachineRecord) -> None:
    stmt = select(MachineRecord).where(
        MachineRecord.source_url == record.source_url,
        MachineRecord.item_name == record.item_name,
    )
    existing = session.exec(stmt).first()
    if existing:
        existing.amount_brl = record.amount_brl or existing.amount_brl
        existing.validity_start = record.validity_start or existing.validity_start
        existing.validity_end = record.validity_end or existing.validity_end
        existing.status = record.status or existing.status
        existing.raw_excerpt = record.raw_excerpt or existing.raw_excerpt
        session.add(existing)
    else:
        session.add(record)


def ingest_keyword(keyword: str) -> int:
    payload = search_pncp(keyword)
    inserted = 0
    with Session(engine) as session:
        for item in iter_results(payload):
            text_parts = [str(v) for v in item.values() if isinstance(v, (str, int, float))]
            joined = " | ".join(text_parts)
            category = normalize_category(joined)
            if not category:
                continue
            source_url = item.get("linkSistemaOrigem") or item.get("url") or item.get("link") or f"pncp://{keyword}/{hash(joined)}"
            contract_type = "ata" if "ata" in joined.lower() else "compra"
            status = "vigente" if any(t in joined.lower() for t in ["vigente", "vigência", "validade"]) else "desconhecido"
            record = MachineRecord(
                source="pncp",
                source_url=str(source_url),
                source_document_url=item.get("linkProcesso") if isinstance(item.get("linkProcesso"), str) else None,
                item_category=category,
                item_name=item.get("objetoCompra") or item.get("objeto") or category,
                organ_name=item.get("orgaoEntidade") or item.get("unidadeOrgao") or "Órgão não identificado",
                municipality=item.get("municipioNome") or item.get("municipio") or None,
                supplier_name=item.get("nomeRazaoSocialFornecedor") or item.get("fornecedor") or None,
                contract_type=contract_type,
                process_number=item.get("sequencialCompra") or item.get("numeroControlePNCP") or None,
                ata_number=item.get("numeroAtaRegistroPreco") or None,
                purchase_year=datetime.utcnow().year,
                amount_brl=extract_amount(joined),
                validity_start=None,
                validity_end=None,
                status=status,
                raw_excerpt=joined[:1500],
            )
            upsert_record(session, record)
            inserted += 1
        session.commit()
    return inserted


def main() -> None:
    create_db_and_tables()
    total = 0
    for keyword in KEYWORDS:
        try:
            total += ingest_keyword(keyword)
        except Exception as exc:  # noqa: BLE001
            print(f"Falha em '{keyword}': {exc}")
    print(f"Processamento concluído. Registros tocados: {total}")

if __name__ == "__main__":
    main()
