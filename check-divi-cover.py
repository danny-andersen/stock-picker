from yahoofinance import getDividends, getKeyStatistics
from datetime import datetime, timedelta

if __name__ == "__main__":
    stock="TSCO.L" 
    dividends = getDividends(stock)
    #Determine this years dividend, average and max dividend
    thisYearDividend = 0
    avgDividend = 0
    maxDividend = 0
    now = datetime.now();
    for divi in dividends:
    	date = divi['date']
    	dividend = float(divi['dividend'])
    	if (now - date < timedelta(days=366)):
    		thisYearDividend += dividend
    	if (maxDividend < dividend):
    		maxDividend = dividend
    	avgDividend += dividend
    avgDividend = avgDividend / len(dividends)
    print (f"This year dividend: {thisYearDividend}, Max Dividend: {maxDividend}, Avg Dividend: {avgDividend}")
    stats = getKeyStatistics(stock)
    eps = float(stats['Diluted EPS'])
    diviCover = eps / thisYearDividend
    print (f"Dividend cover = {diviCover}")



