import csv
from io import StringIO
import os
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from datetime import datetime, timedelta, date, timezone
from statistics import mean
from saveRetreiveFiles import getAllStockTxnSaved, saveStockTransactions, saveStockLedger
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

SECONDS_IN_YEAR = 365.25*24*3600

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
    qty: float = 0.0
    price: Decimal = Decimal(0.0)
    debit: Decimal = Decimal(0.0)
    credit: Decimal = Decimal(0.0)
    type: str = 'Unknown'

@dataclass_json
@dataclass
class Security:
    #An investment security held in an Account
    date: datetime
    symbol: str
    desc: str
    qty: int = 0
    currentPrice: Decimal = Decimal(0.0)
    avgBuyPrice: Decimal = Decimal(0.0)
    bookCost: Decimal = Decimal(0.0)
    gain: Decimal = Decimal(0.0)

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
        return self.calcTotalGain(datetime.now(timezone.utc), sellPrice)

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

def processStockTxns(config, securities, stock, txns):
    totalCosts = 0
    totalStock = 0
    totalShareInvested = 0 
    capitalGainPerYear = dict() #total capital gain realised by tax year
    # realGainPerYear = dict()
    avgShareCost = 0
    invCostsPerYear = dict()  #By tax year
    dividendPerYear = dict() #By tax year
    dividendYieldPerYear = dict() #By tax year
    # adjIinvestmentHistory = list()
    fullIinvestmentHistory = list()
    reinvestDiviTotal = 0
    totalCashInvested = 0
    stockName = None
    stockSymbol = None
    stockSedol = None
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
            if txn.date < firstBought:
                firstBought = txn.date
            totalStock += txn.qty
            priceIncCosts = txn.debit / txn.qty
            if (txn.price != 0):
                costs = txn.debit - (txn.qty * txn.price)
            else:
                costs = 0
            totalShareInvested += txn.debit
            #If its a reinvested dividend, need to take this off total gain
            if (lastDiviDate 
                    and (txn.date - lastDiviDate < timedelta(days=7))
                    and (lastDivi >= txn.debit)):
                reinvestDiviTotal += txn.debit
            else:
                totalCashInvested += txn.debit
            avgShareCost = totalShareInvested / totalStock
            invCostsPerYear[taxYear] = invCostsPerYear.get(taxYear, 0) + costs #Stamp duty and charges
            totalCosts += costs
            # adjIinvestmentHistory.append(CapitalGain(date = txn.date, qty = txn.qty, price = txn.price))
            fullIinvestmentHistory.append(CapitalGain(date = txn.date, qty = txn.qty, price = priceIncCosts))
        elif type == SELL:
            priceIncCosts = txn.credit / txn.qty
            gain = (priceIncCosts - avgShareCost) * txn.qty #CGT uses average purchase price at time of selling
            capitalGainPerYear[taxYear] = capitalGainPerYear.get(taxYear, 0) + gain
            totalStock -= txn.qty
            if (txn.price != 0):
                totalCosts += (txn.price * txn.qty) - txn.credit #Diff between what should have received vs what was credited
            totalShareInvested = avgShareCost * totalStock  
            fullIinvestmentHistory.append(CapitalGain(date = txn.date, qty = txn.qty, price = priceIncCosts, transaction = SELL))
            #Use last stock buy txn
            # stockSold = txn.qty
            # while stockSold > 0:
            #     if len(adjIinvestmentHistory) > 0:
            #         buyTxn = adjIinvestmentHistory.pop()
            #         (gain, stockSold, avgYield) = buyTxn.calcGain(txn.date, txn.price, stockSold)
            #         realGainPerYear[taxYear] = realGainPerYear.get(taxYear, 0) + gain
            #         if (stockSold < 0):
            #             #Put any remaining stock back into stock history
            #             adjIinvestmentHistory.append(CapitalGain(date = buyTxn.date, qty = -stockSold, price = buyTxn.price))
            #     else:
            #         print(f"{stock}: Run out of investment history to sell {txn.qty} shares - remaining: {stockSold}\n")
            #         break
        elif type == DIVIDEND:
            divi = txn.credit
            lastDivi = divi
            lastDiviDate = txn.date
            totalDivi += divi
            dividendPerYear[taxYear] = dividendPerYear.get(taxYear, 0) + divi
            yearYield = dividendYieldPerYear.get(taxYear, 0) + 100*float(divi/totalShareInvested)
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
                # - totalCosts
                # + (sum(dividendPerYear.values()) if len(dividendYieldPerYear) > 0 else 0) \
    if details['totalGain'] and totalCashInvested:
        details['totalGainPerc'] = 100.0 * float(details['totalGain']/totalCashInvested)
        details['avgGainPerYear'] = float(details['totalGain'])/yearsHeld
        details['avgGainPerYearPerc'] = details['totalGainPerc']/yearsHeld
    else:
        details['totalGainPerc'] = 0
        details['avgGainPerYear'] = 0
        details['avgGainPerYearPerc'] = 0
    
    return details

