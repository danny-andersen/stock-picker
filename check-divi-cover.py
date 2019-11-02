from yahoofinance import getDividends, getKeyStatistics, getFreeCashFlow, getBalanceSheet, getIncomeStatement, getCashFlow
from calcStatistics import calculateDCF
from datetime import datetime
from alphaAdvantage import getLatestDailyPrices
import locale

if __name__ == "__main__":
    locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' ) 

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
    for year in years:
    	dividend = years[year]
    	if year == now.year:
	   		thisYearDividend = dividend
    	if (maxDividend < dividend):
    		maxDividend = dividend
    	avgDividend += dividend
    avgDividend = avgDividend / len(years)
    
    stats = getKeyStatistics(stock)
    exDivDate = datetime.strptime(stats['Ex-Dividend Date4'], "%b %d, %Y")
    daysToExDiv = (exDivDate - now).days
    forwardDivi = float(stats['Forward Annual Dividend Yield4'].split('%')[0])
    eps = float(stats['Diluted EPS'])
    diviCover = eps / thisYearDividend
    currentRatio = float(stats['Current Ratio'])
    
    keyFile = "alphaAdvantage.apikey"
    f = open(keyFile)
    apiKey = f.readline().strip('\n');
    prices = getLatestDailyPrices(apiKey, stock)
    dailyPrices = prices['dailyPrices']
    dailyPrices.sort(key=lambda x:x['date'], reverse=True)
    currentPrice = (dailyPrices[0]['high'] + dailyPrices[0]['low'])/2

    #Work out Discounted cash flow valuation
    #Firstly determine WACC
    #WACC = Weighted average cost of capital
    balanceSheet = getBalanceSheet(stock)
    incomeStatement = getIncomeStatement(stock)
    cashFlow = getCashFlow(stock)
    
    totalDebt = locale.atoi(balanceSheet['Total non-current liabilities'])
    totalEquity = locale.atoi(balanceSheet['Stockholder Equity'])
    totalCapital = totalDebt + totalEquity
    costOfEquity = -locale.atoi(cashFlow['Dividends paid'])
    costOfEquityPerc = 100.0 * costOfEquity / totalEquity #Going to assume 0% dividend growth
    costOfDebt = locale.atoi(incomeStatement['Interest expense'])
    costOfDebtPerc = 100.0 * costOfDebt / totalDebt
    wacc = (costOfEquityPerc * totalEquity / totalCapital) + (costOfDebtPerc * totalDebt / totalCapital)

    operatingProfit = locale.atoi(incomeStatement['Operating Profit'])
    interestCover = operatingProfit / costOfDebt
    
    #Use to calculate DCF from FCF
    fcf = getFreeCashFlow(stock)
    #order historic cf,  Sum (cf/(1+wacc)^n)
    dcf = calculateDCF(fcf, wacc)
    
    print (f"This year dividend: {thisYearDividend}, Max Dividend: {maxDividend:.2f}, Avg Dividend: {avgDividend:.2f}")
    print (f"Current Year Yield = {100*thisYearDividend/currentPrice:.2f}%")
    print (f"Forward Dividend Yield = {forwardDivi}%")
    print (f"Days to Ex-Dividend = {daysToExDiv} {exDivDate.strftime('%Y-%m-%d')}")
    print (f"Dividend cover = {diviCover:.2f}")
    print(f"Current Ratio = {currentRatio}")
    print(f"Interest Cover= {interestCover}")

    print (f"WACC % = {100*wacc:.2f}")
    print (f"DCF = {dcf:.2f}")
