from datetime import datetime, timedelta
import time
#from urllib.request import urlopen
import httplib2
from bs4 import BeautifulSoup
import re
import locale
from random import random
import yfinance as yf

#Chrome on Win 10
#header = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'}
#Chromium on Pi
#header = {'user-agent': 'Mozilla/5.0 (X11; Linux armv7l) AppleWebKit/537.36 (KHTML, like Gecko) Raspbian Chromium/74.0.3729.157 Chrome/74.0.3729.157 Safari/537.36'}
header = {'user-agent':'Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Mobile Safari/535.19'}
baseUrl = "https://uk.advfn.com/p.php?pid=financials&symbol=LSE"

def getUrlHtml(url):
    http = httplib2.Http()
    data = http.request(url, method="GET", headers=header)[1]
    dom = BeautifulSoup(data, "html5lib")
    #dom = BeautifulSoup(data, "html.parser")
    #dom = BeautifulSoup(data, "lxml")
    time.sleep(1 + 2 * random())  #Sleep for up to 3 seconds to limit number of gets on web site to prevent blacklisting
    return dom

def removeNones(d):
    nd = dict()
    for k in d.keys():
        v = d[k]
        if (not v):
            nd[k] = 0
        else:
            nd[k] = v
    return nd 

def checkValueStrNotSet(valStr):
    return (not valStr or valStr == 'N/A' or valStr == '-' or valStr == '')

# pageValueMultiplier is set if some pages being processed show numbers in thousands
def convertToValue(valStr, multiplier):
    if checkValueStrNotSet(valStr):
        value = 0
    else:
        if (multiplier == 'm'):
            multi = 1000000
        elif (multiplier == 'b'):
            multi = 1000000000
        elif (multiplier == 'k'):
            multi = 1000
        else:
            multi = 1
        valStr = valStr.replace(',', '')
        value = locale.atof(valStr) * multi
    return value

def getDividends(dom):
    diviTable = None
    diviTableHeader = dom.find("h2", string=re.compile(".* Dividends"))
    if (diviTableHeader): diviTable = diviTableHeader.next_sibling
    divi = []
    if (diviTable):
        first = True
        for tr in diviTable.find_all("tr"):
            if (first): 
                first = False
                continue
            td = tr.find_all("td")
            if (not checkValueStrNotSet(td[8]) and not checkValueStrNotSet(td[3])):
                try:
                    # Use record date, which is towards the end of the period it is for and just after it goes ex-divi
                    divDate = datetime.strptime(td[7].string, "%d/%m/%Y")
                    dividend = float(td[3].string)
                except:
                    #Invalid date or value - ignore
                    continue
                divi.append({'date': divDate, 'dividend':float(dividend)})
    return (divi)

def getFreeCashFlow(dom, rowNum):
    #Find line containing dates
    dates = []
    fcf = []
    cfTableH2 = dom.find("h2", string=re.compile(".* Cash Flow Statement"))
    if (cfTableH2):
        cfTable = cfTableH2.next_sibling
        rows = cfTable.find_all("tr")
        cells = rows[0].find_all("td")
        for cell in cells:
            str = cell.string
            if (str and str != ''):
                dateStr = str.split("(")[0].strip()
                try:
                    dates.append(datetime.strptime(dateStr, "%d %b %Y"))
                except:
                    dates.append(None)
        numRows = len(rows)
        if (numRows > rowNum):
            cells = rows[rowNum].find_all("td") 
            lastCell = len(cells) - 1
            multiplier = cells[lastCell].string
            for cell in cells[1:lastCell]:
                str = cell.string
                if (str and str != ''):
                    fcf.append(convertToValue(str, multiplier))
    return list(zip(dates, fcf))

def getTableValue(html, searchStr, index=0, valueCell=2, multiplier=None, default=None):
    value = default #default return value of None means that no value was available
    regex = re.compile(searchStr)
    cellLinks = html.find_all("a", string=regex)
    if (cellLinks and len(cellLinks) > index):
        cellLink = cellLinks[index]
        cell = cellLink.parent  #table cell (td) is parent of link <a>
        row = cell.parent
        cells = row.find_all("td")
        lastCell = len(cells) - 1
        if (not multiplier):
            multiplier = cells[lastCell].string
        #Get latest value
        value = cells[lastCell - valueCell].string
        value = convertToValue(value, multiplier)
    else:
        print(f"Failed to find table cell with content of {searchStr}")
    return value

# def hasTitle(div):
#     return div.name == 'div' and div.has_attr('title') 
 
