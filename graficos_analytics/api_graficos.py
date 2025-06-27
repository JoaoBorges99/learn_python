from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pandas as pd
import plotly.express as px
import uuid
import os
import json

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

def converter_valor_por_sufixo(key, value):
    if '__int' in key.lower():
        try:
            return int(float(str(value).replace(',', '.')))
        except:
            return 0
    elif '__double' in key.lower() or '__perc' in key.lower():
        try:
            return float(str(value).replace(',', '.'))
        except:
            return 0.0
    elif '__no_metrics' in key.lower() or 'cod' in key.lower():
        return str(value).strip()
    else:
        try:
            return float(str(value).replace(',', '.'))
        except:
            try:
                return int(float(str(value).replace(',', '.')))
            except:
                return str(value).strip()

def getTipoGrafico(tipo:str):
    match tipo.lower():
        case "barra":
            return px.bar
        case "linha":
            return px.line
        case "area":
            return px.area
        case "funil":
            return px.funnel
        case "scatter":
            return px.scatter
        case _:
            return px.bar

@app.get("/")
async def root():
    return {"message": "API de Gráficos Dinâmicos. Envie dados via POST para /graficos."}

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("favicon.ico")

@app.post("/graficos")
async def gerar_grafico(request: Request):
    agora = pd.Timestamp.now()
    expira = agora + pd.Timedelta(hours=1)

    try:
        print('Carregando graficos...')
        data = await request.json()
        
        # Converter os dados recebidos
        data_convertido = []
        for item in json.loads(data['dados']):
            novo_item = {}
            for key, value in item.items():
                novo_item[key] = converter_valor_por_sufixo(key, value)
            data_convertido.append(novo_item)

        titulo = f"Gráficos - {data['titulo']}"
        emitente = data['matricula']
        data_expiracao = expira.strftime("%d/%m/%Y %H:%M:%S")
        data_emissao = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M:%S")
        grafico = getTipoGrafico('scatter')

        print(f"grafico emitido por {emitente} em {data_emissao}, expira em {data_expiracao} do relatório {titulo}")

        # Usar o novo JSON convertido para o DataFrame e gráficos
        df = pd.DataFrame(data_convertido)

        numericas = []
        dimensionais = []
        for col in df.columns:
            if '__no_metrics' in col.lower() or 'cod' in col.lower():
                df[col] = df[col].astype(str)
                dimensionais.append(col)
            else:
                numericas.append(col)  

        graficos_html = []
        for dim in dimensionais:
            for met in numericas:
                try:
                    agrupado = df.groupby(dim, as_index=False)[met].sum()
                    # agrupado = agrupado.sort_values(by=met, ascending=True)
                    fig = px.bar(
                        agrupado
                        , x=dim
                        , y=met
                        , color=met
                        , labels={dim: formatar_nomeColuna(dim),  met: formatar_nomeColuna(met)}
                        , title=f"{formatar_nomeColuna(met)} por {formatar_nomeColuna(dim)}"
                        , category_orders={dim: list(agrupado[dim])}
                    )
                    html = fig.to_html(full_html=False, include_plotlyjs='cdn')
                    graficos_html.append(f'<div class="grafico">{html}</div>')
                except Exception as e:
                    print(f"Erro ao gerar gráfico para {dim} x {met}: {e}")

        if not graficos_html:
            return JSONResponse(content={"error": "Nenhum gráfico válido gerado."}, status_code=400)

        # 4) Verificar e carregar template
        template_path = os.path.join(STATIC_DIR, "pagina_template/template.html")
        if not os.path.exists(template_path):
            return JSONResponse(content={"error": f"Não foi possivel criar a pagina"}, status_code=500)

        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        # Substituir placeholders
        pagina = template.replace("{{titulo}}", str(titulo)) \
                         .replace("{{emitente}}", str(emitente)) \
                         .replace("{{data_emissao}}", str(data_emissao)) \
                         .replace("{{data_expiracao}}", str(data_expiracao)) \
                         .replace("{{graficos}}", "<hr>".join(graficos_html))

        filename = f"grafico_{uuid.uuid4().hex}.html"
        filepath = os.path.join(STATIC_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(pagina)

        return JSONResponse(content={
            "url": f"/static/{filename}"
        })

    except Exception as e:
        print(f"Erro geral: {e}")
        return JSONResponse(content={"url": f"/error_page/erro.html"}, status_code=500)
    finally:
        print('Processamento de gráficos concluído.')
        print('-----------------------------------')