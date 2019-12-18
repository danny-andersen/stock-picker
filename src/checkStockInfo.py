import sys
from saveRetreiveFiles import getStockInfoSaved, getStockScores

def countZeros(d):
    retVal = False
    if (d):
        zero = 0
        v = 0
        for (key, value) in d.items():
            if (value == 0):
                zero += 1
            else:
                v += 1
        retVal = True if zero > v else False
    return retVal
    
def checkStockInfo(info):
    if (info):
        missing = 0
        if (len(info['dividends']) == 0):
            missing +=1
        d = info['balanceSheet']
        if (countZeros(d)):
            missing += 1
        d = info['incomeStatement']
        if (countZeros(d)):
            missing += 1
        fcf = info['freeCashFlow']
        if (len(fcf) == 0):
            missing += 1
        if (missing > 2):
            p = False
        else:
            p = True
    else:
        p = False
    return p

def checkStockSpark(bconfig, stock, local):
    info = getStockInfoSaved(bconfig.value['store'], stock, local)
    return stock if not checkStockInfo(info) else None
   
if __name__ == "__main__":
    import argparse
    import configparser
    import locale
    parser = argparse.ArgumentParser(description='Re-calculate and display metrics and scores of given stock symbols')
    parser.add_argument('-n', '--num', type=int, default=10,
                       help='top number of stock scores to show, defaults to 10')
    parser.add_argument('-l', '--local', action='store_const', const=True, default=False,
                       help='Set if using local filesystem rather than HDFS store (False)')
    args = parser.parse_args()
    
    #Read in ini file
    config = configparser.ConfigParser()
    config.read('../stockpicker.ini')
    localeStr = config['stats']['locale']
    locale.setlocale( locale.LC_ALL, localeStr) 
    storeConfig = config['store']
    
    #Read score file
    scores = getStockScores(storeConfig, args.local)
    if (not scores):
        print("Failed to retreive saved scores - please check filesystem or re-run scoring")
        sys.exit(1)
    stocksThatFailed = []
    for score in scores:
        stock = score['stock']
        info = getStockInfoSaved(storeConfig, stock, args.local)
        if (not checkStockInfo(info)):
            stocksThatFailed.append(stock)
    if (stocksThatFailed):
        with open('stocksToReprocess.txt', 'w+') as f:
            for stock in stocksThatFailed:
                if (stock):
                    f.write(f"{stock}\n")
    