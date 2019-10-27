from yahoofinance import getKeyStatistics, getFreeCashFlow, getBalanceSheet

if __name__ == "__main__":
    stock="TSCO.L"
    #stats = getKeyStatistics(stock)
    #print (stats)

    #fcf = getFreeCashFlow(stock)
   # print (fcf)
    
    balance = getBalanceSheet(stock)
    print (balance)
