from datetime import datetime, timedelta
import time
import locale
from saveRetreiveFiles import getStockPricesSaved, saveStockPrices
from alphaAdvantage import getLatestDailyPrices, getAllDailyPrices
from trustnet import getFundPrices

def getAndSaveStockPricesSpark(bcConfig, stock):
    return getAndSaveStockPrices(bcConfig.value, "AlphaAdvantage", stock)

def getAndSaveStockPrices(config, stock, api, periodBetweenCalls=0, lastTime=0):
    maxPriceAgeDays = config['stats'].getint('maxPriceAgeDays')
    storeConfig = config['store']
    localeStr = config['stats']['locale']

    locale.setlocale(locale.LC_ALL, localeStr)
    nowTime = datetime.now()

    prices = getStockPricesSaved(storeConfig, stock)
    refreshPrices = False
    if (prices):
        latestPriceDate = prices['endDate']
        #Determine the last attempt date - if not in stats then assume 2 days ago to get the latest
        lastAttemptDate = prices.get('lastRetrievalDate', nowTime - timedelta(days=2))
        if (latestPriceDate):
            howOld = nowTime - latestPriceDate
        if (not latestPriceDate):
            refreshPrices = True
        elif (howOld.days > maxPriceAgeDays):
            howLongSinceLastRetrieval = nowTime - lastAttemptDate
            if (howLongSinceLastRetrieval.days > 1):
                refreshPrices = True
        elif (not prices['dailyPrices']):
            refreshPrices = True
    else:
        refreshPrices = True
    if (refreshPrices):
        # If no latest price data or more than max age, refresh
        newPrices = None
        if (periodBetweenCalls):
            sleepTime = periodBetweenCalls - (datetime.now() - lastTime).seconds + 1
            if (sleepTime > 0):
                time.sleep(sleepTime)
        if (api == 'AlphaAdvantage'):
            print(f"{stock}: Refreshing stock prices from AlphaAdvantage")
            apiKey = config['keys']['alphaAdvantageApiKey']
            if (prices and len(prices) > 0):
                newPrices = getLatestDailyPrices(apiKey, stock, prices)
            else:
                # Get all daily prices to save
                print(f"{stock}: Getting all stock prices")
                newPrices = getAllDailyPrices(apiKey, stock)
        elif (api == 'TrustNet'):
            print(f"{stock}: Refreshing fund prices from TrustNet")
            newPrices = getFundPrices(stock, prices)
        lastTime = datetime.now()
        if (newPrices and newPrices['dailyPrices']):
            prices = newPrices
            saveStockPrices(storeConfig, stock, prices)
        else:
            print(f"{stock}: Failed to get any stock prices from API {api}")
    return (prices, lastTime)

def getLatestPrices(config, rateLimit, stocks):
    periodBetweenCalls = 60.0 / rateLimit
    nowTime = datetime.now()
    lastTime = nowTime - timedelta(seconds = periodBetweenCalls + 1)
    for stock in stocks:
        (prices, lastTime) = getAndSaveStockPrices(config, stock, "AlphaAdvantage", periodBetweenCalls, lastTime)
