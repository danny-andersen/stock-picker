import sys
sys.path.insert(0, '/home/danny/git/stock-picker/src')

from adfn import getStockInfoAdfn


if __name__ == "__main__":
    stock="AV.L" 
    stockInfo = getStockInfoAdfn(stock)
    print (stockInfo)
    # dividends = getDividends(stock)
    # for divi in dividends:
    #     print (f"Date: {divi['date'].strftime('%Y-%m-%d')} Dividend: {divi['dividend']}")
    #print (dividends)
