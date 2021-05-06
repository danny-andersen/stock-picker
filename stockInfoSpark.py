import sys
import os
if (os.path.exists('processStock.zip')):
    sys.path.insert(0, 'processStock.zip')
else:
    sys.path.insert(0, './src')
import configparser
import locale

from pyspark import SparkConf, SparkContext

from retrieveStockInfo import retrieveStockInfoSpark
from checkStockInfo import checkStockSpark
from getLatestPrices import getLatestPrices

def updateStockInfo(stockFile, iniFile):
    config = configparser.ConfigParser()
    config.read(iniFile)
    localeStr = config['stats']['locale']
    locale.setlocale(locale.LC_ALL, localeStr) 
    configStore = config['store']
    numJobs = config['spark']['numJobs']

    stocks = []
    with open(stockFile, 'r') as stockFile:
        for stock in stockFile:
            stock = stock.strip(' \n\r')
            if (stock != ''):
                stocks.append(stock)

    if (stocks is None or len(stocks) == 0):
        print (f"Failed to read any stocks from file: {stockFile}")
        exit

    conf = SparkConf().setAppName("LatestStockInfo")
    sc = SparkContext(conf = conf)

    broadCastConfig = sc.broadcast(config)

    tries = 5
    attempts = 1
    startStocksNum = len(stocks)
    lastCount = startStocksNum
    # processedCount = 0
    while tries > 0:
        #Parallise the stock list - one spark process per stock
        print(f"****************Attempt {attempts}: Parallelising stock processing job for {len(stocks)} stocks....standby")
        rdd = sc.parallelize(stocks, numSlices=numJobs)
        #This does the actual work of retrieving the stock data and working out the metrics and scores
        #It returns a dict of scores
        mrdd = rdd.map(lambda stock: retrieveStockInfoSpark(broadCastConfig, stock))
        #Collect the info by combining the returned dicts holding the info, this triggers the map operation
        infos = mrdd.collect()
        infos = [s for s in infos if s] 
        print (f"*************Attempt {attempts}: Collected {len(infos)} stocks out of {len(stocks)}")
        #Check that we have all the info 
        print (f"***************Attempt {attempts}: Checking all info retreived")
        mrdd = rdd.map(lambda stock: checkStockSpark(broadCastConfig, stock))
        stocks = mrdd.collect()
        #Remove Nones 
        stocks = [s for s in stocks if s] 
        if (len(stocks) == 0):
            print(f"***************Attempt {attempts}: All stocks info check out apparently")
            #Done
            break
        if (len(stocks) == lastCount):
            print(f"***************Attempt {attempts}: Number of stocks left {len(stocks)} is the same as last attempt - aborting")
            if (len(stocks) < 20):
                print(f"***************Failed stocks: {stocks}")
            #Done
            break
        tries -= 1
        attempts += 1
        print (f"***************Attempt {attempts}: Retrying for stocks: {stocks}")
    print (f"***************Job complete: Processed {startStocksNum - len(stocks)} out of {startStocksNum} stocks")


if __name__ == "__main__":
    stockFileName = 'stocklist.txt'
    iniFileName = 'stockpicker.ini'

    if (not os.path.exists(stockFileName) or not os.path.exists(iniFileName)):
        print ("Missing stockfile {stockFileName} or inifile {iniFileName} - aborting")
        exit
    updateStockInfo(stockFileName, iniFileName)