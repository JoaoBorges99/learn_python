import os
import pandas as pd

def get_excel (caminho_arquivo:str):
    try:
        if os.path.isfile:
            raise FileNotFoundError("Não foi possivel ler o arquivo")
        
        _, extensao = os.path.splitext(caminho_arquivo)

        if extensao == 'csv':
            return pd.read_csv(caminho_arquivo)
        elif extensao in ['.xls', 'xlsx']:
            return pd.read_excel(caminho_arquivo)
        else:
            raise Exception('Extensão do arquivo não é valida!')

    except Exception as e:
        print(e)
        return None