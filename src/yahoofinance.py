from datetime import datetime
#from urllib.request import urlopen
import httplib2
from bs4 import BeautifulSoup
import re
import locale

header = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'}

# pageValueMultiplier is set if some pages being processed show numbers in thousands
def convertToValue(valStr, pageValueMultiplier=1):
    multiplier = 1 # This converts M and B to the relevant values
    value = None
    if (valStr is not None):
        if ('M' in valStr):
            multiplier = 1000000
            valStr = valStr.strip('M')
        if ('B' in valStr):
            multiplier = 1000000000
            valStr = valStr.strip('B')
        if (valStr == 'N/A' or valStr == '-'):
            value = 0
        else:
            try:
                value = locale.atof(valStr.replace(',','')) * pageValueMultiplier
                value = value * multiplier
            except ValueError:
                value = None
    return value


def getDividends(stock):
    baseUrl = "https://finance.yahoo.com/quote/"
    endPeriod = int(datetime.now().timestamp())
    dividendHistory = f"/history?period1=927500400&period2={endPeriod}&interval=div%7Csplit&filter=div&frequency=1d"
    url = baseUrl + stock + dividendHistory

    http = httplib2.Http()
    data = http.request(url, method="GET", headers=header)[1]
#    response = urlopen(url)
#    data = response.read().decode("utf-8")

    html = BeautifulSoup(data, "html5lib")
    diviTable = html.find("table", attrs = {'data-test' :"historical-prices"});
    divi = []
    if (diviTable):
        for tr in diviTable.find_all("tr"):
            td = tr.find_all("td")
            if len(td) == 2:
                strs = td[0].stripped_strings;
                divDate = ''
                for str in strs:
                    d = divDate + str;
                divDate = datetime.strptime(d, "%b %d, %Y")
                dividend = ''
                strs = td[1].stripped_strings;
                for str in strs:
                    dividend = dividend + str;
                    break #first one only
                divi.append({'date': divDate, 'dividend':float(dividend)})
    return (divi)

def getFreeCashFlow(stock):
    baseUrl = "https://finance.yahoo.com/quote/"
    cf = "/cash-flow?p="
    url = baseUrl + stock + cf + stock

    http = httplib2.Http()
    data = http.request(url, method="GET", headers=header)[1]
#    response = urlopen(url)
#    data = response.read().decode("utf-8")

    html = BeautifulSoup(data, "html5lib")
    #Find line containing dates
    dates = []
    fcf = []
    datesSpan = html.find("span", string=re.compile("Breakdown", re.IGNORECASE))
    if (datesSpan):
        datesSection = datesSpan.parent
        datesSection = datesSection.next_sibling #skip ttm field
        while datesSection is not None:
            dateStr = datesSection.find("span").string
            if (dateStr != 'ttm'):
                dates.append(datetime.strptime(dateStr, "%m/%d/%Y"))
            datesSection = datesSection.next_sibling
        #Find 2 lines containing fcf
        fcfSpan = html.find_all("span", string=re.compile("^Free"), limit=2);
        #We want the second one
        fcfSection = fcfSpan[1].parent.parent
        fcfSection = fcfSection.next_sibling #Advance to values
        fcfSection = fcfSection.next_sibling #Skip first value - trailing twelve months
        while fcfSection is not None:
            valueStr = fcfSection.find("span")
            if (valueStr):
                fcf.append(locale.atoi(valueStr.string)*1000)
            fcfSection = fcfSection.next_sibling
    return list(zip(dates, fcf))

def getTableValue(html, title, first=False):
    div = html.find("div", attrs={"title":re.compile(title, re.IGNORECASE)})
    value = None
    if (div is not None):
        section = div.parent
        section = section.next_sibling #Advance to first value
        if (not first):
            section = section.next_sibling #Advance to second value
        if (section is not None):
            span = section.find("span")
            if (span is not None):
                value = span.string
    return convertToValue(value, 1000) #All table values in thousands
  
def getBalanceSheet(stock):
    baseUrl = "https://finance.yahoo.com/quote/"
    cf = "/balance-sheet?p="
    url = baseUrl + stock + cf + stock
#    response = urlopen(url)
#    data = response.read().decode("utf-8")
    http = httplib2.Http()
    data = http.request(url, method="GET", headers=header)[1]
    html = BeautifulSoup(data, "html5lib")
#    fp = open("balance.html", "w")
#    fp.write(data)
#    fp.close()
    balanceSheet = dict()

    value = getTableValue(html, "Total Current Assets", True)
