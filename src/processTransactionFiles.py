import csv
from io import StringIO
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from statistics import mean
from saveRetreiveFiles import getStockInfoSaved, getStockTxnSaved, saveStockTransactions, getStockPricesSaved, saveStockLedger
from processStock import calcPriceData
from getStockLedgerStr import getTaxYear

CASH_IN = 'Cash in'
CASH_OUT = 'Cash out'
SELL = 'Sell'
BUY = 'Buy'
DIVIDEND = 'Dividend'
FEES = 'Fees'
NONE = 'No stock'

@dataclass
class Transaction:
    #An investment transaction of some sort
    date: datetime
    ref: str
    stock: str
    sedol: str
    isin: str
    desc: str
    qty: int = 0
    price: float = 0.0
    debit: float = 0.0
    credit: float = 0.0

@dataclass
class CapitalGain:
    #Buy and sell history of stock
    date: datetime
    qty: int
    price: float
    transaction: str = BUY
    def calcGain(self, sellDate, sellPrice, sellQty):
        timeHeld = sellDate - self.date
        gain = (sellPrice - self.price) * sellQty
        yld = 100*gain/self.price
        avgYieldPerYear = yld / (timeHeld.days / 365)
        return (gain, sellQty - self.qty, avgYieldPerYear)
    def calcTotalGain(self, sellDate, sellPrice):
        return self.calcGain(sellDate, sellPrice, self.qty)
    def calcTotalCurrentGain(self, sellDate, sellPrice):
        return self.calcTotalGain(datetime.now(), sellPrice)

def getExistingTxns(config, accountName, stockList, stock):
    txns = stockList.get(stock, None)
    if (not txns):
        txns = getStockTxnSaved(config, accountName, stock)
        if (not txns or len(txns) == 0):
            #Check those saved against current stocklist
            txns = stockList.get(stock, None)
            if (not txns):
                txns = list()
        stockList[stock] = txns
    return txns

def processAccountTxns(summary, txns):
    cashInPerYear = dict()
    cashOutPerYear = dict()
    feesPerYear = dict()
    dateOpened = datetime.now()
    for txn in txns:
        type = txn.type
        taxYear = getTaxYear(txn.date)
        if (txn.date < dateOpened):
            dateOpened = txn.date
        if type == CASH_IN:
            cashInPerYear = cashInPerYear.get(taxYear, 0) + txn.credit
        elif type == CASH_OUT:
            cashOutPerYear = cashOutPerYear.get(taxYear, 0) + txn.debit
        elif type == FEES:
            feesPerYear = feesPerYear.get(taxYear, 0) + txn.debit
    summary['dateOpened'] = dateOpened
    summary['cashInPerYear'] = cashInPerYear
    summary['cashOutPerYear'] = cashOutPerYear
    summary['feesPerYear'] = feesPerYear
    return summary

