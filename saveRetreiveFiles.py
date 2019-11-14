from datetime import datetime
import json
from os import path
from hdfs import InsecureClient
from dateutil.parser import parse
import re

baseDir = 'C:\\Data\\stockdata\\'
hdfsInfoBaseDir = '/data/stockdata/'
hdfsUrl = 'hdfs://host:port'

def myconverter(o):
    if isinstance(o, datetime):
        return o.__str__()

def datetime_parser(value):
    datePattern = re.compile(".*date.*", re.IGNORECASE)
    if isinstance(value, dict):
        for (k, v) in value.items():
            if (type(v) is str and datePattern.search(k)):
                value[k] = parse(v)
            else:
                value[k] = datetime_parser(v)
    elif isinstance(value, list):
        for index, row in enumerate(value):
            value[index] = datetime_parser(row)
    elif isinstance(value, str) and value:
        print (value)
        if re.match('^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', value):
            try:
                value = parse(value)
            except (ValueError, AttributeError):
                pass
    return value

def retreiveLocal(fileName):
    jsonContent = None
    if (path.exists(fileName)):
        fp = open(fileName, 'r')
        jsonContent = json.load(fp, object_hook=datetime_parser)
        fp.close()
    return jsonContent

def saveLocal(fileName, content):
    fp = open(fileName, 'w+')
    infoJson = json.dumps(content, default = myconverter)
    fp.write(infoJson)
    fp.close()
    
def retreiveHdfs(fileName):
    jsonContent = None
    client = InsecureClient(hdfsUrl, user='hdfs')
    if client.status(fileName != None):
        with client.read(fileName, encoding='utf-8') as reader:
          jsonContent = json.load(reader, object_hook=datetime_parser)
    return jsonContent

def saveHdfs(fileName, content):
    client = InsecureClient(hdfsUrl, user='hdfs')
    with client.write(fileName, encoding='utf-8') as writer:
      json.dump(content, writer)

def getStockInfoSaved(stock, local=True):
    #Load from HFDS file
    info = None
    if (local):
        fileName = baseDir + "info\\" + stock + '.json'
        info = retreiveLocal(fileName)
    else: #load from HDFS
        stockFile = hdfsInfoBaseDir + 'info/' + stock + '.json'
        info = retreiveHdfs(stockFile)
    return info
    
def saveStockInfo(stock, info, local=True):
    if (local):
        fileName = baseDir + "info\\" + stock + '.json' 
        saveLocal(fileName, info)
    else: #load from HDFS
         fileName = hdfsInfoBaseDir + 'info/' + stock
         saveHdfs(fileName, info)

def saveStockMetrics(stock, metrics, local=True):
    if (local):
        fileName = baseDir + "metrics\\" + stock + '.json' 
        saveLocal(fileName, metrics)
    else: #load from HDFS
         fileName = hdfsInfoBaseDir + 'metric/' + stock
         saveHdfs(fileName, metrics)
    