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
