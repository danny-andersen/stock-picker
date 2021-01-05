from calcStatistics import calculateDCF
from datetime import datetime, timedelta
import locale
from retreiveStockInfo import getStockInfo
from scoreStock import calcScore
from saveRetreiveFiles import getStockInfoSaved, saveStockInfo, saveStockMetrics, getStockPricesSaved, saveStockPrices, saveStringToDropbox
from alphaAdvantage import getLatestDailyPrices, getAllDailyPrices, checkPrices
from checkStockInfo import checkStockInfo, isStockInfoBetter, countInfoNones
from printResults import getResultsStr
from pricePeriod import getWeightedSlope, calcPriceStatisticsForPeriod


def processStockSpark(bcConfig, stock, local):
    return processStock(bcConfig.value, stock, local)


def processStock(config, stock, local):
    print(f"Processing stock: {stock}")
    # Set config
    version = config['stats'].getfloat('version')
    maxPriceAgeDays = config['stats'].getint('maxPriceAgeDays')
    statsMaxAgeDays = config['stats'].getint('statsMaxAgeDays')
    apiKey = config['keys']['alhaAdvantageApiKey']
    maxNonesInInfo = config['stats'].getint('maxNonesInInfo')
    storeConfig = config['store']
    localeStr = config['stats']['locale']
    locale.setlocale(locale.LC_ALL, localeStr)

    # Check to see if stock info needs to be updated
    # Read info from file
    info = getStockInfoSaved(storeConfig, stock, local)
    currentInfo = info
    newInfoReqd = False
    if (info):
        infoAge = datetime.now() - info['metadata']['storedDate']
        if (infoAge.days > statsMaxAgeDays or info['metadata']['version'] < version):
            newInfoReqd = True
            print(
                f"{stock}: Stored info v{info['metadata']['version']} needs to be updated to v{version}")
            info = None
    else:
        print(f"{stock}: No info stored")
    # Count if info has any nulls / nones,
    numNones = countInfoNones(info)
    # if it has more than a configured threshold then it will be replaced if what we get is any better
    if (numNones > maxNonesInInfo):
        print(f"{stock} Stored version has {numNones} nulls, which is more than the threshold ({maxNonesInInfo})")
        info = None
    if (info):
        # Check info is valid
        if (not checkStockInfo(info)):
            print(f"{stock}: Stored info invalid - retrying")
            info = None
    if (not info):
        print(f"{stock}: Retreiving latest stock info")
        info = getStockInfo(config, version, stock)
        if (info and ((newInfoReqd and checkStockInfo(info)) or isStockInfoBetter(currentInfo, info))):
            saveStockInfo(storeConfig, stock, info, local)
        else:
            print(f"{stock}: Retreived info incomplete")
            info = None
    prices = getStockPricesSaved(storeConfig, stock, local)
    if (prices):
        latestPriceDate = prices['endDate']
        howOld = datetime.now() - latestPriceDate
        if (howOld.days > maxPriceAgeDays):
            # If more than a week old, refresh
            print(f"{stock}: Refreshing prices")
            prices = getLatestDailyPrices(apiKey, stock, prices['dailyPrices'])
            saveStockPrices(storeConfig, stock, prices, local)
        else:
            # Check saved prices to determine if have any prices in pounds and convert
            # Note: This step can be removed once all old stock reprocessed
            checkedPrices = checkPrices(prices['dailyPrices'])
            if (checkedPrices):
                prices['dailyPrices'] = checkedPrices
                saveStockPrices(storeConfig, stock, prices, local)
    if (prices is None):
        # Get all daily prices to save
        print("f{stock}: Getting stock prices")
        prices = getAllDailyPrices(apiKey, stock)
        saveStockPrices(storeConfig, stock, prices, local)
    if (info and prices):
        metrics = processStockStats(info, prices['dailyPrices'])
        saveStockMetrics(storeConfig, stock, metrics, local)
        scores = calcScore(stock, metrics)
        resultStr = getResultsStr(stock, scores, metrics)
        saveStringToDropbox(
            storeConfig, "/details/{0}-results.txt".format(stock), resultStr)
    else:
        scores = None

    return scores

def getValue(dictHolder, name, default):
    val = dictHolder.get(name, default)
    if (not val): val = default
    return val

