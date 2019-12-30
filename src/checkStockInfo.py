import sys
from saveRetreiveFiles import getStockInfoSaved, getStockScores
from datetime import datetime

def countNones(d):
    retVal = False
    if (d):
        zero = 0
        v = 0
        for (key, value) in d.items():
            if (value == None):
                zero += 1
            else:
                v += 1
        retVal = True if zero > v else False
    return (zero, retVal)
    
def checkStockInfo(info):
    if (info):
        missing = 0
        d = info['balanceSheet']
        if (countNones(d)[1]):
            missing += 1
        d = info['incomeStatement']
        if (countNones(d)[1]):
            missing += 1
        d = info['stats']
        if (countNones(d)[1]):
            missing += 1
        if (missing > 2):
            p = False
        else:
            p = True
    else:
        p = False
    return p

def isStockInfoBetter(currentInfo, newInfo):
    cnt = 0
    newCnt = 0
    if (currentInfo):
        d = currentInfo['balanceSheet']
        cnt += countNones(d)[0]
        d = currentInfo['incomeStatement']
        cnt += countNones(d)[0]
        d = currentInfo['stats']
        cnt += countNones(d)[0]
    if (newInfo):
        d = newInfo['balanceSheet']
        newCnt += countNones(d)[0]
        d = newInfo['incomeStatement']
        newCnt += countNones(d)[0]
        d = newInfo['stats']
        newCnt += countNones(d)[0]
    return newCnt > cnt

def checkStockSpark(bconfig, stock, local):
    info = getStockInfoSaved(bconfig.value['store'], stock, local)
    return stock if not checkStockInfo(info) else None
   
if __name__ == "__main__":
    import argparse
    import configparser
    import locale
    parser = argparse.ArgumentParser(description='Check saved stock info of stock in saved scores')
    parser.add_argument('-l', '--local', action='store_const', const=True, default=False,
                       help='Set if using local filesystem rather than HDFS store (False)')
    args = parser.parse_args()
    
    #Read in ini file
    config = configparser.ConfigParser()
    config.read('../stockpicker.ini')
    localeStr = config['stats']['locale']
    locale.setlocale( locale.LC_ALL, localeStr) 
    storeConfig = config['store']
    version = config['stats'].getfloat('version')
    statsMaxAgeDays = config['stats'].getint('statsMaxAgeDays')
   
    #Read score file
    scores = getStockScores(storeConfig, args.local)
    if (not scores):
        print("Failed to retreive saved scores - please check filesystem or re-run scoring")
        sys.exit(1)
    stocksThatFailed = []
    staleStocks = []
    for score in scores:
        stock = score['stock']
        info = getStockInfoSaved(storeConfig, stock, args.local)
        infoAge = datetime.now() - info['metadata']['storedDate']
        if (infoAge.days > statsMaxAgeDays or info['metadata']['version'] < version):
            staleStocks.append(stock)
        else:
            if (not checkStockInfo(info)):
                stocksThatFailed.append(stock)
    print (f"Number of stocks processed: {len(scores)}, number that were stale: {len(staleStocks)}, number that failed check {len(stocksThatFailed)}")
    if (stocksThatFailed):
        with open('stocksToReprocess.txt', 'w+') as f:
            for stock in stocksThatFailed:
                if (stock):
                    f.write(f"{stock}\n")
    