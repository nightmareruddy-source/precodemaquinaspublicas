from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
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
        ]
        partes: list[str] = []
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
            try:
                return float(valor)
            except ValueError:
                pass
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


def upsert_record(session: Session, record: MachineRecord) -> bool:
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
        existing.organ_name = record.organ_name or existing.organ_name
        existing.municipality = record.municipality or existing.municipality
        existing.item_category = record.item_category or existing.item_category
        session.add(existing)
        return False

    session.add(record)
    return True


def ingest_keyword(keyword: str) -> int:
    payload = search_pncp(keyword)
    inserted = 0

    with Session(engine) as session:
        for item in iter_results(payload):
            text_parts = flatten_values(item)
            joined = " | ".join(text_parts)

            category = normalize_category(joined)
            if not category:
                continue

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

            organ_name = extract_organ_name(item)
            municipality = extract_municipality(item)

            record = MachineRecord(
                source="pncp",
                source_url=str(source_url)[:500],
                source_document_url=(
                    as_text(item.get("linkProcesso"))[:500]
                    if as_text(item.get("linkProcesso"))
                    else None
                ),
                item_category=category,
                item_name=item_name[:255],
                organ_name=organ_name,
                municipality=municipality,
                supplier_name=(
                    as_text(item.get("nomeRazaoSocialFornecedor"))
                    or as_text(item.get("fornecedor"))
                ),
                contract_type=extract_contract_type(joined, item),
                process_number=(
                    as_text(item.get("sequencialCompra"))
                    or as_text(item.get("numeroControlePNCP"))
                ),
                ata_number=as_text(item.get("numeroAtaRegistroPreco")),
                purchase_year=extract_year(item),
                amount_brl=extract_amount(joined, item),
                validity_start=None,
                validity_end=None,
                status=extract_status(joined),
                raw_excerpt=joined[:1500],
            )

            foi_novo = upsert_record(session, record)
            if foi_novo:
                inserted += 1

        session.commit()

    return inserted


def main() -> None:
    create_db_and_tables()
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
