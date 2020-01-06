import sys
sys.path.insert(0, './src')
from datetime import datetime, timedelta
import numpy as np
from statistics import stdev, median, mean
import math

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

def getPriceSamples(priceTimeStamps, prices, startDate, endDate):
    #print ([datetime.fromtimestamp(t) for t in priceTimeStamps])
    #Find prices for previous year
    #startYear = startDate.year
    if (priceTimeStamps[0] > startDate.timestamp()):
        #Dont have enough samples
        sampleDate = datetime.fromtimestamp(priceTimeStamps[0])
    incDate = timedelta(days=1)
    priceSamples = []
    priceTimes = []
    index = 0
    sampleDate = startDate
    while sampleDate <= endDate:
        try:
            lastIndex = index
            index = findNearestSample(index, priceTimeStamps, sampleDate.timestamp())
            if (lastIndex != index):
                #print (f"Looking for {sampleDate.timestamp()} found {priceTimeStamps[index]}")
                ts = priceTimeStamps[index]
                priceTimes.append(datetime.fromtimestamp(ts))
                (max, min) = prices[ts]
                priceSamples.append((max+min)/2)
        except KeyError:
            print(f"Missing day {sampleDate}")
        sampleDate += incDate
    return (priceTimes, priceSamples)

def calcPriceStatisticsForPeriod(prices, start, end):
    stats = dict()
    if (prices):
        ts = sorted(prices)
        (times, samples) = getPriceSamples(ts, prices, start, end)
        stats['stddevPrice'] = stdev(samples)/100
        stats['medianPrice'] = median(samples)/100
        stats['avgPrice'] = mean(samples)/100
        stats['maxPrice'] = max(samples)/100
        stats['minPrice'] = min(samples)/100
    else:
        stats['stddevPrice'] = 0
        stats['medianPrice'] = 0
        stats['avgPrice'] = 0
        stats['maxPrice'] = 0
        stats['minPrice'] = 0
    return (stats)
    
def getPriceChangeFrequency(priceTimeStamps, prices):
    endDate = datetime.now()
    startDate = endDate - (3*timedelta(days=365)) #Do previous 3 years if available
    (priceTimes, priceSamples) = getPriceSamples(priceTimeStamps, prices, startDate, endDate)
    #Do an FFT of the daily prices
    N = len(priceSamples)
    samples = np.array(priceSamples)
#    window = np.blackman(len(values))
#    freq = np.fft.fft(samples*window)
    freq = np.fft.fft(samples)
    #Each Frequency step in returned array = fs / N
    #In our case fs = 1 per day
    #0 component is the DC bias component (ignore)
    #First half of samples are positive frequencies, the second half negative
    #Get absolute values of amplitude of positive frequencies using convenience function
    fval = np.abs(freq[1:(N//2)])
    #Get phase angle values
    fPhase = np.angle(freq[1:(N//2)], deg=True)
#    dcVal = np.abs(freq[0])
#    print (dcVal)
#    plt.plot(fval)
#    plt.show()
    #Inverse of frequencies is the day period
    days = 1/(np.fft.fftfreq(N)[1:])
    #Generate tuple of (index, amplitude value) sorted by descending value of frequency
    sortedfval = [i for i in sorted(enumerate(fval[1:]), key=lambda x:x[1], reverse=True )]
    maxVal = sortedfval[0][1]
    #Generate tuple of (day period, relative amplitude, phase), where value is relative to the first frequency
    fvalWithFreq = [(days[i[0]],i[1]/maxVal, fPhase[i[0]]) for i in sortedfval]
    return (priceTimes, priceSamples, fvalWithFreq)

def calcWeightedSlope(dateToCalcFrom, priceTimeStamps, prices, fvalF):
    totalWeightedSlope = 0
    totalWeightedPeriodForward = 0
    percOfPeriodToBaseForecast = 20
    totalWeights = 0
    secsPerDay = 1440 * 60
    for i in range(2,10):
        period = fvalF[i][0]
        weight = fvalF[i][1]
        if (period == 0 or weight == 0):
            continue
        #angle = fvalF[i][2]
        start = dateToCalcFrom - timedelta(days=period)  #forward project from period
        end = dateToCalcFrom - timedelta(days=period*(1-percOfPeriodToBaseForecast/100)) #20% of period forward
        (priceTimes, priceSamples) = getPriceSamples(priceTimeStamps, prices, start, end)
        if (priceSamples and len(priceSamples) > 0):
            startts = start.timestamp()
            times = [int((t.timestamp() - startts)/secsPerDay) for t in priceTimes]
            x = np.array(times)
            y = np.array(priceSamples)
            X = x - x.mean()
            Y = y - y.mean()
            slope = X.dot(Y) / X.dot(X)
            weightedSlope = slope * weight
            weightedPeriodForward = weight * period * (1-percOfPeriodToBaseForecast/100)
            #print (f"Period {i} {period:0.1f} days: weightedSlope {weightedSlope*100:0.2f}% slope {slope:.2f} phase {angle:.2f} deg")
            #print (f"(Price period {start} to {end} for freq period {period:0.0F} of weight {weight:0.2f}, slope is {slope}, weighted: {weightedSlope}")
            if (not math.isnan(weightedSlope)):
                totalWeightedSlope += weightedSlope
                totalWeightedPeriodForward += weightedPeriodForward
                totalWeights += weight
    if (totalWeights != 0):
        avgSlope = totalWeightedSlope / totalWeights
        avgPeriod = totalWeightedPeriodForward / totalWeights
    else:
        avgSlope = 0
        avgPeriod = 0
    return (avgSlope, avgPeriod)

def getWeightedSlope(prices):
    priceTimeStamps = sorted(prices)
    (priceTimes, priceSamples, fvalWithFreq) = getPriceChangeFrequency(priceTimeStamps, prices)
    totalWeightedSlope = calcWeightedSlope(datetime.now(), priceTimeStamps, prices, fvalWithFreq)
    return totalWeightedSlope
    
