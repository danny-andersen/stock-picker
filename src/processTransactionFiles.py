import csv
from io import StringIO
import os
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from datetime import datetime
from statistics import mean
from saveRetreiveFiles import getStockInfoSaved, getAllStockTxnSaved, getStockTxnSaved, saveStockTransactions, saveStockLedger
from getLatestPrices import getAndSaveStockPrices

from processStock import calcPriceData
from getStockLedgerStr import getTaxYear
from decimal import Decimal

CASH_IN = 'Cash in'
CASH_OUT = 'Cash out'
SELL = 'Sell'
BUY = 'Buy'
DIVIDEND = 'Dividend'
FEES = 'Fees'
REFUND ='Refund'
NONE = 'No stock'

@dataclass_json
@dataclass
class Transaction:
    #An investment transaction of some sort
    date: datetime
    ref: str
    symbol: str
    sedol: str
    isin: str
    desc: str
    qty: int = 0
    price: Decimal = Decimal(0.0)
    debit: Decimal = Decimal(0.0)
    credit: Decimal = Decimal(0.0)

@dataclass
class CapitalGain:
    #Buy and sell history of stock
    date: datetime
    qty: int
    price: Decimal
    transaction: str = BUY
    def calcGain(self, sellDate, sellPrice, sellQty):
        timeHeld = sellDate - self.date
        gain = (sellPrice - self.price) * sellQty
        yld = float(100*gain/self.price)
        avgYieldPerYear = yld / (timeHeld.days / 365)
        return (gain, sellQty - self.qty, avgYieldPerYear)
    def calcTotalGain(self, sellDate, sellPrice):
        return self.calcGain(sellDate, sellPrice, self.qty)
    def calcTotalCurrentGain(self, sellPrice):
        return self.calcTotalGain(datetime.now(), sellPrice)

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

