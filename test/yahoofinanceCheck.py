import sys
sys.path.insert(0, '../src')
from datetime import datetime, timedelta
import time
#from urllib.request import urlopen
import httplib2
from bs4 import BeautifulSoup
import re
import locale

from yahoofinance import getUrlHtml, getTableValue, hasTitle

header = {'user-agent':'Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Mobile Safari/535.19'}
baseUrl = "https://finance.yahoo.com/quote/"
stock = "TSCO.L"

cf = "/balance-sheet?p="
url = baseUrl + stock + cf + stock
html = getUrlHtml(url)

#Get the start of the Balance Sheet
start = html.find("span", string=re.compile("^Breakdown"))
if (start):
    html = start.parent.parent.parent.parent
    #See if we can find Assets tag
    iter = html.children
    tag = next(iter)
    tag = next(iter)
    ch = tag.children
    tag1 = next(ch)
    print(tag1)
    tag2 = next(ch)
    print(tag2)
    tag2 = next(ch)
    print(tag2)
else:
    print("Couldn't find start of Balance Sheet Breakdown") 
#divs = html.find_all("div", attrs={"title":re.compile(".*")})
divs = html.find_all(hasTitle)
for div in divs:
    print(div['title'])
span = html.find("span", string="Assets")
if (span):
    div = span.parent
else:
    print(f"Failed to get span with content of Assets")

balanceSheet = dict()

value = getTableValue(html, "^total.current.assets", True)
