
import sys
sys.path.insert(0, './src')

from processStock import processStockStats
from scoreStock import calcScore
from saveRetreiveFiles import getStockInfoSaved, getStockPricesSaved, getStockMetricsSaved
from printResults import printResults
import configparser
import locale

import argparse

parser = argparse.ArgumentParser(description='Re-calculate and display metrics and scores of given stock symbols')
parser.add_argument('stocks', metavar='sym', type=str, nargs='+',
                   help='space seperated list of stock symbols, e.g. TSCO.L')

parser.add_argument('--recalc', '-r', action='store_true',
                   help='recalculate the metrics, the default is to read previously calculated version')
args = parser.parse_args()

config = configparser.ConfigParser()
config.read('./stockpicker.ini')
storeConfig = config['store']
localeStr = config['stats']['locale']
locale.setlocale(locale.LC_ALL, localeStr) 

local = False

if (args.recalc):
    print("Recalculating metrics...")

for stock in args.stocks:
    
    #Read metrics from file 
    if (args.recalc):
        info = getStockInfoSaved(storeConfig, stock, local)
        prices = getStockPricesSaved(storeConfig, stock, local)
        metrics = processStockStats(info, prices['dailyPrices'])
    else:
        metrics = getStockMetricsSaved(storeConfig, stock, local)
    if (metrics):
        scores = calcScore(stock, metrics)
        printResults(stock, scores, metrics)
    else:
        print(f"No results saved for stock {stock} - please check symbol or re-process stocklist")
