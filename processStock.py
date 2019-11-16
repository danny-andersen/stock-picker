from calcStatistics import calculateDCF
from datetime import datetime
import locale

locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' ) 

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
    avgDividend = avgDividend / len(years)
    
    stats = info['stats']
    exDivDate = stats['Ex-Dividend Date']
    daysSinceExDiv = -(exDivDate - now).days
    forwardYield = locale.atof(stats['Forward Annual Dividend Yield'].split('%')[0])
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

    priceDatesSorted = sorted(dailyPrices)
    latestPriceDate = priceDatesSorted[len(priceDatesSorted)-1]
    (low, high) = dailyPrices[latestPriceDate]
    #Use the average of the last price range we have
    currentPrice = ((high + low)/2)/100
    metrics['currentPrice'] = currentPrice
    
    balanceSheet = info['balanceSheet']
    totalDebt = balanceSheet['Total non-current liabilities']
    totalEquity = balanceSheet['Stockholder Equity'] ##THIS IS THE WRONG STATISTIC - should be market cap
    totalCapital = totalDebt + totalEquity
    
    cashFlow = info['cashFlow']
    costOfEquity = cashFlow['Dividends paid']
#    if (cf is None):
#        costOfEquity = 0
#    else:
#        costOfEquity = -locale.atoi(cf) * 1000
    costOfEquityPerc = 100.0 * costOfEquity / totalEquity #Going to assume 0% dividend growth
    
    incomeStatement = info['incomeStatement']
    costOfDebt = incomeStatement['Interest expense']
    costOfDebtPerc = 100.0 * costOfDebt / totalDebt
    wacc = (costOfEquityPerc * totalEquity / totalCapital) + (costOfDebtPerc * totalDebt / totalCapital)
    metrics['wacc'] = wacc

    operatingProfit = incomeStatement['Operating Profit']
    metrics['operatingProfit'] = operatingProfit
    metrics['interestCover'] = operatingProfit / costOfDebt
    marketCap = stats['Market Cap']
    noOfShares = marketCap / currentPrice
    metrics['marketCap'] = marketCap
    metrics['noOfShares'] = noOfShares
    
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
    metrics['grossProfitPerc'] = 100 * (tr - incomeStatement['Cost of revenue']) / tr
    metrics['operatingProfitPerc'] = 100 * incomeStatement['Operating profit'] / tr
    metrics['overheadPerc'] = 100 * incomeStatement['Central overhead'] / tr

    return metrics
    