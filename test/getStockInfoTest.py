import sys
sys.path.insert(0, '../src')

from processStock import processStockStats
from scoreStock import calcScore
from saveRetreiveFiles import getStockInfoSaved, getStockPricesSaved, saveStockInfo
import configparser
import locale
from printResults import printResults
from datetime import datetime
import argparse
from checkStockInfo import checkStockInfo
from retreiveStockInfo import getStockInfo

parser = argparse.ArgumentParser(description='Re-calculate and display metrics and scores of given stock symbols')
parser.add_argument('stocks', metavar='sym', type=str, nargs='+',
                   help='space seperated list of stock symbols, e.g. TSCO.L')
args = parser.parse_args()

config = configparser.ConfigParser()
config.read('../stockpicker.ini')
localeStr = config['stats']['locale']
locale.setlocale( locale.LC_ALL, localeStr) 
version = config['stats'].getfloat('version')
maxPriceAgeDays = config['stats'].getint('maxPriceAgeDays')
statsMaxAgeDays = config['stats'].getint('statsMaxAgeDays')
apiKey = config['keys']['alhaAdvantageApiKey']
storeConfig = config['store']
localeStr = config['stats']['locale']
locale.setlocale(locale.LC_ALL, localeStr) 


local = False

for stock in args.stocks:
    #Read metrics from file 
    info = getStockInfoSaved(storeConfig, stock, local)
    if (info):
        infoAge = datetime.now() - info['metadata']['storedDate']
        if (infoAge.days > statsMaxAgeDays or info['metadata']['version'] < version):
            info = None
    if (info):
        #Check info is valid
        if (not checkStockInfo(info)):
            print(f"{stock}: Refreshing info")
            info = None
    if (not info):
        info = getStockInfo(version, stock)
        if (checkStockInfo(info)):
#            saveStockInfo(storeConfig, stock, info, local)
             print
        else:
            print(f"{stock}: Retreived info incomplete")
            info = None
    if (info):
        prices = getStockPricesSaved(storeConfig, stock, local)
        if (prices):
            metrics = processStockStats(info, prices['dailyPrices'])
            #metrics = getStockMetricsSaved(storeConfig, stock, local)
            if (metrics):
                scores = calcScore(stock, metrics)
                printResults(stock, scores, metrics)    
            else:
                print(f"No metrics saved for stock {stock} - please check symbol or re-process stocklist")
        else:
            print(f"No prices saved for stock {stock} - please check symbol or re-process stocklist")
    else:
        print(f"No info saved or retreived for stock {stock} - please check symbol or re-process stocklist")
    
