# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 20:17:35 2019

@author: S243372
"""

from datetime import datetime
import httplib2
import json

header = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'}

def getPrices(apiKey, stock, outputSize, existingPrices):
    function="TIME_SERIES_DAILY_ADJUSTED"
    baseUrl = "https://www.alphavantage.co/query?"
    #outputSize = "full"
    dailyPrice=f"function={function}&symbol={stock}&outputsize={outputSize}&apikey={apiKey}"
    url = baseUrl + dailyPrice

    http = httplib2.Http()
    data = http.request(url, method="GET", headers=header)[1]

#    response = urlopen(url)
#    data = response.read().decode("utf-8")
    priceArray = json.loads(data).get("Time Series (Daily)", [])
    dailyPrices = dict()
    for dateKey in priceArray:
        price = priceArray[dateKey]
        high = float(price["2. high"])
        low = float(price["3. low"])
        dt = datetime.strptime(dateKey, "%Y-%m-%d")
        dailyPrices[int(dt.timestamp())] = (low, high)
    if (existingPrices):
        dailyPrices.update(existingPrices)
    if (len((dailyPrices)) > 0):
        priceDatesSorted = sorted(dailyPrices)
        latestPriceDate = priceDatesSorted[len(priceDatesSorted)-1]
        earliestPriceDate = priceDatesSorted[0]
        startDate = datetime.fromtimestamp(earliestPriceDate)
        endDate = datetime.fromtimestamp(latestPriceDate)
    else:
        startDate = datetime.min
        endDate = datetime.min
    #dailyPrices.sort(key=lambda x:x['date'], reverse=True)
    stockPrices = { "stock": stock, 
                   "startDate" : startDate,
                   "endDate": endDate,
                   "dailyPrices": dailyPrices}

    return stockPrices

def getLatestDailyPrices(apiKey, stock, prices):
    return getPrices(apiKey, stock, "compact", prices)
    
def getAllDailyPrices(apiKey, stock):
    return getPrices(apiKey, stock, "full", None)
 