def summarisePerformance(account, accountSummary, stockSummary):
    totalShareInvested = 0
    totalCashInvested = 0
    totalDiviReInvested = 0
    totalCosts = 0
    totalPaperGainForTax = 0
    totalGain = 0
    # totalRealisedGain = dict()
    totalRealisedForTaxGain = dict()
    totalDealingCosts = dict()
    totalDivi = dict()
    aggInvestedByYear = dict()
    totalDiviYieldByYear = dict()
    totalMarketValue = 0
    for details in stockSummary.values():
        totalMarketValue += details.get('marketValue', 0)
        totalCashInvested += details['totalCashInvested']
        totalDiviReInvested += details['totalDiviReinvested']
        totalShareInvested += details['totalInvested']
        totalCosts += details['dealingCosts']
        totalPaperGainForTax += details.get('totalPaperCGT', 0)
        totalGain += details.get('totalGain', 0)
        # for year,gain in details['realisedCapitalGainPerYear'].items():
        #     totalRealisedGain[year] = totalRealisedGain.get(year, 0) + gain
        for year,gain in details['realisedCapitalGainForTaxPerYear'].items():
            totalRealisedForTaxGain[year] = totalRealisedForTaxGain.get(year, 0) + gain
        for year,costs in details['dealingCostsPerYear'].items():
            totalDealingCosts[year] = totalDealingCosts.get(year, 0) + costs
        for year,divi in details['dividendsPerYear'].items():
            totalDivi[year] = totalDivi.get(year, 0) + divi

    startYear = accountSummary['dateOpened']
    endYear = datetime.now(timezone.utc) + timedelta(days=365) # Make sure we have this tax year
    procYear = startYear
    sumInvested = 0
    while procYear < endYear:
        year = getTaxYear(procYear)
        sumInvested += accountSummary['cashInPerYear'].get(year, 0) - accountSummary['cashOutPerYear'].get(year,0)
        aggInvestedByYear[year] = sumInvested
        if sumInvested > 0:
            if totalDivi.get(year, 0) != 0:
                totalDiviYieldByYear[year] = 100*totalDivi.get(year, 0) / sumInvested
        procYear += timedelta(days=365)

    #Add in monthly fees trading account that is taken by DD since Jan 2020
    if (account.lower() == 'trading'):
        feesDirectDebitDate = datetime(year=2020, month=1, day=14)
        endTime = datetime.now()
        increment = timedelta(days=30)
        feesPerYear = accountSummary['feesPerYear']
        while (feesDirectDebitDate < endTime):
            taxYear = getTaxYear(feesDirectDebitDate)
            feesPerYear[taxYear] = feesPerYear.get(taxYear, 0) + Decimal(9.99)
            feesDirectDebitDate += increment 

    accountSummary['totalInvested'] = sum(accountSummary['cashInPerYear'].values()) - sum(accountSummary['cashOutPerYear'].values())
    accountSummary['totalCashInvested'] = totalCashInvested
    accountSummary['totalFees'] = sum(accountSummary['feesPerYear'].values())
    accountSummary['totalDiviReInvested'] = totalDiviReInvested
    accountSummary['totalMarketValue'] = totalMarketValue
    accountSummary['totalInvestedInSecurities'] = totalShareInvested
    accountSummary['totalDealingCosts'] = totalCosts
    accountSummary['totalPaperGainForTax'] = totalPaperGainForTax
    accountSummary['totalPaperGainForTaxPerc'] = 100.0 * float(totalPaperGainForTax / totalShareInvested)
    accountSummary['totalRealisedGain'] = sum(totalRealisedForTaxGain.values())
    accountSummary['totalGainFromInvestments'] = totalMarketValue - accountSummary['totalInvested']
    accountSummary['totalGainFromInvPerc'] = 100 * float(accountSummary['totalGainFromInvestments'] / totalShareInvested)
    accountSummary['totalGain'] = totalGain - accountSummary['totalFees']  #Dealing costs are wrapped up in stock price received
    accountSummary['totalGainPerc'] = 100 * float(accountSummary['totalGain'] / totalShareInvested)
    accountSummary['aggInvestedByYear'] = aggInvestedByYear
    accountSummary['realisedGainForTaxPerYear']  = totalRealisedForTaxGain
    accountSummary['dealingCostsPerYear']  = totalDealingCosts
    accountSummary['dividendsPerYear']  = totalDivi
    accountSummary['dividendYieldPerYear']  = totalDiviYieldByYear