def processStockStats(info, dailyPrices):
    now = datetime.now()
    metrics = dict()
    metrics['infoDate'] = info['metadata']['storedDate']
    stockInfo = info['info']
    stats = info['stats']
    dividends = info['dividends']
    cashFlow = info['cashFlow']
    incomeStatement = info['incomeStatement']
    fcf = info['freeCashFlow']
    balanceSheet = info['balanceSheet']

    marketCap = getValue(stats, "Market Cap", None)
    if (not marketCap):
        marketCap = getValue(stockInfo, 'marketCap', 0)
    metrics['marketCap'] = marketCap
    noOfShares = getValue(stats, 'Shares Outstanding', None)
    if (not noOfShares):
        noOfShares = getValue(stockInfo, 'sharesOutstanding', 0)
    metrics['noOfShares'] = noOfShares
    totalWeightedSlope = 0
    if (len(dailyPrices) > 0):
        priceDatesSorted = sorted(dailyPrices)
        latestPriceDate = priceDatesSorted[len(priceDatesSorted)-1]
        metrics['currentPriceDate'] = datetime.fromtimestamp(latestPriceDate)
        (low, high) = dailyPrices[latestPriceDate]
        # Use the average of the last price range we have
        currentPrice = ((high + low)/2)/100
        if (noOfShares == 0):
            noOfShares = marketCap / currentPrice
        # Calculate slope as to whether price is increasing or decreasing
        # For each harmonic determine if the current price is at a local mimima x days ago +/- 10% days
        (totalWeightedSlope, forecastPeriod) = getWeightedSlope(dailyPrices)
        metrics['weightedSlopePerc'] = totalWeightedSlope * 100
        metrics['slopeForecastPeriodDays'] = forecastPeriod
    else:
        # Couldnt retreive the prices - use market cap
        if (noOfShares != 0):
            currentPrice = marketCap / noOfShares
        else:
            currentPrice = 0
        metrics['weightedSlopePerc'] = 0
    priceStats = calcPriceStatisticsForPeriod(
        dailyPrices, now-timedelta(days=364), now)
    metrics.update(priceStats)
    metrics['currentPrice'] = currentPrice

    forwardYield = getValue(stats, 'Forward Annual Dividend Yield', None)
    if (not forwardYield):
        forwardYield = getValue(stockInfo, 'dividendYield', 0)
    metrics['forwardYield'] = forwardYield

    # Determine this years dividend, average and max dividend
    # Calc dividend by year
    years = {}
    for divi in dividends:
        date = divi['date']
        dividend = divi['dividend']
        years[date.year] = dividend + years.get(date.year, 0)
    avgDividend = 0
    maxDividend = 0
    thisYearDividend = 0
    lastYearDividend = 0
    lastYear = now.year - 1
    for year in years:
        dividend = years[year]
        if (year == now.year):
            thisYearDividend = dividend
        if (year == lastYear):
            lastYearDividend = dividend
        if (maxDividend < dividend):
            maxDividend = dividend
        avgDividend += dividend
    if (thisYearDividend == 0):
        if (lastYearDividend):
            thisYearDividend = lastYearDividend
        else:
            thisYearDividend = forwardYield * currentPrice
    metrics['thisYearDividend'] = thisYearDividend
    if (len(years) != 0):
        avgDividend = avgDividend / len(years)
    else:
        avgDividend = thisYearDividend
    metrics['maxDividend'] = maxDividend
    metrics['avgDividend'] = avgDividend
    exDivDate = getValue(stats, 'Ex-Dividend Date', getValue(stockInfo, 'exDividendDate', None))
    metrics['exDivDate'] = exDivDate
    if (exDivDate):
        daysSinceExDiv = -(exDivDate - now).days
    else:
        daysSinceExDiv = 0
    metrics['daysSinceExDiv'] = daysSinceExDiv
    eps = getValue(stats, 'Diluted EPS', getValue(stats, "Revenue per share", getValue(stockInfo, 'trailingEps', 0)))
    metrics['eps'] = eps
    if (thisYearDividend != 0 and eps != 0):
        diviCover = eps / thisYearDividend
    else:
        diviCover = getValue(stockInfo,'diviCover', 0)
    metrics['diviCover'] = diviCover

    if (currentPrice > 0):
        metrics['currentYield'] = thisYearDividend/currentPrice
        metrics['maxYield'] = maxDividend/currentPrice
        metrics['avgYield'] = avgDividend/currentPrice
    else:
        metrics['currentYield'] = 0
        metrics['maxYield'] = 0
        metrics['avgYield'] = 0

    totalDebt = getValue(balanceSheet, 'Total non-current liabilities', 0)
    metrics['totalDebt'] = totalDebt
    totalEquity = getValue(balanceSheet, 'Stockholder Equity', 0)     # THIS IS THE WRONG STATISTIC - should be market cap
    totalCapital = totalDebt + totalEquity

    cf = cashFlow.get('Dividends paid', 0)
    costOfEquity = -cf
