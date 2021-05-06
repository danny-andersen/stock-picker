import sys
import os
if (os.path.exists('processStock.zip')):
    sys.path.insert(0, 'processStock.zip')
else:
    sys.path.insert(0, './src')
import configparser
import locale

from pyspark import SparkConf, SparkContext

from getLatestPrices import getLatestPrices, getAndSaveStockPricesSpark

def updateStockPrices(stockFile, iniFile):
    config = configparser.ConfigParser()
    config.read(iniFile)
    localeStr = config['stats']['locale']
    locale.setlocale(locale.LC_ALL, localeStr) 
    configStore = config['store']
    numJobs = config['spark']['numJobs']
    priceRateLimit = config['stats'].getint('priceRateLimit')

    stocks = []
    with open(stockFile, 'r') as stockFile:
        for stock in stockFile:
            stock = stock.strip(' \n\r')
            if (stock != ''):
                stocks.append(stock)

    if (stocks is None or len(stocks) == 0):
        print (f"Failed to read any stocks from file: {stockFile}")
        exit

    if (priceRateLimit):
        #Rate limit (sigh) so need to do single threaded
        print(f"Getting latest prices with a rate limit of {priceRateLimit} per min, please wait")
        getLatestPrices(config, priceRateLimit, stocks)
    else:
        #Submit spark job to parallelise update
        conf = SparkConf().setAppName("StockPriceUpdate")
        #         .setMaster("local")
        #         .set("spark.executor.memory", "1g")
        sc = SparkContext(conf = conf)

        broadCastConfig = sc.broadcast(config)

        #Parallise the stock list - one spark process per stock
        print(f"****************Attempt {attempts}: Parallelising stock price job for {len(stocks)} stocks....standby")
        rdd = sc.parallelize(stocks, numSlices=numJobs)
        #This does the actual work of retrieving the stock data and working out the metrics and scores
        #It returns a dict of scores
        mrdd = rdd.map(lambda stock: getAndSaveStockPricesSpark(broadCastConfig, stock))
        #Reduce the scores by combining the returned dicts holding the scores, this triggers the map operation
        results = mrdd.collect()
        results = [s for s in results if s] 
        print (f"************* Collected {len(results)} scores out of {len(stocks)}")
    print (f"***************Job complete")


if __name__ == "__main__":
    stockFileName = 'stocklist.txt'
    iniFileName = 'stockpicker.ini'

    if (not os.path.exists(stockFileName) or not os.path.exists(iniFileName)):
        print ("Missing stockfile {stockFileName} or inifile {iniFileName} - aborting")
        exit
    updateStockPrices(stockFileName, iniFileName)