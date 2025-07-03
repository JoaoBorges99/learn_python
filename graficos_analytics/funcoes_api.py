import pandas as pd
import plotly.express as px

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

def validar_tipo_coluna (nome:str):
    chave = nome.lower()
    return chave in ("__no_metrics", "cod", "nome", "__string", "__nochartarea")

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

        texto += f"""
        <li">
            <b>🔹 {formatar_nomeColuna(col.upper())}</a><br>
            <span">Média:</span> <span style="color:#00796b;">{media:.2f}</span>
            <span">Mediana:</span> <span style="color:#00796b;">{mediana:.2f}</span>
            <span">Mínimo:</span> <span style="color:#00796b;">{minimo}</span>,
            <span">Máximo:</span> <span style="color:#00796b;">{maximo}</span>
            <span">Desvio padrão:</span> <span style="color:#00796b;">{desvio:.2f}</span><br>
            Observação: {"alta dispersão dos dados." if desvio > media * 0.5 else "dados relativamente concentrados."}
        </li>
        """
    return texto