#    if (value is None):
#        value = getBalanceSheetValue(html, "Total Current assets")
#    if (value is None):
#        value = getBalanceSheetValue(html, "Total current assets")
    balanceSheet['Total Current Assets'] = value

    value = getTableValue(html, "Net property, plant and equipment", True)
    balanceSheet['Total Plant'] = value

    value = getTableValue(html, "Total Assets", True)
    balanceSheet['Total Assets'] = value

    value = getTableValue(html, "Interest expense", True)
    balanceSheet['Interest expense'] = value
    
    value = getTableValue(html, "Total Current Liabilities", True)
    balanceSheet['Total current liabilities'] = value
    
    value = getTableValue(html, "Total non-current liabilities", True)
    balanceSheet['Total non-current liabilities'] = value
    
    value = getTableValue(html, "Total stockholders' equity", True)
    balanceSheet['Stockholder Equity'] = value
    return balanceSheet

def getIncomeStatement(stock):
    baseUrl = "https://finance.yahoo.com/quote/"
    cf = "/financials?p="
    url = baseUrl + stock + cf + stock
#    response = urlopen(url)
#    data = response.read().decode("utf-8")
    http = httplib2.Http()
    data = http.request(url, method="GET", headers=header)[1]
#    fp = open("income.html", "w")
#    fp.write(data)
#    fp.close()
    html = BeautifulSoup(data, "html5lib")
    income = dict()
    income['Total revenue'] = getTableValue(html, "Total revenue")
    income['Cost of revenue'] = getTableValue(html, "Cost of revenue")
    income['Central overhead'] = getTableValue(html, "Selling general and administrative")
    income['Interest expense'] = getTableValue(html, "Interest Expense")
    income['Net income'] = getTableValue(html, "Net Income")
    income['Operating profit'] = getTableValue(html, "Operating Income or Loss")

    return income

def getCashFlow(stock):
    baseUrl = "https://finance.yahoo.com/quote/"
    cf = "/cash-flow?p="
    url = baseUrl + stock + cf + stock
    http = httplib2.Http()
    data = http.request(url, method="GET", headers=header)[1]
#    response = urlopen(url)
#    data = response.read().decode("utf-8")
    html = BeautifulSoup(data, "html5lib")
    cash = dict()
    value = getTableValue(html, "Dividends Paid")
    cash['Dividends paid'] = value
    return cash
   
def findAndProcessTable(html, inStr):
    regex = re.compile(inStr,  re.IGNORECASE)
    elements = html.find_all(string=regex);
    #print (f"No of \'{inStr}\' strings found: {len(elements)}")
    statValue = None
    inStr = inStr.strip('^') # remove regex control chars
    for element in elements:
        #print (element)
        statsTable = element.find_parent("table")
        if (statsTable != None):
            for tr in statsTable.find_all("tr"):
                td = tr.find_all("td")
                #print (len(td))
                if len(td) == 2:
                    strs = td[0].stripped_strings
                    statName = ''
                    for str in strs:
                        statName = statName + str
                    value = ''
                    strs = td[1].stripped_strings
                    for str in strs:
                        value = value + str
                        break #first one only
                    if ('(' in statName):
                        statName = statName.split('(')[0].strip()
                    if (regex.match(statName)):
                        statValue = value
    return (statValue)

def getKeyStatistics(stock):
    baseUrl = "https://finance.yahoo.com/quote/"
    stats = "/key-statistics?p="

    url = baseUrl + stock + stats + stock

    http = httplib2.Http()
    data = http.request(url, method="GET", headers=header)[1]
#    response = urlopen(url)
#    data = response.read().decode("utf-8")

    html = BeautifulSoup(data, "html5lib")
    stats = {}
    searchStr = "Market Cap"
    stats[searchStr] = convertToValue(findAndProcessTable(html, searchStr))
    searchStr = "Return on Assets"
    stats[searchStr] = findAndProcessTable(html, searchStr)
    searchStr = "Revenue per share"
    stats[searchStr] = findAndProcessTable(html, searchStr)
    searchStr = "^Shares outstanding"
    stats["Shares Outstanding"] = convertToValue(findAndProcessTable(html, searchStr))
    searchStr= "Diluted EPS"
    stats[searchStr] = convertToValue(findAndProcessTable(html, searchStr))
    searchStr= "Current Ratio"
    stats[searchStr] = convertToValue(findAndProcessTable( html, searchStr))
    searchStr= "Ex-Dividend Date"
    divDate = findAndProcessTable(html, searchStr)
    if (divDate != "N/A"):
        try:
            stats[searchStr] = datetime.strptime(divDate, "%b %d, %Y")
        except ValueError:
            stats[searchStr] = None
    else:
        stats[searchStr] = None
    searchStr= "Forward Annual Dividend Yield"
    val = findAndProcessTable(html, searchStr)
    if (val):
        stats[searchStr] = convertToValue(val.split('%')[0])
    else:
        stats[searchStr] = val
    return (stats)