def processStockTxns(config, stock, txns):
    configStore = config['store']
    totalCosts = 0
    totalStock = 0
    totalShareInvested = 0 
    capitalGainPerYear = dict() #total capital gain realised by tax year
    realGainPerYear = dict()
    avgShareCost = 0
    invCostsPerYear = dict()  #By tax year
    dividendPerYear = dict() #By tax year
    dividendYieldPerYear = dict() #By tax year
    adjIinvestmentHistory = list()
    fullIinvestmentHistory = list()
    stockName = None
    stockSymbol = None
    firstBought = datetime.now()
    for txn in txns:
        type = txn.type
        taxYear = getTaxYear(txn.date)
        if type == BUY:
            if not stockName:
                stockName = txn.desc
            if not stockSymbol and txn.symbol != '':
                stockSymbol = txn.symbol + '.L'
            if (txn.date < firstBought):
                firstBought = txn.date
            totalStock += txn.qty
            if (txn.price == 0):
                shareValue = txn.debit
                txn.price = txn.debit / txn.qty
            else:
                shareValue = txn.price * txn.qty
            totalShareInvested += shareValue
            avgShareCost = totalShareInvested / totalStock
            invCostsPerYear[taxYear] = invCostsPerYear.get(taxYear, 0) + txn.debit - shareValue #Stamp duty and charges
            adjIinvestmentHistory.append(CapitalGain(date = txn.date, qty = txn.qty, price = txn.price))
            fullIinvestmentHistory.append(CapitalGain(date = txn.date, qty = txn.qty, price = txn.price))
        elif type == SELL:
            gain = (txn.price - avgShareCost) * txn.qty #CGT uses average purchase price at time of selling
            capitalGainPerYear[taxYear] = capitalGainPerYear.get(taxYear, 0) + gain
            totalStock -= txn.qty
            if (txn.price == 0):
                shareValue = txn.credit
                txn.price = txn.credit / txn.qty
            else:
                shareValue = txn.price * txn.qty
            shareValue = txn.price * txn.qty
            totalShareInvested -= shareValue
            totalCosts += shareValue - txn.credit #Diff between what should have received vs what was credited
            fullIinvestmentHistory.append(CapitalGain(date = txn.date, qty = txn.qty, price = txn.price, transaction = SELL))
            #Use last stock buy txn
            stockSold = txn.qty
            while stockSold > 0:
                if len(adjIinvestmentHistory) > 0:
                    buyTxn = adjIinvestmentHistory.pop()
                    (gain, stockSold, avgYield) = buyTxn.calcGain(txn.date, txn.price, stockSold)
                    realGainPerYear[taxYear] = realGainPerYear.get(taxYear, 0) + gain
                    if (stockSold < 0):
                        #Put any remaining stock back into stock history
                        adjIinvestmentHistory.append(CapitalGain(date = buyTxn.date, qty = -stockSold, price = buyTxn.price))
                else:
                    print(f"{stock}: Run out of investment history to sell {txn.qty} shares - remaining: {stockSold}\n")
                    break
        elif type == DIVIDEND:
            divi = txn.credit
            yearYield = dividendYieldPerYear.get(taxYear, 0) + divi/totalShareInvested
            dividendPerYear[taxYear] = dividendPerYear.get(taxYear, 0) + divi
            dividendYieldPerYear[taxYear] = yearYield
    #From remaining stock history workout paper gain
    totalPaperGain = 0
    details = dict()
    if (stockSymbol):
        #Its a share or ETF
        details['stockSymbol'] = stockSymbol
        (prices, retrieveDate) = getAndSaveStockPrices(config, stockSymbol, "AlphaAdvantage")
    else:
        #Its a fund
        details['stockSymbol'] = stock
        (prices, retrieveDate) = getAndSaveStockPrices(config, stock, "TrustNet")
    currentPrice = None
    if (prices):
        dailyPrices = prices['dailyPrices']
        if (len(dailyPrices) > 0):
            priceDatesSorted = sorted(dailyPrices)
            latestPriceDateStamp = priceDatesSorted[len(priceDatesSorted)-1]
            latestPriceDate = datetime.fromtimestamp(latestPriceDateStamp)
            (low, high) = dailyPrices[latestPriceDateStamp]
            # Use the average of the last price range we have
            currentPricePence = Decimal(high + low)/2
            currentPrice = currentPricePence/100

    if currentPrice:
        for hist in adjIinvestmentHistory:
            (gain, stockSold, avgYield) = hist.calcTotalCurrentGain(currentPrice)
            totalPaperGain += gain
        remainingCGT = (currentPrice * totalStock) - (avgShareCost * totalStock)
    else:
        totalPaperGain = 0
        
    details['stockName'] = stockName
    details['stockHeld'] = totalStock
    details['heldSince'] = firstBought
    details['totalInvested'] = totalShareInvested
    details['capitalGainForTaxPerYear'] = capitalGainPerYear
    details['realisedCapitalGainPerYear'] = realGainPerYear
    details['investmentHistory'] = fullIinvestmentHistory
    if currentPrice:
        details['currentSharePrice'] = currentPrice
        details['priceDate'] = latestPriceDate
        details['totalPaperGain'] = totalPaperGain
    details['dealingCostsPerYear'] = invCostsPerYear
    details['avgSharePrice'] = avgShareCost
    details['dealingCosts'] = totalCosts
    details['dividendsPerYear'] = dividendPerYear
    details['dividendYieldPerYear'] = dividendYieldPerYear
    details['averageYearlyDiviYield'] = mean(dividendYieldPerYear.values()) if len(dividendYieldPerYear) > 0 else 0
    details['totalGain'] = totalPaperGain \
                + (sum(dividendPerYear.values()) if len(dividendYieldPerYear) > 0 else 0) \
                + (sum(realGainPerYear.values()) if len(realGainPerYear) > 0 else 0) \
                - totalCosts
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
    for details in stockSummary.values():
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
    years = list(accountSummary['cashInPerYear'].keys())
    years.sort()
    sumInvested = 0
    for year in years:
        sumInvested += accountSummary['cashInPerYear'].get(year, 0)
        aggInvestedByYear[year] = sumInvested
        if sumInvested > 0:
            totalDiviYieldByYear[year] = totalDivi.get(year, 0)

    accountSummary['totalInvested'] = sum(accountSummary['cashInPerYear'].values()) - sum(accountSummary['cashOutPerYear'].values())
    accountSummary['totalFees'] = sum(accountSummary['feesPerYear'].values())
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

