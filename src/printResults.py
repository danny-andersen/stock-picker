
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
#    print(f"Gross Profit {metrics['grossProfitPerc']:0.2f}%, Operating Profit {metrics['preTaxProfitPerc']:0.2f}%, Overhead {metrics['overheadPerc']:0.2f}%")
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
    retStr += str.format(f"Book value = {metrics['bookValue']/1000000000:.3f}B\n")
    retStr += str.format(f"Net Asset value (shareholder funds) = {metrics['netAssetValue']/1000000000:.3f}B\n")
    retStr += str.format(f"Intrinsic value (breakup + DCF) = {metrics['intrinsicValue']/1000000000:.3f}B +/- {metrics['intrinsicValueRange']/1000000000:0.2f}B\n")
    retStr += str.format(f"Intrinsic value inc intangibles = {metrics['intrinsicWithIntangibles']/1000000000:.3f}B +/- {metrics['intrinsicValueRange']/1000000000:0.2f}B\n")
    retStr += str.format(f"Total non-current debt = {metrics['totalDebt']/1000000000:.3f}B\n")
    retStr += str.format(f"Enterprise value = {metrics['enterpriseValue']/1000000000:.3f}B\n")

    retStr += str.format(f"------Share value:------------------\n")
    retStr += str.format(f"Current share price ({metrics['currentPriceDate'].strftime('%Y-%m-%d')}): {metrics['currentPrice']:0.2f}\n")
    retStr += str.format(f"12 month share price: {metrics['minPrice']:0.2f}-{metrics['maxPrice']:0.2f}, avg: {metrics['avgPrice']:0.2f} median: {metrics['medianPrice']:0.2f} std dev: {metrics['stddevPrice']:0.2f} \n")
    
    retStr += str.format(f"DCF value Share price range: {metrics['lowerSharePriceValue']:0.2f} - {metrics['upperSharePriceValue']:0.2f}\n")    
    retStr += str.format(f"Intrinsic value with intangibles price: {metrics['intrinsicWithIntangiblesPrice']:0.2f}\n")    
    retStr += str.format(f"Fixed asset value Share price: {metrics['assetSharePriceValue']:0.2f}\n")
    retStr += str.format(f"Book value Share price: {metrics['bookPrice']:0.2f}\n")
    retStr += str.format(f"Net asset value Share price: {metrics['netAssetValuePrice']:0.2f}\n")
    retStr += str.format(f"Enterprise value (to buy org) Share price: {metrics['evSharePrice']:0.2f}\n")

    retStr += str.format(f"------Dividends:--------------------\n")
    retStr += str.format(f"Dividend: Latest: {metrics['thisYearDividend']:0.2f}p Max: {metrics['maxDividend']:0.2f}p Avg: {metrics['avgDividend']:0.2f}p Median: {metrics['medianDividend']:0.2f}p\n")
    retStr += str.format(f"Yield: Max: {metrics['maxYield']:0.2f}%, Avg: {metrics['avgYield']:0.2f}%\n")
    if (metrics['exDivDate']):
        retStr += str.format(f"Days since Ex-Dividend = {metrics['daysSinceExDiv']} Date: {metrics['exDivDate'].strftime('%Y-%m-%d')}\n")
    retStr += str.format(f"Current Year Yield = {metrics['currentYield']:0.2f}%\n")
    retStr += str.format(f"Forward Dividend Yield = {metrics['forwardYield']:0.2f}%\n")

    retStr += str.format(f"------Profitability:----------------\n")
    retStr += str.format(f"Gross Profit {metrics['grossProfitPerc']:0.2f}%\n")
    retStr += str.format(f"Pre-tax Profit {metrics['preTaxProfitPerc']:0.2f}%\n")
    retStr += str.format(f"Net Profit {metrics['netProfitPerc']:0.2f}%\n")
    retStr += str.format(f"Overhead {metrics['overheadPerc']:0.2f}%\n")
    if (metrics['fcfForecastSlope']):
        retStr += str.format(f"Cash flow trend: {'Up' if metrics['fcfForecastSlope']> 0 else 'Down'}\n")
    else:
        retStr += str.format("Cash flow forecast not available\n")
    
    retStr += str.format(f"------Key Ratios:-------------------\n")
    retStr += str.format(f"Dividend cover = {metrics['diviCover']:0.2f}\n")
    retStr += str.format(f"Current Ratio = {metrics['currentRatio']:0.2f}\n")
    retStr += str.format(f"Interest Cover = {metrics['interestCover']:0.2f}\n")
    retStr += str.format(f"P/E Ratio = {metrics['PEratio']:0.2f}\n")
    retStr += str.format(f"Gearing exc Intangibles (<0.5 good, >1.0 bad) = {metrics['gearing']:0.2f}\n")
    retStr += str.format(f"Price to Book Ratio (<1.0, potential bargain) = {metrics['priceToBook']:0.2f}\n")
    retStr += str.format(f"Price to Book Ratio (exc Intangibles) (<1.0, potential real bargain) = {metrics['priceToBookNoIntangibles']:0.2f}\n")
    retStr += str.format(f"Return on Equity (RoE) = {metrics['returnOnEquity']:0.2f}%\n")
    retStr += str.format(f"Return on Capital Employed (RoCE) = {metrics['returnOnCapitalEmployed']:0.2f}%\n")
    retStr += str.format(f"Percentage of Liabilities are Stockholder funds: {metrics['stockHolderEquityPerc']:0.1f}%\n")

    retStr += str.format(f"------Investment Scores:-------------------\n")
    retStr += str.format(f"AltmannZ score (<1.8 is bad, >3 is good): {metrics['altmannZ']:0.2f}\n")
    retStr += str.format(f"Piotroski F score (<3 is bad, 8 or 9 - get it bought!): {metrics['piotroskiFScore']:0.2f}\n")
    
    retStr += str.format(f"------Summary:----------------------\n")
    retStr += str.format(f"Buy signal weighted slope forecast = {metrics['weightedSlopePerc']:0.0f}%\n")
    retStr += str.format(f"Buy signal forecast period = {scores['buySignalDays']:0.0f} days\n")
    retStr += str.format(f"Buy Signal = {scores['buySignal']}\n")
    retStr += str.format(f"Share income Score: {scores['incomeScore']:0.2f}%\n")
    retStr += str.format(f"Share overall Score: {scores['stockScore']:0.2f}%\n")
    return retStr
