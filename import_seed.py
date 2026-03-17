from sqlmodel import Session, select
from database import engine, create_db_and_tables
from models import MachineRecord
from seeds import SEED_RECORDS

create_db_and_tables()
with Session(engine) as session:
    existing = session.exec(select(MachineRecord)).first()
    if not existing:
        session.add_all(SEED_RECORDS)
        session.commit()
        print("Seed importado.")
    else:
        print("Banco já possui dados; seed ignorado.")
