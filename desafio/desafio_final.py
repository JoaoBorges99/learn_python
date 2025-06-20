import pandas as pd
import time
import requests

url_api = 'https://servicodados.ibge.gov.br/api/'


# Função para obter os dados de uma API
def getData (versao:str, caminho:str) :
    url = url_api + versao + '/' + caminho
    response = requests.get(url)
    if response.status_code == 200:
        print(f"Requisição bem-sucedida: {response.status_code}")
        return response.json()
    else:
        print(f"Erro ao acessar a API: {response.status_code}")
        return None

# Função para retornar dados de Area de UFs especificas pré carregadas em uma lista
def getAreaUf (listaUf:list):
    ufArea = {}
    for uf in listaUf:
        dados = getData('v3', f'malhas/estados/{uf}/metadados')
        dados_area = dados[0]['area']['dimensao']
        ufArea[uf] = dados_area

    return ufArea

if __name__ == '__main__':
    list_estados = [uf['sigla'] for uf in getData('v1', 'localidades/estados')]

    getAreaUf(list_estados)