def getBalanceSheet(stock, dom, yearCell):

    bsTable = None
    bsTableHeader = dom.find_all("h2", string=re.compile(".* Balance Sheet"), limit=2)
    if (bsTableHeader and len(bsTableHeader) > 1): bsTable = bsTableHeader[1].next_sibling
    balanceSheet = dict()

    if (bsTable):
        currentAssets = getTableValue(bsTable, "current assets.*", valueCell=yearCell, default=0)
        currentAssets += getTableValue(bsTable, "cash.*", valueCell=yearCell, default=0)
        value = getTableValue(bsTable, "^debtors", valueCell=yearCell, default=0)
        balanceSheet['Debtors'] = value
        currentAssets += value
        value = getTableValue(bsTable, "^stocks", valueCell=yearCell, default=0)
        balanceSheet['Inventory'] = value
        currentAssets += value
        balanceSheet['Total Current Assets'] = currentAssets 

        value = getTableValue(bsTable, "^intangibles", valueCell=yearCell)
        balanceSheet['Intangibles'] = value
        value = getTableValue(bsTable, ".*investments", valueCell=yearCell)
        balanceSheet['Investments'] = value
        value = getTableValue(bsTable, "fixed assets", valueCell=yearCell)
        balanceSheet['Total Plant'] = value
        value = getTableValue(bsTable, "^TOTAL", valueCell=yearCell)
        balanceSheet['Total Assets'] = value

        #Move to next section of table with liabilities
        # liabilityStart = bsTable.find("span", string="LIABILITIES").parent.parent
        # print (liabilityStart)
        value = getTableValue(bsTable, "creditors - short", valueCell=yearCell)
        balanceSheet['Total current liabilities'] = value
        
        value1 = getTableValue(bsTable, "creditors - long", valueCell=yearCell)
        value2 = getTableValue(bsTable, "creditors - other", valueCell=yearCell)
        if (value1 and value2): value = value1 + value2
        elif (value1): value = value1
        elif (value2): value = value2
        else: value = 0
        balanceSheet['Total non-current liabilities'] = value
        
        value = getTableValue(bsTable, "^TOTAL", index=1, valueCell=yearCell)
        balanceSheet['Total Liabilities'] = value

        # equityStart = liabilityStart.find("span", string="EQUITY").parent
        value = getTableValue(bsTable, "^TOTAL", index=2, valueCell=yearCell)
        balanceSheet['Stockholder Equity'] = value
    else:
        print(f"No Balance Sheet table for stock {stock}")
    
    return balanceSheet

def getIncomeStatement(dom, yearCell):
    income = dict()
    fundamentalTableLink = dom.find("a", string="turnover")
    if (fundamentalTableLink):
        fundamentalTable = fundamentalTableLink.parent.parent.parent
        income['Total revenue'] = getTableValue(fundamentalTable, "turnover", valueCell=yearCell)
        # income['Cost of revenue'] = getTableValue(incTable, "Cost of revenue")
        # income['Central overhead'] = getTableValue(incTable, "^Selling general.*")
        # income['Interest expense'] = getTableValue(incTable, "Interest Expense")
        income['Net income'] = getTableValue(fundamentalTable, "attributable profit", valueCell=yearCell)
        income['Pre-tax profit'] = getTableValue(fundamentalTable, "pre tax profit", valueCell=yearCell)
        income['Dividend per share'] = getTableValue(fundamentalTable, "dividends per share", valueCell=yearCell)
        income["Revenue per share"] = getTableValue(fundamentalTable, "^eps - basic.*", valueCell=yearCell)
        income["Diluted EPS"] = getTableValue(fundamentalTable, "^eps - diluted.*", valueCell=yearCell)
    return income

def getKeyFigures(dom, income):
    cash = dict()
    stats = {}

    dps = income.get('Dividend per share', 0)
    keyTableH2 = dom.find("h2", string=re.compile(".* Key Figures"))
    if (keyTableH2):
        keyTable = keyTableH2.next_sibling
        value = getTableValue(keyTable, "Shares In Issue", valueCell=1)
        stats["Shares Outstanding"] = value
        # row = keyTable.find_all("tr")[2]
        # cells = row.find_all("td")
        # valStr = cells[1].string
        # multiplier = cells[2].string
        # value = convertToValue(valStr, multiplier)
        cash['Dividends paid'] = value * dps / 100
        stats["Market Cap"] = getTableValue(keyTable, "^Market Cap", valueCell=1)
        stats["Forward Annual Dividend Yield"] = getTableValue(keyTable, "^Dividend Yield", valueCell=1)
        stats["Return on Assets"] = getTableValue(keyTable, "Return On Equity .*", valueCell=1)
    
    ratioTableH2 = dom.find("h2", string=re.compile(".* Financial Ratios"))
    if (ratioTableH2):
        ratioTable = ratioTableH2.next_sibling
        value = getTableValue(ratioTable, "^Current Ratio", valueCell=1, multiplier=1)
        stats["Current Ratio"] = value

    value = None
    diviTableH2 = dom.find("h2", string=re.compile(".* Dividends"))
    if (diviTableH2):
        diviTable = diviTableH2.next_sibling
        rows = diviTable.find_all("tr")
        if (rows and len(rows) > 1):
            row = rows[1]
            divDate = row.find_all("td")[6].string
            if (divDate):
                if (divDate == 'N/A' or divDate == '-' or divDate == ''):
                    value = None
                else:
                    value = datetime.strptime(divDate, "%d/%m/%Y")
    stats["Ex-Dividend Date"] = value
    return (cash, stats)

