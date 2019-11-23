import sys
sys.path.insert(0, '../src')

from processStock import processStockStats
from scoreStock import calcScore
from saveRetreiveFiles import getStockInfoSaved, getStockPricesSaved, getStockMetricsSaved
import configparser
import locale
from printResults import printResults

import argparse

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
apiKey = config['keys']['alhaAdvantageApiKey']
storeConfig = config['store']
localeStr = config['stats']['locale']
locale.setlocale(locale.LC_ALL, localeStr) 


local = False

for stock in args.stocks:
    #Read metrics from file 
    info = getStockInfoSaved(storeConfig, stock, local)
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
        print(f"No infosaved for stock {stock} - please check symbol or re-process stocklist")
    
