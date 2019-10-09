from datetime import datetime
import sys
from urllib.request import urlopen
from bs4 import BeautifulSoup


def getDividends(stock):
    baseUrl = "https://finance.yahoo.com/quote/"
    dividendHistory = "/history?period1=1410994800&period2=1568761200&interval=div%7Csplit&filter=div&frequency=1d"
    url = baseUrl + stock + dividendHistory 

    response = urlopen(url)
    data = response.read().decode("utf-8")

    # if len(sys.argv) != 2:
     # sys.stderr.write("Please provide a file to parse\n")
     # sys.exit(1)
    html = BeautifulSoup(data, "html5lib")
    #Find start of hourly forecast
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
            divi.append({'date': divDate, 'dividend':dividend})
    return (divi)

def findAndProcessTable(stats, html, inStr):
    elements = html.find_all(string=inStr);
    #print (f"No of \'{inStr}\' strings found: {len(elements)}")
    for element in elements:
        #print (element)
        statsTable = element.find_parent("table")
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
                    statName = statName.split('(')[0]
                stats[statName] = statValue
    return (stats)

def getKeyStatistics(stock):
    baseUrl = "https://finance.yahoo.com/quote/"
    stats = "/key-statistics?p="

    url = baseUrl + stock + stats + stock

    response = urlopen(url)
    data = response.read().decode("utf-8")

    # if len(sys.argv) != 2:
     # sys.stderr.write("Please provide a file to parse\n")
     # sys.exit(1)
    html = BeautifulSoup(data, "html5lib")
    #Find start of hourly forecast
    stats = {}
    ratioStr = "Return on Assets"
    stats = findAndProcessTable(stats, html, ratioStr)
    searchStr = "Revenue per share"
    stats = findAndProcessTable(stats, html, searchStr)
    epsStr= "Diluted EPS"
    stats = findAndProcessTable(stats, html, epsStr)
    return (stats)

