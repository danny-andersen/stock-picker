def normaliseValue(value, min, max):
    if value > max:
        score = max / (max - min)
    elif value < min:
        score = min / (max - min)
    else:
        score = (value - min) / (max - min)
    return score


def calcScore(metrics):
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
    if (metrics['netAssetValuePrice'] > currentPrice): score += 1
    if (metrics['assetSharePriceValue'] > currentPrice): score += 1
    if (metrics['lowerSharePriceValue'] > currentPrice): score += 1
    scorePerc = 100 * score / 9
    scoreStats = dict()
    scoreStats['incomeScorePerc'] = incomeScorePerc
    scoreStats['scorePerc'] = scorePerc
    
    return scoreStats
