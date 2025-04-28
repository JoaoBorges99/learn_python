import pandas as pd
import requests, logging
from datetime import datetime as dt

def getProduct (product:str):
    url = "https://world.openfoodfacts.net/api/v2/product/"
    api_get = requests.get(f'{url}{product}')
    try:
        if api_get.status_code == 200:
            return api_get.json()
        else:
            raise Exception('Erro ao buscar produto')
    except Exception as erro:
        logging.warning(erro)
        return {}

def formatDateTime (df:pd.DataFrame):
    new_df = df.rename(columns = {'last_modified_t' : 'last_modified', 'product_name': 'product'})
    new_df['process_date'] = dt.now().strftime('%d/%m/%Y - %H:%M:%S')
    new_df['process_by'] = 'elf_process'
    new_df['last_modified'] = pd.to_datetime(new_df['last_modified'], unit='s')
    
    return new_df

def transformData (data:dict):
    info = data.get('product',None)
    df = pd.json_normalize(info)
    select_columns = df[['code', 'product_name', 'image_front_url', 'last_modified_t']].copy()
    select_columns = formatDateTime(select_columns)
    return select_columns

def saveFile (file:dict):
    file.to_csv('./data/raw/csv/novo_prod.csv', index=False)


if __name__ == '__main__':
    product = '7891000369371'
    api_get = getProduct(product)
    validate = api_get is None
    
    if validate:
        logging.warning(f'Erro ao receber dados!')
    else:
        df = transformData(api_get)
        try:
            saveFile(df)
            logging.warning('Arquivo CSV salvo com sucesso!')
        except Exception as erro:
            logging.warning("Erro ao slavar arquivo!\n\n")
            logging.warning(f"Erro: {erro}")
            
        