def priceStrToDec(strValue):
    valStr = strValue.replace('£', '')
    valStr = valStr.replace(',', '')
    if ('p' in valStr):
        valStr = valStr.replace('p', '')
        val = Decimal(valStr) / 100
    else:
        val = Decimal(valStr)
    return val

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

    #List portfolio directory for account portfolio files
    dirEntries = os.scandir('portfolio/')
    portfolioFiles = list()
    for dirEntry in dirEntries:
        if (dirEntry.is_file() and not dirEntry.name.startswith('.') and '.csv' in dirEntry.name):
            portfolioFiles.append((dirEntry.name, datetime.fromtimestamp(dirEntry.stat().st_mtime)))

    #Process each portfolio file
    securitiesByAccount = dict()
    for (portfolioFile, mtime) in portfolioFiles:
        print(f"Processing portfolio file {portfolioFile}")
        # Extract account name
        accountName = portfolioFile.split('_')[0]
        securitiesBySymbol = dict()
        securitiesByAccount[accountName] = securitiesBySymbol
        with open('portfolio/' + portfolioFile) as csvFile:
            csv_reader = csv.DictReader(csvFile)
            for row in csv_reader:
                if (row['\ufeff"Symbol"'].strip() != ''):
                    security = Security (
                        date = mtime,
                        symbol = row['\ufeff"Symbol"'].strip().replace('..','.'),
                        qty = 0 if row['Qty'] == '' else float(row['Qty']),
                        currentPrice = 0 if row['Price'] == '' else priceStrToDec(row['Price']),
                        desc = row['Description'],
                        avgBuyPrice = row['Average Price'],
                        bookCost = row['Book Cost'],
                        gain = row['Gain']
                    )
                    securitiesBySymbol[security.symbol] = security

    #List transactions directory for account history files
    dirEntries = os.scandir('transactions/')
    txnFiles = list()
    for dirEntry in dirEntries:
        if (dirEntry.is_file() and not dirEntry.name.startswith('.') and '.csv' in dirEntry.name):
            txnFiles.append(dirEntry.name)

    #For each trading and isa account file, read in transactions into list
    for txnFile in txnFiles:
        print(f"Processing txn file {txnFile}")
        # Extract account name
        accountName = txnFile.split('_')[0]
        stockList = stockListByAcc.get(accountName, None)
        if (not stockList):
            stockList = dict()
            stockListByAcc[accountName] = stockList

        with open('transactions/' + txnFile) as csvFile:
            csv_reader = csv.DictReader(csvFile)
            for row in csv_reader:
                if (len(row['Date'])) == 8: 
                    fmt = "%d/%m/%y"
                else:
                    fmt = "%d/%m/%Y"
                txn = Transaction(
                    date = datetime.strptime(row['Date'], fmt).replace(tzinfo=timezone.utc),
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
                desc = txn.desc.lower() 
                if (txn.isin != ''):
                    #Map any old isin to new isin
                    txn.isin = isinMapping.get(txn.isin, txn.isin)
                if (desc.startswith('div') 
                        or desc.startswith('equalisation')
                        or 'optional dividend' in desc):
                    txn.type = DIVIDEND
                elif (txn.isin.startswith('No stock') or (txn.isin == '' and txn.symbol == '')):
                    txn.isin = NONE
                    if (desc.startswith("debit card") 
                            or 'subscription' in desc 
                            or desc.startswith("trf")
                            or 'transfer' in desc
                            or 'cashback' in desc
                            or 'lump sum' in desc):
                        if (txn.credit != 0):
                            txn.type = CASH_IN
                        else:
                            txn.type = CASH_OUT 
                    elif (('fee' in desc
                            or 'payment' in desc)
                                and txn.debit != 0):
                        txn.type = FEES
                    elif ('refund' in desc
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
                # Update existing transactions - this will overwrite a transaction if it already exists
                # And so allows updates to existing transactions to be made
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
                stockLedger[stock] = processStockTxns(config, securitiesByAccount[account], stock, txns) 
            else:
                processAccountTxns(accountSummary, txns)
        #Summarise transactions and yields etc
        summarisePerformance(account, accountSummary, stockLedger)
        #Save to Dropbox file
        saveStockLedger(configStore, account, accountSummary, stockLedger)
