from yahoofinance import getDividends, getKeyStatistics, getFreeCashFlow, getBalanceSheet, getIncomeStatement, getCashFlow
from alphaAdvantage import getLatestDailyPrices
from datetime import datetime

     
def getStockInfo(apiKey, stock, showResults=False):
    #stock="MTC.L" 
    #stock="TSCO.L" 
    dividends = getDividends(stock)
    
    prices = getLatestDailyPrices(apiKey, stock)
    dailyPrices = prices['dailyPrices']
    dailyPrices.sort(key=lambda x:x['date'], reverse=True)

    #Work out Discounted cash flow valuation
    #Firstly determine WACC
    #WACC = Weighted average cost of capital
    balanceSheet = getBalanceSheet(stock)
    incomeStatement = getIncomeStatement(stock)
    cashFlow = getCashFlow(stock)
    stats = getKeyStatistics(stock)
    fcf = getFreeCashFlow(stock)
    meta = { 'version': '1.0',
             'storedDate': datetime.now(),
             }

    info = {'metadata': meta,
            'dividends': dividends,
            'balanceSheet': balanceSheet,
            'incomeStatement': incomeStatement,
            'cashFlow': cashFlow,
            'freeCashFlow': fcf,
            'dailyPrices': dailyPrices,
            'stats': stats,
            }
    return info