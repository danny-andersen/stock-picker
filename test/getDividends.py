from yahoofinance import getDividends
from datetime import datetime


if __name__ == "__main__":
    stock="TSCO.L" 
    dividends = getDividends(stock)
    for divi in dividends:
        print (f"Date: {divi['date'].strftime('%Y-%m-%d')} Dividend: {divi['dividend']}")
    #print (dividends)
