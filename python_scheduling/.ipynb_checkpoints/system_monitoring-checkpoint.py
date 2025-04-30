from rocketry import rocketry
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
    return list.append(compInfo)
    