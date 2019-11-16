from yahoofinance import getDividends, getKeyStatistics, getFreeCashFlow, getBalanceSheet, getIncomeStatement, getCashFlow
from datetime import datetime

     
def getStockInfo(version, stock):
    #stock="MTC.L" 
    #stock="TSCO.L" 
    dividends = getDividends(stock)
    
    #Work out Discounted cash flow valuation
    #Firstly determine WACC
    #WACC = Weighted average cost of capital
    balanceSheet = getBalanceSheet(stock)
    incomeStatement = getIncomeStatement(stock)
    cashFlow = getCashFlow(stock)
    stats = getKeyStatistics(stock)
    fcf = getFreeCashFlow(stock)
    meta = { 'version': version,
             'storedDate': datetime.now(),
             }

    info = {'metadata': meta,
            'dividends': dividends,
            'balanceSheet': balanceSheet,
            'incomeStatement': incomeStatement,
            'cashFlow': cashFlow,
            'freeCashFlow': fcf,
            'stats': stats,
            }
    
    return info