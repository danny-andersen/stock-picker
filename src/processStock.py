from calcStatistics import calculateDCF
from datetime import datetime
import locale
from retreiveStockInfo import getStockInfo
from scoreStock import calcScore
from saveRetreiveFiles import getStockInfoSaved, saveStockInfo, saveStockMetrics, getStockPricesSaved, saveStockPrices
from alphaAdvantage import getLatestDailyPrices, getAllDailyPrices

def processStockSpark(bcConfig, stock, local):
    return processStock(bcConfig.value, stock, local)

def processStock(config, stock, local):
    print (f"Processing stock: {stock}.")
    #Set config
    version = config['stats'].getfloat('version')
    maxPriceAgeDays = config['stats'].getint('maxPriceAgeDays')
    statsMaxAgeDays = config['stats'].getint('statsMaxAgeDays')
    apiKey = config['keys']['alhaAdvantageApiKey']
    storeConfig = config['store']
    localeStr = config['stats']['locale']
    locale.setlocale(locale.LC_ALL, localeStr) 

    #Check to see if stock info needs to be updated
    #Read info from file 
    info = getStockInfoSaved(storeConfig, stock, local)
    if (info):
        infoAge = datetime.now() - info['metadata']['storedDate']
        if (infoAge.days > statsMaxAgeDays or info['metadata']['version'] < version):
            info = None
    if (info is None):
        if (info): print("Refreshing info")
        info = getStockInfo(version, stock)
        saveStockInfo(storeConfig, stock, info, local)
    
    prices = getStockPricesSaved(storeConfig, stock, local)
    if (prices):
        latestPriceDate = prices['endDate']
        howOld = datetime.now() - latestPriceDate
        if (howOld.days > maxPriceAgeDays):
            #If more than a week old, refresh
            print ("Refreshing prices")
            prices = getLatestDailyPrices(apiKey, stock, prices['dailyPrices'])
            saveStockPrices(storeConfig, stock, prices, local)
    if (prices is None):
        #Get all daily prices to save
        print ("Getting stock prices")
        prices = getAllDailyPrices(apiKey, stock)
        saveStockPrices(storeConfig, stock, prices, local)
    metrics = processStockStats(info, prices['dailyPrices'])
    saveStockMetrics(storeConfig, stock, metrics, local)
    scores = calcScore(stock, metrics)
    return scores


def processStockStats(info, dailyPrices):
    now = datetime.now();
    metrics = dict()
    #Determine this years dividend, average and max dividend
    dividends = info['dividends']
    #Calc dividend by year
    years = {}
    for divi in dividends:
    	date = divi['date']
    	dividend = divi['dividend']
    	years[date.year] = dividend + years.get(date.year, 0)
    avgDividend = 0
    maxDividend = 0
    thisYearDividend = 0
    for year in years:
        	dividend = years[year] / 100
        	if year == now.year:
    	   		thisYearDividend = dividend
        	if (maxDividend < dividend):
        		maxDividend = dividend
        	avgDividend += dividend

    if (len(years) != 0):
        avgDividend = avgDividend / len(years)
    else:
        avgDividend = 0
    
    stats = info['stats']
    exDivDate = stats['Ex-Dividend Date']
    if (exDivDate):
        daysSinceExDiv = -(exDivDate - now).days
    else:
        daysSinceExDiv = 0
    fy = stats['Forward Annual Dividend Yield'].split('%')[0]
    if (fy != '-' and fy != 'N/A'):
        forwardYield = locale.atof(fy)
    else:
        forwardYield = 0
    eps = stats['Diluted EPS'] / 100
    if (thisYearDividend != 0):
        diviCover = eps / thisYearDividend
    else:
        diviCover = 0
    currentRatio = stats['Current Ratio']
    
    metrics['thisYearDividend'] = thisYearDividend
    metrics['maxDividend'] = maxDividend
    metrics['avgDividend'] = avgDividend
    metrics['forwardYield'] = forwardYield
    metrics['exDivDate'] = exDivDate
    metrics['daysSinceExDiv'] = daysSinceExDiv
    metrics['eps'] = eps
    metrics['diviCover'] = diviCover
    metrics['currentRatio'] = currentRatio

    marketCap = stats['Market Cap']
    noOfShares = stats['Shares Outstanding']
    metrics['marketCap'] = marketCap
    
    if (len(dailyPrices) > 0):
        priceDatesSorted = sorted(dailyPrices)
        latestPriceDate = priceDatesSorted[len(priceDatesSorted)-1]
        (low, high) = dailyPrices[latestPriceDate]
        #Use the average of the last price range we have
        currentPrice = ((high + low)/2)/100
        if (noOfShares == 0):
            noOfShares = marketCap / currentPrice
            
    else:
        #Couldnt retreive the prices - use market cap
        currentPrice = marketCap / noOfShares

    metrics['currentPrice'] = currentPrice
    metrics['noOfShares'] = noOfShares
    
    balanceSheet = info['balanceSheet']
    totalDebt = balanceSheet['Total non-current liabilities']
    totalEquity = balanceSheet['Stockholder Equity'] ##THIS IS THE WRONG STATISTIC - should be market cap
    totalCapital = totalDebt + totalEquity
    
    cashFlow = info['cashFlow']
    costOfEquity = -cashFlow['Dividends paid']
