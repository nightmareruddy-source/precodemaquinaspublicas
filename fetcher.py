from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
import re

from database import get_conn, create_db
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


def flatten_values(obj: Any) -> list[str]:
    valores: list[str] = []

    if obj is None:
        return valores

    if isinstance(obj, dict):
        for value in obj.values():
            valores.extend(flatten_values(value))
        return valores

    if isinstance(obj, (list, tuple, set)):
        for value in obj:
            valores.extend(flatten_values(value))
        return valores

    if isinstance(obj, (str, int, float, bool)):
        valores.append(str(obj))
        return valores

    return valores


def as_text(value: Any) -> Optional[str]:
    if value is None:
        return None

    if isinstance(value, str):
        texto = value.strip()
        return texto or None

    if isinstance(value, (int, float)):
        return str(value)

    if isinstance(value, dict):
        candidatos = [
            "razaoSocial",
            "nomeRazaoSocial",
            "nomeUnidade",
            "nome",
            "descricao",
            "municipioNome",
            "ufSigla",
            "nomeMunicipio",
        ]
        partes = []
        for chave in candidatos:
            v = value.get(chave)
            if isinstance(v, str) and v.strip():
                partes.append(v.strip())
        if partes:
            return " - ".join(partes)

    return None


def extract_amount(text: str, item: dict[str, Any]) -> Optional[float]:
    campos_diretos = [
        "valorTotalEstimado",
        "valorTotalHomologado",
        "valorTotal",
        "valorGlobal",
        "valor",
    ]

    for campo in campos_diretos:
        valor = item.get(campo)
        if isinstance(valor, (int, float)):
            return float(valor)
        if isinstance(valor, str):
            valor_limpo = valor.replace(".", "").replace(",", ".")
            try:
                return float(valor_limpo)
            except ValueError:
                pass

    match = re.search(r"R\$\s*([\d\.\,]+)", text)
    if not match:
        return None

    bruto = match.group(1).strip()
    if "," in bruto:
        bruto = bruto.replace(".", "").replace(",", ".")
    else:
        bruto = bruto.replace(".", "")

    try:
        return float(bruto)
    except ValueError:
        return None


def extract_year(item: dict[str, Any]) -> int:
    campos = [
        item.get("anoCompra"),
        item.get("ano"),
        item.get("dataPublicacaoPncp"),
        item.get("dataInclusao"),
        item.get("dataAtualizacao"),
    ]

    for valor in campos:
        if isinstance(valor, int):
            return valor
        if isinstance(valor, str):
            match = re.search(r"(20\d{2})", valor)
            if match:
                return int(match.group(1))

    return datetime.utcnow().year


def extract_status(joined: str) -> str:
    low = joined.lower()

    if any(t in low for t in ["encerrad", "expirad", "vencid", "cancelad"]):
        return "encerrado"

    if any(t in low for t in ["vigente", "vigência", "validade", "ativo"]):
        return "vigente"

    return "desconhecido"


def extract_contract_type(joined: str, item: dict[str, Any]) -> str:
    campos = [
        as_text(item.get("categoriaProcesso")),
        as_text(item.get("modalidadeNome")),
        as_text(item.get("instrumentoConvocatorio")),
    ]
    texto = " | ".join([c for c in campos if c] + [joined]).lower()

    if "ata" in texto or "registro de preço" in texto or "registro de preços" in texto:
        return "ata"

    return "compra"


def extract_organ_name(item: dict[str, Any]) -> str:
    candidatos = [
        as_text(item.get("orgaoEntidade")),
        as_text(item.get("unidadeOrgao")),
        as_text(item.get("orgao")),
        as_text(item.get("unidade")),
    ]

    for candidato in candidatos:
        if candidato:
            return candidato[:255]

    return "Órgão não identificado"


def extract_municipality(item: dict[str, Any]) -> Optional[str]:
    candidatos = [
        as_text(item.get("municipioNome")),
        as_text(item.get("municipio")),
    ]

    orgao = item.get("orgaoEntidade")
    if isinstance(orgao, dict):
        candidatos.append(as_text(orgao.get("municipioNome")))
        candidatos.append(as_text(orgao.get("nomeMunicipio")))

    unidade = item.get("unidadeOrgao")
    if isinstance(unidade, dict):
        candidatos.append(as_text(unidade.get("municipioNome")))
        candidatos.append(as_text(unidade.get("nomeMunicipio")))

    for candidato in candidatos:
        if candidato:
            return candidato[:120]

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


def ingest_keyword(keyword: str) -> int:
    payload = search_pncp(keyword)
    inserted = 0

    conn = get_conn()
    cur = conn.cursor()

    total_recebidos = 0
    total_categorizados = 0

    for item in iter_results(payload):
        total_recebidos += 1

        text_parts = flatten_values(item)
        joined = " | ".join(text_parts)

        category = normalize_category(joined)
        if not category:
            continue

        total_categorizados += 1

        source_url = (
            item.get("linkSistemaOrigem")
            or item.get("url")
            or item.get("link")
            or f"pncp://{keyword}/{hash(joined)}"
        )

        item_name = (
            as_text(item.get("objetoCompra"))
            or as_text(item.get("objeto"))
            or category
        )

        registro = {
            "source": "pncp",
            "source_url": str(source_url)[:500],
            "source_document_url": as_text(item.get("linkProcesso")),
            "item_category": category,
            "item_name": item_name[:255],
            "organ_name": extract_organ_name(item),
            "municipality": extract_municipality(item),
            "supplier_name": (
                as_text(item.get("nomeRazaoSocialFornecedor"))
                or as_text(item.get("fornecedor"))
            ),
            "contract_type": extract_contract_type(joined, item),
            "process_number": (
                as_text(item.get("sequencialCompra"))
                or as_text(item.get("numeroControlePNCP"))
            ),
            "ata_number": as_text(item.get("numeroAtaRegistroPreco")),
            "purchase_year": extract_year(item),
            "amount_brl": extract_amount(joined, item),
            "validity_start": None,
            "validity_end": None,
            "status": extract_status(joined),
            "raw_excerpt": joined[:1500],
        }

        foi_novo = upsert_record(cur, registro)
        if foi_novo:
            inserted += 1

    conn.commit()
    conn.close()

    print(f"[{keyword}] recebidos={total_recebidos} categorizados={total_categorizados} inseridos={inserted}")
    return inserted

def main() -> None:
    create_db()
    total = 0

    for keyword in KEYWORDS:
        try:
            qtd = ingest_keyword(keyword)
            total += qtd
            print(f"{keyword}: {qtd} novos")
        except Exception as exc:
            print(f"Falha em '{keyword}': {exc}")

    print(f"Processamento concluído. Registros novos: {total}")


if __name__ == "__main__":
    main()
