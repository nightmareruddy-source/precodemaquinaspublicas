# Preço de Máquinas Públicas — MVP inicial

MVP inicial do projeto `precodemaquinaspublicas.com.br`.

## Objetivo
Consultar **atas de registro de preços** e **preços históricos de compras públicas** para:
- escavadeira hidráulica
- pá carregadeira
- motoniveladora
- retroescavadeira
- rolo compactador
- caminhões (caçamba, pipa, coletor, chassi, carroceria, toco)

## Stack
- FastAPI
- SQLModel + SQLite
- Python requests
- HTML simples para o frontend

## Rodando localmente
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
python import_seed.py
uvicorn main:app --reload
```
Depois abra `http://localhost:8000`.

## Usando Docker
```bash
docker compose up
```

## Importando dados reais do PNCP
1. Copie `.env.example` para `.env`.
2. Ajuste `PNCP_SEARCH_ENDPOINT` conforme o endpoint escolhido no Swagger do PNCP.
3. Rode:
```bash
cd backend
python fetcher.py
```

## Observação importante
Este pacote **não está implantado em produção**. Ele é um MVP local para você ou um técnico publicar em hospedagem.
