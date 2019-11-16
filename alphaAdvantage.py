# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 20:17:35 2019

@author: S243372
"""

from datetime import datetime
from urllib.request import urlopen
import json

def getPrices(apiKey, stock, outputSize, existingPrices):
    function="TIME_SERIES_DAILY_ADJUSTED"
    baseUrl = "https://www.alphavantage.co/query?"
    #outputSize = "full"
    dailyPrice=f"function={function}&symbol={stock}&outputsize={outputSize}&apikey={apiKey}"
    url = baseUrl + dailyPrice

    response = urlopen(url)
    data = response.read().decode("utf-8")
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
    priceDatesSorted = sorted(dailyPrices)
    latestPriceDate = priceDatesSorted[len(priceDatesSorted)-1]
    earliestPriceDate = priceDatesSorted[0]
    startDate = datetime.fromtimestamp(earliestPriceDate)
    endDate = datetime.fromtimestamp(latestPriceDate)
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
 