#    if (cf is None):
#        costOfEquity = 0
#    else:
#        costOfEquity = -locale.atoi(cf) * 1000
    if (totalEquity != 0):
        costOfEquityPerc = 100.0 * costOfEquity / totalEquity #Going to assume 0% dividend growth
    else:
        costOfEquityPerc = 0
    incomeStatement = info['incomeStatement']
    costOfDebt = incomeStatement['Interest expense']
    if (totalDebt != 0):
        costOfDebtPerc = 100.0 * costOfDebt / totalDebt
    else:
        costOfDebtPerc = 0
    if (totalCapital != 0):
        wacc = (costOfEquityPerc * totalEquity / totalCapital) + (costOfDebtPerc * totalDebt / totalCapital)
    else:
        wacc = 0
    metrics['wacc'] = wacc

    operatingProfit = incomeStatement['Operating Profit']
    metrics['operatingProfit'] = operatingProfit
    if (costOfDebt != 0):
        metrics['interestCover'] = operatingProfit / costOfDebt
    else:
        metrics['interestCover'] = 0
    
    #Use to calculate DCF from FCF
    fcf = info['freeCashFlow']
    (dcf, error, fcfForecastSlope) = calculateDCF(fcf, wacc, 5)
    metrics['discountedCashFlow'] = dcf
    metrics['dcfError'] = error
    metrics['fcfForecastSlope'] = fcfForecastSlope
    #Intrinsic value = plant equipment + current assets + 10 year DCF
    currentAssets = balanceSheet['Total Current Assets']
    assetValue = balanceSheet['Total Plant'] + currentAssets #Does not include intangibles + goodwill
    breakUpValue = assetValue - totalDebt - balanceSheet['Total current liabilities']
    metrics['breakUpValue'] = breakUpValue
    intrinsicValue = breakUpValue + dcf
    metrics['intrinsicValue'] = intrinsicValue
    intrinsicValueRange = dcf*error
    metrics['intrinsicValueRange'] = intrinsicValueRange
    lowerSharePriceValue = (intrinsicValue - intrinsicValueRange) / noOfShares
    upperSharePriceValue = (intrinsicValue + intrinsicValueRange)/ noOfShares
    assetSharePriceValue = assetValue / noOfShares
    enterpriseValue = (marketCap + totalDebt - currentAssets) #Price to buy the organisation
    shareholderFunds = balanceSheet['Stockholder Equity']
    metrics['netAssetValue'] = shareholderFunds
    evSharePrice = enterpriseValue / noOfShares
    currentYield = 100*thisYearDividend/currentPrice
    metrics['lowerSharePriceValue'] = lowerSharePriceValue
    metrics['upperSharePriceValue'] = upperSharePriceValue
    metrics['assetSharePriceValue'] = assetSharePriceValue
    metrics['enterpriseValue'] = enterpriseValue
    metrics['breakUpPrice'] = breakUpValue / noOfShares # Tangible assets - total liabilities
    metrics['netAssetValuePrice'] = shareholderFunds / noOfShares #Balance sheet NAV = Total assets - total liabilities (which is shareholder funds)
    metrics['evSharePrice'] = evSharePrice
    metrics['currentYield'] = currentYield
    tr = incomeStatement['Total revenue']
    if (tr != 0):
        metrics['grossProfitPerc'] = 100 * (tr - incomeStatement['Cost of revenue']) / tr
        metrics['operatingProfitPerc'] = 100 * incomeStatement['Operating profit'] / tr
        metrics['overheadPerc'] = 100 * incomeStatement['Central overhead'] / tr
    else:
        metrics['grossProfitPerc'] = 0
        metrics['operatingProfitPerc'] = 0
        metrics['overheadPerc'] = 0

    return metrics
    