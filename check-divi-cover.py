from yahoofinance import getDividends, getKeyStatistics
from datetime import datetime, timedelta

if __name__ == "__main__":
    stock="TSCO.L" 
    dividends = getDividends(stock)
    #Determine this years dividend, average and max dividend
    now = datetime.now();
    #Calc dividend by year
    years = {}
    for divi in dividends:
    	date = divi['date']
    	dividend = float(divi['dividend'])
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
    currentPrice = 227.4 #TODO
    print (f"This year dividend: {thisYearDividend}, Max Dividend: {maxDividend:.2f}, Avg Dividend: {avgDividend:.2f}")
    print (f"Current Year Yield = {100*thisYearDividend/currentPrice:.2f}")
    print (f"Forward Dividend Yield = {forwardDivi}")
    print (f"Days to Ex-Dividend = {daysToExDiv} {exDivDate.strftime('%Y-%m-%d')}")
    print (f"Dividend cover = {diviCover:.2f}")
    print(f"Current Raio = {currentRatio}")




