from retreiveStockInfo import getStockInfo

keyFile = "alphaAdvantage.apikey"
f = open(keyFile)
apiKey = f.readline().strip('\n');

info = getStockInfo('TSCO.L')
