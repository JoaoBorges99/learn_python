import os
import pandas as pd

def get_file_dataframe (caminho_arquivo:str):
    try:
        if not os.path.isfile(caminho_arquivo):
            raise FileNotFoundError("Não foi possivel ler o arquivo")
        
        _, extensao = os.path.splitext(caminho_arquivo)

        if extensao == '.csv':
            try:
                return pd.read_csv(caminho_arquivo, sep=';', encoding='utf-8')
            except UnicodeDecodeError:
                return pd.read_csv(caminho_arquivo, sep=';', encoding='latin1')
        elif extensao in ['.xls', '.xlsx']:
            return pd.read_excel(caminho_arquivo)
        else:
            raise Exception(f'A Extensão {extensao} não é valida!')

    except Exception as e:
        print(e)
        return None