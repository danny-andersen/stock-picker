import sys
import os
if (os.path.exists('processStock.zip')):
    sys.path.insert(0, 'processStock.zip')
else:
    sys.path.insert(0, './src')
from processStock import processStockSpark
from saveRetreiveFiles import mergeAndSaveScores
from checkStockInfo import checkStockSpark
import configparser
import locale
from pyspark import SparkConf, SparkContext

local=False  #False = from HDFS, True = local filesystem
stockFileName = 'stocklist.txt'
iniFileName = 'stockpicker.ini'

if (not os.path.exists(stockFileName) or not os.path.exists(iniFileName)):
    print ("Missing stockfile {stockFileName} or inifile {iniFileName} - aborting")
    exit
config = configparser.ConfigParser()
config.read('stockpicker.ini')
localeStr = config['stats']['locale']
locale.setlocale(locale.LC_ALL, localeStr) 
configStore = config['store']

stocks = []
with open(stockFileName, 'r') as stockFile:
    for stock in stockFile:
        stock = stock.strip(' \n\r')
        if (stock != ''):
            stocks.append(stock)

if (stocks is None or len(stocks) == 0):
    print (f"Failed to read any stocks from file: {stockFileName}")
    exit
    
conf = SparkConf().setAppName("StockPicker")
#         .setMaster("local")
#         .set("spark.executor.memory", "1g")
sc = SparkContext(conf = conf)

broadCastConfig = sc.broadcast(config)

tries = 5
attempts = 1
startStocksNum = len(stocks)
while tries > 0:
    #Parallise the stock list - one spark process per stock
    print(f"Attempt {attempts}: Parallelising stock processing job for {len(stocks)} stocks....standby")
    rdd = sc.parallelize(stocks)
    #This does the actual work of retrieving the stock data and working out the metrics and scores
    #It returns a dict of scores
    mrdd = rdd.map(lambda stock: processStockSpark(broadCastConfig, stock, local))
    #Reduce the scores by combining the returned dicts holding the scores, this triggers the map operation
    scores = mrdd.collect()
    scores = [s for s in scores if s] 
    print (f"Attempt {attempts}: Collected {len(scores)} scores out of {len(stocks)} stocks")
    mergeAndSaveScores(configStore, scores, local)
    if (len(scores) == len(stocks)):
        #Done!
        print (f"Got all the scores after {attempts} attempts")
        break
    #Check that we have all the info 
    print (f"Attempt {attempts}: Checking all info retreived")
    mrdd = rdd.map(lambda stock: checkStockSpark(broadCastConfig, stock, local))
    stocks = mrdd.collect()
    #Remove Nones 
    stocks = [s for s in stocks if s] 
    if (len(stocks) == 0):
        print(f"Attempt {attempts}: All stocks info check out apparently")
        #Done
        break
    tries -= 1
    attempts += 1
print (f"Job complete: Processed {startStocksNum - len(stocks)} out of {startStocksNum}")


