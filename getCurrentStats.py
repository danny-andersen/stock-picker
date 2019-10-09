from yahoofinance import getKeyStatistics

if __name__ == "__main__":
    stock="TSCO.L"
    stats = getKeyStatistics(stock)
    print (stats)
