from retreiveStockInfo import getStockInfo
from processStock import processStockStats
from scoreStock import calcScore
from saveRetreiveFiles import getStockInfoSaved, saveStockInfo, saveStockMetrics, getStockPricesSaved, saveStockPrices
from alphaAdvantage import getLatestDailyPrices, getAllDailyPrices
from datetime import datetime
import configparser
from hdfs import InsecureClient

local=False
stockFileName = 'stocklist.txt'

config = configparser.ConfigParser()
config.read('stockpicker.ini')
version = config['stats'].getfloat('version')
maxPriceAgeDays = config['stats'].getint('maxPriceAgeDays')
apiKey = config['keys']['alhaAdvantageApiKey']
if (not local):
    #Create HDFS client once and add into config
    hdfsUrl = config['store']['hdfsUrl']
    hdfsClient = InsecureClient(hdfsUrl, user='hdfs')
else:
    hdfsClient = None
storeConfig = (config['store'], hdfsClient)

with open(stockFileName, 'r') as stockFile:
    for stock in stockFile:
        stock = stock.strip(' \n\r')
        print (f"Processing stock: {stock}.")
        #Check to see if stock info needs to be updated
        #Read info from file 
        info = getStockInfoSaved(storeConfig, stock, local)
        if (info is None or info['metadata']['version'] < version):
            if (info): print("Refreshing info")
            info = getStockInfo(version, stock)
            saveStockInfo(storeConfig, stock, info, local)

        prices = getStockPricesSaved(storeConfig, stock)
        if (prices):
            latestPriceDate = prices['endDate']
            howOld = datetime.now() - latestPriceDate
            if (howOld.days > maxPriceAgeDays):
                #If more than a week old, refresh
                print ("Refreshing prices")
                prices = getLatestDailyPrices(apiKey, stock, prices['dailyPrices'])
        if (prices is None):
            #Get all daily prices to save
            prices = getAllDailyPrices(apiKey, stock)
        saveStockPrices(storeConfig, stock, prices, local)
        metrics = processStockStats(info, prices['dailyPrices'])
        saveStockMetrics(storeConfig, stock, metrics, local)
        scores = calcScore(metrics)
