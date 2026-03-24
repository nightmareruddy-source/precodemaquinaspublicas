from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from database import get_conn, create_db

app = FastAPI(title="Preço de Máquinas Públicas", version="1.0.0")

create_db()


@app.get("/")
def home():
    return {"ok": True, "projeto": "Preço de Máquinas Públicas"}


@app.get("/health")
def health():
    return {"status": "ok", "arquivo": "main_sqlite_puro"}


@app.get("/maquinas")
def maquinas(tipo: str = Query(default=None)):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM maquinas ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    termo = (tipo or "").lower().strip()
    resultado = []

    for r in rows:
        item_name = r["item_name"] or ""
        item_category = r["item_category"] or ""
        municipality = r["municipality"] or ""
        organ_name = r["organ_name"] or ""

        if termo:
            texto_busca = " | ".join([
                item_name.lower(),
                item_category.lower(),
                municipality.lower(),
                organ_name.lower(),
            ])
            if termo not in texto_busca:
                continue

        resultado.append({
            "id": r["id"],
            "item": item_name,
            "categoria": item_category,
            "municipio": municipality,
            "orgao": organ_name,
            "valor": r["amount_brl"],
            "ano": r["purchase_year"],
            "status": r["status"],
            "fonte": r["source"],
            "link": r["source_url"],
        })

    return resultado


@app.get("/rodar-fetcher")
def rodar_fetcher():
    try:
        from fetcher import main as run_fetcher
        run_fetcher()
        return {"ok": True, "mensagem": "Fetcher executado"}
    except Exception as e:
        return {"ok": False, "erro": str(e)}


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
                <button onclick="rodarFetcher()">Atualizar base</button>

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

                <p id="status"></p>
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

                async function rodarFetcher() {
                    document.getElementById('status').innerText = 'Rodando coleta...';
                    const res = await fetch('/rodar-fetcher');
                    const dados = await res.json();

                    if (dados.ok) {
                        document.getElementById('status').innerText = 'Coleta executada.';
                        await carregar();
                    } else {
                        document.getElementById('status').innerText = 'Erro: ' + (dados.erro || 'falha');
                    }
                }

                function formatarValor(valor) {
                    if (valor === null || valor === undefined) return '';
                    return 'R$ ' + Number(valor).toLocaleString('pt-BR', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    });
                }

                function render(dados) {
                    const tbody = document.querySelector('#tabela tbody');
                    tbody.innerHTML = '';

                    dados.forEach(function(d) {
                        const linkFonte = d.link
                            ? '<a href="' + d.link + '" target="_blank">Abrir</a>'
                            : '';

                        const linha =
                            '<tr>' +
                                '<td>' + (d.item || '') + '</td>' +
                                '<td>' + (d.categoria || '') + '</td>' +
                                '<td>' + (d.municipio || '') + '</td>' +
                                '<td>' + (d.orgao || '') + '</td>' +
                                '<td>' + formatarValor(d.valor) + '</td>' +
                                '<td>' + (d.ano || '') + '</td>' +
                                '<td>' + (d.status || '') + '</td>' +
                                '<td>' + linkFonte + '</td>' +
                            '</tr>';

                        tbody.innerHTML += linha;
                    });
                }

                carregar();
            </script>
        </body>
    </html>
    """
    return html
