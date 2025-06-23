from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pandas as pd
import plotly.express as px
import uuid
import os

app = FastAPI()

STATIC_DIR = "static"
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/error_page", StaticFiles(directory="error_page"), name="error_page")

def formatar_nomeColuna(text: str):
    text = str(text).upper().replace('__PERC', '_%')
    text = str(text).upper().replace('__INT_STRING', '')
    text = str(text).upper().replace('__STRING', '')
    text = str(text).upper().replace('__DOUBLE', '')
    text = str(text).upper().replace('__INT', '')
    text = str(text).upper().replace('__NO_METRICS', '')
    text = str(text).upper().replace('__NOCHARTAREA', '')
    text = str(text).upper().replace('__INVISIBLE', '')
    text = str(text).upper().replace('__DONTSUM', '')
    text = str(text).upper().replace('__FREEZE', '')
    temp = text.split('__')
    text = temp[0]
    text = str(text).replace('_', ' ')
    return text.strip()

def chamar_htmlErro ():
    filename = "erro.html"
    filepath = os.path.join('error_page', filename)
    with open(filepath, 'r') as arquivo:
        conteudo = arquivo.read()
    return JSONResponse(content={"url": f"/{filepath}"})

@app.get("/")
async def root():
    return {"message": "API de Gráficos Dinâmicos. Envie dados via POST para /graficos."}

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("favicon.ico")

@app.post("/graficos")
async def gerar_grafico(request: Request):
    try:
        data = await request.json()
        df = pd.DataFrame(data)

        numericas = []
        dimensionais = []
        for col in df.columns:
            if '__int' in col.lower():
                for value in df[col]:
                    int(value)
            elif '__double' in col.lower() or '__perc' in col.lower():
                for value in df[col]:
                    float(value)
            else:
                for value in df[col]:
                    str(value)

            if '__no_metrics' in col.lower():
                dimensionais.append(col)
            else:
                numericas.append(col)

        print("Dimensão:", dimensionais)
        print("Métrica:", numericas)

        graficos_html = []
        for dim in dimensionais:
            for met in numericas:
                try:
                    agrupado = df.groupby(dim, as_index=False)[met].sum()
                    fig = px.bar(agrupado, x=dim, y=met,title=f"{formatar_nomeColuna(met)} por {formatar_nomeColuna(dim)}")
                    html = fig.to_html(full_html=True, include_plotlyjs=False)
                    graficos_html.append(html)
                except Exception as e: 
                    print(f"Erro ao gerar gráfico para {dim} x {met}: {e}")

        if not graficos_html:
            # ⚠️ Nenhum gráfico válido gerado: retorne página de erro
            return chamar_htmlErro()
           

        pagina = """<html>
        <head>
          <title>Gráficos Dinâmicos</title>
          <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
          <link rel="icon" type="image/x-icon" href="http://localhost:8000/favicon.ico">
        </head>
        <body>"""

        for graf in graficos_html:
            pagina += graf + "<hr>"

        pagina += "</body></html>"

        filename = f"grafico_{uuid.uuid4().hex}.html"
        filepath = os.path.join(STATIC_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(pagina)

        return JSONResponse(content={"url": f"/static/{filename}"})

    except Exception as e:
        print(f"Erro geral: {e}")
        return chamar_htmlErro()