def processStockTxns(config, stock, txns):
    totalCosts = 0
    totalStock = 0
    totalShareInvested = 0 
    capitalGainPerYear = dict() #total capital gain realised by tax year
    realGainPerYear = dict()
    avgShareCost = 0
    invCostsPerYear = dict()  #By tax year
    dividendPerYear = dict() #By tax year
    dividendYieldPerYear = dict() #By tax year
    adjIinvestmentHistory = list[CapitalGain]
    fullIinvestmentHistory = list[CapitalGain]
    stockName = None
    firstBought = datetime.now()
    for txn in txns:
        type = txn.type
        taxYear = getTaxYear(txn.date)
        if type == BUY:
            if not stockName:
                stockName = txn.desc
            if (txn.date < firstBought):
                firstBought = txn.date
            totalStock += txn.qty
            shareValue = txn.price * txn.qty
            totalShareInvested += shareValue
            avgShareCost = totalShareInvested / totalStock
            invCostsPerYear[taxYear] = invCostsPerYear.get(taxYear, 0) + txn.debit - shareValue #Stamp duty and charges
            adjIinvestmentHistory.append(CapitalGain(date = txn.date, qty = txn.qty, price = txn.price))
            fullIinvestmentHistory.append(CapitalGain(date = txn.date, qty = txn.qty, price = txn.price))
        elif type == SELL:
            gain = (txn.price - avgShareCost) * txn.qty #CGT uses average purchase price at time of selling
            fullIinvestmentHistory.append(CapitalGain(date = txn.date, qty = txn.qty, price = txn.price, transaction = SELL))
            capitalGainPerYear[taxYear] = capitalGainPerYear.get(taxYear, 0) + gain
            totalStock -= txn.qty
            shareValue = txn.price * txn.qty
            totalShareInvested -= shareValue
            totalCosts += shareValue - txn.credit #Diff between what should have received vs what was credited
            #Use last stock buy txn
            stockSold = txn.qty
            while stockSold > 0:
                buyTxn = adjIinvestmentHistory.pop()
                (gain, stockSold, avgYield) = buyTxn.calcYield(txn.date, txn.price, stockSold)
                realGainPerYear[taxYear] = realGainPerYear.get(taxYear, 0) + gain
                if (stockSold < 0):
                    #Put any remaining stock back into stock history
                    adjIinvestmentHistory.append(CapitalGain(date = buyTxn.date, qty = -stockSold, price = buyTxn.price))
        elif type == DIVIDEND:
            divi = txn.credit
            yearYield = dividendYieldPerYear.get(taxYear, 0) + divi/totalShareInvested
            dividendPerYear[taxYear] = ((dividendPerYear.get(taxYear, 0) + divi), (yearYield))
            dividendYieldPerYear[taxYear] = yearYield
    #From remaining stock history workout paper gain
    totalPaperGain = 0
    info = getStockInfoSaved(config, stock)
    metrics = dict()
    prices = getStockPricesSaved(config, stock)
    calcPriceData(metrics, info, prices['dailyPrices'])
    latestPriceDate = metrics['currentPriceDate']
    currentPrice = metrics['currentPrice']

    for hist in adjIinvestmentHistory:
        (gain, stockSold, avgYield) = hist.calcTotalYield(currentPrice)
        totalPaperGain += gain
    remainingCGT = (currentPrice * totalStock) - (avgShareCost * totalStock)
    details = dict()
    details['stockSymbol'] = stock
    details['stockName'] = stockName
    details['stockHeld'] = totalStock
    details['heldSince'] = firstBought
    details['totalInvested'] = totalShareInvested
    details['investmentHistory'] = asdict(fullIinvestmentHistory)
    details['realisedCapitalGainPerYear'] = realGainPerYear
    details['capitalGainForTaxPerYear'] = capitalGainPerYear
    details['dealingCostsPerYear'] = invCostsPerYear
    details['avgSharePrice'] = avgShareCost
    details['dealingCosts'] = totalCosts
    details['totalPaperGain'] = totalPaperGain
    details['currentSharePrice'] = currentPrice
    details['priceDate'] = latestPriceDate
    details['dividendsPerYear'] = dividendPerYear
    details['dividendYieldPerYear'] = dividendYieldPerYear
    details['averageYearlyDiviYield'] = mean(dividendYieldPerYear.values)
    details['totalGain'] = totalPaperGain + sum(dividendPerYear.values) + sum(realGainPerYear.values) - totalCosts
    return details

def summarisePerformance(accountSummary, stockSummary):
    totalShareInvested = 0
    totalCosts = 0
    totalPaperGain = 0
    totalGain = 0
    totalYearlyGain = dict()
    totalCapitalGain = dict()
    totalDealingCosts = dict()
    totalDivi = dict()
    aggInvestedByYear = dict()
    totalDiviYieldByYear = dict()
    for details in stockSummary:
        totalShareInvested += details['totalInvested']
        totalCosts += details['dealingCosts']
        totalPaperGain += details['totalPaperGain']
        totalGain += details['totalGain']
        for year,gain in details['realisedCapitalGainPerYear'].items():
            totalYearlyGain[year] = totalYearlyGain.get(year, 0) + gain
        for year,gain in details['capitalGainForTaxPerYear'].items():
            totalCapitalGain[year] = totalCapitalGain.get(year, 0) + gain
        for year,costs in details['dealingCostsPerYear'].items():
            totalDealingCosts[year] = totalDealingCosts.get(year, 0) + costs
        for year,divi in details['dividendsPerYear'].items():
            totalDivi[year] = totalDivi.get(year, 0) + divi
    byYear = accountSummary['cashInPerYear'].keys().sort()
    sumInvested = 0
    for year in byYear:
        sumInvested += accountSummary['cashInPerYear'].get(year, 0)
        aggInvestedByYear[year] = sumInvested
        if sumInvested > 0:
            totalDiviYieldByYear[year] = totalDivi.get(year, 0)

    accountSummary['totalInvested'] = sum(accountSummary['cashInPerYear'].values) - sum(accountSummary['cashOutPerYear'].values)
    accountSummary['totalFees'] = sum(accountSummary['feesPerYear'].values)
    accountSummary['totalInvestedInSecurities'] = totalShareInvested
    accountSummary['totalDealingCosts'] = totalCosts
    accountSummary['totalPaperGain'] = totalPaperGain
    accountSummary['totalGain'] = totalGain
    accountSummary['aggInvestedByYear'] = aggInvestedByYear
    accountSummary['realisedGainPerYear']  = totalYearlyGain
    accountSummary['realisedCapitalTaxGainPerYear']  = totalCapitalGain
    accountSummary['dealingCostsPerYear']  = totalDealingCosts
    accountSummary['dividendsPerYear']  = totalDivi
    accountSummary['dividendYieldPerYear']  = totalDiviYieldByYear

