
import sys
sys.path.insert(0, './src')

from processStock import processStockStats
from scoreStock import calcScore
from saveRetreiveFiles import getStockInfoSaved, getStockPricesSaved, getStockMetricsSaved
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
localeStr = config['stats']['locale']
locale.setlocale( locale.LC_ALL, localeStr) 
storeConfig = config['store']
localeStr = config['stats']['locale']
locale.setlocale(locale.LC_ALL, localeStr) 

local = False
stock = 'TSCO.L'

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
        
    scores = calcScore(stock, metrics)
    print ("-----------------------------------------------------------------------------------------------------")
    print (f"---------------------------------------Metrics for Stock {stock}------------------------------------")
    print (f"This year dividend: {metrics['thisYearDividend']}, Max Dividend: {metrics['maxDividend']:.2f}, Avg Dividend: {metrics['avgDividend']:.2f}")
    print (f"Days since Ex-Dividend = {metrics['daysSinceExDiv']} {metrics['exDivDate'].strftime('%Y-%m-%d')}")
    
    print (f"WACC % = {metrics['wacc']:.2f}")
    print (f"5 year DCF = {metrics['discountedCashFlow']/1000000000:.3f}B (Forecast FCF error: {metrics['dcfError']*100:.1f}%)")
    print (f"Market Cap value = {metrics['marketCap']/1000000000:.3f}B")
    print (f"Intrinsic value (breakup + DCF) = {metrics['intrinsicValue']/1000000000:.3f}B +/- {metrics['intrinsicValueRange']/1000000000:0.2f}B")
    print (f"Net Asset value = {metrics['netAssetValue']/1000000000:.3f}B")
    print (f"Break up value = {metrics['breakUpValue']/1000000000:.3f}B")
    print (f"Enterprise value = {metrics['enterpriseValue']/1000000000:.3f}B")
    
    print (f"Dividend cover = {metrics['diviCover']:.2f}")
    print(f"Current Ratio = {metrics['currentRatio']}")
    print(f"Interest Cover= {metrics['interestCover']:0.2f}")
    if (metrics['fcfForecastSlope']):
        print(f"Cash flow trend: {'Up' if metrics['fcfForecastSlope']> 0 else 'Down'}")
    else:
        print("Dividend forecast not available")
    
    print(f"Gross Profit {metrics['grossProfitPerc']:0.2f}%, Operating Profit {metrics['operatingProfitPerc']:0.2f}%, Overhead {metrics['overheadPerc']:0.2f}%")
    print (f"Current share price: {metrics['currentPrice']:0.2f}")
    print (f"DCF value Share price range: {metrics['lowerSharePriceValue']:0.2f} - {metrics['upperSharePriceValue']:0.2f}")    
    print (f"Fixed asset value Share price: {metrics['assetSharePriceValue']:0.2f}")
    print (f"Break up value Share price: {metrics['breakUpPrice']:0.2f}")
    print (f"Net asset value Share price: {metrics['netAssetValuePrice']:0.2f}")
    print (f"Enterprise value (to buy org) Share price: {metrics['evSharePrice']:0.2f}")
    print (f"Current Year Yield = {metrics['currentYield']:.2f}%")
    print (f"Forward Dividend Yield = {metrics['forwardYield']}%")
    
    print (f"Share income Score: {scores['incomeScorePerc']:0.2f}%")
    print (f"Share overall Score: {scores['scorePerc']:0.2f}%")
    
