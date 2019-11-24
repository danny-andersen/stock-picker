import sys
import os
if (os.path.exists('processStock.zip')):
    sys.path.insert(0, 'processStock.zip')
else:
    sys.path.insert(0, './src')
from processStock import processStockSpark
from saveRetreiveFiles import mergeAndSaveScores, deleteStockScores
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

#Parallise the stock list - one spark process per stock
rdd = sc.parallelize(stocks)
#This does the actual work of retrieving the stock data and working out the metrics and scores
#It returns a dict of scores
mrdd = rdd.map(lambda stock: processStockSpark(broadCastConfig, stock, local))
#Reduce the scores by combining the returned dicts holding the scores, this triggers the map operation
scores = mrdd.collect()
mergeAndSaveScores(configStore, scores, local)

print (scores)


