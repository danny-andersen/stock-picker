from datetime import datetime
import json
from os import path
from hdfs import InsecureClient
from dateutil.parser import parse
import re

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
        #print (value)
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
    
def retreiveHdfs(client, fileName):
    jsonContent = None
    if (client.status(fileName, strict=False) != None):
        with client.read(fileName, encoding='utf-8') as reader:
          jsonContent = json.load(reader, object_hook=datetime_parser)
    return jsonContent

def saveHdfs(client, fileName, content):
    if (client.status(fileName, strict=False) != None):
        #File is being replaced - need to delete first
        client.delete(fileName)
    with client.write(fileName, encoding='utf-8') as writer:
      json.dump(content, writer, default=myconverter)

def getStock(storeConfig, stock, name, local):
    content = None
    if (local):
        baseDir = storeConfig['baseDir']
        fileName = baseDir + name + "\\" + stock + '.json'
        content = retreiveLocal(fileName)
    else: #load from HDFS
        hdfsBaseDir = storeConfig['hdfsBaseDir']
        stockFile = hdfsBaseDir + name + '/' + stock + '.json'
        hdfsUrl = storeConfig['hdfsUrl']
        hdfsClient = InsecureClient(hdfsUrl, user='hdfs')
        content = retreiveHdfs(hdfsClient, stockFile)
    return content

def saveStock(storeConfig, stock, name, content, local):
    if (local):
        baseDir = storeConfig['baseDir']
        fileName = baseDir + name + "\\" + stock + '.json' 
        saveLocal(fileName, content)
    else: #load from HDFS
        hdfsBaseDir = storeConfig['hdfsBaseDir']
        fileName = hdfsBaseDir + name + '/' + stock + '.json' 
        hdfsUrl = storeConfig['hdfsUrl']
        hdfsClient = InsecureClient(hdfsUrl, user='hdfs')
        saveHdfs(hdfsClient, fileName, content)
    
def getStockInfoSaved(config, stock, local=True):
    return getStock(config, stock, 'info', local)

def getStockPricesSaved(storeConfig, stock, local):
    stockPrices = getStock(storeConfig, stock, 'prices', local)
    #Convert key from str to int, and value from list to tuple
    if (stockPrices):
        munged = stockPrices['dailyPrices']
        unmunged = dict()
        for k,v in munged.items():
            unmunged[int(k)] = (v[0], v[1])
        stockPrices['dailyPrices'] = unmunged
    return stockPrices

def getStockMetricsSaved(storeConfig, stock, local):
    return getStock(storeConfig, stock, 'metrics', local)

def saveStockInfo(config, stock, info, local):
    saveStock(config, stock, 'info', info, local)

def saveStockMetrics(config, stock, metrics, local):
    saveStock(config, stock, 'metrics', metrics, local)
    
def saveStockPrices(config, stock, stockPrices, local):
    saveStock(config, stock, 'prices', stockPrices, local)

def saveStockScores(config, name, scores, local):
    saveStock(config, name, '', scores, local)