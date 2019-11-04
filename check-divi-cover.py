from yahoofinance import getDividends, getKeyStatistics, getFreeCashFlow, getBalanceSheet, getIncomeStatement, getCashFlow
from calcStatistics import calculateDCF
from datetime import datetime
from alphaAdvantage import getLatestDailyPrices
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

def normaliseValue(value, min, max):
    if value > max:
        score = 1
    elif value < min:
        score = 0
    else:
        score = (value - min) / (max - min)
    return score

if __name__ == "__main__":

    stock="TSCO.L" 
    dividends = getDividends(stock)
    #Determine this years dividend, average and max dividend
    now = datetime.now();
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
    	dividend = years[year]
    	if year == now.year:
	   		thisYearDividend = dividend / 100
    	if (maxDividend < dividend):
    		maxDividend = dividend
    	avgDividend += dividend
    avgDividend = avgDividend / (100*len(years))
    
    stats = getKeyStatistics(stock)
    exDivDate = datetime.strptime(stats['Ex-Dividend Date4'], "%b %d, %Y")
    daysSinceExDiv = -(exDivDate - now).days
    forwardDivi = convertToValue(stats['Forward Annual Dividend Yield4'].split('%')[0])
    eps = convertToValue(stats['Diluted EPS']) / 100
    if (thisYearDividend != 0):
        diviCover = eps / thisYearDividend
    else:
        diviCover = 0
    currentRatio = convertToValue(stats['Current Ratio'])
    
    keyFile = "alphaAdvantage.apikey"
    f = open(keyFile)
    apiKey = f.readline().strip('\n');
    prices = getLatestDailyPrices(apiKey, stock)
    dailyPrices = prices['dailyPrices']
    dailyPrices.sort(key=lambda x:x['date'], reverse=True)
    currentPrice = ((dailyPrices[0]['high'] + dailyPrices[0]['low'])/2)/100

    #Work out Discounted cash flow valuation
    #Firstly determine WACC
    #WACC = Weighted average cost of capital
    balanceSheet = getBalanceSheet(stock)
    incomeStatement = getIncomeStatement(stock)
    cashFlow = getCashFlow(stock)
    
    totalDebt = locale.atoi(balanceSheet['Total non-current liabilities'])
    totalEquity = locale.atoi(balanceSheet['Stockholder Equity']) ##THIS IS THE WRONG STATISTIC - should be market cap
    totalCapital = totalDebt + totalEquity
    cf = cashFlow['Dividends paid']
    if (cf is None):
        costOfEquity = 0
    else:
        costOfEquity = -locale.atoi(cf)
    costOfEquityPerc = 100.0 * costOfEquity / totalEquity #Going to assume 0% dividend growth
    costOfDebt = locale.atoi(incomeStatement['Interest expense'])
    costOfDebtPerc = 100.0 * costOfDebt / totalDebt
    wacc = (costOfEquityPerc * totalEquity / totalCapital) + (costOfDebtPerc * totalDebt / totalCapital)

    operatingProfit = locale.atoi(incomeStatement['Operating Profit'])
    interestCover = operatingProfit / costOfDebt
    marketCap = convertToValue(stats['Market Cap'])
    noOfShares = marketCap / currentPrice
    
    #Use to calculate DCF from FCF
    fcf = getFreeCashFlow(stock)
    (dcf, error, fcfForecastSlope) = calculateDCF(fcf, wacc, 5)
    #Intrinsic value = plant equipment + current assets + 10 year DCF
    fixedAssetValue = locale.atoi(balanceSheet['Total Plant']) + locale.atoi(balanceSheet['Total Current Assets'])
    intrinsicValue = fixedAssetValue + dcf
    intrinsicValueRange = dcf*error
    lowerSharePriceValue = (intrinsicValue - intrinsicValueRange) * 1000 / noOfShares
    upperSharePriceValue = (intrinsicValue + intrinsicValueRange) * 1000/ noOfShares
    assetSharePriceValue = fixedAssetValue * 1000 / noOfShares
    
    #Determine score between 0 - 1
    score = 0
    score += normaliseValue(diviCover, 0, 1.5)
    score += normaliseValue(interestCover, 0, 1)
    score += normaliseValue(currentRatio, 0, 1)
    score += normaliseValue(fcfForecastSlope, -1, 1)
    if (assetSharePriceValue > currentPrice): score += 1
    if (lowerSharePriceValue > currentPrice): score += 1
    
    print (f"This year dividend: {thisYearDividend}, Max Dividend: {maxDividend:.2f}, Avg Dividend: {avgDividend:.2f}")
    print (f"Current Year Yield = {100*thisYearDividend/currentPrice:.2f}%")
    print (f"Forward Dividend Yield = {forwardDivi}%")
    print (f"Days to Ex-Dividend = {daysSinceExDiv} {exDivDate.strftime('%Y-%m-%d')}")
    print (f"Dividend cover = {diviCover:.2f}")
    print(f"Current Ratio = {currentRatio}")
    print(f"Interest Cover= {interestCover}")

    print (f"WACC % = {wacc:.2f}")
    print (f"5 year DCF = {dcf/1000000:.3f}B (Forecast FCF error: {error*100:.1f}%)")
    print (f"Intrinsic value = {intrinsicValue/1000000:.3f}B +/- {intrinsicValueRange/1000000:0.2f}B")

    print (f"Current share price: {currentPrice:0.2f}")
    print (f"Share price DCF value range: {lowerSharePriceValue:0.2f} - {upperSharePriceValue:0.2f}")    
    print (f"Share price Fixed asset value : {assetSharePriceValue:0.2f}")
    print (f"Score: {score} / 6")
