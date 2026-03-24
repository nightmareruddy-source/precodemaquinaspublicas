from __future__ import annotations

from typing import Any, Optional
import re

from database import get_conn, create_db
from pncp_adapter import search_atas, iter_results


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
    low = (text or "").lower()
    for category, patterns in CATEGORY_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, low):
                return category
    return None


def as_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        texto = value.strip()
        return texto or None
    if isinstance(value, (int, float)):
        return str(value)
    return None


def upsert_record(cur, registro: dict) -> bool:
    cur.execute("""
        SELECT id FROM maquinas
        WHERE source_url = ? AND item_name = ?
    """, (registro["source_url"], registro["item_name"]))
    existente = cur.fetchone()

    if existente:
        cur.execute("""
            UPDATE maquinas
            SET amount_brl = COALESCE(?, amount_brl),
                validity_start = COALESCE(?, validity_start),
                validity_end = COALESCE(?, validity_end),
                status = COALESCE(?, status),
                raw_excerpt = COALESCE(?, raw_excerpt),
                organ_name = COALESCE(?, organ_name),
                municipality = COALESCE(?, municipality),
                item_category = COALESCE(?, item_category)
            WHERE id = ?
        """, (
            registro["amount_brl"],
            registro["validity_start"],
            registro["validity_end"],
            registro["status"],
            registro["raw_excerpt"],
            registro["organ_name"],
            registro["municipality"],
            registro["item_category"],
            existente["id"],
        ))
        return False

    cur.execute("""
        INSERT INTO maquinas (
            source, source_url, source_document_url, item_category, item_name,
            organ_name, municipality, supplier_name, contract_type,
            process_number, ata_number, purchase_year, amount_brl,
            validity_start, validity_end, status, raw_excerpt
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        registro["source"],
        registro["source_url"],
        registro["source_document_url"],
        registro["item_category"],
        registro["item_name"],
        registro["organ_name"],
        registro["municipality"],
        registro["supplier_name"],
        registro["contract_type"],
        registro["process_number"],
        registro["ata_number"],
        registro["purchase_year"],
        registro["amount_brl"],
        registro["validity_start"],
        registro["validity_end"],
        registro["status"],
        registro["raw_excerpt"],
    ))
    return True


def main() -> None:
    create_db()

    payload = search_atas(page=1, page_size=100)

    conn = get_conn()
    cur = conn.cursor()

    recebidos = 0
    categorizados = 0
    inseridos = 0

    for item in iter_results(payload):
        recebidos += 1

        objeto = as_text(item.get("objeto")) or ""
        categoria = normalize_category(objeto)

        if not categoria:
            continue

        categorizados += 1

        ano_compra = item.get("anoCompra")
        try:
            purchase_year = int(ano_compra) if ano_compra is not None else None
        except (ValueError, TypeError):
            purchase_year = None

        valor_total = item.get("valorTotal")
        try:
            amount_brl = float(valor_total) if valor_total is not None else None
        except (ValueError, TypeError):
            amount_brl = None

        registro = {
            "source": "compras_gov_arp",
            "source_url": as_text(item.get("linkAtaPNCP")) or "",
            "source_document_url": as_text(item.get("linkCompraPNCP")),
            "item_category": categoria,
            "item_name": objeto[:255] if objeto else categoria,
            "organ_name": (
                as_text(item.get("nomeOrgao"))
                or as_text(item.get("nomeUnidadeGerenciadora"))
                or "Órgão não identificado"
            ),
            "municipality": None,
            "supplier_name": None,
            "contract_type": "ata",
            "process_number": as_text(item.get("numeroCompra")),
            "ata_number": as_text(item.get("numeroAtaRegistroPreco")),
            "purchase_year": purchase_year,
            "amount_brl": amount_brl,
            "validity_start": as_text(item.get("dataVigenciaInicial")),
            "validity_end": as_text(item.get("dataVigenciaFinal")),
            "status": as_text(item.get("statusAta")) or "desconhecido",
            "raw_excerpt": objeto[:1500],
        }

        if not registro["source_url"]:
            continue

        foi_novo = upsert_record(cur, registro)
        if foi_novo:
            inseridos += 1

    conn.commit()
    conn.close()

    print(f"ARP recebidas={recebidos} categorizadas={categorizados} inseridas={inseridos}")


if __name__ == "__main__":
    main()