def priceStrToDec(strValue):
    valStr = strValue.replace('£', '')
    valStr = valStr.replace(',', '')
    return Decimal(valStr)

def processTxnFiles(config):
    configStore = config['store']
    isinMapping = config['isinmappings']
    changedStockTxnsByAcc = dict() #Dict keyed by account with Set of stocks whose transactions have been appended to and so need to be saved back to HDFS

    #Dict of stocks by accountname, stocks are a dict of stock txns keyed by symbol
    stockListByAcc = getAllStockTxnSaved(configStore)
    #Need to convert transactions from json to dataclass 
    for acc in stockListByAcc.keys():
        for stock in stockListByAcc[acc].keys():
            for txKey, txn in stockListByAcc[acc][stock].items():
                stockListByAcc[acc][stock][txKey] = Transaction.from_json(txn)

    #List transactions directory for account history files
    dirEntries = os.scandir('transactions/')
    txnFiles = list()
    for dirEntry in dirEntries:
        if (dirEntry.is_file() and not dirEntry.name.startswith('.') and '.csv' in dirEntry.name):
            txnFiles.append(dirEntry.name)

    #For each trading and isa account file, read in transactions into list
    for txnFile in txnFiles:
        print(f"Processing file {txnFile}")
        # Extract account name
        accountName = txnFile.split('_')[0]
        stockList = stockListByAcc.get(accountName, None)
        if (not stockList):
            stockList = dict()
            stockListByAcc[accountName] = stockList

        with open('transactions/' + txnFile) as csvFile:
            csv_reader = csv.DictReader(csvFile)
            for row in csv_reader:
                txn = Transaction(
                    date = datetime.strptime(row['Date'], "%d/%m/%Y"),
                    ref = row['Reference'],
                    symbol = row['Symbol'].strip(),
                    sedol = row['Sedol'].strip(),
                    isin = row['ISIN'].strip(),
                    qty = 0 if row['Quantity'] == '' else int(row['Quantity']),
                    price = 0 if row['Price'] == '' else priceStrToDec(row['Price']),
                    desc = row['Description'],
                    debit = 0 if row['Debit'] == '' else priceStrToDec(row['Debit']),
                    credit = 0 if row['Credit'] == '' else priceStrToDec(row['Credit'])
                    )
                if (txn.isin != ''):
                    #Map any old isin to new isin
                    txn.isin = isinMapping.get(txn.isin, txn.isin)
                if (txn.desc.startswith('Div') 
                        or txn.desc.lower().startswith('equalisation')
                        or 'optional dividend' in txn.desc.lower()):
                    txn.type = DIVIDEND
                elif (txn.isin.startswith('No stock') or (txn.isin == '' and txn.symbol == '')):
                    txn.isin = NONE
                    if (txn.desc.startswith("Debit card") 
                            or 'subscription' in txn.desc.lower() 
                            or txn.desc.startswith("Trf")
                            or 'transfer' in txn.desc.lower()):
                        if (txn.credit != 0):
                            txn.type = CASH_IN
                        else:
                            txn.type = CASH_OUT 
                    elif (('fee' in txn.desc.lower()
                            or 'payment' in txn.desc.lower())
                                and txn.debit != 0):
                        txn.type = FEES
                    elif ('refund' in txn.desc.lower()
                            and txn.credit != 0):
                        txn.type = REFUND
                    else:
                        print(f"Unknown transaction type {txn}")
                elif (txn.qty != 0):
                    if (txn.credit != 0): 
                        txn.type = SELL
                    else:
                        txn.type = BUY
                else:
                    print(f"Unknown transaction type {txn}")
                # Retrieve transactions by stock symbol
                existingTxns = stockList.get(txn.isin, None)
                if (not existingTxns):
                    existingTxns = dict()
                    stockList[txn.isin] = existingTxns
                txnKey = f"{accountName}-{txn.date}-{txn.ref}" 
                # check transaction in current list, if not add
                if (not existingTxns.get(txnKey, None)):
                    #Add new transaction to existing list
                    existingTxns[txnKey] = txn
                    #Set stock to be saved
                    changed = changedStockTxnsByAcc.get(accountName, None)
                    if not changed:
                        changed = set()
                        changedStockTxnsByAcc[accountName] = changed
                    changed.add(txn.isin)

    #Extract all descriptions of BUY transactions
    #These are used to match Divi payments to stocks that have not ISIN
    txnByDesc = dict() #Dict of buy txns by their description - allows stock details to be found by description
    for acc in stockListByAcc.keys():
        for stock in stockListByAcc[acc].keys():
            for txKey in stockListByAcc[acc][stock].keys():
                tx = stockListByAcc[acc][stock][txKey]
                if (tx.type == BUY or tx.type == SELL) and tx.isin != '':
                    desc = tx.desc.replace(' ', '') #Strip out whitespace
                    txnByDesc[desc] = tx
    for acc in stockListByAcc.keys():
        for stock in stockListByAcc[acc].keys():
            stockTxns = stockListByAcc[acc][stock].copy()
            for txKey in stockTxns.keys():
                tx = stockListByAcc[acc][stock][txKey]
                if tx.type == DIVIDEND and tx.isin == '':
                    #Some Div payments dont have an isin - match with buy
                    for desc in txnByDesc.keys():
                        #Strip out whitespace to make comparison better
                        txdescStrip = tx.desc.replace(' ', '')
                        if (desc in txdescStrip):
                            buyTxn = txnByDesc[desc]
                            tx.isin = buyTxn.isin
                            tx.symbol = buyTxn.symbol
                            tx.sedol = buyTxn.sedol
                            #Need to add to existing stock txns
                            txns = stockListByAcc[acc][tx.isin]
                            txns[txKey] = tx
                            #Remove from current list
                            stockListByAcc[acc][stock].pop(txKey)
                            changed = changedStockTxnsByAcc.get(acc, None)
                            if not changed:
                                changed = set()
                                changedStockTxnsByAcc[accountName] = changed
                            changed.add(tx.isin)

    #Save any changed transactions
    for account, stocks in changedStockTxnsByAcc.items():
        for stock in stocks:
            noTxns = len(stockListByAcc[account][stock])
            if stock != '':
                print(f"{account} Updating transactions for {stock} with {noTxns} txns")
                txns = stockListByAcc[account][stock]
                jsonTxns = dict()
                for key, txn in txns.items():
                    jsonTxns[key] = txn.to_json() 
                saveStockTransactions(configStore, account, stock, jsonTxns)
            elif noTxns > 0:
                print(f"WARNING: {noTxns} Transactions have no stock name set")
            else:
                #Remove empty stock
                stockListByAcc[account].pop('')
    
    #For each account process each stock transactions to work out cash flow and share ledger
    totalCosts = 0
    for account, stocks in stockListByAcc.items():
        stockLedger = dict()
        accountSummary = dict()
        for stock in stocks:
            #Sort transactions by date
            txns = sorted(list(stocks[stock].values()), key= lambda txn: txn.date)
            if (stock != NONE):
                stockLedger[stock] = processStockTxns(config, stock, txns) 
            else:
                processAccountTxns(accountSummary, txns)
        #Summarise transactions and yields etc
        summarisePerformance(accountSummary, stockLedger)
        #Save to Dropbox file
        saveStockLedger(configStore, account, accountSummary, stockLedger)
