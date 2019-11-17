from yahoofinance import getKeyStatistics, getFreeCashFlow, getBalanceSheet, getIncomeStatement

if __name__ == "__main__":
    stock="TSCO.L"
    #stats = getKeyStatistics(stock)
    #print (stats)

    #fcf = getFreeCashFlow(stock)
    #print (fcf)
    
    #balance = getBalanceSheet(stock)
    #print (balance)

    income = getIncomeStatement(stock)
    print (income)