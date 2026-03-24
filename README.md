# Preço de Máquinas Públicas

MVP para consulta de preços públicos e atas de máquinas e caminhões.

## Estrutura atual
- `main.py` -> app principal FastAPI
- `database.py` -> conexão SQLite/SQLModel
- `models.py` -> schema `MachineRecord`
- `pncp_adapter.py` -> integração PNCP
- `fetcher.py` -> coletor separado

## Requisitos
- Python 3.11+
- Render ou ambiente compatível

## Rodando localmente
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate    # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

## Start Command no Render
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Endpoints
- `/health` -> status da aplicação
- `/maquinas` -> lista registros do banco
- `/maquinas?tipo=retro` -> filtro simples
- `/tabela` -> interface web básica

## Coleta
O `fetcher.py` deve ser executado separadamente do app.
Primeiro estabilize o site. Depois teste a coleta isolada.
