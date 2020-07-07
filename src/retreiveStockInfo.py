from yahoofinance import getDividends, getKeyStatistics, getFreeCashFlow, getBalanceSheet, getIncomeStatement, getCashFlow
from datetime import datetime
import yfinance as yf

    
def getStockInfo(config, version, stock):
    api = config['stats']['api']
    if (api == "Yahoo"):
        info = getStockInfoYahoo(stock)
    elif (api == "ADFVN"):
        info = get StockInfoAdfn(stock)
    else
        info = None
        print(f"Invalid API {api}")
    return info

def getStockInfoYahoo(version, stock):
    dividends = getDividends(stock)
    
    balanceSheet = getBalanceSheet(stock)
    incomeStatement = getIncomeStatement(stock)
    (cfHtml, cashFlow) = getCashFlow(stock)
    fcf = getFreeCashFlow(cfHtml)
    stats = getKeyStatistics(stock)
    #Get stats from yahooFinance API project
    st = yf.Ticker(stock)
    stockInfo = st.info
    stockInfo = removeNones(stockInfo)
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
            'info' : stockInfo,
            }
    
    return info

def getStockInfoAdfn(version, stock):
    info = getAdfnData(stock)
    #Get additional stats from yahooFinance API project
    st = yf.Ticker(stock)
    stockInfo = st.info
    stockInfo = removeNones(stockInfo)
    info['info'] = stockInfo
    info['metadata'] = { 'version': version,
             'storedDate': datetime.now(),
             }
    
    return info

def removeNones(d):
    nd = dict()
    for k in d.keys():
        v = d[k]
        if (not v):
            nd[k] = 0
        else:
            nd[k] = v
    return nd 
        