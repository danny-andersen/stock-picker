import csv
import os
from saveRetreiveFiles import getAllStockTxnSaved, saveStockTransactions, saveStockLedger
from getStockLedgerStr import getTaxYear
from transactionDefs import *
from processTransactions import processAccountTxns, processStockTxns

def summarisePerformance(account, accountSummary, stockSummary):
    totalShareInvested = 0
    totalCashInvested = 0
    totalDiviReInvested = 0
    totalCosts = 0
    totalPaperGainForTax = 0
    totalGain = 0
    totalRealisedForTaxGain = dict()
    totalDealingCosts = dict()
    totalDivi = dict()
    aggInvestedByYear = dict()
    totalDiviYieldByYear = dict()
    totalMarketValue = 0
    for details in stockSummary:
        totalMarketValue += details.get('marketValue', 0)
        totalCashInvested += details['totalCashInvested']
        totalDiviReInvested += details['totalDiviReinvested']
        totalShareInvested += details['totalInvested']
        totalCosts += details['dealingCosts']
        totalPaperGainForTax += details.get('totalPaperCGT', 0)
        totalGain += details.get('totalGain', 0)
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
                        desc = row['Description'],
                        avgBuyPrice = row['Average Price'],
                        bookCost = row['Book Cost'],
                        gain = row['Gain']
                    )
                    (security.currency, security.currentPrice) = priceStrToDec(row['Price'])
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
                    desc = row['Description'],
                    )
                (txn.priceCurrency, txn.price) = priceStrToDec(row['Price'])
                (txn.debitCurrency, txn.debit) = priceStrToDec(row['Debit'])
                (txn.creditCurrency, txn.credit) = priceStrToDec(row['Credit'])
                desc = txn.desc.lower() 
                if (txn.isin != ''):
                    #Map any old isin to new isin
                    txn.isin = isinMapping.get(txn.isin, txn.isin)
                if (desc.startswith('div') 
                        or desc.startswith('equalisation')
                        or desc.endswith('distribution')
                        or desc.endswith('rights')
                        or 'optional dividend' in desc):
                    txn.type = DIVIDEND
                elif (txn.isin.startswith(NONE) or (txn.isin == '' and txn.symbol == '')):
                    txn.isin = NONE
                    if (desc.startswith("debit card") 
                            or 'subscription' in desc 
                            or desc.startswith("trf")
                            or 'transfer' in desc
                            or 'cashback' in desc
                            or '(di)' in desc
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
    
                if (txn.type == BUY and (txn.isin == USD or txn.isin == EUR)):
                    #Ignore currency conversion BUY transactions 
                    continue
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
        sortedStocks = dict()
        for stock in stocks:
            #Sort all transactions by date first
            sortedStocks[stock] = sorted(list(stocks[stock].values()), key= lambda txn: txn.date)
        for stock in stocks:
            if (stock == USD or stock == EUR):
                #Dont process currency conversion txns
                continue
            if (stock != NONE):
                stockLedger[stock] = processStockTxns(config, securitiesByAccount[account], sortedStocks, stock) 
            else:
                processAccountTxns(accountSummary, sortedStocks[stock])
        #Summarise transactions and yields etc
        stockLedgerList = sorted(list(stockLedger.values()), key = lambda stock: stock['avgGainPerYearPerc'], reverse = True)
        summarisePerformance(account, accountSummary, stockLedgerList)
        #Save to Dropbox file
        saveStockLedger(configStore, account, accountSummary, stockLedgerList)
