from imports_api import*
from autenticacao_hmac import auth_request

app = FastAPI()
cache_request = TTLCache(maxsize=1000, ttl=25)

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
        
def gerar_analise(df: pd.DataFrame, colunas: list):
    texto = ""
    for col in colunas:
        media = df[col].mean()
        mediana = df[col].median()
        desvio = df[col].std()
        maximo = df[col].max()
        minimo = df[col].min()

        texto += f"\n🔹 **{col.upper()}**\n"
        texto += f" - Média: {media:.2f}\n"
        texto += f" - Mediana: {mediana:.2f}\n"
        texto += f" - Mínimo: {minimo}, Máximo: {maximo}\n"
        texto += f" - Desvio padrão: {desvio:.2f}\n"

    if desvio > media * 0.5:
        texto += " - Observação: alta dispersão dos dados.\n"
    else:
        texto += " - Observação: dados relativamente concentrados.\n"

    return texto

# Modelo Pydantic para os dados recebidos
class GraficoData(BaseModel):
    titulo: str = Field(..., max_length=100)
    matricula: str = Field(..., max_length=50)
    dados: str
    agrupamentos: list
    grafico: str

@app.get("/")
async def root():
    return {"message": "API de Gráficos Dinâmicos. Envie dados via POST para /graficos."}

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("favicon.ico")

@app.post("/auth")
async def protection(validacao: bool = Depends(auth_request)):
    return {"success": "Autenticado com sucesso"}  

@app.post("/graficos")
async def gerar_grafico(request: Request, payload: GraficoData, _validacao: bool = Depends(auth_request)):
    agora = pd.Timestamp.now()
    expira = agora + pd.Timedelta(hours=1)

    user = request.client.host if request.client is not None else None

    if user is None:
        return JSONResponse(content={"error": "Não foi possivel validar usuario"}, status_code=401)

    if user in cache_request:
        return JSONResponse(content={"error": "Limite de requisições por minuto alcançado!"}, status_code=429)
    
    cache_request[user] = True

    try:
        print('Carregando graficos...')
        data = dict(payload)

        # Converter os dados recebidos
        data_convertido = []
        try:
            dados_json = json.loads(data['dados'])
        except Exception:
            return JSONResponse(content={"error": "Formato de dados inválido."}, status_code=400)
        for item in dados_json:
            novo_item = {}
            for key, value in item.items():
                novo_item[key] = converter_valor_por_sufixo(key, value)
            data_convertido.append(novo_item)

        titulo = f"Gráficos - {data['titulo']}"
        emitente = data['matricula']
        data_expiracao = expira.strftime("%d/%m/%Y %H:%M:%S")
        data_emissao = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M:%S")
        agrupamentos = data['agrupamentos']
        grafico = getTipoGrafico(data['grafico'])

        print(f"grafico emitido por {emitente} em {data_emissao}, expira em {data_expiracao} do relatório {titulo}")

        # Usar o novo JSON convertido para o DataFrame e gráficos
        df = pd.DataFrame(data_convertido)

        numericas = []
        dimensionais = []
        for agg in agrupamentos:
            if agg['agrupamento'] not in dimensionais:
                dimensionais.append(agg['agrupamento'])
            if agg['metrica'] not in numericas:                
                numericas.append(agg['metrica'])
        
        analise = gerar_analise(df, numericas)

        for col in df.columns:
            if '__no_metrics' in col.lower() or 'cod' in col.lower():
                df[col] = df[col].astype(str)

        graficos_html = []
        for dim in dimensionais:
            for met in numericas:
                try:
                    agrupado = df.groupby(dim, as_index=False)[met].sum()
                    # agrupado = agrupado.sort_values(by=met, ascending=True)
                    fig = grafico(
                        agrupado
                        , x=dim
                        , y=met
                        , color=met
                        , labels={dim: formatar_nomeColuna(dim),  met: formatar_nomeColuna(met)}
                        , title=f"{formatar_nomeColuna(met)} por {formatar_nomeColuna(dim)}"
                        , category_orders={dim: list(agrupado[dim])}
                    )
                    html = fig.to_html(full_html=False, include_plotlyjs=False)
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
        logging.basicConfig(filename='error.log', level=logging.ERROR)
        logging.error(f"Erro geral: {e}")
        return JSONResponse(content={"error": "Erro interno ao processar a requisição."}, status_code=500)
    finally:
        print('Processamento de gráficos concluído.')
        print('-----------------------------------')