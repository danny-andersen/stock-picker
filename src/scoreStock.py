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
    (score, total) = getScore(metrics['diviCover'], 0, 1.5, score, total)
    (score, total) = getScore(metrics['interestCover'], 0, 1.2, score, total)
    (score, total) = getScore(metrics['currentRatio'], 0, 1.2, score, total)
    (score, total) = getScore(metrics['fcfForecastSlope'], 0, 1, score, total)
    (score, total) = getScore(metrics['currentYield'], 2.5, 4, score, total)
    (score, total) = getScore(metrics['forwardYield'], 2.5, 4, score, total)
    if (total > 0):
        incomeScorePerc = 100 * score / total
    else:
        incomeScorePerc = 0
    score = 0 # Reset score - score stock separate from income
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
        if (altmann > 3.0): # Financially sound company
            score += 2 #Skew scoring by Altmann
        elif (altmann > 2.5):
            score += 1 
        elif (altmann < 1.8):
            score -= 2 #Potentially bankrupt stock.....
    fscore = metrics['piotroskiFScore']
    if (fscore != 0):
        if (fscore >= 8.0):
            score += 2 #Skew scoring by Piotroski F Score
        elif (fscore >=6 ):
            score += 1
        elif (fscore < 3):
            score -= 1 #Potentially Problem stock
    gearing = metrics['gearing']
    if (gearing != 0):
        if (gearing < 0.5):
            score += 1
        elif (gearing > 1.0):
            score -= 1
    scorePerc = 100 * score / 11
    scoreStats = dict()
    scoreStats['stock'] = stock
    scoreStats['incomeScore'] = incomeScorePerc
    scoreStats['stockScore'] = scorePerc
    scoreStats['altmannZ'] = altmann
    scoreStats['piotroskiFScore'] = fscore
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

def calcPiotroskiFScore(stock, info, metrics):
    score = 0
    latestIncome = info['incomeStatement']         
    if (latestIncome['Net income'] > 0): score +=1

    ocf = info['operatingCashFlow']
    sortedocf = sorted(ocf, key=lambda d: d[0])
    latestOcf = sortedocf[len(sortedocf)-1][1]
    if (latestOcf > 0): score +=1
    if (latestOcf > latestIncome['Net income']): score +=1
    
    stats = info['stats']
    if (stats['Return on Assets'] > 0): score +=1
    
    currentBalanceSheet = info['balanceSheet']
    prevYearBalanceSheet = info['prevYearBalanceSheet']
    if (currentBalanceSheet['Total non-current liabilities'] < prevYearBalanceSheet['Total non-current liabilities']): score +=1
    prevLiabilities = prevYearBalanceSheet['Total current liabilities']
    if (prevLiabilities != 0):
        prevCurrentRatio = prevYearBalanceSheet['Total Current Assets'] / prevLiabilities
        if (metrics['currentRatio'] > prevCurrentRatio): score += 1
    
    score += 1 #Assume no change in shares issued in past year (dont have the data)

    latestGM = metrics['preTaxProfitPerc']
    latestTurnover = latestIncome.get('Total revenue', 0)
    prevIncome = info['prevYearIncomeStatement']         
    prevTurnover = prevIncome.get('Total revenue', 0)
    if (prevTurnover > 0):
        prevGM = prevIncome.get('Pre-tax profit', 0) / prevTurnover
    else:
        prevGM = 0
    if (latestGM >= prevGM): score += 1

    latestAssets = currentBalanceSheet.get('Total Assets', 0)
    if (latestAssets > 0):
        latestAssetTurnover = latestTurnover / latestAssets
    else:
        latestAssetTurnover = 0
    prevAssets = prevYearBalanceSheet.get('Total Assets', 0)
    if (prevAssets > 0):
        prevAssetTurnover = prevTurnover / prevAssets
    else:
        prevAssetTurnover = 0
    if (latestAssetTurnover >= prevAssetTurnover): score += 1

    metrics['piotroskiFScore'] = score

