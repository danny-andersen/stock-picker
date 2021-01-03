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
    #time.sleep(1 + 5 * random())  #Sleep for up to 10 seconds to limit number of gets on web site to prevent blacklisting
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
            if (checkValueStrNotSet(td[8]) and checkValueStrNotSet(td[3])):
                divDate = datetime.strptime(td[8].string, "%d/%m/%Y")
                dividend = td[3].string
                divi.append({'date': divDate, 'dividend':float(dividend)})
    return (divi)

def getFreeCashFlow(dom):
    #Find line containing dates
    dates = []
    fcf = []
    cfTable = dom.find("h2", string=re.compile(".* Cash Flow Statement")).next_sibling
    rows = cfTable.find_all("tr")
    cells = rows[0].find_all("td")
    for cell in cells:
        str = cell.string
        if (str and str != ''):
            dateStr = str.split("(")[0].strip()
            dates.append(datetime.strptime(dateStr, "%d %b %Y"))
    cells = rows[3].find_all("td") # Using Retained Cash Flow
    lastCell = len(cells) - 1
    multiplier = cells[lastCell].string
    for cell in cells[1:lastCell]:
        str = cell.string
        if (str and str != ''):
            fcf.append(convertToValue(str, multiplier))
    return list(zip(dates, fcf))

def getTableValue(html, searchStr, index=0, valueCell=2, multiplier=None):
    value = None
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
 
def getBalanceSheet(dom):

    bsTable = None
    bsTableHeader = dom.find_all("h2", string=re.compile(".* Balance Sheet"), limit=2)
    if (bsTableHeader and len(bsTableHeader) > 1): bsTable = bsTableHeader[1].next_sibling
    balanceSheet = dict()

    value1 = getTableValue(bsTable, "current assets.*", valueCell=2)
    value2 = getTableValue(bsTable, "cash.*", valueCell=2)
    if (value1 and value2): value = value1 + value2
    elif (value1): value = value1
    elif (value2): value = value2
    else: value = None
    balanceSheet['Total Current Assets'] = value

    value = getTableValue(bsTable, "^intangibles", valueCell=2)
    balanceSheet['Intangibles'] = value
    value = getTableValue(bsTable, "^stocks", valueCell=2)
    balanceSheet['Inventory'] = value
    value = getTableValue(bsTable, "fixed assets", valueCell=2)
    balanceSheet['Total Plant'] = value
    value = getTableValue(bsTable, "^TOTAL", valueCell=2)
    balanceSheet['Total Assets'] = value

    #Move to next section of table with liabilities
    # liabilityStart = bsTable.find("span", string="LIABILITIES").parent.parent
    # print (liabilityStart)
    value = getTableValue(bsTable, "creditors - short", valueCell=2)
    balanceSheet['Total current liabilities'] = value
    
    value1 = getTableValue(bsTable, "creditors - long", valueCell=2)
    value2 = getTableValue(bsTable, "creditors - other", valueCell=2)
    if (value1 and value2): value = value1 + value2
    elif (value1): value = value1
    elif (value2): value = value2
    else: value = None
    balanceSheet['Total non-current liabilities'] = value
    
    value = getTableValue(bsTable, "^TOTAL", index=1, valueCell=2)
    balanceSheet['Total Liabilities'] = value

    # equityStart = liabilityStart.find("span", string="EQUITY").parent
    value = getTableValue(bsTable, "^TOTAL", index=2, valueCell=2)
    balanceSheet['Stockholder Equity'] = value
    
    return balanceSheet

