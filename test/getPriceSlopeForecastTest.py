import sys
sys.path.insert(0, '../src')

from saveRetreiveFiles import getStockPricesSaved
from pricePeriod import getPriceChangeFrequency, calcWeightedSlope, getPriceSamples
import locale
from datetime import datetime,timedelta
import configparser
import argparse
import matplotlib.pyplot as plt
import numpy as np
from alphaAdvantage import checkPrices
from tabulate import tabulate
from math import log10

parser = argparse.ArgumentParser(description='Calculate price rise/fall forecast for given stock symbols')
parser.add_argument('stocks', metavar='symbols', type=str, nargs='*',
               help='space seperated list of stock symbols, e.g. TSCO.L')
parser.add_argument('-v', '--verbose', action='store_true',
               help='set to show detailed output and plots')
args = parser.parse_args()

#Read in ini file
config = configparser.ConfigParser()
config.read('../stockpicker.ini')
localeStr = config['stats']['locale']
locale.setlocale( locale.LC_ALL, localeStr) 
storeConfig = config['store']

if (args.stocks):
    stocks = args.stocks
else:
    #Read from stockfile
    stocks = []
    stockFileName = '../stocklist.txt'
    with open(stockFileName, 'r') as stockFile:
        for stock in stockFile:
            stock = stock.strip(' \n\r')
            stocks.append(stock)

results = []
accuratePred = 0
incDecCorrect = 0
crudeCorrect = 0
stocksProcessed = 0
forwardDaysToPredict = 28 # How far forward to test / check prediction
secsPerDay = 1440 * 60

#For each stock, read prices, prices is a dict with key of timestamp and values of (min,max)
for stock in stocks:
    prices = getStockPricesSaved(storeConfig, stock, False)['dailyPrices']
    if (prices and len(prices) > 0):
        checkedPrices = checkPrices(prices)
        if (checkedPrices):
            prices = checkedPrices
        priceTimeStamps = sorted(prices)
        (priceTimes, priceSamples, fvalWithFreq) = getPriceChangeFrequency(priceTimeStamps, prices)
        if (args.verbose):
            plt.plot(priceTimes, priceSamples)
            plt.show()
            #print (fvalWithFreq[0:20])
            plt.bar(*zip(*fvalWithFreq[2:10]))
            plt.show()
        #For each harmonic determine if the current price is at a local mimima x days ago +/- 10% days
        now = datetime.now()
        startDate = now - timedelta(days=100)
        (predSlope, period) = calcWeightedSlope(startDate, priceTimeStamps, prices, fvalWithFreq)
        #Determine what actually happened, based on calculated weighted periods
        endDate = startDate + timedelta(days=period)
        (times, samples) = getPriceSamples(priceTimeStamps, prices, startDate, endDate)
        if (samples and len(samples) > 0):
            stocksProcessed += 1
            #check what happened
            #day = range(1, len(times)+1)
            #x = np.array(day).reshape((-1,1))
            startts = startDate.timestamp()
            times = [int((t.timestamp() - startts)/secsPerDay) for t in times]
            x = np.array(times)
            y = np.array(samples)
            X = x - x.mean()
            Y = y - y.mean()
            actualSlope = X.dot(Y) / X.dot(X)
            crudePositive = samples[len(samples)-1] > samples[0]
#            model = LinearRegression(True).fit(x,y)
#            actualSlope = model.coef_[0]
#            #Determine accuracy
#            cfcheck = model.predict(x)
#            #Determine root mean squared error as %
#            rmse = mean_squared_error(samples, cfcheck)**0.5
#            vrange = max(samples) - min(samples)
#            if (vrange > 0):
#                rmse = rmse / vrange
#            else:
#                rmse = 0
            if (args.verbose):
                print (f"Stock: Forecast Percent likelihood price will inc (dec) in next 28 days: {predSlope*100:0.2f}%")
                plt.plot(times, samples)
                plt.show()
                print (f"Price at start: {samples[0]:0.0f}, Price at end: {samples[len(samples)-1]:0.0f}, Regression slope: {actualSlope:0.3f}")
            if ((actualSlope < 0 and predSlope > 0) or (actualSlope > 0 and predSlope < 0)):
                accuracy = -1
            else:
                if (actualSlope == 0): actualSlope = 0.01
                if (predSlope == 0): predSlope = 0.01
                accuracy = abs(log10(abs(actualSlope)) - log10(abs(predSlope)))
                incDecCorrect += 1
                if (accuracy <= 1.5): accuratePred += 1
            if (crudePositive and predSlope > 0): 
                crudeAccuracy = 1
                crudeCorrect += 1
            else:
                crudeAccuracy = 0
            results.append({'Stock':stock, 'Forecast':predSlope, 'Actual': actualSlope, 'Accuracy':accuracy, 'CrudeAcc': crudeAccuracy})
        else:
            print (f"Insufficient prices for {stock}")
    else:
        print (f"Prices missing for {stock}")

print (tabulate(results, headers='keys', showindex="always"))
print (f"Correct direction accuracy = {100*incDecCorrect/stocksProcessed:0.1f}, Crude direction accuracy = {100*crudeCorrect/stocksProcessed:0.1f}")
print (f"Prediction accurate enough = {100*accuratePred/stocksProcessed:0.1f}")