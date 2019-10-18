# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 20:17:35 2019

@author: S243372
"""

from datetime import datetime
from urllib.request import urlopen
import json


def getPrices(apiKey, stock, outputSize):
    function="TIME_SERIES_DAILY_ADJUSTED"
    baseUrl = "https://www.alphavantage.co/query?"
    #outputSize = "full"
    dailyPrice=f"function={function}&symbol={stock}&outputsize={outputSize}&apikey={apiKey}"
    url = baseUrl + dailyPrice

    response = urlopen(url)
    data = response.read().decode("utf-8")
    priceArray = json.loads(data).get("Time Series (Daily)", [])
    dailyPrices = []
    for dateKey in priceArray:
        price = priceArray[dateKey]
        high = float(price["2. high"])
        low = float(price["3. low"])
        date = datetime.strptime(dateKey, "%Y-%m-%d")
        d = { "date": date, "high": high, "low": low}
        dailyPrices.append(d)
    stockPrices = { "stock": stock, "dailyPrices": dailyPrices}
    return stockPrices

def getLatestDailyPrices(apiKey, stock):
    return getPrices(apiKey, stock, "compact")
    
def getAllDailyPrices(apiKey, stock):
    return getPrices(apiKey, stock, "full")
    
