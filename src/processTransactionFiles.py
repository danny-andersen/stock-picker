import csv
import os
from saveRetreiveFiles import getAllStockTxnSaved, saveStringToDropbox, saveStockTransactions
from getStockLedgerStr import getTaxYear
from transactionDefs import *
from processTransactions import processAccountTxns, processStockTxns
from getStockLedgerStr import getStockLedgerStr, getAccountSummaryStr, getAccountSummaryHtml

def saveStockLedger(config, accountSummary: AccountSummary, stockLedgerList: list[SecurityDetails]):
    for details in stockLedgerList:
        detailsStr = getStockLedgerStr(details)
        saveStringToDropbox(config, f"/performance/{accountSummary.name}/{details.symbol}.txt", detailsStr)

def saveAccountSummary(config, accountSummary: AccountSummary, stockLedgerList: list[SecurityDetails]):
    accSummaryTxt = getAccountSummaryStr(accountSummary, stockLedgerList)
    saveStringToDropbox(config, f"/performance/{accountSummary.name}-Summary.txt", accSummaryTxt)
    accSummaryHtml = getAccountSummaryHtml(accountSummary, stockLedgerList)
    saveStringToDropbox(config, f"/performance/{accountSummary.name}-Summary.html", accSummaryHtml)

def summarisePerformance(accountSummary: AccountSummary, stockSummary: list[SecurityDetails], funds: dict[str, FundOverview]):
    totalShareInvested = Decimal(0.0)
    totalCashInvested = Decimal(0.0)
    totalDiviReInvested = Decimal(0.0)
    totalCosts = Decimal(0.0)
    totalPaperGainForTax = Decimal(0.0)
    totalGain = Decimal(0.0)
    totalRealisedForTaxGain = dict()
    totalDealingCosts = accountSummary.feesByYear
    totalDivi = accountSummary.dividendsByYear
    totalIncome = accountSummary.incomeByYear
    totalInterest = accountSummary.interestByYear
    fundTotals: dict[FundType, FundOverview] = dict()
    for typ in FundType:
        fundTotals[typ] = FundOverview("None", "None", typ)
    aggInvestedByYear = dict()
    totalDiviYieldByYear = dict()
    totalIncomeYieldByYear = dict()
    totalYieldByYear = dict()
    totalMarketValue = accountSummary.cashBalance
    totalByInstitution: dict[str, Decimal] = dict()
    detailsToProcess: list[SecurityDetails] = list()
    detailsToProcess.extend(stockSummary)
    for details in stockSummary:
        detailsToProcess.extend(details.historicHoldings)
    
    for details in detailsToProcess:
        value = float(details.marketValue())
        fund = details.fundOverview
        if (fund):
            if value == 0:
                value = float(details.totalInvested)
            fundType = fund.fundType
            if totalByInstitution.get(fund.institution, None):
               totalByInstitution[fund.institution] += Decimal(value)
            else:
               totalByInstitution[fund.institution] = Decimal(value) 
            fundTotals[fundType].alpha3Yr += fund.alpha3Yr * value
            fundTotals[fundType].americas += fund.americas * value
            fundTotals[fundType].americasEmerging += fund.americasEmerging * value
            fundTotals[fundType].asia += fund.asia * value
            fundTotals[fundType].asiaEmerging += fund.asiaEmerging * value
            fundTotals[fundType].beta3Yr += fund.beta3Yr * value
            fundTotals[fundType].cyclical += fund.cyclical * value
            fundTotals[fundType].defensive += fund.defensive * value
            fundTotals[fundType].uk += fund.uk * value
            fundTotals[fundType].europe += fund.europe * value
            fundTotals[fundType].europeEmerging += fund.europeEmerging * value
            fundTotals[fundType].fees += fund.fees * value
            fundTotals[fundType].maturity += fund.maturity * value
            fundTotals[fundType].return3Yr += fund.return3Yr * value
            fundTotals[fundType].return5Yr += fund.return5Yr * value
            fundTotals[fundType].sensitive += fund.sensitive * value
            fundTotals[fundType].sharpe3Yr += fund.sharpe3Yr * value
            fundTotals[fundType].stdDev3Yr += fund.stdDev3Yr * value
            fundTotals[fundType].totalValue += Decimal(value)
            fundTotals[fundType].totalInvested += details.totalInvested
            fundTotals[fundType].actualReturn += details.avgGainPerYearPerc() * value
            if (fund.alpha3Yr + fund.beta3Yr + fund.sharpe3Yr + fund.stdDev3Yr >0): fundTotals[fundType].totRiskVal += Decimal(value)
            if (fund.cyclical + fund.defensive + fund.sensitive >0): fundTotals[fundType].totDivVal += Decimal(value)
            if (fund.americasEmerging + fund.americas + fund.asia + fund.asiaEmerging + fund.uk + fund.europe + fund.europeEmerging >0): fundTotals[fundType].totGeoVal += Decimal(value)
            if (fund.maturity): fundTotals[fundType].totMatVal += Decimal(value)
        else:
            #Assume a share stock
            fundTotals[FundType.SHARE].totalValue += Decimal(value)
            fundTotals[FundType.SHARE].uk += 100 * value  #Assume all shares are UK based
            fundTotals[FundType.SHARE].totGeoVal += Decimal(value)
            fundTotals[FundType.SHARE].totalInvested += details.totalInvested
            fundTotals[FundType.SHARE].actualReturn += details.avgGainPerYearPerc() * value

        totalMarketValue += details.marketValue()
        totalCashInvested += details.cashInvested
        totalDiviReInvested += details.diviInvested
        totalShareInvested += details.totalInvested
        totalCosts += details.totalCosts
        totalPaperGainForTax += details.paperCGT()
        totalGain += details.totalGain()
        for year,gain in details.realisedCapitalGainByYear.items():
            totalRealisedForTaxGain[year] = totalRealisedForTaxGain.get(year, Decimal(0.0)) + gain
        for year,costs in details.costsByYear.items():
            totalDealingCosts[year] = totalDealingCosts.get(year, Decimal(0.0)) + costs
        if fund:
            if fund.isBondType:
                #A bond payment is treated as income for tax reasons
                for year,inc in details.dividendsByYear.items():
                    totalIncome[year] = totalIncome.get(year, Decimal(0.0)) + inc
            elif fund.isCashType:
                #Savings interest
                for year,inc in details.dividendsByYear.items():
                    totalInterest[year] = totalInterest.get(year, Decimal(0.0)) + inc
        if (not fund or not(fund.isBondType or fund.isCashType)):
            for year,divi in details.dividendsByYear.items():
                totalDivi[year] = totalDivi.get(year, Decimal(0.0)) + divi


    #If a cash account, add in to CASH type
    if accountSummary.name in funds.keys():
        fund = funds[accountSummary.name]
        fundType = fund.fundType
        if totalByInstitution.get(fund.institution, None):
            totalByInstitution[fund.institution] += Decimal(accountSummary.cashBalance)
        else:
            totalByInstitution[fund.institution] = Decimal(accountSummary.cashBalance) 
        fundTotals[fundType].totalValue += accountSummary.cashBalance
        fundTotals[fundType].totalInvested += accountSummary.totalInvested()
        fundTotals[fundType].uk += 100 * float(accountSummary.cashBalance)  #Assume UK based
        fundTotals[fundType].totGeoVal += accountSummary.cashBalance
        fundTotals[fundType].actualReturn += 100 * float(accountSummary.cashBalance - accountSummary.totalInvested()) #This is a %
        #If its a cash account, convert 
    else:
        #Add any cash balance of account to Cash fund
        fundType = FundType.CASH
        fundTotals[fundType].totalValue += accountSummary.cashBalance
        fundTotals[fundType].uk += 100 * float(accountSummary.cashBalance)  #Assume UK based
        fundTotals[fundType].totGeoVal += accountSummary.cashBalance

    for typ, fund in fundTotals.items():
        value = float(fund.totalValue)
        if value == 0:
            continue
        fund.alpha3Yr = fund.alpha3Yr / float(fund.totRiskVal) if fund.totRiskVal != 0 else 0.0
        fund.americas = fund.americas / float(fund.totGeoVal) if fund.totGeoVal != 0 else 0.0
        fund.americasEmerging = fund.americasEmerging / float(fund.totGeoVal) if fund.totGeoVal != 0 else 0.0
        fund.asia = fund.asia / float(fund.totGeoVal) if fund.totGeoVal != 0 else 0.0
        fund.asiaEmerging = fund.asiaEmerging / float(fund.totGeoVal) if fund.totGeoVal != 0 else 0.0
        fund.beta3Yr = fund.beta3Yr / float(fund.totRiskVal) if fund.totRiskVal != 0 else 0.0
        fund.cyclical = fund.cyclical / float(fund.totDivVal) if fund.totDivVal != 0 else 0.0
        fund.defensive = fund.defensive / float(fund.totDivVal) if fund.totDivVal != 0 else 0.0
        fund.uk = fund.uk / float(fund.totGeoVal) if fund.totGeoVal != 0 else 0.0
        fund.europe = fund.europe / float(fund.totGeoVal) if fund.totGeoVal != 0 else 0.0
        fund.europeEmerging = fund.europeEmerging / float(fund.totGeoVal) if fund.totGeoVal != 0 else 0.0
        fund.fees = fund.fees / value
        fund.maturity = fund.maturity / float(fund.totMatVal) if fund.totMatVal != 0 else 0.0
        fund.return3Yr = fund.return3Yr / value
        fund.return5Yr = fund.return5Yr / value
        fund.sensitive = fund.sensitive / float(fund.totDivVal) if fund.totDivVal != 0 else 0.0
        fund.sharpe3Yr = fund.sharpe3Yr / float(fund.totRiskVal) if fund.totRiskVal != 0 else 0.0
        fund.stdDev3Yr = fund.stdDev3Yr / float(fund.totRiskVal) if fund.totRiskVal != 0 else 0.0
        fund.actualReturn = fund.actualReturn / value

    startYear = accountSummary.dateOpened
    endYear = datetime.now(timezone.utc) + timedelta(days=365) # Make sure we have this tax year
    procYear = startYear
    sumInvested = 0
    while procYear < endYear:
        year = getTaxYear(procYear)
        sumInvested += accountSummary.cashInByYear.get(year, Decimal(0.0)) - accountSummary.cashOutByYear.get(year,Decimal(0.0))
        aggInvestedByYear[year] = sumInvested
        if sumInvested > 0:
            totYld = 0
            if totalDivi.get(year, Decimal(0.0)) != 0:
                yld = 100*totalDivi.get(year, Decimal(0.0)) / sumInvested
                totalDiviYieldByYear[year] = yld
                totYld += yld
            if totalIncome.get(year, Decimal(0.0)) != 0 or totalInterest.get(year, Decimal(0.0)) != 0:
                yld = 100*(totalIncome.get(year, Decimal(0.0)) + totalInterest.get(year, Decimal(0.0))) / sumInvested
                totalIncomeYieldByYear[year] = yld
                totYld += yld
            if totYld > 0:
                totalYieldByYear[year] = totYld

        procYear += timedelta(days=365)

    #Add in monthly fees trading account that is taken by DD since Jan 2020
    if (accountSummary.name.lower() == 'trading'):
        feesDirectDebitDate = datetime(year=2020, month=1, day=14)
        endTime = datetime.now()
        increment = timedelta(days=30)
        feesPerYear = accountSummary.feesByYear
        while (feesDirectDebitDate < endTime):
            taxYear = getTaxYear(feesDirectDebitDate)
            feesPerYear[taxYear] = feesPerYear.get(taxYear, Decimal(0.0)) + Decimal(9.99)
            feesDirectDebitDate += increment 

    accountSummary.totalCashInvested = totalCashInvested
    accountSummary.totalDiviReInvested = totalDiviReInvested
    accountSummary.totalMarketValue = totalMarketValue
    accountSummary.totalInvestedInSecurities = totalShareInvested
    accountSummary.totalDealingCosts = totalCosts
    accountSummary.totalPaperGainForTax = totalPaperGainForTax
    accountSummary.totalGain = totalGain
    accountSummary.aggInvestedByYear = aggInvestedByYear
    accountSummary.realisedGainForTaxByYear = totalRealisedForTaxGain
    accountSummary.dealingCostsByYear  = totalDealingCosts
    accountSummary.dividendsByYear = totalDivi
    accountSummary.dividendYieldByYear = totalDiviYieldByYear
    accountSummary.incomeByYear = totalIncome
    accountSummary.incomeYieldByYear = totalIncomeYieldByYear
    accountSummary.interestByYear = totalInterest
    accountSummary.totalYieldByYear = totalYieldByYear
    accountSummary.fundTotals = fundTotals
    accountSummary.totalByInstitution = totalByInstitution