def getKeyFigures(dom):
    income = dict()
    cash = dict()
    stats = {}

    fundamentalTable = dom.find("a", string="turnover").parent.parent.parent
    income['Total revenue'] = getTableValue(fundamentalTable, "turnover")
    # income['Cost of revenue'] = getTableValue(incTable, "Cost of revenue")
    # income['Central overhead'] = getTableValue(incTable, "^Selling general.*")
    # income['Interest expense'] = getTableValue(incTable, "Interest Expense")
    income['Net income'] = getTableValue(fundamentalTable, "attributable profit")
    income['Operating profit'] = getTableValue(fundamentalTable, "pre tax profit")
    dps = getTableValue(fundamentalTable, "dividends per share")
 
    keyTable = dom.find("h2", string=re.compile(".* Key Figures")).next_sibling
    value = getTableValue(keyTable, "Shares In Issue", valueCell=1)
    stats["Shares Outstanding"] = value
    # row = keyTable.find_all("tr")[2]
    # cells = row.find_all("td")
    # valStr = cells[1].string
    # multiplier = cells[2].string
    # value = convertToValue(valStr, multiplier)
    cash['Dividends paid'] = value * dps / 100
    stats["Market Cap"] = getTableValue(keyTable, "^Market Cap", valueCell=1)
    stats["Revenue per share"] = getTableValue(fundamentalTable, "^eps - basic .*", valueCell=2)
    stats["Forward Annual Dividend Yield"] = getTableValue(keyTable, "^Dividend Yield", valueCell=1)
    stats["Return on Assets"] = getTableValue(keyTable, "Return On Equity .*", valueCell=1)
    # searchStr= "^Diluted EPS"
    stats["Diluted EPS"] = getTableValue(fundamentalTable, "^eps - diluted .*", valueCell=2)
    ratioTable = dom.find("h2", string=re.compile(".* Financial Ratios")).next_sibling
    value = getTableValue(ratioTable, "^Current Ratio", valueCell=1, multiplier=1)
    stats["Current Ratio"] = value

    diviTable = dom.find("h2", string=re.compile(".* Dividends")).next_sibling
    row = diviTable.find_all("tr")[1]
    divDate = row.find_all("td")[6].string
    if (divDate):
        if (divDate == 'N/A' or divDate == '-' or divDate == ''):
            value = 0
        else:
            value = datetime.strptime(divDate, "%d/%m/%Y")
            # except ValueError:
            #     value = 0
    else:
        value = None
    stats["Ex-Dividend Date"] = value
    return (income, cash, stats)

def getStockInfo(dom, info):
    invTable = dom.find("h2", string=re.compile(".* Investment Ratios")).next_sibling
    ratioTable = dom.find("h2", string=re.compile(".* Financial Ratios")).next_sibling
    operatingTable = dom.find("h2", string=re.compile(".* Operating Ratios")).next_sibling
    keyTable = dom.find("h2", string=re.compile(".* Key Figures")).next_sibling
    info['dividendRate'] = getTableValue(invTable, "^Dividend Yield", valueCell=1, multiplier=1)
    info['enterpriseValue'] = getTableValue(ratioTable, "^Enterprise Value", valueCell=1)
    info['navPrice'] = getTableValue(keyTable, "^Net Asset Value .*", valueCell=1, multiplier=1)
    info['priceToBook'] = getTableValue(invTable, "^Market-to-Book .*", valueCell=1, multiplier=1)
    info['PQ Ratio'] = getTableValue(invTable, "^PQ Ratio", valueCell=1, multiplier=1)
    info['forwardPE'] = getTableValue(invTable, "^PE Ratio", valueCell=1, multiplier=1)
    info['profitMargins'] = getTableValue(operatingTable, "^Net Profit Margin", valueCell=1, multiplier=1)
    
    return info

def getStockInfoAdfn(stockName):
    stock = stockName.split(".")[0]
    if (len(stock) == 2): stock += "."
    url = baseUrl + ":" + stock
    dom = getUrlHtml(url)
    
    dividends = getDividends(dom)
    balanceSheet = getBalanceSheet(dom)
    (incomeStatement, cashFlow, stats) = getKeyFigures(dom)
    fcf = getFreeCashFlow(dom)
    
    #Get additional stats from yahooFinance API project -doesnt work if hammered...
    # st = yf.Ticker(stockName) #Use full name with exchange (e.g. XX.L)
    # stockInfo = st.info
    # stockInfo = removeNones(stockInfo)

    #Overlay yahoo info with adfn
    stockInfo = getStockInfo(dom, stockInfo)
        
    info = {
        'dividends': dividends,
        'balanceSheet': balanceSheet,
        'incomeStatement': incomeStatement,
        'cashFlow': cashFlow,
        'freeCashFlow': fcf,
        'stats': stats,
        'info' : stockInfo,
        }
   
    return info