#    if (cf is None):
#        costOfEquity = 0
#    else:
#        costOfEquity = -locale.atoi(cf) * 1000
    if (totalEquity != 0):
        costOfEquityPerc = 100.0 * costOfEquity / \
            totalEquity  # Going to assume 0% dividend growth
    else:
        costOfEquityPerc = 0
    costOfDebt = incomeStatement.get('Interest expense', 0)
    if (totalDebt != 0):
        costOfDebtPerc = 100.0 * costOfDebt / totalDebt
    else:
        costOfDebtPerc = 0
    if (totalCapital != 0):
        wacc = (costOfEquityPerc * totalEquity / totalCapital) + \
            (costOfDebtPerc * totalDebt / totalCapital)
    else:
        wacc = 0
    metrics['wacc'] = wacc

    # Use to calculate DCF from FCF
    if (fcf and len(fcf) > 0):
        (dcf, error, fcfForecastSlope) = calculateDCF(fcf, wacc, 5)
    else:
        (dcf, error, fcfForecastSlope) = (0, 0, 0)
    metrics['discountedCashFlow'] = dcf
    metrics['dcfError'] = error
    metrics['fcfForecastSlope'] = fcfForecastSlope
    # Intrinsic value = plant equipment + current assets + 10 year DCF
    currentAssets = getValue(balanceSheet, 'Total Current Assets', 0)
    totalPlant = getValue(balanceSheet, 'Total Plant', 0)
    investments = getValue(balanceSheet, 'Investments', 0)
    inventory = getValue(balanceSheet, 'Inventory', 0)
    debtors = getValue(balanceSheet, 'Debtors', 0)
    # Dont include intangibles + goodwill
    assetValue = totalPlant + currentAssets
    currentLiabilities = getValue(balanceSheet,'Total current liabilities', 0)
    if (currentAssets == 0 or currentLiabilities == 0):
        currentRatio = stats.get('Current Ratio', 0)
    else:
        currentRatio = (currentAssets + debtors + inventory) / currentLiabilities
    metrics['currentRatio'] = currentRatio
    breakUpValue = assetValue - totalDebt - currentLiabilities
    metrics['breakUpValue'] = breakUpValue
    if (breakUpValue != 0):
        metrics['priceToBookNoIntangibles'] = marketCap / breakUpValue
    else:
        metrics['priceToBookNoIntangibles'] = 0
    intrinsicValue = breakUpValue + dcf
    metrics['intrinsicValue'] = intrinsicValue
    intrinsicValueRange = dcf*error
    metrics['intrinsicValueRange'] = intrinsicValueRange
    if (marketCap and totalDebt and currentAssets):
        # Price to buy the organisation
        enterpriseValue = (marketCap + totalDebt - currentAssets)
    else:
        enterpriseValue = stockInfo.get('enterpriseValue', 0)
    shareholderFunds = balanceSheet.get('Stockholder Equity', None)
    totalAssets = balanceSheet.get('Total Assets', None)
    if (not shareholderFunds):
        if (not totalAssets):
            shareholderFunds = stockInfo.get('navPrice', 0) * noOfShares
        else:
            shareholderFunds = totalAssets - totalDebt - currentLiabilities
    if (not totalAssets):
        if (totalDebt > 0 and currentLiabilities > 0):
            totalAssets = shareholderFunds + totalDebt + currentLiabilities
        else:
            totalAssets = 0
    metrics['netAssetValue'] = shareholderFunds
    netIncome = incomeStatement.get('Net income', None)
    if (not netIncome):
        netIncome = stockInfo.get('netIncomeToCommon', 0)
    if (shareholderFunds > 0):
        gearing = (enterpriseValue - marketCap) / shareholderFunds
        metrics['gearing'] = gearing
        if (netIncome != 0):
            metrics['returnOnEquity'] = 100*netIncome / shareholderFunds
        else:
            metrics['returnOnEquity'] = stockInfo.get('returnOnEquity', 0)
            netIncome = metrics['returnOnEquity'] * shareholderFunds / 100
        metrics['intrinsicWithIntangibles'] = shareholderFunds + dcf
        metrics['priceToBook'] = marketCap / shareholderFunds
    else:
        metrics['gearing'] = 0
        metrics['returnOnEquity'] = stockInfo.get('returnOnEquity', 0)
        metrics['intrinsicWithIntangibles'] = 0
        metrics['priceToBook'] = stockInfo.get('priceToBook', 0)
    if (totalAssets > 0):
        metrics['returnOnCapitalEmployed'] = 100 * \
            netIncome / (totalAssets - currentLiabilities)
        metrics['stockHolderEquityPerc'] = 100 * shareholderFunds / totalAssets
    else:
        metrics['returnOnCapitalEmployed'] = 0
        metrics['stockHolderEquityPerc'] = 0
    if (noOfShares != 0):
        lowerSharePriceValue = (
            intrinsicValue - intrinsicValueRange) / noOfShares
        upperSharePriceValue = (
            intrinsicValue + intrinsicValueRange) / noOfShares
        assetSharePriceValue = assetValue / noOfShares
        evSharePrice = enterpriseValue / noOfShares
        metrics['intrinsicWithIntangiblesPrice'] = metrics['intrinsicWithIntangibles'] / noOfShares
        metrics['breakUpPrice'] = breakUpValue / noOfShares  # Tangible assets - total liabilities
        # Balance sheet NAV = Total assets - total liabilities (which is shareholder funds)
        metrics['netAssetValuePrice'] = shareholderFunds / noOfShares
    else:
        lowerSharePriceValue = 0
        upperSharePriceValue = 0
        assetSharePriceValue = 0
        evSharePrice = 0
        metrics['intrinsicWithIntangiblesPrice'] = 0
        metrics['breakUpPrice'] = 0  # Tangible assets - total liabilities
        metrics['netAssetValuePrice'] = stockInfo.get('navPrice', 0)
    metrics['lowerSharePriceValue'] = lowerSharePriceValue
    metrics['upperSharePriceValue'] = upperSharePriceValue
    metrics['assetSharePriceValue'] = assetSharePriceValue
    metrics['enterpriseValue'] = enterpriseValue
    metrics['evSharePrice'] = evSharePrice
    operatingProfit = incomeStatement.get('Operating profit', 0)
    metrics['operatingProfit'] = operatingProfit
    if (costOfDebt != 0):
        metrics['interestCover'] = operatingProfit / costOfDebt
    else:
        metrics['interestCover'] = 0
    metrics['EPS'] = eps / 100
    if (eps != 0):
        pe = currentPrice / eps
    else:
        pe = stockInfo.get('forwardPE', 0)
    metrics['PEratio'] = pe
    metrics['PQratio'] = stockInfo.get('PQ Ratio', 0)
    tr = incomeStatement.get('Total revenue', 0)
    if (tr != 0):
        val = incomeStatement.get('Cost of revenue', 0)
        metrics['grossProfitPerc'] = 100 * (tr - val) / tr

        metrics['operatingProfitPerc'] = 100 * operatingProfit / tr

        val = incomeStatement.get('Central overhead', 0)
        metrics['overheadPerc'] = 100 * val / tr

        val = incomeStatement.get('Net income', None)
        if (not val):
            metrics['netProfitPerc'] = stockInfo.get('profitMargins', 0)
        else:
            metrics['netProfitPerc'] = 100 * val / tr
    else:
        metrics['grossProfitPerc'] = 0
        metrics['operatingProfitPerc'] = 0
        metrics['overheadPerc'] = 0
        metrics['netProfitPerc'] = stockInfo.get('profitMargins', 0)
    # Altmann Z score = 1.2A + 1.4B + 3.3C + 0.6D + 1.0E
    retainedEarnings = balanceSheet.get('Retained earnings', 0)
    if (totalAssets != 0 and currentAssets != 0 and \
            currentLiabilities != 0 and netIncome != 0 and \
            marketCap != 0 and totalDebt != 0 and tr != 0):
        # A = Working capital (Current assets - current liabilities) / Total assets
        A = (currentAssets - currentLiabilities) / totalAssets
        # B = Retained earnings / Total assets
        B = retainedEarnings / totalAssets
        # C = Net income  / total Assets
        C = netIncome / totalAssets
        # D = Capitilisation / total liabilities
        D = marketCap / (totalDebt + currentLiabilities)
        # E = Sales / total assets
        E = tr / totalAssets
        metrics['altmannZ'] = 1.2*A + 1.4*B + 3.3*C + 0.6*D + 1.0*E
    else:
        metrics['altmannZ'] = 0
    return metrics