def getPortfolioOverviews(config):
    #List portfolio directory for account portfolio files
    overviewDir = config['files']['portfoliosLocation']
    dirEntries = os.scandir(overviewDir)
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
    return securitiesByAccount

def getStoredTransactions(configStore):

    #Dict of stocks by accountname, stocks are a dict of stock txns keyed by symbol
    stockListByAcc = getAllStockTxnSaved(configStore)
    #Need to convert transactions from json to dataclass 
    for acc in stockListByAcc.keys():
        for stock in stockListByAcc[acc].keys():
            for txKey, txn in stockListByAcc[acc][stock].items():
                stockListByAcc[acc][stock][txKey] = Transaction.from_json(txn)
    return stockListByAcc

def processLatestTxnFiles(config, stockListByAcc):

    isinMapping = config['isinmappings']
    configStore = config['store']
    transDir = config['files']['transactionsLocation']
    changedStockTxnsByAcc = dict() #Dict keyed by account with Set of stocks whose transactions have been appended to and so need to be saved back to HDFS
    #List transactions directory for account history files
    allTxnsByAcc: dict[str,list[Transaction]] = dict()
    dirEntries = os.scandir(transDir)
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
                dt = row['Date']
                fmt = None
                if ('/' in dt):
                    if len(dt) == 8: 
                        fmt = "%d/%m/%y"
                    elif len(dt) == 10:
                        fmt = "%d/%m/%Y"
                elif ('-' in dt and len(dt) == 10):
                    fmt = "%Y-%m-%d"
                if (not fmt):
                    print(f"Unsupported date format: {dt}. Exiting!! \n")
                    exit()
                txn = Transaction(
                    date = datetime.strptime(row['Date'], fmt).replace(tzinfo=timezone.utc),
                    ref = row['Reference'],
                    symbol = row['Symbol'].strip(),
                    sedol = row['Sedol'].strip(),
                    isin = row['ISIN'].strip(),
                    qty = 0 if row['Quantity'] == '' else int(row['Quantity']),
                    desc = row['Description']
                    )
                (txn.priceCurrency, txn.price) = priceStrToDec(row['Price'])
                (txn.debitCurrency, txn.debit) = priceStrToDec(row['Debit'])
                (txn.creditCurrency, txn.credit) = priceStrToDec(row['Credit'])
                desc = txn.desc.lower() 
                if (txn.isin != ''):
                    #Map any old isin to new isin
                    txn.isin = isinMapping.get(txn.isin, txn.isin)
                if (txn.isin.startswith(NO_STOCK) or (txn.isin == '' and txn.symbol == '')):
                    txn.isin = NO_STOCK
                if (desc.startswith('div') 
                        or desc.startswith('equalisation')
                        or desc.endswith('distribution')
                        or desc.endswith('rights')
                        or 'final frac pay' in desc
                        or 'optional dividend' in desc):
                    txn.type = DIVIDEND
                elif (txn.qty != 0):
                    if (txn.credit != 0): 
                        txn.type = SELL
                    else:
                        txn.type = BUY
                elif (desc.startswith("debit card") 
                            or 'subscription' in desc 
                            or desc.startswith("trf")
                            or 'transfer' in desc
                            or 'faster payment' in desc
                            or 'cashback' in desc
                            # or '(di)' in desc
                            or 'lump sum' in desc):
                        if (txn.credit != 0):
                            txn.type = CASH_IN
                        else:
                            txn.type = CASH_OUT 
                elif 'interest' in desc:
                    txn.type = INTEREST
                elif (('fee' in desc
                        or 'payment' in desc)
                            and txn.debit != 0):
                    txn.type = FEES
                elif ('refund' in desc
                        and txn.credit != 0):
                    txn.type = REFUND
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
                txnKey = f"{accountName}-{txn.date}-{txn.ref}-{txn.debit}-{txn.credit}" 
                # Update existing transactions - this will overwrite a transaction if it already exists
                # And so allows updates to existing transactions to be made
                existingTxns[txnKey] = txn
                #Set stock to be saved
                changed = changedStockTxnsByAcc.get(accountName, None)
                if not changed:
                    changed = set()
                    changedStockTxnsByAcc[accountName] = changed
                changed.add(txn.isin)

    txnByDesc = dict() #Dict of buy txns by their description - allows stock details to be found by description
    for acc in stockListByAcc.keys():
        if (not allTxnsByAcc.get(acc, None)):
            allTxnsByAcc[acc] = list()
        txns = allTxnsByAcc[acc]
        for stock in stockListByAcc[acc].keys():
            for txKey in stockListByAcc[acc][stock].keys():
                tx = stockListByAcc[acc][stock][txKey]
                if (tx.type == BUY or tx.type == SELL) and tx.isin != '':
                    desc = tx.desc.replace(' ', '') #Strip out whitespace
                    txnByDesc[desc] = tx
                txns.append(tx)
                
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
    #Sort all transactions by date
    for acc in allTxnsByAcc.keys():
        allTxnsByAcc[acc] = sorted(allTxnsByAcc[acc], key= lambda txn: txn.date)
    return allTxnsByAcc

