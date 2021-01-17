from datetime import datetime
import json
import os
from hdfs import InsecureClient
from dateutil.parser import parse
import re
from tabulate import tabulate
import dropbox


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
        # print (value)
        if re.match('^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', value):
            try:
                value = parse(value)
            except (ValueError, AttributeError):
                pass
    return value


def retreiveLocal(fileName):
    jsonContent = None
    if (os.path.exists(fileName)):
        fp = open(fileName, 'r')
        try:
            jsonContent = json.load(fp, object_hook=datetime_parser)
        except json.JSONDecodeError:
            print (f"!!!!!!!!!!!! Failed to parse json in file {fileName} - ignoring file !!!!!!!")
        fp.close()
    return jsonContent


def saveLocal(fileName, content):
    fp = open(fileName, 'w+')
    infoJson = json.dumps(content, default=myconverter)
    fp.write(infoJson)
    fp.close()


def deleteLocal(fileName):
    ret = True
    if (os.path.exists(fileName)):
        ret = os.remove(fileName)
    return ret


def retreiveHdfs(client, fileName):
    jsonContent = None
    if (client.status(fileName, strict=False) != None):
        with client.read(fileName, encoding='utf-8') as reader:
            try:
                jsonContent = json.load(reader, object_hook=datetime_parser)
            except json.JSONDecodeError:
                print (f"!!!!!!!!!!!! Failed to parse json in file {fileName} - ignoring file !!!!!!!")
    return jsonContent

def saveHdfs(client, fileName, content):
    if (client.status(fileName, strict=False) != None):
        # File is being replaced - need to delete first
        deleteHdfsFile(client,fileName)
    with client.write(fileName, encoding='utf-8') as writer:
      json.dump(content, writer, default=myconverter)

def deleteHdfsFile(client, fileName):
    if (client.status(fileName, strict=False) != None):
        # File is being replaced - need to delete first
        if (not client.delete(fileName)):
            print (f"Failed to delete file {fileName}")
    
def getStock(storeConfig, stock, name, local):
    content = None
    if (local):
        baseDir = storeConfig['baseDir']
        fileName = baseDir + name + "/" + stock + '.json'
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
        fileName = baseDir + name + "/" + stock + '.json' 
        saveLocal(fileName, content)
    else: #load from HDFS
        hdfsBaseDir = storeConfig['hdfsBaseDir']
        fileName = hdfsBaseDir + name + '/' + stock + '.json' 
        hdfsUrl = storeConfig['hdfsUrl']
        hdfsClient = InsecureClient(hdfsUrl, user='hdfs')
        saveHdfs(hdfsClient, fileName, content)

def deleteStockFile(storeConfig, stock, name, local):
    if (local):
        baseDir = storeConfig['baseDir']
        fileName = baseDir + name + "\\" + stock + '.json' 
        deleteLocal(fileName)
    else: #delete from HDFS
        hdfsBaseDir = storeConfig['hdfsBaseDir']
        fileName = hdfsBaseDir + name + '/' + stock + '.json' 
        hdfsUrl = storeConfig['hdfsUrl']
        hdfsClient = InsecureClient(hdfsUrl, user='hdfs')
        deleteHdfsFile(hdfsClient, fileName)
    
def getStockInfoSaved(config, stock, local=True):
    return getStock(config, stock, 'info', local)

def getStockPricesSaved(storeConfig, stock, local):
    stockPrices = getStock(storeConfig, stock, 'prices', local)
    # Convert key from str to int, and value from list to tuple
    if (stockPrices and stockPrices['dailyPrices'] != None):
        munged = stockPrices['dailyPrices'] 
        unmunged = dict()
        for k,v in munged.items():
            unmunged[int(k)] = (v[0], v[1]) #timestamp = (min, max)
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

def saveStockScores(config, scores, type, local):
    saveStock(config, f'scores-by-{type}', '', scores, local)

def deleteStockScores(config, local):
    deleteStockFile(config, 'scores', '', local)
    
def getStockScores(config, local):
    return getStock(config, "scores", '', local)

def addRelativePostionByStock(stocks, scores, heading):
    positionByStock = dict()
    i = 0
    for s in scores:
        positionByStock[s['stock']] = i
        i += 1
    for s in stocks:
        stockName = s['stock']
        # Find the position for the stock
        pos = positionByStock[stockName]
        # Save the position against the heading
        s[heading] = pos
    
def mergeAndSaveScores(storeConfig, scores, heldStocks, local):
    if (scores):
        # Remove any nulls
        scores = [s for s in scores if s]
        # Get list of stocks
        scoreStocks = [s['stock'] for s in scores]
        # Create list of held stock dicts
        heldDict = []
        for hs in heldStocks:
            for s in scores:
                if (hs == s['stock']):
                    heldDict.append(s)
        # Add in ones that we already have that are missing (if any)
        currentScores = getStockScores(storeConfig, local)
        if (currentScores):
            for cs in currentScores:
                if (cs['stock'] not in scoreStocks):
                    scores.append(cs)
        # Sort scores in reverse order so get highest scoring first
        scores.sort(key=lambda score:score['stockScore'], reverse=True)
        addRelativePostionByStock(heldDict, scores, 'stockPosition')
        saveStockScores(storeConfig, scores, 'stock', local)
        summary = tabulate(scores, headers='keys', showindex="always")
        path="/summary-by-stockScore.txt"
        saveStringToDropbox(storeConfig, path, summary)
        scores.sort(key=lambda score:score['currentYield'], reverse=True)
        addRelativePostionByStock(heldDict, scores, 'yieldPosition')
        saveStockScores(storeConfig, scores, 'yield', local)
        summary = tabulate(scores, headers='keys', showindex="always")
        path="/summary-by-currentYield.txt"
        saveStringToDropbox(storeConfig, path, summary)
        scores.sort(key=lambda score:score['avgYield'], reverse=True)
        addRelativePostionByStock(heldDict, scores, 'yieldPosition')
        saveStockScores(storeConfig, scores, 'avgYield', local)
        summary = tabulate(scores, headers='keys', showindex="always")
        path="/summary-by-avgYield.txt"
        saveStringToDropbox(storeConfig, path, summary)
        scores.sort(key=lambda score:score['incomeScore'], reverse=True)
        addRelativePostionByStock(heldDict, scores, 'incomePosition')
        saveStockScores(storeConfig, scores, 'income', local)
        summary = tabulate(scores, headers='keys', showindex="always")
        path="/summary-by-incomeScore.txt"
        saveStringToDropbox(storeConfig, path, summary)

        heldDict.sort(key=lambda h:h['stockPosition'], reverse=False)
        saveStockScores(storeConfig, heldDict, 'held', local)
        summary = tabulate(heldDict, headers='keys', showindex="always")
        path="/held-scores-summary.txt"
        saveStringToDropbox(storeConfig, path, summary)

def saveStringToDropbox(config, path, dataStr):
    dropboxAccessToken = config['dropboxAccessToken']
    dbx = dropbox.Dropbox(dropboxAccessToken)
    dbx.files_upload(dataStr.encode("utf-8"), path, mode=dropbox.files.WriteMode.overwrite, mute=True)
