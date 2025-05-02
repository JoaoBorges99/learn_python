from rocketry import Rocketry
from rocketry.conds import cron
from datetime import datetime as dt

import psutil, csv, os, logging

app = Rocketry()

def getComponentsUsage ():
    ramUse = psutil.virtual_memory().percent
    cpuUse = psutil.cpu_percent()
    return {'ram' : ramUse, 'cpu' : cpuUse}


def transformaData (compInfo:dict):
    logging.warning('Transformando os dados de CPU e RAM')
    update_time = dt.now().strftime('%d/%m/%Y %H:%M:%S')
    compInfo['updated_at'] = update_time
    return [compInfo]


def saveData (data:dict):
    file_path = './saved_data/system_monitor.csv'
    file_exists = os.path.exists(file_path)
    with open(file_path, 'a', encoding='UTF-8') as file:
        columns = ['ram', 'cpu', 'updated_at']
        writer = csv.DictWriter(file, fieldnames=columns)
        if not file_exists:
            writer.writeheader()
        writer.writerows(data)

    return True


@app.task(cron('* * * * *'))

def task ():
    data = getComponentsUsage()
    system_usage = transformaData(data)
    saveData(system_usage)

if __name__ == '__main__':
    app.run()