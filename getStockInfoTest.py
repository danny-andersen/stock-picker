from retreiveStockInfo import getStockInfo

keyFile = "alphaAdvantage.apikey"
f = open(keyFile)
apiKey = f.readline().strip('\n');
stock = 'TSCO.L'
info = getStockInfo(apiKey, stock, True)

print (f"Stock: {stock} Income rating: {info['metrics']['incomeScorePerc']:0.1f}% Overall rating: {info['metrics']['scorePerc']:0.1f}%")
