
from datetime import datetime
import httplib2
import json
import time
from math import log10
from random import random

header = {'user-agent': 'Mozilla/5.0 (X11; Linux armv7l) AppleWebKit/537.36 (KHTML, like Gecko) Raspbian Chromium/74.0.3729.157 Chrome/74.0.3729.157 Safari/537.36'}
#header = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'}

def checkPrices(prices):
     #Check prices dont vary wildy between days, if they do, delete the day
     newPrices = dict()
     changed = False #Use to indicate if changes made - if none made then return None
     if (prices):
        pricedates = sorted(prices)
        (priceLow, priceHigh) = prices[pricedates[0]]
        lastPrice = (priceLow + priceHigh) / 2
        for pricedate in pricedates:
            (priceLow, priceHigh) = prices[pricedate]
            price = (priceLow + priceHigh) /2
            if (abs(int(log10(price)) - int(log10(lastPrice))) >= 2):
                if (lastPrice > price):
                    price *= 100  # price in pounds - convert to pence
                    priceLow *= 100
                    priceHigh *= 100
                    changed = True
    #         reldelta = abs(price - lastPrice) / price
    #         if (reldelta > 0.5): 

            newPrices[pricedate] = (priceLow, priceHigh)
            lastPrice = price
     if (changed):
         return newPrices
     else:
         return None
             
     
def getPrices(apiKey, stock, outputSize, priceData):
    existingPrices = priceData['dailyPrices']
    # latestPriceDate = priceData['endDate']
    nowTime = datetime.now()
    lastAttemptDate = priceData.get('lastRetrievalDate', nowTime)
    function="TIME_SERIES_DAILY"
    baseUrl = "https://www.alphavantage.co/query?"
    #outputSize = "full"
    dailyPrice=f"function={function}&symbol={stock}&outputsize={outputSize}&apikey={apiKey}"
    url = baseUrl + dailyPrice

    http = httplib2.Http()
    data = http.request(url, method="GET", headers=header)[1]
    # time.sleep(3 + 2 * random())  #Sleep for up to 5 seconds to limit number of gets to prevent blacklisting
    
#    response = urlopen(url)
#    data = response.read().decode("utf-8")
    if (data and data != ""):
        priceArray = json.loads(data).get("Time Series (Daily)", [])
        lastAttemptDate = nowTime
    else:
        print(f"Failed to load latest prices for {stock}")
        priceArray = None
    dailyPrices = dict()
    for dateKey in priceArray:
        price = priceArray[dateKey]
        high = float(price["2. high"])
        low = float(price["3. low"])
        dt = datetime.strptime(dateKey, "%Y-%m-%d")
        dailyPrices[int(dt.timestamp())] = (low, high)
    if (len((dailyPrices)) > 0):
        if (existingPrices):
            existingPrices.update(dailyPrices)
        else:
            existingPrices = dailyPrices
    if (existingPrices):
        priceDatesSorted = sorted(existingPrices)
        latestPriceDate = priceDatesSorted[len(priceDatesSorted)-1]
        earliestPriceDate = priceDatesSorted[0]
        startDate = datetime.fromtimestamp(earliestPriceDate)
        endDate = datetime.fromtimestamp(latestPriceDate)
    else:
        startDate = datetime.min
        endDate = datetime.min
    #Correct any prices that are in pounds, not pence
    checkedPrices = checkPrices(existingPrices)
    if (checkedPrices):
        existingPrices = checkedPrices
    stockPrices = { "stock": stock, 
                   "startDate" : startDate,
                   "lastRetrievalDate" : lastAttemptDate,
                   "endDate": endDate,
                   "dailyPrices": existingPrices}

    return stockPrices

def getLatestDailyPrices(apiKey, stock, prices):
    return getPrices(apiKey, stock, "compact", prices)
    
def getAllDailyPrices(apiKey, stock):
    return getPrices(apiKey, stock, "full", None)
 
