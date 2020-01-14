
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
    retStr = str.format("-----------------------------------------------------------------------------------------------\n")
    retStr += str.format(f"-----------------Metrics for Stock {stock}, based on info dated {metrics['infoDate'].strftime('%Y-%m-%d')}---------------------------\n")

    retStr += str.format(f"--------Valuations:----------------\n")
    retStr += str.format(f"WACC % = {metrics['wacc']:.2f}\n")
    retStr += str.format(f"5 year DCF = {metrics['discountedCashFlow']/1000000000:.3f}B (Forecast FCF error: {metrics['dcfError']*100:.1f}%)\n")
    retStr += str.format(f"Market Cap value = {metrics['marketCap']/1000000000:.3f}B\n")
    retStr += str.format(f"Intrinsic value (breakup + DCF) = {metrics['intrinsicValue']/1000000000:.3f}B +/- {metrics['intrinsicValueRange']/1000000000:0.2f}B\n")
    retStr += str.format(f"Net Asset value = {metrics['netAssetValue']/1000000000:.3f}B\n")
    retStr += str.format(f"Break up value = {metrics['breakUpValue']/1000000000:.3f}B\n")
    retStr += str.format(f"Enterprise value = {metrics['enterpriseValue']/1000000000:.3f}B\n")

    retStr += str.format(f"------Share value:------------------\n")
    retStr += str.format(f"Current share price ({metrics['currentPriceDate'].strftime('%Y-%m-%d')}): {metrics['currentPrice']:0.2f}\n")
    retStr += str.format(f"12 month share price: {metrics['minPrice']:0.2f}-{metrics['maxPrice']:0.2f}, avg: {metrics['avgPrice']:0.2f} median: {metrics['medianPrice']:0.2f} std dev: {metrics['stddevPrice']:0.2f} \n")
    
    retStr += str.format(f"DCF value Share price range: {metrics['lowerSharePriceValue']:0.2f} - {metrics['upperSharePriceValue']:0.2f}\n")    
    retStr += str.format(f"Fixed asset value Share price: {metrics['assetSharePriceValue']:0.2f}\n")
    retStr += str.format(f"Break up value Share price: {metrics['breakUpPrice']:0.2f}\n")
    retStr += str.format(f"Net asset value Share price: {metrics['netAssetValuePrice']:0.2f}\n")
    retStr += str.format(f"Enterprise value (to buy org) Share price: {metrics['evSharePrice']:0.2f}\n")

    retStr += str.format(f"------Dividends:--------------------\n")
    retStr += str.format(f"This year dividend: {metrics['thisYearDividend']:0.2f}p({metrics['currentYield']:0.2f}%), Max Dividend: {metrics['maxDividend']:0.2f}p ({metrics['maxYield']:0.2f}%), Avg Dividend: {metrics['avgDividend']:0.2f} ({metrics['avgYield']:0.2f}%)\n")
    if (metrics['exDivDate']):
        retStr += str.format(f"Days since Ex-Dividend = {metrics['daysSinceExDiv']} Date: {metrics['exDivDate'].strftime('%Y-%m-%d')}\n")
    retStr += str.format(f"Current Year Yield = {metrics['currentYield']:0.2f}%\n")
    retStr += str.format(f"Forward Dividend Yield = {metrics['forwardYield']:0.2f}%\n")

    retStr += str.format(f"------Profitability:----------------\n")
    retStr += str.format(f"Gross Profit {metrics['grossProfitPerc']:0.2f}%, Operating Profit {metrics['operatingProfitPerc']:0.2f}%, Net Profit {metrics['netProfitPerc']:0.2f}%\n")
    retStr += str.format(f"Overhead {metrics['overheadPerc']:0.2f}%\n")
    if (metrics['fcfForecastSlope']):
        retStr += str.format(f"Cash flow trend: {'Up' if metrics['fcfForecastSlope']> 0 else 'Down'}\n")
    else:
        retStr += str.format("Cash flow forecast not available\n")
    
    retStr += str.format(f"------Key Ratios:-------------------\n")
    retStr += str.format(f"Dividend cover = {metrics['diviCover']:0.2f}\n")
    retStr += str.format(f"Current Ratio = {metrics['currentRatio']:0.2f}\n")
    retStr += str.format(f"Interest Cover = {metrics['interestCover']:0.2f}\n")
    retStr += str.format(f"Return on Equity = {metrics['returnOnEquity']:0.2f}%\n")
    retStr += str.format(f"Return on Assets = {metrics['returnOnAssets']:0.2f}%\n")
    retStr += str.format(f"Percentage of Liabilities are Stockholder funds {metrics['stockHolderEquityPerc']:0.2f}%\n")

    retStr += str.format(f"------Summary:----------------------\n")
    retStr += str.format(f"Buy signal weighted slope forecast = {metrics['weightedSlopePerc']:0.0f}%\n")
    retStr += str.format(f"Buy signal forecast period = {scores['buySignalDays']:0.0f} days\n")
    retStr += str.format(f"Buy Signal = {scores['buySignal']}\n")
    retStr += str.format(f"Share income Score: {scores['incomeScore']:0.2f}%\n")
    retStr += str.format(f"Share overall Score: {scores['stockScore']:0.2f}%\n")
    return retStr
