
from decimal import Decimal
from datetime import datetime, timedelta, date, timezone
from statistics import mean

from getLatestPrices import getAndSaveStockPrices
from processStock import calcPriceData
from getStockLedgerStr import getTaxYear
from transactionDefs import *

def processAccountTxns(summary, txns):
    cashInPerYear = dict()
    cashOutPerYear = dict()
    feesPerYear = dict()
    # dateOpened = datetime.now().replace(tzinfo=None)
    dateOpened = datetime.now(timezone.utc)
    for txn in txns:
        type = txn.type
        taxYear = getTaxYear(txn.date)
        # txn.date = txn.date.replace(tzinfo=None) #Make the date naive if not already
        if (txn.date < dateOpened):
            dateOpened = txn.date
        if type == CASH_IN:
            cashInPerYear[taxYear] = cashInPerYear.get(taxYear, 0) + txn.credit
        elif type == CASH_OUT:
            cashOutPerYear[taxYear] = cashOutPerYear.get(taxYear, 0) + txn.debit
        elif type == FEES:
            feesPerYear[taxYear] = feesPerYear.get(taxYear, 0) + txn.debit
        elif type == REFUND:
            feesPerYear[taxYear] = feesPerYear.get(taxYear, 0) - txn.credit
    summary['dateOpened'] = dateOpened
    summary['cashInPerYear'] = cashInPerYear
    summary['cashOutPerYear'] = cashOutPerYear
    summary['feesPerYear'] = feesPerYear
    return summary

