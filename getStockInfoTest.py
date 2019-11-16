from retreiveStockInfo import getStockInfo
from processStock import processStockStats
from scoreStock import calcScore
from saveRetreiveFiles import getStockInfoSaved, saveStockInfo, saveStockMetrics

keyFile = "alphaAdvantage.apikey"
f = open(keyFile)
apiKey = f.readline().strip('\n');
stock = 'TSCO.L'

#Read info from file 
info = getStockInfoSaved(stock, True)
version = 1.0
if (info is None or info['metadata']['version'] < version):
    info = getStockInfo(apiKey, version, stock, True)
    saveStockInfo(stock, info, True)
metrics = processStockStats(info)
saveStockMetrics(stock, metrics)
scores = calcScore(metrics)

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
print(f"Cash flow trend: {'Up' if metrics['fcfForecastSlope']> 0 else 'Down'}")

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

#TODO Save Metrics