def getFundOverviews(config):
    fundsFile = config['files']['fundsOverview']

    fundOverviews: dict[str, FundOverview] = dict()
    #List portfolio directory for account portfolio files
    with open(fundsFile) as csvFile:
        csv_reader = csv.DictReader(csvFile)
        for row in csv_reader:
            isin = row['ISIN'].strip()
            if (isin != ''):
                fund = FundOverview (
                    isin = isin,
                    name = row['Name'],
                    fundType = FundType[row['Type'].strip().upper()],
                    institution= row['Institution'].strip()
                )
                fundOverviews[isin] = fund
                if (row['Income'].strip().lower() == 'inc'):
                    fund.income = True
                else:
                    fund.income = False
                fund.fees = float(row['Fees']) if row['Fees'].strip() != '' else float(0.0)
                fund.maturity = float(row['Maturity']) if row['Maturity'].strip() != '' else float(0.0)
                fund.risk = Risk[row['Risk'].strip().upper()]
                grade = row['Bond-Grade'].strip()
                if (grade != ''):
                    fund.bondGrade = BondGrade[grade]
                fund.americas = float(row['Americas']) if row['Americas'].strip() != '' else float(0.0)
                fund.americasEmerging = float(row['Americas-Emerging']) if row['Americas-Emerging'].strip() != '' else float(0.0)
                fund.uk = float(row['UK']) if row['UK'].strip() != '' else float(0.0)
                fund.europe = float(row['Europe']) if row['Europe'].strip() != '' else float(0.0)
                fund.europeEmerging = float(row['Euro-Emerging']) if row['Euro-Emerging'].strip() != '' else float(0.0)
                fund.asia = float(row['Asia']) if row['Asia'].strip() != '' else float(0.0)
                fund.asiaEmerging = float(row['Asia-Emerging']) if row['Asia-Emerging'].strip() != '' else float(0.0)
                fund.cyclical = float(row['Cyclical']) if row['Cyclical'].strip() != '' else float(0.0)
                fund.sensitive = float(row['Sensitive']) if row['Sensitive'].strip() != '' else float(0.0)
                fund.defensive = float(row['Defensive']) if row['Defensive'].strip() != '' else float(0.0)
                fund.alpha3Yr = float(row['3yr-Alpha']) if row['3yr-Alpha'].strip() != '' else float(0.0)
                fund.beta3Yr = float(row['3yr-Beta']) if row['3yr-Beta'].strip() != '' else float(0.0)
                fund.sharpe3Yr = float(row['3yr-Sharpe']) if row['3yr-Sharpe'].strip() != '' else float(0.0)
                fund.stdDev3Yr = float(row['3yr-SD']) if row['3yr-SD'].strip() != '' else float(0.0)
                fund.return3Yr = float(row['3yr-Ret']) if row['3yr-Ret'].strip() != '' else float(0.0)
                fund.return5Yr = float(row['5yr-Ret']) if row['3yr-Ret'].strip() != '' else float(0.0)

    return fundOverviews

