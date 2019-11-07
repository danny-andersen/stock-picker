from calcStatistics import calculateDCF
from datetime import datetime
import locale

locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' ) 

def convertToValue(valStr):
    multiplier = 1
    if ('M' in valStr):
        multiplier = 1000000
        valStr = valStr.strip('M')
    if ('B' in valStr):
        multiplier = 1000000000
        valStr = valStr.strip('B')
    if (valStr == 'N/A' or valStr == '-'):
        value = 0
    else:
        value = locale.atof(valStr)
    return value * multiplier

def processStockStats(info):
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
    avgDividend = avgDividend / len(years)
    
    stats = info['stats']
    exDivDate = datetime.strptime(stats['Ex-Dividend Date4'], "%b %d, %Y")
    daysSinceExDiv = -(exDivDate - now).days
    forwardYield = convertToValue(stats['Forward Annual Dividend Yield4'].split('%')[0])
    eps = convertToValue(stats['Diluted EPS']) / 100
    if (thisYearDividend != 0):
        diviCover = eps / thisYearDividend
    else:
        diviCover = 0
    currentRatio = convertToValue(stats['Current Ratio'])
    
    metrics['forwardYield'] = forwardYield
    metrics['avgDividend'] = avgDividend
    metrics['exDivDate'] = exDivDate
    metrics['daysSinceExDiv'] = daysSinceExDiv
    metrics['eps'] = eps
    metrics['diviCover'] = diviCover
    metrics['currentRatio'] = currentRatio

    dailyPrices = info['dailyPrices']
    currentPrice = ((dailyPrices[0]['high'] + dailyPrices[0]['low'])/2)/100
    metrics['currentPrice'] = currentPrice
    
    balanceSheet = info['balanceSheet']
    totalDebt = locale.atoi(balanceSheet['Total non-current liabilities']) * 1000
    shareholderFunds = locale.atoi(balanceSheet['Stockholder Equity']) * 1000 ##THIS IS THE WRONG STATISTIC - should be market cap
    totalEquity = locale.atoi(balanceSheet['Stockholder Equity']) * 1000 ##THIS IS THE WRONG STATISTIC - should be market cap
    totalCapital = totalDebt + totalEquity
    
    cashFlow = info['cashFlow']
    cf = cashFlow['Dividends paid']
    if (cf is None):
        costOfEquity = 0
    else:
        costOfEquity = -locale.atoi(cf) * 1000
    costOfEquityPerc = 100.0 * costOfEquity / totalEquity #Going to assume 0% dividend growth
    
    incomeStatement = info['incomeStatement']
    costOfDebt = locale.atoi(incomeStatement['Interest expense']) * 1000
    costOfDebtPerc = 100.0 * costOfDebt / totalDebt
    wacc = (costOfEquityPerc * totalEquity / totalCapital) + (costOfDebtPerc * totalDebt / totalCapital)

    operatingProfit = locale.atoi(incomeStatement['Operating Profit']) * 1000
    metrics['interestCover'] = operatingProfit / costOfDebt
    marketCap = convertToValue(stats['Market Cap'])
    noOfShares = marketCap / currentPrice
    
    #Use to calculate DCF from FCF
    fcf = info['freeCashFlow']
    (dcf, error, fcfForecastSlope) = calculateDCF(fcf, wacc, 5)
    metrics['discountedCashFlow'] = dcf
    metrics['dcfError'] = error
    metrics['fcfForecastSlope'] = fcfForecastSlope
    #Intrinsic value = plant equipment + current assets + 10 year DCF
    currentAssets = locale.atoi(balanceSheet['Total Current Assets']) * 1000
    assetValue = locale.atoi(balanceSheet['Total Plant']) * 1000 + currentAssets #Does not include intangibles + goodwill
    metrics['assetValue'] = assetValue
    intrinsicValue = assetValue + dcf
    metrics['intrinsicValue'] = intrinsicValue
    intrinsicValueRange = dcf*error
    metrics['intrinsicValueRange'] = intrinsicValueRange
    lowerSharePriceValue = (intrinsicValue - intrinsicValueRange) / noOfShares
    upperSharePriceValue = (intrinsicValue + intrinsicValueRange)/ noOfShares
    assetSharePriceValue = assetValue / noOfShares
    enterpriseValue = (marketCap + totalDebt - currentAssets) #Price to buy the organisation
    netAssetValuePrice = shareholderFunds / noOfShares #NAV = Total assets - total liabilities (which is shareholder funds)
    evSharePrice = enterpriseValue / noOfShares
    currentYield = 100*thisYearDividend/currentPrice
    metrics['lowerSharePriceValue'] = lowerSharePriceValue
    metrics['upperSharePriceValue'] = upperSharePriceValue
    metrics['assetSharePriceValue'] = assetSharePriceValue
    metrics['enterpriseValue'] = enterpriseValue
    metrics['netAssetValuePrice'] = netAssetValuePrice
    metrics['evSharePrice'] = evSharePrice
    metrics['currentYield'] = currentYield

    return metrics
    