def normaliseValue(value, min, max):
    if (value is None or value == 0):
        score = -1
    elif value >= max:
        score = 1
    elif value <= min:
        score = 0
    else:
        score = (value - min) / (max - min)
    return score

def getScore(value, min, max, score, total):
    norm = normaliseValue(value, min, max)
    if (norm != -1):
        score += norm
        total += 1
    return (score, total)
    
def calcScore(stock, metrics):
    #Determine score between 0 - 1
    score = 0
    total = 0
    (score, total) = getScore(metrics['interestCover'], 0, 1.2, score, total)
    (score, total) = getScore(metrics['currentRatio'], 0, 1.2, score, total)
    (score, total) = getScore(metrics['fcfForecastSlope'], 0, 1, score, total)
    (score, total) = getScore(metrics['currentYield'], 2.5, 4, score, total)
    (score, total) = getScore(metrics['forwardYield'], 2.5, 4, score, total)
    if (total > 0):
        incomeScorePerc = 100 * score / total
    else:
        incomeScorePerc = 0
    currentPrice = metrics['currentPrice']
    if (metrics['bookPrice'] > currentPrice): 
        score += 1
    elif (metrics['bookPrice'] < 0):
        score -= 1 # penalise stock that has negative break up value, i.e. net asset value less intangibles
    if (metrics['assetSharePriceValue'] > currentPrice): score += 1
    if (metrics['lowerSharePriceValue'] > currentPrice): score += 1
    if (metrics['intrinsicWithIntangiblesPrice'] > currentPrice): score += 1
    if (metrics['priceToBook'] < 1): score += 1
    if (metrics['returnOnEquity'] > 11 or metrics['returnOnCapitalEmployed'] > 11):
        #Stock is beating the market average
        score += 1
    altmann = metrics['altmannZ']
    if (altmann != 0):
        if (altmann > 3.0):
            score += 1 #Artificially increase % for a good altmann by not increasing perfect score count
        elif (altmann < 1.8):
            score -= 2 #Potentially bankrupt stock.....
    gearing = metrics['gearing']
    if (gearing != 0):
        if (gearing < 0.5):
            score += 1
        elif (gearing > 1.0):
            score -= 1
    scorePerc = 100 * score / 13
    scoreStats = dict()
    scoreStats['stock'] = stock
    scoreStats['incomeScore'] = incomeScorePerc
    scoreStats['stockScore'] = scorePerc
    scoreStats['altmannZ'] = altmann
    scoreStats['currentYield'] = metrics['currentYield']
    scoreStats['avgYield'] = metrics['avgYield']
    #One tick per 20%
    numTicks = int(metrics['weightedSlopePerc']/20)
    if (numTicks > 0):
        tick = '+'
    else:
        tick = '-'
    buySell = ''
    if (abs(numTicks) > 10): 
        numTicks=10
    for i in range(0,abs(numTicks)):
        buySell += tick
    scoreStats['buySignal'] = buySell
    scoreStats['buySignalDays'] = metrics['slopeForecastPeriodDays']
    return scoreStats
