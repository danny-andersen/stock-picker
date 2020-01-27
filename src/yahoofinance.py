from datetime import datetime, timedelta
import time
#from urllib.request import urlopen
import httplib2
from bs4 import BeautifulSoup
import re
import locale
from random import random

#Chrome on Win 10
#header = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'}
#Chromium on Pi
header = {'user-agent': 'Mozilla/5.0 (X11; Linux armv7l) AppleWebKit/537.36 (KHTML, like Gecko) Raspbian Chromium/74.0.3729.157 Chrome/74.0.3729.157 Safari/537.36'}
baseUrl = "https://finance.yahoo.com/quote/"

def getUrlHtml(url):
    http = httplib2.Http()
    data = http.request(url, method="GET", headers=header)[1]
    dom = BeautifulSoup(data, "html5lib")
    time.sleep(15 + 15 * random())  #Sleep for up to 30 seconds to limit number of gets on yahoo web site to prevent blacklisting
    return dom

# pageValueMultiplier is set if some pages being processed show numbers in thousands
def convertToValue(valStr, pageValueMultiplier=1):
    multiplier = 1 # This converts M and B to the relevant values
    value = None
    if (valStr is not None):
        if (valStr == 'N/A' or valStr == '-' or valStr == ''):
            value = 0
        else:
            if ('M' in valStr):
                multiplier = 1000000
                valStr = valStr.strip('M')
            elif ('B' in valStr):
                multiplier = 1000000000
                valStr = valStr.strip('B')
            elif ('K' in valStr):
                multiplier = 1000
                valStr = valStr.strip('K')
            try:
                value = locale.atof(valStr.replace(',','')) * pageValueMultiplier
                value = value * multiplier
            except ValueError:
                value = 0
    return value

#Note: this doesent work 
def getLatestPrice(stock):
    now = datetime.now()
    start = now - timedelta(days = 15)
    endPeriod = int(now.timestamp())
    startPeriod = int(start.timestamp())
    dividendHistory = f"/history?period1={startPeriod}&period2={endPeriod}&interval=1d&filter=history&frequency=1d"
    url = baseUrl + stock + dividendHistory

    html = getUrlHtml(url)
    priceTable = html.find("table", attrs = {'data-test' :"historical-prices"});
    priceAndDate = dict()
    if (priceTable):
        for tr in priceTable.find_all("tr"):
            td = tr.find_all("td")
            if len(td) == 2:
                strs = td[0].stripped_strings;
                priceDate = ''
                for str in strs:
                    d = priceDate + str;
                priceDate = datetime.strptime(d, "%b %d, %Y")
                price = ''
                strs = td[1].stripped_strings;
                for str in strs:
                    price = price + str;
                    break #first one only
                priceAndDate.append({'date': priceDate, 'price':float(price)})
    return (priceAndDate)

def getDividends(stock):
    endPeriod = int(datetime.now().timestamp())
    dividendHistory = f"/history?period1=927500400&period2={endPeriod}&interval=div%7Csplit&filter=div&frequency=1d"
    url = baseUrl + stock + dividendHistory

    html = getUrlHtml(url)
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

def getFreeCashFlow(html):
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
            else:
                #If no value then no span
                value = ""
        else:
            print (f"Failed to retreive section of sibling of title {title} from html")

    else:
        print (f"Failed to retreive div with title {title} from html")
    return convertToValue(value, 1000) #All table values in thousands
  
def getBalanceSheet(stock):
    cf = "/balance-sheet?p="
    url = baseUrl + stock + cf + stock
    html = getUrlHtml(url)

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

    value = getTableValue(html, "Retained earnings", True)
    balanceSheet['Retained earnings'] = value
    
    value = getTableValue(html, "Total Current Liabilities", True)
    balanceSheet['Total current liabilities'] = value
    
    value = getTableValue(html, "Total non-current liabilities", True)
    balanceSheet['Total non-current liabilities'] = value
    
    value = getTableValue(html, "Total stockholders' equity", True)
    balanceSheet['Stockholder Equity'] = value
    return balanceSheet

def getIncomeStatement(stock):
    cf = "/financials?p="
    url = baseUrl + stock + cf + stock
    html = getUrlHtml(url)
    income = dict()
    income['Total revenue'] = getTableValue(html, "Total revenue")
    income['Cost of revenue'] = getTableValue(html, "Cost of revenue")
    income['Central overhead'] = getTableValue(html, "Selling general and administrative")
    income['Interest expense'] = getTableValue(html, "Interest Expense")
    income['Net income'] = getTableValue(html, "Net Income")
    income['Operating profit'] = getTableValue(html, "Operating Income or Loss")

    return income

def getCashFlow(stock):
    cf = "/cash-flow?p="
    url = baseUrl + stock + cf + stock
    html = getUrlHtml(url)
    cash = dict()
    value = getTableValue(html, "Dividends Paid")
    cash['Dividends paid'] = value
    return (html, cash)
   
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
            if (not statValue):
                print (f"Failed to table value for {inStr} from html")
        else:
            print (f"Failed to retreive table for {inStr} from html")
    return (statValue)

def getKeyStatistics(stock):
    stats = "/key-statistics?p="

    url = baseUrl + stock + stats + stock
    html = getUrlHtml(url)

    stats = {}
    searchStr = "^Market Cap"
    stats["Market Cap"] = convertToValue(findAndProcessTable(html, searchStr))
    searchStr = "^Return on Assets"
    stats["Return on Assets"] = findAndProcessTable(html, searchStr)
    searchStr = "^Revenue per share"
    stats["Revenue per share"] = findAndProcessTable(html, searchStr)
    searchStr = "^Shares outstanding"
    stats["Shares Outstanding"] = convertToValue(findAndProcessTable(html, searchStr))
    searchStr= "^Diluted EPS"
    stats["Diluted EPS"] = convertToValue(findAndProcessTable(html, searchStr))
    searchStr= "^Current Ratio"
    stats["Current Ratio"] = convertToValue(findAndProcessTable( html, searchStr))
    searchStr= "^Ex-Dividend Date"
    divDate = findAndProcessTable(html, searchStr)
    if (divDate):
        if (divDate == 'N/A' or divDate == '-' or divDate == ''):
            value = 0
        else:
            try:
                value = datetime.strptime(divDate, "%b %d, %Y")
            except ValueError:
                value = 0
    else:
        value = None
    stats["Ex-Dividend Date"] = value
    searchStr= "^Forward Annual Dividend Yield"
    val = findAndProcessTable(html, searchStr)
    if (val):
        stats["Forward Annual Dividend Yield"] = convertToValue(val.split('%')[0])
    else:
        stats["Forward Annual Dividend Yield"] = None
    return (stats)

