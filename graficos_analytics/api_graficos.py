from imports_api import*
from autenticacao_hmac import auth_request
from funcoes_api import*
from excel_graficos import*
import csv

app = FastAPI(
    title="API Graphic Generator",
    description="Gere graficos e analise através de JSON.",
    version="1.0.0"
)

cache_request = TTLCache(maxsize=1000, ttl=10)

STATIC_DIR = "static"
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/error_page", StaticFiles(directory="error_page"), name="error_page")

def chamar_htmlErro ():
    filename = "erro.html"
    filepath = os.path.join('error_page', filename)
    with open(filepath, 'r') as arquivo:
        conteudo = arquivo.read()
    return JSONResponse(content={"url": f"/{filepath}"})

# Modelo Pydantic para os dados recebidos
class GraficoData(BaseModel):
    titulo: str = Field(..., max_length=100)
    matricula: str = Field(..., max_length=50)
    dados: str
    agrupamentos: list
    grafico: str

@app.get("/", include_in_schema=False)
async def index():
    template_path = os.path.join(STATIC_DIR, "pagina_template/index.html")
    return FileResponse(template_path, media_type="text/html")

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/pagina_template/favicon.ico")

@app.get("/upload_excel", include_in_schema=False)
async def upload_excel_page():
    template_path = os.path.join(STATIC_DIR, "pagina_template/upload_excel.html")
    return FileResponse(template_path, media_type="text/html")

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

        for col in df.columns:
            if validar_tipo_coluna(col):
                df[col] = df[col].astype(str)

        graficos_html = []
        for dim in dimensionais:
            for met in numericas:
                try:
                    agrupado = df.groupby(dim, as_index=False)[met].sum()
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
                    analise_grafico = gerar_analise(agrupado, [met])
                    graficos_html.append(
                        f'''
                        <div class="grafico">
                            {html}
                            <div class="analise-grafico">{analise_grafico}</div>
                        </div>
                        '''
                    )
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

@app.post("/graficos_excel")
async def gerar_grafico_com_excel(file: UploadFile = File()):
    try:
        os.makedirs("temp", exist_ok=True)
        file_location = f"temp/{file.filename}"

        with open(file_location, "wb") as f:
            content = await file.read()
            f.write(content)

        df = get_file_dataframe(file_location)

        dimecional = []
        numerica = []
        graficos = []

        if df is None:
            return JSONResponse(content={"error": "Falha ao carregar arquivo, valide as extenções."}, status_code=409)
        else:
            for col in df.columns:
                if validar_tipo_coluna(col):
                    dimecional.append(col)
                    df[col] = df[col].astype(str)
                else:
                    numerica.append(col)
            
            for dim in dimecional:
                for num in numerica:
                    fig = px.bar(df, x=dim, y=num, title=f'{num} por {dim}')
                    html = fig.to_html(full_html=False, include_plotlyjs=False)
                    graficos.append(f'<div class="grafico">{html}</div>')

            if graficos:
                template_path = os.path.join(STATIC_DIR, "pagina_template/template_excel.html")

                with open(template_path, "r", encoding="utf-8") as f:
                    template = f.read()

                pagina = template.replace("{{graficos}}", "\n".join(graficos))
                pagina_html_nome = f"grafico_excel_{uuid.uuid4().hex}.html"
                caminho_html = os.path.join(STATIC_DIR, pagina_html_nome)

                with open(caminho_html, "w", encoding="utf-8") as f:
                    f.write(pagina)
                return JSONResponse(content={"url": f"/static/{pagina_html_nome}"})         
            else:
                return JSONResponse(content={"erro" : "Nenhum grafico foi gerado apartir desse excel"}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"error": f"Falha ao gerar graficos.\n {e}"}, status_code=409)
 