def getStockInfo(dom, info):
    invTableH2 = dom.find("h2", string=re.compile(".* Investment Ratios"))
    if (invTableH2):
        invTable = invTableH2.next_sibling
        info['dividendRate'] = getTableValue(invTable, "^Dividend Yield", valueCell=1, multiplier=1)
        info['priceToBook'] = getTableValue(invTable, "^Market-to-Book .*", valueCell=1, multiplier=1)
        info['PQ Ratio'] = getTableValue(invTable, "^PQ Ratio", valueCell=1, multiplier=1)
        info['forwardPE'] = getTableValue(invTable, "^PE Ratio", valueCell=1, multiplier=1)
        info['priceToBook'] = getTableValue(invTable, "^Market-to-Book Ratio", valueCell=1, multiplier=1)
        
    ratioTableH2 = dom.find("h2", string=re.compile(".* Financial Ratios"))
    if (ratioTableH2):
        ratioTable = ratioTableH2.next_sibling
        info['enterpriseValue'] = getTableValue(ratioTable, "^Enterprise Value", valueCell=1)
        
    operatingTableH2 = dom.find("h2", string=re.compile(".* Operating Ratios"))
    if (operatingTableH2):
        operatingTable = operatingTableH2.next_sibling
        info['profitMargins'] = getTableValue(operatingTable, "^Net Profit Margin", valueCell=1, multiplier=1)
        info['returnOnEquity'] = getTableValue(operatingTable, "^Return On Equity .*", valueCell=1, multiplier=1)

    keyTableH2 = dom.find("h2", string=re.compile(".* Key Figures"))
    if (keyTableH2):
        keyTable = keyTableH2.next_sibling
        info['navPrice'] = getTableValue(keyTable, "^Net Asset Value .*", valueCell=1, multiplier=1)
        info['diviCover'] = getTableValue(keyTable, "^Dividend Cover", valueCell=1, multiplier=1)
  
    return info

def getStockInfoAdfn(stockName):
    stock = stockName.split(".")[0]
    if (len(stock) == 2): stock += "."
    url = baseUrl + ":" + stock
    dom = getUrlHtml(url)
    
    dividends = getDividends(dom)
    latestYearCell = 2 
    balanceSheet = getBalanceSheet(stock, dom, latestYearCell)
    previousYearCell = 3 
    prevBalanceSheet = getBalanceSheet(stock, dom, previousYearCell)
    latestIncomeStatement = getIncomeStatement(dom, latestYearCell)
    prevIncomeStatement = getIncomeStatement(dom, previousYearCell)
    (cashFlow, stats) = getKeyFigures(dom, latestIncomeStatement)

    operatingRowNum = 1 # Operating Cash Flow
    freeCfRowNum = 2 # Operating after investment activities
    retainedRowNum = 3 # Using Retained Cash Flow
    operatingCf = getFreeCashFlow(dom, operatingRowNum)
    freeCf = getFreeCashFlow(dom, freeCfRowNum)
    retainedCf = getFreeCashFlow(dom, retainedRowNum)
    
    stockInfo = dict()
    #Get additional stats from yahooFinance API project -doesnt work if hammered...
    # st = yf.Ticker(stockName) #Use full name with exchange (e.g. XX.L)
    # stockInfo = st.info
    # stockInfo = removeNones(stockInfo)

    #Overlay yahoo info with adfn
    stockInfo = getStockInfo(dom, stockInfo)
        
    info = {
        'dividends': dividends,
        'balanceSheet': balanceSheet,
        'prevYearBalanceSheet': prevBalanceSheet,
        'incomeStatement': latestIncomeStatement,
        'prevYearIncomeStatement': prevIncomeStatement,
        'cashFlow' : cashFlow,
        'freeCashFlow': freeCf,
        'operatingCashFlow': operatingCf,
        'retainedCashFlow': retainedCf,
        'stats': stats,
        'info' : stockInfo,
        }
   
    return info
