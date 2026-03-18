from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import sqlite3
import requests
import threading
import time
app = FastAPI()

# ===== BANCO =====
conn = sqlite3.connect("dados.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS maquinas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item TEXT,
    municipio TEXT,
    valor REAL
)
""")
conn.commit()

# dados iniciais mínimos
cursor.execute("SELECT COUNT(*) FROM maquinas")
total = cursor.fetchone()[0]
if total == 0:
    cursor.executemany(
        "INSERT INTO maquinas (item, municipio, valor) VALUES (?, ?, ?)",
        [
            ("Caminhão Basculante", "Ibiporã", 480000),
            ("Retroescavadeira", "Londrina", 320000),
            ("Motoniveladora", "Cambé", 910000),
        ],
    )
    conn.commit()

# ===== FUNÇÕES =====
def listar_maquinas(tipo=None):
    if tipo:
        cursor.execute(
            "SELECT item, municipio, valor FROM maquinas WHERE LOWER(item) LIKE ? ORDER BY id DESC",
            ('%' + tipo.lower() + '%',)
        )
    else:
        cursor.execute(
            "SELECT item, municipio, valor FROM maquinas ORDER BY id DESC"
        )
    rows = cursor.fetchall()
    return [{"item": r[0], "municipio": r[1], "valor": r[2]} for r in rows]

def importar_pncp(termo="caminhao"):
    url = "https://pncp.gov.br/api/consulta/v1/contratos"
    params = {
        "pagina": 1,
        "tamanhoPagina": 20,
        "termo": termo
    }

    adicionados = 0

    try:
        response = requests.get(url, params=params, timeout=20)
        data = response.json()

        for item in data.get("data", []):
            descricao = item.get("objetoCompra", "")
            valor = item.get("valorTotal", 0)
            orgao = item.get("orgaoEntidade", {}).get("razaoSocial", "")

            if descricao and valor:
                cursor.execute(
                    "INSERT INTO maquinas (item, municipio, valor) VALUES (?, ?, ?)",
                    (descricao[:150], orgao[:120], float(valor))
                )
                adicionados += 1

        conn.commit()
    except Exception as e:
        return {"ok": False, "erro": str(e)}

    return {"ok": True, "adicionados": adicionados, "termo": termo}

# ===== ROTAS =====
@app.get("/")
def home():
    return {"ok": True}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/maquinas")
def maquinas(tipo: str = Query(default=None)):
    return listar_maquinas(tipo)

@app.get("/importar")
def importar(termo: str = Query(default="caminhao")):
    return importar_pncp(termo)

@app.get("/tabela", response_class=HTMLResponse)
def tabela():
    html = """
    <html>
        <head>
            <title>Preço de Máquinas Públicas</title>
            <style>
                body { font-family: Arial; padding: 20px; background: #f5f5f5; }
                .box { background: white; padding: 20px; border-radius: 8px; max-width: 1000px; margin: auto; }
                table { border-collapse: collapse; width: 100%; margin-top: 20px; }
                th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
                th { background-color: #eee; }
                input, button { padding: 8px; margin-right: 6px; }
                h2 { margin-top: 0; }
            </style>
        </head>
        <body>
            <div class="box">
                <h2>Preço de Máquinas Públicas</h2>

                <div>
                    <input type="text" id="filtro" placeholder="Ex: retro, caminhão">
                    <button onclick="filtrar()">Filtrar</button>
                    <button onclick="importar('caminhao')">Importar caminhão</button>
                    <button onclick="importar('retroescavadeira')">Importar retro</button>
                    <button onclick="importar('motoniveladora')">Importar moto</button>
                </div>

                <p id="status"></p>

                <table id="tabela">
                    <thead>
                        <tr>
                            <th>Item</th>
                            <th>Município</th>
                            <th>Valor</th>
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
                    const tipo = document.getElementById('filtro').value;
                    const res = await fetch('/maquinas?tipo=' + encodeURIComponent(tipo));
                    const dados = await res.json();
                    render(dados);
                }

                async function importar(termo) {
                    document.getElementById('status').innerText = 'Importando...';
                    const res = await fetch('/importar?termo=' + encodeURIComponent(termo));
                    const dados = await res.json();
                    document.getElementById('status').innerText =
                        dados.ok ? 'Importação concluída: ' + dados.adicionados + ' registros.' : 'Erro: ' + dados.erro;
                    carregar();
                }

                function render(dados) {
                    const tbody = document.querySelector("#tabela tbody");
                    tbody.innerHTML = "";
                    dados.forEach(d => {
                        tbody.innerHTML += `
                            <tr>
                                <td>${d.item}</td>
                                <td>${d.municipio}</td>
                                <td>R$ ${Number(d.valor).toLocaleString('pt-BR')}</td>
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
import threading
import time

def job_automatico():
    while True:
        print("Rodando importação automática...")
        importar_pncp("caminhao")
        importar_pncp("retroescavadeira")
        importar_pncp("motoniveladora")
        time.sleep(3600)  # roda a cada 1 hora

threading.Thread(target=job_automatico, daemon=True).start()
