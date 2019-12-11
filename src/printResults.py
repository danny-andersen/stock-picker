
def printResults(stock, scores, metrics):
    print (getResultsStr(stock, scores, metrics))
#    print ("-----------------------------------------------------------------------------------------------------")
#    print (f"---------------------------------------Metrics for Stock {stock}------------------------------------")
#    print (f"This year dividend: {metrics['thisYearDividend']}, Max Dividend: {metrics['maxDividend']:.2f}, Avg Dividend: {metrics['avgDividend']:.2f}")
#    if (metrics['exDivDate']):
#        print (f"Days since Ex-Dividend = {metrics['daysSinceExDiv']} {metrics['exDivDate'].strftime('%Y-%m-%d')}")
#    
#    print (f"WACC % = {metrics['wacc']:.2f}")
#    print (f"5 year DCF = {metrics['discountedCashFlow']/1000000000:.3f}B (Forecast FCF error: {metrics['dcfError']*100:.1f}%)")
#    print (f"Market Cap value = {metrics['marketCap']/1000000000:.3f}B")
#    print (f"Intrinsic value (breakup + DCF) = {metrics['intrinsicValue']/1000000000:.3f}B +/- {metrics['intrinsicValueRange']/1000000000:0.2f}B")
#    print (f"Net Asset value = {metrics['netAssetValue']/1000000000:.3f}B")
#    print (f"Break up value = {metrics['breakUpValue']/1000000000:.3f}B")
#    print (f"Enterprise value = {metrics['enterpriseValue']/1000000000:.3f}B")
#    
#    print (f"Dividend cover = {metrics['diviCover']:.2f}")
#    print(f"Current Ratio = {metrics['currentRatio']}")
#    print(f"Interest Cover= {metrics['interestCover']:0.2f}")
#    if (metrics['fcfForecastSlope']):
#        print(f"Cash flow trend: {'Up' if metrics['fcfForecastSlope']> 0 else 'Down'}")
#    else:
#        print("Dividend forecast not available")
#    
#    print(f"Gross Profit {metrics['grossProfitPerc']:0.2f}%, Operating Profit {metrics['operatingProfitPerc']:0.2f}%, Overhead {metrics['overheadPerc']:0.2f}%")
#    print (f"Current share price: {metrics['currentPrice']:0.2f}")
#    print (f"DCF value Share price range: {metrics['lowerSharePriceValue']:0.2f} - {metrics['upperSharePriceValue']:0.2f}")    
#    print (f"Fixed asset value Share price: {metrics['assetSharePriceValue']:0.2f}")
#    print (f"Break up value Share price: {metrics['breakUpPrice']:0.2f}")
#    print (f"Net asset value Share price: {metrics['netAssetValuePrice']:0.2f}")
#    print (f"Enterprise value (to buy org) Share price: {metrics['evSharePrice']:0.2f}")
#    print (f"Current Year Yield = {metrics['currentYield']:.2f}%")
#    print (f"Forward Dividend Yield = {metrics['forwardYield']}%")
#    
#    print (f"Share income Score: {scores['incomeScorePerc']:0.2f}%")
#    print (f"Share overall Score: {scores['scorePerc']:0.2f}%")

def getResultsStr(stock, scores, metrics):
    retStr = str.format("-----------------------------------------------------------------------------------------------------\n")
    retStr += str.format(f"---------------------------------------Metrics for Stock {stock}------------------------------------\n")
    retStr += str.format(f"This year dividend: {metrics['thisYearDividend']}, Max Dividend: {metrics['maxDividend']:.2f}, Avg Dividend: {metrics['avgDividend']:.2f}\n")
    if (metrics['exDivDate']):
        retStr += str.format(f"Days since Ex-Dividend = {metrics['daysSinceExDiv']} {metrics['exDivDate'].strftime('%Y-%m-%d')}\n")
    
    retStr += str.format(f"WACC % = {metrics['wacc']:.2f}\n")
    retStr += str.format(f"5 year DCF = {metrics['discountedCashFlow']/1000000000:.3f}B (Forecast FCF error: {metrics['dcfError']*100:.1f}%)\n")
    retStr += str.format(f"Market Cap value = {metrics['marketCap']/1000000000:.3f}B\n")
    retStr += str.format(f"Intrinsic value (breakup + DCF) = {metrics['intrinsicValue']/1000000000:.3f}B +/- {metrics['intrinsicValueRange']/1000000000:0.2f}B\n")
    retStr += str.format(f"Net Asset value = {metrics['netAssetValue']/1000000000:.3f}B\n")
    retStr += str.format(f"Break up value = {metrics['breakUpValue']/1000000000:.3f}B\n")
    retStr += str.format(f"Enterprise value = {metrics['enterpriseValue']/1000000000:.3f}B\n")
    
    retStr += str.format(f"Dividend cover = {metrics['diviCover']:.2f}\n")
    retStr += str.format(f"Current Ratio = {metrics['currentRatio']}\n")
    retStr += str.format(f"Interest Cover= {metrics['interestCover']:0.2f}\n")
    if (metrics['fcfForecastSlope']):
        retStr += str.format(f"Cash flow trend: {'Up' if metrics['fcfForecastSlope']> 0 else 'Down'}\n")
    else:
        retStr += str.format("Dividend forecast not available")
    
    retStr += str.format(f"Gross Profit {metrics['grossProfitPerc']:0.2f}%, Operating Profit {metrics['operatingProfitPerc']:0.2f}%, Overhead {metrics['overheadPerc']:0.2f}%\n")
    retStr += str.format(f"Current share price: {metrics['currentPrice']:0.2f}\n")
    retStr += str.format(f"DCF value Share price range: {metrics['lowerSharePriceValue']:0.2f} - {metrics['upperSharePriceValue']:0.2f}\n")    
    retStr += str.format(f"Fixed asset value Share price: {metrics['assetSharePriceValue']:0.2f}\n")
    retStr += str.format(f"Break up value Share price: {metrics['breakUpPrice']:0.2f}\n")
    retStr += str.format(f"Net asset value Share price: {metrics['netAssetValuePrice']:0.2f}\n")
    retStr += str.format(f"Enterprise value (to buy org) Share price: {metrics['evSharePrice']:0.2f}\n")
    retStr += str.format(f"Current Year Yield = {metrics['currentYield']:.2f}%\n")
    retStr += str.format(f"Forward Dividend Yield = {metrics['forwardYield']}%\n")
    
    retStr += str.format(f"Share income Score: {scores['incomeScorePerc']:0.2f}%\n")
    retStr += str.format(f"Share overall Score: {scores['scorePerc']:0.2f}%\n")
    return retStr
