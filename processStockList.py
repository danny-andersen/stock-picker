from retreiveStockInfo import getStockInfo
from processStock import processStockStats
from scoreStock import calcScore

keyFile = "alphaAdvantage.apikey"
stockFileName = 'stocklist.txt'
apiKey='key'
with open(keyFile, 'r') as kf:
    apiKey = kf.readline().strip('\n');

with open(stockFileName, 'r') as stockFile:
    for stock in stockFile:
        print (f"Processing stock: {stock}")
        #Check to see if stock info needs to be updated
        
        info = getStockInfo(apiKey, stock, True)
        metrics = processStockStats(info)
        scores = calcScore(metrics)
        
    