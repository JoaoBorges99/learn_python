from rocketry import Rocketry
from rocketry.conds import cron
import os

app = Rocketry()
caminho_pasta = ['static/', 'temp/']

def limpar_html ():
    print("Iniciando limpeza de arquivos HTML...")
    for caminho in caminho_pasta:
        arquivos = os.listdir(caminho)

        if not arquivos:
            print("Não há arquivos para serem removidos.")
            return
        for arquivo in arquivos:
            caminho_arquivo = os.path.join(caminho, arquivo)
            try:
                if os.path.isfile(caminho_arquivo):
                    os.remove(caminho_arquivo)
                    print(f"Arquivo {caminho_arquivo} removido com sucesso.")
                if os.path.isdir(caminho_arquivo):
                    continue
            except Exception as e:
                print(f"Erro ao remover {caminho_arquivo}: {e}")

@app.task(cron('0 * * * *'))

def task ():
    limpar_html()

if __name__ == '__main__':
    app.run()