def processTxnFiles(config):
    stockListByAcc = dict() #Dict of stocks by accountname, stocks are a dict of stock txns keyed by symbol
    changedStockTxnsByAcc = dict() #Dict keyed by account with Set of stocks whose transactions have been appended to and so need to be saved back to HDFS
    #List transactions directory for account history files
    txnFiles = os.listdir('transactions/')

    #For each trading and isa account file, read in transactions into list
    for txnFile in txnFiles:
        # Extract account name
        accountName = txnFile.split('_')[0]
        stockList = stockListByAcc.get(accountName, None)
        if (not stockList):
            stockList = dict()
            stockListByAcc[accountName] = stockList

        lineCount = 0
        with open('transactions/' + txnFile) as csvFile:
            csv_reader = csv.DictReader(csvFile)
            line_count = 0
            for row in csv_reader:
                if (lineCount != 0):
                    txn = Transaction(
                        date = datetime.strptime(row['Date'], "%d/%m/%y"),
                        ref = row['Reference'],
                        stock = row['Symbol'],
                        sedol = row['Sedol'],
                        isin = row['ISIN'],
                        qty = 0 if row['Quantity'] == '' else row['Quantity'],
                        price = 0 if row['Price'] == '' else row['Price'],
                        desc = row['Description'],
                        debit = 0 if row['Debit'] == '' else row['Debit'],
                        credit = 0 if row['Credit'] == '' else row['Credit']
                        )
                    if (txn.sedol == '' and txn.stock == ''):
                        txn.stock = NONE
                        if (txn.desc.startsWith("Debit card")):
                            if (txn.credit != 0):
                                txnType = CASH_IN
                            else:
                                txnType = CASH_OUT 
                        elif (txn.debit != 0):
                            txnType == FEES
                        else:
                            print(f"Unknown transaction type {txn}")
                    elif (txn.qty != ''):
                        if (txn.credit != 0): 
                            txn.type = SELL
                        else:
                            txn.type = BUY
                    elif (txn.desc.startswith('Div')):
                        txn.type = DIVIDEND
                    else:
                        print(f"Unknown transaction type {txn}")
                    # Retrieve transactions
                    existingTxns = getExistingTxns(config, accountName, stockList, txn.stock)
                    txnKey = f"{accountName}-{txn.date}-{txn.ref}" 
                    # check transaction in current list, if not add
                    if (not any(existingTxn.get(txnKey, None) for existingTxn in existingTxns)):
                        #Add new transaction to existing list
                        existingTxns.append(txn)
                        changed = changedStockTxnsByAcc.get(accountName, None)
                        if not changed:
                            changed = set()
                            changedStockTxnsByAcc = changed
                        changed.add(txn.stock)

    #Save any changed transactions
    for account, stocks in changedStockTxnsByAcc.items():
        for stock in stocks:
            #Sort transactions by date
            txns = stockListByAcc[account][stock]
            stockListByAcc[account][stock] = txns.sort(key= lambda txn: txn.date)
            saveStockTransactions(config, accountName, stock, stockListByAcc[account][stock])
    
    #For each account process each stock transactions to work out cash flow and share ledger
    totalCosts = 0
    for account, stocks in stockListByAcc.items():
        stockLedger = dict()
        accountSummary = dict()
        for stock, txns in stocks:
            if (stock != NONE):
                stockLedger[stock] = processStockTxns(config, stock, txns) 
            else:
                processAccountTxns(accountSummary, txns)
        #Summarise transactions and yields etc
        summarisePerformance(accountSummary, stockLedger)
        #Save to Dropbox file
        saveStockLedger(config, account, accountSummary, stockLedger)
