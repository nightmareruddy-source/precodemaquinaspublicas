from fetcher import main as rodar_fetcher
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

from database import engine, create_db_and_tables
from models import MachineRecord

app = FastAPI(title="Preço de Máquinas Públicas", version="1.0.0")

create_db_and_tables()


@app.get("/")
def home():
    return {"ok": True, "projeto": "Preço de Máquinas Públicas"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/maquinas")
def maquinas(tipo: str = Query(default=None)):
    with Session(engine) as session:
        stmt = select(MachineRecord)

        if tipo:
            termo = tipo.lower()
            registros = session.exec(stmt).all()

            filtrados = []
            for r in registros:
                item_name = (r.item_name or "").lower()
                item_category = (r.item_category or "").lower()
                municipality = (r.municipality or "").lower()
                organ_name = (r.organ_name or "").lower()

                if (
                    termo in item_name
                    or termo in item_category
                    or termo in municipality
                    or termo in organ_name
                ):
                    filtrados.append({
                        "id": r.id,
                        "item": r.item_name,
                        "categoria": r.item_category,
                        "municipio": r.municipality,
                        "orgao": r.organ_name,
                        "valor": r.amount_brl,
                        "ano": r.purchase_year,
                        "status": r.status,
                        "fonte": r.source,
                        "link": r.source_url,
                    })

            return filtrados

        registros = session.exec(stmt).all()

        return [
            {
                "id": r.id,
                "item": r.item_name,
                "categoria": r.item_category,
                "municipio": r.municipality,
                "orgao": r.organ_name,
                "valor": r.amount_brl,
                "ano": r.purchase_year,
                "status": r.status,
                "fonte": r.source,
                "link": r.source_url,
            }
            for r in registros
        ]


@app.get("/rodar-fetcher")
def rodar_fetcher_manual():
    rodar_fetcher()
    return {"ok": True, "mensagem": "Fetcher executado"}


@app.get("/tabela", response_class=HTMLResponse)
def tabela():
    html = """
    <html>
        <head>
            <title>Preço de Máquinas Públicas</title>
            <meta charset="utf-8">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    padding: 20px;
                    background: #f4f4f4;
                }
                .box {
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    max-width: 1100px;
                    margin: auto;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                }
                h2 {
                    margin-top: 0;
                }
                table {
                    border-collapse: collapse;
                    width: 100%;
                    margin-top: 20px;
                }
                th, td {
                    border: 1px solid #ccc;
                    padding: 8px;
                    text-align: left;
                    font-size: 14px;
                }
                th {
                    background-color: #eee;
                }
                input, button {
                    padding: 8px;
                    margin-right: 6px;
                    margin-bottom: 8px;
                }
                #status {
                    margin-top: 10px;
                    font-weight: bold;
                }
                a {
                    color: #0b57d0;
                    text-decoration: none;
                }
            </style>
        </head>
        <body>
            <div class="box">
                <h2>Preço de Máquinas Públicas</h2>

                <input type="text" id="filtro" placeholder="Ex: retro, caminhão, motoniveladora">
                <button onclick="filtrar()">Filtrar</button>
                <button onclick="atualizarBase()">Atualizar base</button>

                <p id="status"></p>

                <table id="tabela">
                    <thead>
                        <tr>
                            <th>Item</th>
                            <th>Categoria</th>
                            <th>Município</th>
                            <th>Órgão</th>
                            <th>Valor</th>
                            <th>Ano</th>
                            <th>Status</th>
                            <th>Fonte</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>

            <script>
                async function carregar() {
                    const res = await fetch('/maquinas');
                    const dados = await res.json();
                    render(dados);
                }

                async function filtrar() {
                    const tipo = document.getElementById('filtro').value.trim();
                    const url = tipo ? '/maquinas?tipo=' + encodeURIComponent(tipo) : '/maquinas';
                    const res = await fetch(url);
                    const dados = await res.json();
                    render(dados);
                }

                async function atualizarBase() {
                    document.getElementById('status').innerText = 'Atualizando base... aguarde.';
                    const res = await fetch('/rodar-fetcher');
                    const dados = await res.json();

                    if (dados.ok) {
                        document.getElementById('status').innerText = 'Base atualizada com sucesso.';
                    } else {
                        document.getElementById('status').innerText = 'Erro ao atualizar a base.';
                    }

                    await carregar();
                }

                function formatarValor(valor) {
                    if (valor === null || valor === undefined) return '';
                    return 'R$ ' + Number(valor).toLocaleString('pt-BR', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    });
                }

                function render(dados) {
                    const tbody = document.querySelector("#tabela tbody");
                    tbody.innerHTML = "";

                    dados.forEach(d => {
                        const linkFonte = d.link
                            ? `<a href="${d.link}" target="_blank">Abrir</a>`
                            : '';

                        tbody.innerHTML += `
                            <tr>
                                <td>${d.item || ''}</td>
                                <td>${d.categoria || ''}</td>
                                <td>${d.municipio || ''}</td>
                                <td>${d.orgao || ''}</td>
                                <td>${formatarValor(d.valor)}</td>
                                <td>${d.ano || ''}</td>
                                <td>${d.status || ''}</td>
                                <td>${linkFonte}</td>
                            </tr>
                        `;
                    });
                }

                carregar();
            </script>
        </body>
    </html>
    """
    return html
