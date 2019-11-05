from datetime import datetime
import sys
from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
import locale

locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' ) 

def getDividends(stock):
    baseUrl = "https://finance.yahoo.com/quote/"
    dividendHistory = "/history?period1=583714800&period2=1570662000&interval=div%7Csplit&filter=div&frequency=1d"
    url = baseUrl + stock + dividendHistory

    response = urlopen(url)
    data = response.read().decode("utf-8")

    html = BeautifulSoup(data, "html5lib")
    diviTable = html.find("table", attrs = {'data-test' :"historical-prices"});
    divi = []
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

    response = urlopen(url)
    data = response.read().decode("utf-8")

    html = BeautifulSoup(data, "html5lib")
    #Find line containing dates
    datesSpan = html.find("span", string=re.compile("Breakdown", re.IGNORECASE))
    datesSection = datesSpan.parent
    datesSection = datesSection.next_sibling #skip ttm field
    dates = []
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
    fcf = []
    while fcfSection is not None:
        value = fcfSection.find("span").string
        fcf.append(locale.atoi(value)*1000)
        fcfSection = fcfSection.next_sibling
    return list(zip(dates, fcf))

def getTableValue(html, title):
    div = html.find("div", attrs={"title":re.compile(title, re.IGNORECASE)})
    value = None
    if (div is not None):
        section = div.parent
        section = section.next_sibling #Advance to first value
        if (section is not None):
            span = section.find("span")
            if (span is not None):
                value = span.string
    return value
  
def getBalanceSheet(stock):
    baseUrl = "https://finance.yahoo.com/quote/"
    cf = "/balance-sheet?p="
    url = baseUrl + stock + cf + stock
    response = urlopen(url)
    data = response.read().decode("utf-8")
    html = BeautifulSoup(data, "html5lib")
#    fp = open("balance.html", "w")
#    fp.write(data)
#    fp.close()
    balanceSheet = dict()

    value = getTableValue(html, "Total Current Assets")
#    if (value is None):
#        value = getBalanceSheetValue(html, "Total Current assets")
#    if (value is None):
#        value = getBalanceSheetValue(html, "Total current assets")
    balanceSheet['Total Current Assets'] = value

    value = getTableValue(html, "Net property, plant and equipment")
    balanceSheet['Total Plant'] = value

    value = getTableValue(html, "Total Assets")
    balanceSheet['Total Assets'] = value
    
    div = html.find("div", attrs={"title":"Total Current Liabilities"})
    section = div.parent
    section = section.next_sibling #Advance to first value
    value = section.find("span").string
    balanceSheet['Total current liabilities'] = value
    
    div = html.find("div", attrs={"title":"Total non-current liabilities"})
    section = div.parent
    section = section.next_sibling #Advance to first value
    value = section.find("span").string
    balanceSheet['Total non-current liabilities'] = value
    
    div = html.find("div", attrs={"title":r"Total stockholders' equity"})
    section = div.parent
    section = section.next_sibling #Advance to first value
    value = section.find("span").string
    balanceSheet['Stockholder Equity'] = value
    return balanceSheet

def getIncomeStatement(stock):
    baseUrl = "https://finance.yahoo.com/quote/"
    cf = "/financials?p="
    url = baseUrl + stock + cf + stock
    response = urlopen(url)
    data = response.read().decode("utf-8")
#    fp = open("income.html", "w")
#    fp.write(data)
#    fp.close()
    html = BeautifulSoup(data, "html5lib")
    income = dict()
    div = html.find("div", attrs={"title":"Interest Expense"})
    section = div.parent
    section = section.next_sibling #Advance to first value
    value = section.find("span").string
    income['Interest expense'] = value
    div = html.find("div", attrs={"title":"Operating Income or Loss"})
    section = div.parent
    section = section.next_sibling #Advance to first value
    value = section.find("span").string
    income['Operating Profit'] = value
    return income

def getCashFlow(stock):
    baseUrl = "https://finance.yahoo.com/quote/"
    cf = "/cash-flow?p="
    url = baseUrl + stock + cf + stock
    response = urlopen(url)
    data = response.read().decode("utf-8")
#    fp = open("income.html", "w")
#    fp.write(data)
#    fp.close()
    html = BeautifulSoup(data, "html5lib")
    cash = dict()
    value = getTableValue(html, "Dividends Paid")
    cash['Dividends paid'] = value
    return cash
   
def findAndProcessTable(stats, html, inStr):
    elements = html.find_all(string=re.compile(inStr));
    #print (f"No of \'{inStr}\' strings found: {len(elements)}")
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
                    statValue = ''
                    strs = td[1].stripped_strings
                    for str in strs:
                        statValue = statValue + str
                        break #first one only
                    #stats.append({'statistic': statName, 'value':statValue})
                    if ('(' in statName):
                        statName = statName.split('(')[0].strip()
                    stats[statName] = statValue
    return (stats)

def getKeyStatistics(stock):
    baseUrl = "https://finance.yahoo.com/quote/"
    stats = "/key-statistics?p="

    url = baseUrl + stock + stats + stock

    response = urlopen(url)
    data = response.read().decode("utf-8")

    html = BeautifulSoup(data, "html5lib")
    stats = {}
    ratioStr = "Market Cap"
    stats = findAndProcessTable(stats, html, ratioStr)
    ratioStr = "Return on Assets"
    stats = findAndProcessTable(stats, html, ratioStr)
    searchStr = "Revenue per share"
    stats = findAndProcessTable(stats, html, searchStr)
    epsStr= "Diluted EPS"
    stats = findAndProcessTable(stats, html, epsStr)
    epsStr= "Current Ratio"
    stats = findAndProcessTable(stats, html, epsStr)
    epsStr= "Trailing"
    stats = findAndProcessTable(stats, html, epsStr)
    return (stats)

