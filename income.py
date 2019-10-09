#!/usr/bin/env python

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

import json
import datetime

def get_jsonparsed_data(url):
    response = urlopen(url)
    data = response.read().decode("utf-8")
    return json.loads(data)

url = ("https://financialmodelingprep.com/api/financials/income-statement/AAPL?period=quarter&datatype=json")
income = get_jsonparsed_data(url)
print(f"Stock: {income['symbol']}")
diviStats = []
for point in income['financials']:
    dividend = float(point['Dividend per Share'])
    day = datetime.datetime.strptime(point['date'], "%Y-%m-%d")
    if dividend != 0:
        diviCover = float(point['EPS']) / dividend
    else:   
        diviCover = "N/A"
    #print(f"Date: {day} Dividend: {dividend:.3f} Dividend Cover {diviCover:.3f}")
    diviPoint = {'date': day, 'dividend': dividend, 'divi cover': diviCover} 
    diviStats.append(diviPoint)
 
print(diviStats)
