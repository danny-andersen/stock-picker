def normaliseValue(value, min, max):
    if value is None:
        score = 0
    elif value > max:
        score = 1
    elif value < min:
        score = 0
    else:
        score = (value - min) / (max - min)
    return score


def calcScore(stock, metrics):
    #Determine score between 0 - 1
    score = 0
    score += normaliseValue(metrics['diviCover'], 0, 1.5)
    score += normaliseValue(metrics['interestCover'], 0, 1.2)
    score += normaliseValue(metrics['currentRatio'], 0, 1.2)
    score += normaliseValue(metrics['fcfForecastSlope'], 0, 1)
    score += normaliseValue(metrics['currentYield'], 2.5, 4)
    score += normaliseValue(metrics['forwardYield'], 2.5, 4)
    incomeScorePerc = 100 * score / 6
    currentPrice = metrics['currentPrice']
    if (metrics['breakUpPrice'] > currentPrice): 
        score += 1
    elif (metrics['breakUpPrice'] < 0):
        score -= 1 # penalise stock that has negative break up value, i.e. net asset value less intangibles
    if (metrics['assetSharePriceValue'] > currentPrice): score += 1
    if (metrics['lowerSharePriceValue'] > currentPrice): score += 1
    scorePerc = 100 * score / 9
    scoreStats = dict()
    scoreStats['stock'] = stock
    scoreStats['incomeScorePerc'] = incomeScorePerc
    scoreStats['scorePerc'] = scorePerc
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
    return scoreStats