def processTransactions(config):
    configStore = config['store']

    #Get previously stored transactions
    stockListByAcc = getStoredTransactions(configStore)
    #Process any new transactions
    allTxns: dict[str,list[Transaction]] = processLatestTxnFiles(config, stockListByAcc)
    #Get Latest Account Portfolio positions
    securitiesByAccount = getPortfolioOverviews(config)
    #Get Fund overview stats
    fundOverviews: dict[str, FundOverview] = getFundOverviews(config) 

    #For each account process each stock transactions to work out cash flow and share ledger
    totalCosts = 0
    allStocks = list()
    allAccounts = list()
    taxAllowances = dict()
    for allowance, val in config['tax_thresholds'].items():
        taxAllowances[allowance] = val
    for account, stocks in stockListByAcc.items():
        stockLedger = dict()
        rates = taxAllowances.copy()
        for rate, val in config[account+'_tax_rates'].items():
            rates[rate] = val
        accountSummary = AccountSummary(name = account, portfolioPerc = config['portfolio_ratios'], taxRates=rates)
        sortedStocks = dict()
        for stock in stocks:
            #Sort all transactions by date first
            sortedStocks[stock] = sorted(list(stocks[stock].values()), key= lambda txn: txn.date)
        for stock in stocks:
            if (stock != NO_STOCK and stock != USD and stock != EUR):
                #Dont process currency conversion txns or ones that are not related to a security
                stockLedger[stock] = processStockTxns(accountSummary, securitiesByAccount.get(account, None), fundOverviews, sortedStocks, stock) 
        processAccountTxns(accountSummary, allTxns[account], sortedStocks)
        #Summarise transactions and yields etc
        stockLedgerList = sorted(list(stockLedger.values()), key = lambda stock: stock.avgGainPerYearPerc(), reverse = True)
        allStocks.extend(stockLedgerList)
        #Save to Dropbox file
        saveStockLedger(configStore, accountSummary, stockLedgerList)
        #Summarise account performance
        summarisePerformance(accountSummary, stockLedgerList, fundOverviews)
        allAccounts.append(accountSummary)
    totalStockList = sorted(allStocks, key = lambda stock: stock.avgGainPerYearPerc(), reverse = True)
    totalSummary = AccountSummary(name = 'Total', portfolioPerc = config['portfolio_ratios'])
    currentTaxableIncome = Decimal(0.0)
    lastTaxableIncome = Decimal(0.0)
    currentTaxYear = getTaxYear(datetime.now())
    lastTaxYear = getTaxYear(datetime.now() - timedelta(weeks=52))
    for summary in allAccounts:
        currentTaxableIncome += summary.taxableIncome(currentTaxYear)
        lastTaxableIncome += summary.taxableIncome(lastTaxYear)
        totalSummary.mergeInAccountSummary(summary)

    otherIncome = config['other_income']
    currentTaxableIncome += Decimal(otherIncome['salary_current']) + Decimal(otherIncome['pension_current'])
    lastTaxableIncome += Decimal(otherIncome['salary_last']) + Decimal(otherIncome['pension_last'])
    #Based on total income, calculate the taxband
    totalSummary.taxBandByYear[currentTaxYear] = calcTaxBand(taxAllowances, currentTaxableIncome)
    totalSummary.taxBandByYear[lastTaxYear] = calcTaxBand(taxAllowances, lastTaxableIncome)
    for summary in allAccounts:
        summary.taxBandByYear = totalSummary.taxBandByYear 
        saveAccountSummary(configStore, summary, stockLedgerList)    #Create overall summary of account

    #Add in other account totals that are outside of the scope of these calcs
    #NOTE: If these have a (significant) impact on taxable earnings, they need to be brought into scope and account created for them
    otherAccs = config['other_accs']
    for ft in otherAccs.keys():
        val = Decimal(otherAccs[ft])
        totalSummary.fundTotals[FundType[ft.upper()]].totalValue += val
        totalSummary.totalOtherAccounts += val
    
    saveAccountSummary(configStore, totalSummary, totalStockList)    #Create overall summary
    
    