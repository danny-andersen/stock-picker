
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

plusStars = "+++"
negStars = "---"
def getScoreStr(scores, stat):
    # Return one * per 0.2
    retStr = ""
    numStars = round(scores.get(stat,1000)/0.2)
    if (numStars < 1000) :
        if numStars < 0: numStars = 0
        if (numStars < 3):
            numStars = 3 - numStars
            retStr = negStars[0:numStars] + " "
        else:
            retStr = plusStars[0:(numStars - 2)] + " "
    return retStr

def getResultsStr(stock, scoreStats, metrics):
    scores = metrics['scores']
    retStr = str.format("-----------------------------------------------------------------------------------------------\n")
    retStr += str.format(f"-----------------Metrics for Stock {stock}, based on info dated {metrics['infoDate'].strftime('%Y-%m-%d')}---------------------------\n")

    retStr += str.format(f"--------Valuations:----------------\n")
    retStr += str.format(f"WACC % = {metrics['wacc']:.2f}\n")
    retStr += str.format(f"5 year DCF = {metrics['discountedCashFlow']/1000000000:.3f}B (Forecast FCF error: {metrics['dcfError']*100:.1f}%)\n")
    retStr += str.format(f"Market Cap value = {metrics['marketCap']/1000000000:.3f}B\n")
    retStr += str.format(f"Book value = {metrics['bookValue']/1000000000:.3f}B {getScoreStr(scores,'bookPrice')}\n")
    retStr += str.format(f"Net Asset value (shareholder funds) = {metrics['netAssetValue']/1000000000:.3f}B {getScoreStr(scores,'netAssetValuePrice')}\n")
    retStr += str.format(f"Intrinsic value (breakup + DCF) = {metrics['intrinsicValue']/1000000000:.3f}B +/- {metrics['intrinsicValueRange']/1000000000:0.2f}B {getScoreStr(scores,'intrinsicValuePrice')}\n")
    retStr += str.format(f"Intrinsic value inc intangibles = {metrics['intrinsicWithIntangibles']/1000000000:.3f}B +/- {metrics['intrinsicValueRange']/1000000000:0.2f}B {getScoreStr(scores,'intrinsicWithIntangiblesPrice')}\n")
    retStr += str.format(f"Total non-current debt = {metrics['totalDebt']/1000000000:.3f}B\n")
    retStr += str.format(f"Enterprise value = {metrics['enterpriseValue']/1000000000:.3f}B {getScoreStr(scores,'evSharePrice')}\n")

    retStr += str.format(f"------Share value:------------------\n")
    retStr += str.format(f"Current share price ({metrics['currentPriceDate'].strftime('%Y-%m-%d')}): {metrics['currentPrice']:0.2f}\n")
    retStr += str.format(f"12 month share price: {metrics['minPrice']:0.2f}-{metrics['maxPrice']:0.2f}, avg: {metrics['avgPrice']:0.2f} median: {metrics['medianPrice']:0.2f} std dev: {metrics['stddevPrice']:0.2f} \n")
    
    retStr += str.format(f"DCF value Share price range: {metrics['lowerSharePriceValue']:0.2f} - {metrics['upperSharePriceValue']:0.2f}\n")    
    retStr += str.format(f"Intrinsic value price: {metrics['intrinsicValuePrice']:0.2f} {getScoreStr(scores,'intrinsicValuePrice')}\n")    
    retStr += str.format(f"Intrinsic value with intangibles price: {metrics['intrinsicWithIntangiblesPrice']:0.2f} {getScoreStr(scores,'intrinsicWithIntangiblesPrice')}\n")    
    retStr += str.format(f"Fixed asset value Share price: {metrics['assetSharePriceValue']:0.2f} {getScoreStr(scores,'assetSharePriceValue')}\n")
    retStr += str.format(f"Book value Share price: {metrics['bookPrice']:0.2f} {getScoreStr(scores,'bookPrice')}\n")
    retStr += str.format(f"Net asset value Share price: {metrics['netAssetValuePrice']:0.2f} {getScoreStr(scores,'netAssetValuePrice')}\n")
    retStr += str.format(f"Enterprise value (to buy org) Share price: {metrics['evSharePrice']:0.2f} {getScoreStr(scores,'evSharePrice')}\n")

    retStr += str.format(f"------Price Movement:--------------------\n")
    (priceDeltaPerc, maxPrice, minPrice, medianPrice, stdPrice) = metrics['priceChangeLastWeek'] 
    retStr += str.format(f"Past Week: %change: {priceDeltaPerc:0.2f} Max: {maxPrice:0.2f} Min: {minPrice:0.2f} Median: {medianPrice:0.2f} Std Dev: {stdPrice:0.2f}\n")
    (priceDeltaPerc, maxPrice, minPrice, medianPrice, stdPrice) = metrics['priceChangeLastMonth'] 
    retStr += str.format(f"Past Month: %change: {priceDeltaPerc:0.2f} Max: {maxPrice:0.2f} Min: {minPrice:0.2f} Median: {medianPrice:0.2f} Std Dev: {stdPrice:0.2f}\n")
    (priceDeltaPerc, maxPrice, minPrice, medianPrice, stdPrice) = metrics['priceChangeLast3Month'] 
    retStr += str.format(f"Past 3 Months: %change: {priceDeltaPerc:0.2f} Max: {maxPrice:0.2f} Min: {minPrice:0.2f} Median: {medianPrice:0.2f} Std Dev: {stdPrice:0.2f}\n")
    (priceDeltaPerc, maxPrice, minPrice, medianPrice, stdPrice) = metrics['priceChangeLast6Month'] 
    retStr += str.format(f"Past 6 Months: %change: {priceDeltaPerc:0.2f} Max: {maxPrice:0.2f} Min: {minPrice:0.2f} Median: {medianPrice:0.2f} Std Dev: {stdPrice:0.2f}\n")
    (priceDeltaPerc, maxPrice, minPrice, medianPrice, stdPrice) = metrics['priceChangeLastYear'] 
    retStr += str.format(f"Past Year: %change: {priceDeltaPerc:0.2f} Max: {maxPrice:0.2f} Min: {minPrice:0.2f} Median: {medianPrice:0.2f} Std Dev: {stdPrice:0.2f}\n")
    (priceDeltaPerc, maxPrice, minPrice, medianPrice, stdPrice) = metrics['priceChangeLast2Year'] 
    retStr += str.format(f"Past 2 Years: %change: {priceDeltaPerc:0.2f} Max: {maxPrice:0.2f} Min: {minPrice:0.2f} Median: {medianPrice:0.2f} Std Dev: {stdPrice:0.2f}\n")

    retStr += str.format(f"------Dividends:--------------------\n")
    retStr += str.format(f"Dividend: Last Year: {metrics['thisYearDividend']:0.2f}p Max: {metrics['maxDividend']:0.2f}p Avg: {metrics['avgDividend']:0.2f}p Median: {metrics['medianDividend']:0.2f}p\n")
    retStr += str.format(f"Yield: Last Year: {metrics['currentYield']:0.2f}% {getScoreStr(scores,'currentYield')}Max: {metrics['maxYield']:0.2f}% {getScoreStr(scores,'maxYield')}Avg: {metrics['avgYield']:0.2f}% {getScoreStr(scores,'avgYield')}Median: {metrics['medianYield']:0.2f}% {getScoreStr(scores,'medianYield')}\n")
    retStr += str.format(f"Forward Dividend Yield = {metrics['forwardYield']:0.2f}% {getScoreStr(scores,'currentYield')}\n")
    if (metrics['exDivDate']):
        retStr += str.format(f"Days since Ex-Dividend = {metrics['daysSinceExDiv']} Date: {metrics['exDivDate'].strftime('%Y-%m-%d')}\n")

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
    retStr += str.format(f"Dividend cover = {metrics['diviCover']:0.2f} {getScoreStr(scores,'diviCover')}\n")
    retStr += str.format(f"Current Ratio = {metrics['currentRatio']:0.2f} {getScoreStr(scores,'currentRatio')}\n")
    retStr += str.format(f"Interest Cover = {metrics['interestCover']:0.2f} {getScoreStr(scores,'interestCover')}\n")
    retStr += str.format(f"P/E Ratio = {metrics['PEratio']:0.2f} {getScoreStr(scores,'PEratio')}\n")
    retStr += str.format(f"Gearing exc Intangibles (<0.5 good, >1.0 bad) = {metrics['gearing']:0.2f} {getScoreStr(scores,'gearing')}\n")
    retStr += str.format(f"Price to Book Ratio (<1.0, potential bargain) = {metrics['priceToBook']:0.2f} {getScoreStr(scores,'priceToBook')}\n")
    retStr += str.format(f"Price to Book Ratio (exc Intangibles) (<1.0, potential real bargain) = {metrics['priceToBookNoIntangibles']:0.2f} {getScoreStr(scores,'priceToBookNoIntangibles')}\n")
    retStr += str.format(f"Return on Equity (RoE) = {metrics['returnOnEquity']:0.2f}% {getScoreStr(scores,'returnOnEquity')}\n")
    retStr += str.format(f"Return on Capital Employed (RoCE) = {metrics['returnOnCapitalEmployed']:0.2f}% {getScoreStr(scores,'returnOnCapitalEmployed')}\n")
    retStr += str.format(f"Percentage of Liabilities are Stockholder funds: {metrics['stockHolderEquityPerc']:0.1f}% {getScoreStr(scores,'stockHolderEquityPerc')}\n")

    retStr += str.format(f"------Investment Scores:-------------------\n")
    retStr += str.format(f"AltmannZ score (<1.8 is bad, >3 is good): {metrics['altmannZ']:0.2f} {getScoreStr(scores,'altmannZ')}\n")
    retStr += str.format(f"Piotroski F score (<3 is bad, 8 or 9 - get it bought!): {metrics['piotroskiFScore']:0.2f} {getScoreStr(scores,'piotroskiFScore')}\n")
    
    retStr += str.format(f"------Summary:----------------------\n")
    retStr += str.format(f"Buy signal weighted slope forecast = {metrics['weightedSlopePerc']:0.0f}%\n")
    retStr += str.format(f"Buy signal forecast period = {scoreStats['buySignalDays']:0.0f} days\n")
    retStr += str.format(f"Buy Signal = {scoreStats['buySignal']}\n")
    # retStr += str.format(f"Share income Score: {scoreStats['incomeScore']:0.2f}%\n")
    retStr += str.format(f"Share overall Score: {scoreStats['stockScore']:0.2f}%\n")
    return retStr
