import sys
sys.path.insert(0, './src')
from saveRetreiveFiles import getStockPricesSaved
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np

def findNearestSample(start, timestamps, sampleTimeStamp):
    diff = abs(timestamps[start] - sampleTimeStamp)
    index = start
    for t in timestamps[start:]:
        newdiff = abs(sampleTimeStamp - t) 
        if (newdiff > diff):
            #got nearest already
            break
        else:
            index += 1
            diff = newdiff
    return index-1

def getPriceChangeFrequency(prices):
    priceTimeStamps = sorted(prices)
    #print ([datetime.fromtimestamp(t) for t in priceTimeStamps])
    #Find prices for previous year
    nowTime = datetime.now()
    lastYear = (nowTime - timedelta(days=365)).year
    sampleDate = datetime(day=1,month=1,year=lastYear)
    if (priceTimeStamps[0] > sampleDate.timestamp()):
        #Dont have enough samples
        sampleDate = datetime.fromtimestamp(priceTimeStamps[0])
        endDate = sampleDate + timedelta(days=365)
    else:
        endDate = datetime(day=31,month=12, year=lastYear)
    incDate = timedelta(days=1)
    priceSamples = []
    priceTimes = []
    index = 0
    while sampleDate <= endDate:
        try:
            index = findNearestSample(index, priceTimeStamps, sampleDate.timestamp())
            #print (f"Looking for {sampleDate.timestamp()} found {priceTimeStamps[index]}")
            ts = priceTimeStamps[index]
            priceTimes.append(ts)
            (max, min) = prices[ts]
            priceSamples.append((max+min)/2)
        except KeyError:
            print(f"Missing day {sampleDate}")
        sampleDate += incDate
#    plt.plot(priceTimes, priceSamples)
#    plt.show()
    #Do an FFT of the daily prices
    N = len(priceSamples)
    samples = np.array(priceSamples)
#    window = np.blackman(len(values))
#    freq = np.fft.fft(samples*window)
    freq = np.fft.fft(samples)
    #0 component is the DC bias component
    #Get absolute values of positive frequencies
    fval = np.abs(freq[1:(N//2)])
#    dcVal = np.abs(freq[0])
#    print (dcVal)
#    plt.plot(fval)
#    plt.show()
    #Inverse of frequencies is the day period
    days = 1/(np.fft.fftfreq(N)[1:])
    #Generate tuple of (index, value) sorted by value
    sortedfval = [i for i in sorted(enumerate(fval[1:]), key=lambda x:x[1], reverse=True )]
    maxVal = sortedfval[0][1]
    #Generate tuple of (day period, value)
    fvalWithFreq = [(days[i[0]],i[1]/maxVal) for i in sortedfval]
    return fvalWithFreq
    
if __name__ == "__main__":
    import argparse
    import configparser
    import locale
    parser = argparse.ArgumentParser(description='Re-calculate and display metrics and scores of given stock symbols')
    parser.add_argument('-n', '--num', type=int, default=10,
                       help='top number of stock scores to show, defaults to 10')
    parser.add_argument('-d', '--dfs', action='store_const', const=False, default=True,
                       help='Set if using HDFS filesystem rather than local (True)')
    args = parser.parse_args()
    
    #Read in ini file
    config = configparser.ConfigParser()
    config.read('./stockpicker.ini')
    localeStr = config['stats']['locale']
    locale.setlocale( locale.LC_ALL, localeStr) 
    storeConfig = config['store']
    
    stock='BHP.L'
    #For stock, read prices, prices is a dict with key of timestamp and values of (min,max)
    prices = getStockPricesSaved(storeConfig, stock, args.dfs)['dailyPrices']
    fvalWithFreq = getPriceChangeFrequency(prices)

    print (fvalWithFreq)
    plt.bar(*zip(*fvalWithFreq))