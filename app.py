from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from dados import dados_maquinas

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

from fastapi import Query

@app.get("/maquinas")
def maquinas(tipo: str = Query(default=None)):
    if tipo:
        filtrado = [d for d in dados_maquinas if tipo.lower() in d["item"].lower()]
        return filtrado
    return dados_maquinas

@app.get("/", response_class=HTMLResponse)
def home():
    linhas = ""
    for d in dados_maquinas:
        linhas += f"""
        <tr>
            <td>{d['item']}</td>
            <td>{d['municipio']}</td>
            <td>R$ {d['valor']:,}</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Preço de Máquinas Públicas</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f4f6f8;
                margin: 0;
                padding: 24px;
                color: #222;
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
                background: white;
                padding: 24px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            }}
            h1 {{
                margin-top: 0;
                color: #1f2937;
            }}
            p {{
                color: #555;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            th {{
                background: #f1f5f9;
            }}
            tr:nth-child(even) {{
                background: #fafafa;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Preço de Máquinas Públicas</h1>
            <p>Tabela inicial de preços de referência.</p>

            <table>
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Município</th>
                        <th>Valor</th>
                    </tr>
                </thead>
                <tbody>
                    {linhas}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return html
