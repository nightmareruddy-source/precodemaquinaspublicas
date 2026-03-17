from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

app = FastAPI()

# ===== DADOS (VOCÊ VAI EDITAR AQUI DEPOIS) =====
dados_maquinas = [
    {"item": "Caminhão Basculante", "municipio": "Ibiporã", "valor": 480000},
    {"item": "Retroescavadeira", "municipio": "Londrina", "valor": 320000},
    {"item": "Motoniveladora", "municipio": "Cambé", "valor": 910000}
]

# ===== API =====

@app.get("/")
def home():
    return {"ok": True}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/maquinas")
def maquinas(tipo: str = Query(default=None)):
    if tipo:
        filtrado = [
            d for d in dados_maquinas
            if tipo.lower() in d["item"].lower()
        ]
        return filtrado

    return dados_maquinas

# ===== TELA HTML SIMPLES =====
@app.get("/tabela", response_class=HTMLResponse)
def tabela():
    html = """
    <html>
        <head>
            <title>Preço de Máquinas Públicas</title>
            <style>
                body { font-family: Arial; padding: 20px; }
                table { border-collapse: collapse; width: 80%; margin-top: 20px; }
                th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
                th { background-color: #eee; }
                input { padding: 5px; }
                button { padding: 6px 10px; }
            </style>
        </head>
        <body>
            <h2>Preço de Máquinas Públicas</h2>

            <input type="text" id="filtro" placeholder="Ex: retro, caminhão">
            <button onclick="filtrar()">Filtrar</button>

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

            <script>
                async function carregar() {
                    const res = await fetch('/maquinas');
                    const dados = await res.json();
                    render(dados);
                }

                async function filtrar() {
                    const tipo = document.getElementById('filtro').value;
                    const res = await fetch('/maquinas?tipo=' + tipo);
                    const dados = await res.json();
                    render(dados);
                }

                function render(dados) {
                    const tbody = document.querySelector("#tabela tbody");
                    tbody.innerHTML = "";

                    dados.forEach(d => {
                        const linha = `
                            <tr>
                                <td>${d.item}</td>
                                <td>${d.municipio}</td>
                                <td>R$ ${d.valor.toLocaleString()}</td>
                            </tr>
                        `;
                        tbody.innerHTML += linha;
                    });
                }

                carregar();
            </script>
        </body>
    </html>
    """
    return html