def processStockTxns(config, securities, stocks, stock):
    txns = stocks[stock]
    totalCosts = 0
    totalStock = 0
    totalShareInvested = 0 
    capitalGainPerYear = dict() #total capital gain realised by tax year
    avgShareCost = 0
    invCostsPerYear = dict()  #By tax year
    dividendPerYear = dict() #By tax year
    dividendYieldPerYear = dict() #By tax year
    fullIinvestmentHistory = list()
    reinvestDiviTotal = 0
    totalCashInvested = 0
    stockName = None
    stockSymbol = None
    stockSedol = None
    stockisin = None
    lastDiviDate = None
    lastDivi = 0
    totalDivi = 0
    # firstBought = datetime.now().replace(tzinfo=None)
    firstBought = datetime.now(timezone.utc)
    for txn in txns:
        type = txn.type
        # txn.date = txn.date.replace(tzinfo=None) #Make the date naive if not already
        taxYear = getTaxYear(txn.date)
        if type == BUY:
            if not stockName:
                stockName = txn.desc
            if not stockSymbol and txn.symbol != '':
                if txn.symbol.endswith('.'):
                    stockSymbol = txn.symbol + 'L'
                else:
                    stockSymbol = txn.symbol + '.L'
            if not stockSedol and txn.sedol != '':
                stockSedol = txn.sedol
            if not stockisin == None and txn.isin != '':
                stockisin = txn.isin
            if txn.date < firstBought:
                firstBought = txn.date
            totalStock += txn.qty
            debit = convertToSterling(stocks.get(txn.debitCurrency, None), txn, txn.debit)
            priceIncCosts =  debit / txn.qty
            if (txn.price != 0):
                costs = debit - (txn.qty * txn.price)
            else:
                costs = 0
            totalShareInvested += debit
            #If its a reinvested dividend, need to take this off total gain
            if (lastDiviDate 
                    and (txn.date - lastDiviDate < timedelta(days=7))
                    and (lastDivi >= debit)):
                reinvestDiviTotal += debit
            else:
                totalCashInvested += debit
            avgShareCost = totalShareInvested / totalStock
            invCostsPerYear[taxYear] = invCostsPerYear.get(taxYear, 0) + costs #Stamp duty and charges
            totalCosts += costs
            # adjIinvestmentHistory.append(CapitalGain(date = txn.date, qty = txn.qty, price = txn.price))
            fullIinvestmentHistory.append(CapitalGain(date = txn.date, qty = txn.qty, price = priceIncCosts))
        elif type == SELL:
            if not stockName:
                if (stock.isin == USD or stock.isin == EUR):
                    stockName = stock.isin
                    stockSymbol = stock.isin
            credit = convertToSterling(stocks.get(txn.creditCurrency, None), txn, txn.credit)
            priceIncCosts = credit / txn.qty
            gain = (priceIncCosts - avgShareCost) * txn.qty #CGT uses average purchase price at time of selling
            capitalGainPerYear[taxYear] = capitalGainPerYear.get(taxYear, 0) + gain
            totalStock -= txn.qty
            if (txn.price != 0):
                totalCosts += (txn.price * txn.qty) - credit #Diff between what should have received vs what was credited
            totalShareInvested = avgShareCost * totalStock  
            fullIinvestmentHistory.append(CapitalGain(date = txn.date, qty = txn.qty, price = priceIncCosts, transaction = SELL))
        elif type == DIVIDEND:
            divi = convertToSterling(stocks.get(txn.creditCurrency, None), txn, txn.credit)
            lastDivi = divi
            lastDiviDate = txn.date
            totalDivi += divi
            dividendPerYear[taxYear] = dividendPerYear.get(taxYear, 0) + divi
            if totalShareInvested > 0.01:
                yearYield = dividendYieldPerYear.get(taxYear, 0) + 100*float(divi/totalShareInvested)
            else:
                yearYield = 0
            dividendYieldPerYear[taxYear] = yearYield
    #From remaining stock history workout paper gain
    # totalPaperGain = 0
    details = dict()
    # if (stockSymbol):
    #     #Its a share or ETF
    #     details['stockSymbol'] = stockSymbol
    #     (prices, retrieveDate) = getAndSaveStockPrices(config, stockSymbol, "AlphaAdvantage")
    # else:
    #     #Its a fund
    #     details['stockSymbol'] = stock
    #     (prices, retrieveDate) = getAndSaveStockPrices(config, stock, "TrustNet")
    # currentPrice = None
    # if (prices):
    #     dailyPrices = prices['dailyPrices']
    #     if (len(dailyPrices) > 0):
    #         priceDatesSorted = sorted(dailyPrices)
    #         latestPriceDateStamp = priceDatesSorted[len(priceDatesSorted)-1]
    #         latestPriceDate = date.fromtimestamp(latestPriceDateStamp)
    #         (low, high) = dailyPrices[latestPriceDateStamp]
    #         # Use the average of the last price range we have
    #         currentPricePence = Decimal(high + low)/2
    #         #Price usually in pence - calculate in pounds
    #         currentPrice = currentPricePence/100
    #         if (avgShareCost > currentPrice * 8):
    #             #Price was already in pounds
    #             currentPrice = currentPricePence
    if (stockSymbol):
        #Its a share or ETF
        details['stockSymbol'] = stockSymbol
        security = securities.get(stockSymbol, None)
    else:
        #Its a fund
        details['stockSymbol'] = stockSedol
        security = securities.get(stockSedol, None)
    if security:
        currentPrice = security.currentPrice
        # for hist in adjIinvestmentHistory:
        #     (gain, stockSold, avgYield) = hist.calcTotalCurrentGain(currentPrice)
        #     totalPaperGain += gain
        remainingCGT = (currentPrice * totalStock) - (avgShareCost * totalStock)
    else:
        # totalPaperGain = 0
        remainingCGT = 0

    yearsHeld = float((datetime.now(timezone.utc) - firstBought).total_seconds())/SECONDS_IN_YEAR
    details['sedol'] = stockSedol
    details['isin'] = stockisin
    details['stockName'] = stockName
    details['stockHeld'] = totalStock
    details['heldSince'] = firstBought
    details['totalCashInvested'] = totalCashInvested
    details['totalDiviReinvested'] = reinvestDiviTotal
    details['totalInvested'] = totalShareInvested
    details['realisedCapitalGainForTaxPerYear'] = capitalGainPerYear
    # details['realisedCapitalGainPerYear'] = realGainPerYear
    details['investmentHistory'] = fullIinvestmentHistory
    if security:
        details['marketValue'] = currentPrice * totalStock
        details['currentSharePrice'] = currentPrice
        details['priceDate'] = security.date
        # details['totalPaperGain'] = totalPaperGain
        details['totalPaperCGT'] = remainingCGT
        if (remainingCGT):
            # details['totalPaperGainPerc'] = 100.0 * float(totalPaperGain / totalShareInvested)
            details['totalPaperCGTPerc'] = 100.0 * float(remainingCGT / totalShareInvested)
        else:
            # details['totalPaperGainPerc'] = 0
            details['totalPaperCGTPerc'] = 0
    details['dealingCostsPerYear'] = invCostsPerYear
    details['avgSharePrice'] = avgShareCost
    details['dealingCosts'] = totalCosts
    details['dividendsPerYear'] = dividendPerYear
    details['averageYearlyDivi'] = mean(dividendPerYear.values()) if len(dividendPerYear) > 0 else 0
    details['dividendYieldPerYear'] = dividendYieldPerYear
    details['averageYearlyDiviYield'] = mean(dividendYieldPerYear.values()) if len(dividendYieldPerYear) > 0 else 0
    details['totalDividends'] = totalDivi
    realisedCapitalGain = (sum(capitalGainPerYear.values()) if len(capitalGainPerYear) > 0 else 0)
    if security:
        details['totalGain'] = details['marketValue'] - totalCashInvested + realisedCapitalGain + totalDivi
    else:
        details['totalGain'] = remainingCGT \
                + totalDivi \
                + realisedCapitalGain
    if details['totalGain'] and totalCashInvested:
        details['totalGainPerc'] = 100.0 * float(details['totalGain']/totalCashInvested)
        details['avgGainPerYear'] = float(details['totalGain'])/yearsHeld
        details['avgGainPerYearPerc'] = details['totalGainPerc']/yearsHeld
    else:
        details['totalGainPerc'] = 0
        details['avgGainPerYear'] = 0
        details['avgGainPerYearPerc'] = 0
    
    return details
