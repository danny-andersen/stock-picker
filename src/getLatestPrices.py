from datetime import datetime, timedelta
import time
import locale
from saveRetreiveFiles import getStockPricesSaved, saveStockPrices
from alphaAdvantage import getLatestDailyPrices, getAllDailyPrices, checkPrices

def getLatestPrices(config, rateLimit, stocks):
    maxPriceAgeDays = config['stats'].getint('maxPriceAgeDays')
    apiKey = config['keys']['alhaAdvantageApiKey']
    storeConfig = config['store']
    localeStr = config['stats']['locale']
    locale.setlocale(locale.LC_ALL, localeStr)
    periodBetweenCalls = 60.0 / rateLimit
    lastTime = datetime.now() - timedelta(seconds = periodBetweenCalls + 1)
    for stock in stocks:
        prices = getStockPricesSaved(storeConfig, stock)
        dailyPrices = None
        refreshPrices = False
        if (prices):
            dailyPrices = prices['dailyPrices']
            latestPriceDate = prices['endDate']
            if (latestPriceDate):
                howOld = datetime.now() - latestPriceDate
            if (not latestPriceDate):
                refreshPrices = True
            elif (howOld.days > maxPriceAgeDays):
                refreshPrices = True
            elif (not prices['dailyPrices']):
                refreshPrices = True
        else:
            refreshPrices = True
        if (refreshPrices):
            # If no latest price data or more than max age, refresh
            sleepTime = periodBetweenCalls - (datetime.now() - lastTime).seconds
            if (sleepTime > 0):
                time.sleep(sleepTime)
            print(f"{stock}: Refreshing prices")
            newPrices = getLatestDailyPrices(apiKey, stock, dailyPrices)
            lastTime = datetime.now()
            if (newPrices and newPrices['dailyPrices']):
                prices = newPrices
                saveStockPrices(storeConfig, stock, prices)
            else:
                # Get all daily prices to save
                print(f"{stock}: Getting all stock prices")
                newPrices = getAllDailyPrices(apiKey, stock)
                if (newPrices and newPrices['dailyPrices']):
                    prices = newPrices
                    saveStockPrices(storeConfig, stock, prices)
                else:
                    print(f"{stock}: Failed to get any stock prices")
