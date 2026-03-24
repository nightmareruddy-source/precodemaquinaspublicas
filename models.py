from typing import Optional
from sqlmodel import SQLModel, Field


class MachineRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    source: str
    source_url: str

    item_category: Optional[str] = None
    item_name: Optional[str] = None

    organ_name: Optional[str] = None
    municipality: Optional[str] = None

    supplier_name: Optional[str] = None

    contract_type: Optional[str] = None
    process_number: Optional[str] = None
    ata_number: Optional[str] = None

    purchase_year: Optional[int] = None
    amount_brl: Optional[float] = None

    validity_start: Optional[str] = None
    validity_end: Optional[str] = None

    status: Optional[str] = None
    raw_excerpt: Optional[str] = None
