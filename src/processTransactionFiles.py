import csv
import os
from saveRetreiveFiles import (
    getAllStockTxnSaved,
    saveStringToDropbox,
    saveStockTransactions,
)
from transactionDefs import *

from decimal import Decimal

from processTransactions import processAccountTxns, processStockTxns
from getStockLedgerStr import getStockLedgerStr, getAccountSummaryStrs
from modelDrawdown import runDrawdownModel


def saveStockLedger(config, accountSummary: AccountSummary):
    for details in accountSummary.stocks:
        detailsStr = getStockLedgerStr(details)
        saveStringToDropbox(
            config,
            f"/{accountSummary.owner}-performance/{accountSummary.name}/{details.symbol}.txt",
            detailsStr,
        )


def saveAccountSummary(config, accountSummary: AccountSummary):
    # accSummaryTxt = getAccountSummaryStr(accountSummary)
    # saveStringToDropbox(config, f"/performance/{accountSummary.name}-Summary.txt", accSummaryTxt)
    filesAndStrs: dict[str, str] = getAccountSummaryStrs(accountSummary)
    for fileName, outStr in filesAndStrs.items():
        saveStringToDropbox(
            config, f"/{accountSummary.owner}-performance/{fileName}", outStr
        )


def summarisePerformance(
    accountSummary: AccountSummary, funds: dict[str, FundOverview]
):
    totalShareInvested = Decimal(0.0)
    # totalCashInvested = Decimal(0.0)
    totalDiviReInvested = Decimal(0.0)
    totalPaperGainForTax = Decimal(0.0)
    totalGain = Decimal(0.0)
    totalRealisedForTaxGain = dict()
    totalDealingCostsByYear = dict()
    totalDivi = accountSummary.dividendsByYear
    totalIncome = accountSummary.incomeByYear
    allIncome = accountSummary.allIncomeByYearMonth
    totalInterest = accountSummary.interestByYear
    fundTotals: dict[FundType, FundOverview] = dict()
    for typ in FundType:
        fundTotals[typ] = FundOverview(
            isin="None", symbol="None", name="None", fundType=typ
        )
    aggInvestedByYear = dict()
    totalDiviYieldByYear = dict()
    totalIncomeYieldByYear = dict()
    totalYieldByYear = dict()
    totalMarketValue = 0
    totalByInstitution: dict[str, Decimal] = dict()
    detailsToProcess: list[SecurityDetails] = list()
    detailsToProcess.extend(accountSummary.stocks)
    for details in accountSummary.stocks:
        detailsToProcess.extend(details.historicHoldings)
    for details in detailsToProcess:
        value = float(details.marketValue())
        fundOverview = details.fundOverview
        if fundOverview:
            if value == 0:
                value = float(details.totalInvested)
            fundType = fundOverview.fundType
            if totalByInstitution.get(fundOverview.institution, None):
                totalByInstitution[fundOverview.institution] += Decimal(value)
            else:
                totalByInstitution[fundOverview.institution] = Decimal(value)
            fundTotals[fundType].alpha3Yr += fundOverview.alpha3Yr * value
            for region in Regions:
                fundTotals[fundType].valueByRegion[region] = (
                    fundTotals[fundType].valueByRegion.get(region, 0)
                    + (fundOverview.valueByRegion.get(region, 0) * value) / 100
                )
            fundTotals[fundType].beta3Yr += fundOverview.beta3Yr * value
            fundTotals[fundType].cyclical += fundOverview.cyclical * value
            fundTotals[fundType].defensive += fundOverview.defensive * value
            fundTotals[fundType].fees += fundOverview.fees * value
            fundTotals[fundType].maturity += fundOverview.maturity * value
            fundTotals[fundType].return3Yr += fundOverview.return3Yr * value
            fundTotals[fundType].return5Yr += fundOverview.return5Yr * value
            fundTotals[fundType].sensitive += fundOverview.sensitive * value
            fundTotals[fundType].sharpe3Yr += fundOverview.sharpe3Yr * value
            fundTotals[fundType].stdDev3Yr += fundOverview.stdDev3Yr * value
            fundTotals[fundType].totalValue += Decimal(value)
            fundTotals[fundType].totalInvested += details.totalInvested
            fundTotals[fundType].actualReturn += details.avgGainPerYearPerc() * value
            if (
                fundOverview.alpha3Yr
                + fundOverview.beta3Yr
                + fundOverview.sharpe3Yr
                + fundOverview.stdDev3Yr
                > 0
            ):
                fundTotals[fundType].totRiskVal += Decimal(value)
            if (
                fundOverview.cyclical + fundOverview.defensive + fundOverview.sensitive
                > 0
            ):
                fundTotals[fundType].totDivVal += Decimal(value)
            if fundOverview.maturity:
                fundTotals[fundType].totMatVal += Decimal(value)
        else:
            #Raise an error
            raise ValueError(f"Missing fundOverview for fund {details.isin}")
            # # Assume a share stock
            # fundTotals[FundType.SHARE].totalValue += Decimal(value)
            # fundTotals[FundType.SHARE].uk += (
            #     100 * value
            # )  # Assume all shares are UK based
            # fundTotals[FundType.SHARE].totGeoVal += Decimal(value)
            # fundTotals[FundType.SHARE].totalInvested += details.totalInvested
            # fundTotals[FundType.SHARE].actualReturn += (
            #     details.avgGainPerYearPerc() * value
            # )

        totalMarketValue += details.marketValue()
        # totalCashInvested += details.cashInvested
        totalDiviReInvested += details.diviInvested
        totalShareInvested += details.totalInvested
        totalPaperGainForTax += details.paperCGT()
        totalGain += details.totalGain()
        for year, gain in details.realisedCapitalGainByYear.items():
            totalRealisedForTaxGain[year] = (
                totalRealisedForTaxGain.get(year, Decimal(0.0)) + gain
            )
        for year, costs in details.costsByYear.items():
            totalDealingCostsByYear[year] = (
                totalDealingCostsByYear.get(year, Decimal(0.0)) + costs
            )
        if fundOverview and fundOverview.isBondType():
            # A bond payment is treated as income for tax reasons
            for year, inc in details.dividendsByYear.items():
                totalIncome[year] = totalIncome.get(year, Decimal(0.0)) + inc
            for year in details.dividendTxnsByYear.keys():
                if year in accountSummary.incomeTxnsByYear.keys():
                    accountSummary.incomeTxnsByYear[year].update(
                        details.dividendTxnsByYear[year]
                    )
                else:
                    accountSummary.incomeTxnsByYear[year] = details.dividendTxnsByYear[
                        year
                    ].copy()
        elif fundOverview and fundOverview.isCashType():
            # Savings interest
            for year, inc in details.dividendsByYear.items():
                totalInterest[year] = totalInterest.get(year, Decimal(0.0)) + inc
            for year in details.dividendTxnsByYear.keys():
                if year in accountSummary.dividendTxnsByYear.keys():
                    accountSummary.interestTxnsByYear[year].update(
                        details.dividendTxnsByYear[year]
                    )
                else:
                    accountSummary.interestTxnsByYear[year] = (
                        details.dividendTxnsByYear[year].copy()
                    )
        else:
            for year, divi in details.dividendsByYear.items():
                totalDivi[year] = totalDivi.get(year, Decimal(0.0)) + divi
            for year in details.dividendTxnsByYear.keys():
                if year in accountSummary.dividendTxnsByYear.keys():
                    prelen = len(accountSummary.dividendTxnsByYear[year])
                    uplen = len(details.dividendTxnsByYear[year])
                    accountSummary.dividendTxnsByYear[year].update(
                        details.dividendTxnsByYear[year]
                    )
                    postlen = len(accountSummary.dividendTxnsByYear[year])
                    if postlen != prelen + uplen:
                        print(
                            f"Failed to update txns {uplen} into set pre:{prelen} post:{postlen} - dupe or broken hash?"
                        )
                else:
                    accountSummary.dividendTxnsByYear[year] = (
                        details.dividendTxnsByYear[year].copy()
                    )
        for year, txns in details.dividendTxnsByYear.items():
            for txn in txns:
                month = txn.date.month
                calyr = getCalYear(year, month)
                if calyr not in allIncome:
                    allIncome[calyr] = dict()
                allIncome[calyr][month] = (
                    allIncome[calyr].get(month, Decimal(0.0)) + txn.credit
                )

    # If a cash account, add in to CASH type

    if accountSummary.name in funds.keys():
        fundOverview = funds[accountSummary.name]
        fundType = fundOverview.fundType
        for year, divi in totalDivi.items():
            totalInterest[year] = totalInterest.get(year, Decimal(0.0)) + divi
        totalDivi = (
            dict()
        )  # Reset dividends to zero as all txns classified as dividends are interest payments
        if totalByInstitution.get(fundOverview.institution, None):
            totalByInstitution[fundOverview.institution] += Decimal(
                accountSummary.cashBalance[STERLING]
            )
        else:
            totalByInstitution[fundOverview.institution] = Decimal(
                accountSummary.cashBalance[STERLING]
            )
        fundTotals[fundType].totalValue += accountSummary.cashBalance[STERLING]
        fundTotals[fundType].totalInvested += accountSummary.totalCashInvested()
        # Assume Cash account is UK based
        fundTotals[fundType].valueByRegion[Regions.UK] = fundTotals[
            fundType
        ].valueByRegion.get(Regions.UK, 0.0) + float(
            accountSummary.cashBalance[STERLING]
        )
        fundTotals[fundType].actualReturn += 100 * float(
            accountSummary.cashBalance[STERLING] - accountSummary.totalCashInvested()
        )  # This is a %
        # If its a cash account, update invested totals
        # totalShareInvested += accountSummary.totalCashInvested()
    else:
        # Add any cash balance of account to Cash fund
        fundType = FundType.CASH
        fundTotals[fundType].totalValue += accountSummary.cashBalance[STERLING]
        # Assume Fund is UK based
        fundTotals[fundType].valueByRegion[Regions.UK] = fundTotals[
            fundType
        ].valueByRegion.get(Regions.UK, 0.0) + float(
            accountSummary.cashBalance[STERLING]
        )
        fundTotals[fundType].totGeoVal += accountSummary.cashBalance[STERLING]

    totalGain += accountSummary.totalInterest()

    historic3yrReturn = 0.0
    historic5yrReturn = 0.0

    for typ, fundTypeTotal in fundTotals.items():
        value = float(fundTypeTotal.totalValue)
        if value == 0:
            continue
        fundTypeTotal.alpha3Yr = (
            fundTypeTotal.alpha3Yr / float(fundTypeTotal.totRiskVal)
            if fundTypeTotal.totRiskVal != 0
            else 0.0
        )
        fundTypeTotal.beta3Yr = (
            fundTypeTotal.beta3Yr / float(fundTypeTotal.totRiskVal)
            if fundTypeTotal.totRiskVal != 0
            else 0.0
        )
        fundTypeTotal.cyclical = (
            fundTypeTotal.cyclical / float(fundTypeTotal.totDivVal)
            if fundTypeTotal.totDivVal != 0
            else 0.0
        )
        fundTypeTotal.defensive = (
            fundTypeTotal.defensive / float(fundTypeTotal.totDivVal)
            if fundTypeTotal.totDivVal != 0
            else 0.0
        )
        fundTypeTotal.fees = fundTypeTotal.fees / value
        fundTypeTotal.maturity = (
            fundTypeTotal.maturity / float(fundTypeTotal.totMatVal)
            if fundTypeTotal.totMatVal != 0
            else 0.0
        )
        historic3yrReturn += fundTypeTotal.return3Yr
        historic5yrReturn += fundTypeTotal.return5Yr
        fundTypeTotal.return3Yr = fundTypeTotal.return3Yr / value
        fundTypeTotal.return5Yr = fundTypeTotal.return5Yr / value
        fundTypeTotal.sensitive = (
            fundTypeTotal.sensitive / float(fundTypeTotal.totDivVal)
            if fundTypeTotal.totDivVal != 0
            else 0.0
        )
        fundTypeTotal.sharpe3Yr = (
            fundTypeTotal.sharpe3Yr / float(fundTypeTotal.totRiskVal)
            if fundTypeTotal.totRiskVal != 0
            else 0.0
        )
        fundTypeTotal.stdDev3Yr = (
            fundTypeTotal.stdDev3Yr / float(fundTypeTotal.totRiskVal)
            if fundTypeTotal.totRiskVal != 0
            else 0.0
        )
        fundTypeTotal.actualReturn = fundTypeTotal.actualReturn / value

    startYear = accountSummary.dateOpened
    endYear = datetime.now(timezone.utc) + timedelta(
        days=365
    )  # Make sure we have this tax year
    procYear = startYear
    sumInvested = 0
    while procYear < endYear:
        year = getTaxYear(procYear)
        sumInvested += accountSummary.cashInByYear.get(
            year, Decimal(0.0)
        ) - accountSummary.cashOutByYear.get(year, Decimal(0.0))
        aggInvestedByYear[year] = sumInvested
        if sumInvested > 0:
            totYld = 0
            if totalDivi.get(year, Decimal(0.0)) != 0:
                yld = 100 * totalDivi.get(year, Decimal(0.0)) / sumInvested
                totalDiviYieldByYear[year] = yld
                totYld += yld
            if (
                totalIncome.get(year, Decimal(0.0)) != 0
                or totalInterest.get(year, Decimal(0.0)) != 0
            ):
                yld = (
                    100
                    * (
                        totalIncome.get(year, Decimal(0.0))
                        + totalInterest.get(year, Decimal(0.0))
                    )
                    / sumInvested
                )
                totalIncomeYieldByYear[year] = yld
                totYld += yld
            if totYld > 0:
                totalYieldByYear[year] = totYld

        procYear += timedelta(days=365)

    # Add in monthly fees trading account that is taken by DD since Jan 2020
    if accountSummary.name.lower() == "trading":
        feesDirectDebitDate = datetime(year=2020, month=1, day=14)
        endTime = datetime.now()
        increment = timedelta(days=30)
        feesPerYear = accountSummary.feesByYear
        while feesDirectDebitDate < endTime:
            taxYear = getTaxYear(feesDirectDebitDate)
            feesPerYear[taxYear] = feesPerYear.get(taxYear, Decimal(0.0)) + Decimal(
                9.99
            )
            feesDirectDebitDate += increment

    # if (
    #     totalCashInvested == 0
    # ):  # This will be 0 if a cash account and so use the total invested figure
    #     accountSummary.totalCashInvested = accountSummary.totalCashInvested()
    # else:
    #     accountSummary.totalCashInvested = totalCashInvested
    accountSummary.totalDiviReInvested = totalDiviReInvested
    accountSummary.totalMarketValue = totalMarketValue
    accountSummary.totalInvestedInSecurities = totalShareInvested
    accountSummary.totalPaperGainForTax = totalPaperGainForTax
    # accountSummary.totalGain = totalGain
    accountSummary.aggInvestedByYear = aggInvestedByYear
    accountSummary.realisedGainForTaxByYear = totalRealisedForTaxGain
    accountSummary.dealingCostsByYear = totalDealingCostsByYear
    accountSummary.dividendsByYear = totalDivi
    accountSummary.dividendYieldByYear = totalDiviYieldByYear
    accountSummary.incomeByYear = totalIncome
    accountSummary.allIncomeByYearMonth = allIncome
    accountSummary.incomeYieldByYear = totalIncomeYieldByYear
    accountSummary.interestByYear = totalInterest
    accountSummary.totalYieldByYear = totalYieldByYear
    accountSummary.fundTotals = fundTotals
    accountSummary.totalByInstitution = totalByInstitution
    accountSummary.avgFund3YrReturn = (
        historic3yrReturn / float(totalMarketValue) if totalMarketValue > 0 else 0.0
    )
    accountSummary.avgFund5YrReturn = (
        historic5yrReturn / float(totalMarketValue) if totalMarketValue > 0 else 0.0
    )


def getPortfolioOverviews(
    portfolioDir, isinBySymbol, fundOverviews: dict[str, FundOverview]
):
    # List portfolio directory for account portfolio files
    dirEntries = os.scandir(portfolioDir)
    portfolioFiles = list()
    for dirEntry in dirEntries:
        if (
            dirEntry.is_file()
            and not dirEntry.name.startswith(".")
            and ".csv" in dirEntry.name
        ):
            portfolioFiles.append(
                (dirEntry.name, datetime.fromtimestamp(dirEntry.stat().st_mtime))
            )

    # Process each portfolio file
    securitiesByDateByAccount: dict[datetime, dict[str, dict[str, Security]]] = dict()
    for portfolioFile, mtime in portfolioFiles:
        # print(f"Processing portfolio file {portfolioFile}")
        accountName = portfolioFile.split("_")[0]
        dtStr = portfolioFile.split("_")[6]
        portDate = datetime.strptime(dtStr, "%Y%m%d.csv")
        securitiesByDate = securitiesByDateByAccount.get(accountName, None)
        if not securitiesByDate:
            securitiesByDate: dict[datetime, dict[str, Security]] = dict()
            securitiesByDateByAccount[accountName] = securitiesByDate
        # Extract account name
        securitiesBySymbol = securitiesByDate.get(portDate, None)
        if not securitiesBySymbol:
            securitiesBySymbol: dict[str, Security] = dict()
            securitiesByDate[portDate] = securitiesBySymbol
        with open(f"{portfolioDir}/{portfolioFile}", encoding="utf-8") as csvFile:
            csv_reader = csv.DictReader(csvFile, dialect="excel")
            # print(csv_reader.fieldnames)
            symbolField = None
            gainField = "Gain"
            for fieldname in csv_reader.fieldnames:
                if "Symbol" in fieldname:
                    symbolField = fieldname
                if "Gain/Loss" in fieldname:
                    gainField = "Gain/Loss"
            for row in csv_reader:
                symbolTxt = row[symbolField].strip()
                if symbolTxt != "" and not "Total" in symbolTxt:
                    security = Security(
                        date=mtime,
                        symbol=symbolTxt.replace("..", "."),
                        qty=0 if row["Qty"] == "" else float(row["Qty"]),
                        desc=row.get("Description", ""),
                        gain=row[gainField],
                    )
                    if security.symbol.endswith("."):
                        security.symbol = security.symbol + "L"
                    elif len(security.symbol) < 6:
                        security.symbol = security.symbol + ".L"
                    security.isin = isinBySymbol.get(security.symbol, None)
                    if security.isin:
                        security.type = fundOverviews[security.isin].fundType
                    (security.currency, security.currentPrice) = priceStrToDec(
                        row["Price"]
                    )
                    (security.currency, security.bookCost) = priceStrToDec(
                        row["Book Cost"]
                    )
                    (security.currency, security.marketValue) = priceStrToDec(
                        row["Market Value"]
                    )
                    (security.currency, security.avgBuyPrice) = priceStrToDec(
                        row["Average Price"]
                    )
                    securitiesBySymbol[security.symbol] = security
    return securitiesByDateByAccount


def getStoredTransactions(config):
    # Dict of stocks by accountname, stocks are a dict of stock txns keyed by symbol
    stockListByAcc = getAllStockTxnSaved(config)
    # Need to convert transactions from json to dataclass
    for acc, stocks in stockListByAcc.items():
        for stock in stocks:
            for txKey, txn in stockListByAcc[acc][stock].items():
                stockListByAcc[acc][stock][txKey] = Transaction.from_json(txn)
    return stockListByAcc


def processLatestTxnFiles(config, stockListByAcc, isinBySymbol):
    """_summary_

    Args:
        config (_type_): _description_
        stockListByAcc (_type_): _description_

    Returns:
        _type_: _description_
    """

    # symbolByIsIn = dict(zip(isinBySymbol.values(), isinBySymbol.keys())

    isinMapping = config["isinmappings"]
    configStore = config["store"]
    owner = config["owner"]["accountowner"]
    transDir = f"{owner}/{config['files']['transactionsLocation']}"
    changedStockTxnsByAcc = (
        dict()
    )  # Dict keyed by account with Set of stocks whose transactions have been appended to and so need to be saved back to HDFS
    # List transactions directory for account history files
    allTxnsByAcc: dict[str, list[Transaction]] = dict()
    dirEntries = os.scandir(transDir)
    txnFiles = list()
    for dirEntry in dirEntries:
        if (
            dirEntry.is_file()
            and not dirEntry.name.startswith(".")
            and ".csv" in dirEntry.name
        ):
            txnFiles.append(dirEntry.name)

    # For each trading and isa account file, read in transactions into list
    for txnFile in txnFiles:
        print(f"Processing txn file {txnFile}")
        # Extract account name
        accountName = txnFile.split("_")[0]
        stockList = stockListByAcc.get(accountName, None)
        if not stockList:
            stockList = dict()
            stockListByAcc[accountName] = stockList

        with open(f"{transDir}/{txnFile}", encoding="utf-8") as csvFile:
            csv_reader = csv.DictReader(csvFile)
            dateField = None
            for fieldname in csv_reader.fieldnames:
                fdn: str = fieldname.strip()
                if fdn.endswith("Date") and not "Settlement Date" in fdn:
                    dateField = fieldname
            if not dateField:
                dateField = "Settlement Date"
            for row in csv_reader:
                # print(", ".join(row))
                dt = row[dateField].strip()
                fmt = None
                if "/" in dt:
                    if len(dt) == 8:
                        fmt = "%d/%m/%y"
                    elif len(dt) == 10:
                        fmt = "%d/%m/%Y"
                elif "-" in dt and len(dt) == 10:
                    fmt = "%Y-%m-%d"
                if not fmt:
                    print(f"Unsupported date format: {dt}. Exiting!! \n")
                    exit()
                rowQuant = row.get("Quantity", "").strip()
                qty = -1 if rowQuant in ("", "n/a") else strToDec(rowQuant)
                txn = Transaction(
                    date=datetime.strptime(row[dateField], fmt).replace(
                        tzinfo=timezone.utc
                    ),
                    ref=row["Reference"],
                    symbol=row["Symbol"].strip(),
                    sedol=row["Sedol"].strip(),
                    isin=row.get("ISIN", "x").strip(),
                    qty=qty,
                    desc=row["Description"],
                    accountName=accountName,
                )
                (txn.priceCurrency, txn.price) = priceStrToDec(row.get("Price", ""))
                (txn.debitCurrency, txn.debit) = priceStrToDec(row.get("Debit", ""))
                (txn.creditCurrency, txn.credit) = priceStrToDec(row.get("Credit", ""))
                desc = txn.desc.lower()
                if txn.qty == -1:
                    if "s date" in desc:
                        # Missing quantity column and its a buy /sell txn - derive from desc
                        descParts = desc.split()
                        vals = []
                        for p in descParts:
                            v = strToDec(p)
                            if v != -1:
                                vals.append(v)
                        if len(vals) >= 2:
                            txn.qty = vals[0]
                            txn.price = vals[1]
                    else:
                        txn.qty = 0
                if (
                    txn.symbol != "n/a"
                    and not txn.symbol.startswith(NO_STOCK)
                    and txn.symbol != ""
                ):
                    if txn.symbol.endswith("."):
                        txn.symbol = txn.symbol + "L"
                    elif len(txn.symbol) < 6 and not txn.symbol.endswith(".L"):
                        txn.symbol = txn.symbol + ".L"
                    if txn.isin == "x":
                        # ISIN was not in CSV file - use mapping file
                        if (
                            txn.symbol != "n/a"
                            and not txn.symbol.startswith(NO_STOCK)
                            and txn.symbol != ""
                        ):
                            # This will blow up if missing stock from overview file
                            txn.isin = isinBySymbol[txn.symbol]
                elif txn.sedol != "n/a" and txn.sedol != "":
                    # Map by Sedol
                    # This will blow up if missing stock from overview file
                    txn.isin = isinBySymbol[txn.sedol]
                    txn.symbol = txn.sedol
                else:
                    txn.isin = ""
                if txn.isin != "":
                    # Map any old isin to new isin
                    txn.isin = isinMapping.get(txn.isin, txn.isin)
                if (
                    txn.isin.startswith(NO_STOCK)
                    or (txn.isin == "" and txn.symbol == "")
                    or txn.symbol == "n/a"
                ):
                    txn.isin = NO_STOCK
                    txn.symbol = NO_STOCK
                if (
                    desc.startswith("div")
                    or desc.endswith("distribution")
                    or desc.endswith("rights")
                    or "final frac pay" in desc
                    or "optional dividend" in desc
                ):
                    txn.type = DIVIDEND
                elif txn.qty != 0:
                    if txn.credit != 0:
                        txn.type = SELL
                    elif txn.debit != 0:
                        txn.type = BUY
                elif (
                    desc.startswith("debit card")
                    or "subscription" in desc
                    or desc.startswith("trf")
                    or desc.startswith("to ")
                    or "transfer" in desc
                    or "faster payment" in desc
                    or "tax relief" in desc
                    or "cashback" in desc
                    or ("payment" in desc and "andersen" in desc)
                    or "lump sum" in desc
                ):
                    if txn.credit != 0:
                        txn.type = CASH_IN
                    else:
                        txn.type = CASH_OUT
                elif "interest" in desc or "prize" in desc:
                    txn.type = INTEREST
                elif desc.startswith("equalisation"):
                    txn.type = EQUALISATION
                elif (
                    "fee" in desc
                    or ("payment" in desc and "andersen" not in desc)
                    and txn.debit != 0
                ):
                    txn.type = FEES
                elif "refund" in desc and txn.credit != 0:
                    txn.type = REFUND
                elif "mandatory redemption" in desc and txn.credit != 0:
                    # Fund has been closed and all held stock sold
                    txn.type = REDEMPTION
                else:
                    print(f"Unknown transaction type {txn}")

                # if txn.type == BUY and (txn.isin == USD or txn.isin == EUR):
                #     # Ignore currency conversion BUY transactions
                #     continue
                # Retrieve transactions by stock symbol
                existingTxns = stockList.get(txn.isin, None)
                if not existingTxns:
                    existingTxns = dict()
                    stockList[txn.isin] = existingTxns
                txnKey = f"{accountName}-{txn.date}-{txn.ref}-{txn.debit}-{txn.credit}"
                # Update existing transactions -
                # this will overwrite a transaction if it already exists
                # And so allows updates to existing transactions to be made
                existingTxns[txnKey] = txn
                # Set stock to be saved
                changed = changedStockTxnsByAcc.get(accountName, None)
                if not changed:
                    changed = set()
                    changedStockTxnsByAcc[accountName] = changed
                changed.add(txn.isin)

    txnByDesc = dict()
    # Dict of buy txns by their description - allows stock details to be found by description
    for acc in stockListByAcc.keys():
        if not allTxnsByAcc.get(acc, None):
            allTxnsByAcc[acc] = list()
        txns = allTxnsByAcc[acc]
        for stock in stockListByAcc[acc].keys():
            for txKey in stockListByAcc[acc][stock].keys():
                tx = stockListByAcc[acc][stock][txKey]
                if (tx.type == BUY or tx.type == SELL) and tx.isin != "":
                    desc = tx.desc.replace(" ", "")  # Strip out whitespace
                    txnByDesc[desc] = tx
                txns.append(tx)

    for acc in stockListByAcc.keys():
        for stock in stockListByAcc[acc].keys():
            stockTxns = stockListByAcc[acc][stock].copy()
            for txKey in stockTxns.keys():
                tx = stockListByAcc[acc][stock][txKey]
                if tx.type == DIVIDEND and tx.isin == "":
                    # Some Div payments dont have an isin - match with buy
                    for desc, txn in txnByDesc.items():
                        # Strip out whitespace to make comparison better
                        txdescStrip = tx.desc.replace(" ", "")
                        if desc in txdescStrip:
                            buyTxn = txn
                            tx.isin = buyTxn.isin
                            tx.symbol = buyTxn.symbol
                            tx.sedol = buyTxn.sedol
                            # Need to add to existing stock txns
                            txns = stockListByAcc[acc][tx.isin]
                            txns[txKey] = tx
                            # Remove from current list
                            stockListByAcc[acc][stock].pop(txKey)
                            changed = changedStockTxnsByAcc.get(acc, None)
                            if not changed:
                                changed = set()
                                changedStockTxnsByAcc[accountName] = changed
                            changed.add(tx.isin)

    # Save any changed transactions
    for account, stocks in changedStockTxnsByAcc.items():
        for stock in stocks:
            noTxns = len(stockListByAcc[account][stock])
            if stock != "":
                print(f"{account} Updating transactions for {stock} with {noTxns} txns")
                txns = stockListByAcc[account][stock]
                jsonTxns = dict()
                for key, txn in txns.items():
                    jsonTxns[key] = txn.to_json()
                saveStockTransactions(configStore, owner, account, stock, jsonTxns)
            elif noTxns > 0:
                print(f"WARNING: {noTxns} Transactions have no stock name set")
            else:
                # Remove empty stock
                stockListByAcc[account].pop("")
    # Sort all transactions by date
    for acc, txns in allTxnsByAcc.items():
        txns = sorted(txns, key=lambda txn: txn.date)
    return allTxnsByAcc


def getFundOverviews(config):
    fundsFile = config["files"]["fundsOverview"]

    fundOverviews: dict[str, FundOverview] = dict()
    isinBySymbol: dict[str, str] = dict()
    # List portfolio directory for account portfolio files
    with open(fundsFile, encoding="utf-8") as csvFile:
        csv_reader = csv.DictReader(csvFile)
        for row in csv_reader:
            isin = row["ISIN"].strip()
            if isin != "":
                fund = FundOverview(
                    isin=isin,
                    symbol=row["Symbol"],
                    name=row["Name"],
                    fundType=FundType[row["Type"].strip().upper()],
                    institution=row["Institution"].strip(),
                )
                fundOverviews[isin] = fund
                isinBySymbol[fund.symbol] = isin
                if row["Income"].strip().lower() == "inc":
                    fund.income = True
                else:
                    fund.income = False
                fund.fees = (
                    float(row["Fees"]) if row["Fees"].strip() != "" else float(0.0)
                )
                fund.maturity = (
                    float(row["Maturity"])
                    if row["Maturity"].strip() != ""
                    else float(0.0)
                )
                fund.risk = Risk[row["Risk"].strip().upper()]
                grade = row["Bond-Grade"].strip()
                if grade != "":
                    fund.bondGrade = BondGrade[grade]
                for region in Regions:
                    fund.valueByRegion[region] = (
                        float(row[region.value])
                        if row[region.value].strip() != ""
                        else float(0.0)
                    )

                fund.cyclical = (
                    float(row["Cyclical"])
                    if row["Cyclical"].strip() != ""
                    else float(0.0)
                )
                fund.sensitive = (
                    float(row["Sensitive"])
                    if row["Sensitive"].strip() != ""
                    else float(0.0)
                )
                fund.defensive = (
                    float(row["Defensive"])
                    if row["Defensive"].strip() != ""
                    else float(0.0)
                )
                fund.alpha3Yr = (
                    float(row["3yr-Alpha"])
                    if row["3yr-Alpha"].strip() != ""
                    else float(0.0)
                )
                fund.beta3Yr = (
                    float(row["3yr-Beta"])
                    if row["3yr-Beta"].strip() != ""
                    else float(0.0)
                )
                fund.sharpe3Yr = (
                    float(row["3yr-Sharpe"])
                    if row["3yr-Sharpe"].strip() != ""
                    else float(0.0)
                )
                fund.stdDev3Yr = (
                    float(row["3yr-SD"]) if row["3yr-SD"].strip() != "" else float(0.0)
                )
                fund.return3Yr = (
                    float(row["3yr-Ret"])
                    if row["3yr-Ret"].strip() != ""
                    else float(0.0)
                )
                fund.return5Yr = (
                    float(row["5yr-Ret"])
                    if row["3yr-Ret"].strip() != ""
                    else float(0.0)
                )

    return (fundOverviews, isinBySymbol)


def processTransactions(config):
    configStore = config["store"]
    owner = config["owner"]["accountowner"]

    # Get Fund overview stats
    fundOverviews: dict[str, FundOverview]
    (fundOverviews, isinBySymbol) = getFundOverviews(config)
    # Get previously stored transactions
    stockListByAcc = getStoredTransactions(config)
    # Process any new transactions
    print(f"{datetime.now()}: Processing latest transaction files", flush=True)
    allTxns: dict[str, list[Transaction]] = processLatestTxnFiles(
        config, stockListByAcc, isinBySymbol
    )
    # Get Latest Account Portfolio positions
    portfolioDir = (
        f"{config['owner']['accountowner']}/{config['files']['portfoliosLocation']}"
    )
    print(f"{datetime.now()}: Processing latest portfolio files", flush=True)
    # Top directory should only have one set of portfolio files, all with the same date
    currentPortfolioByDateByAccount: dict[str, dict[datetime, dict[str, Security]]] = (
        getPortfolioOverviews(portfolioDir, isinBySymbol, fundOverviews)
    )
    # Get historic Account portolio positions
    print(f"{datetime.now()}: Processing historic portfolio files", flush=True)
    portfolioDir = f"{config['owner']['accountowner']}/{config['files']['portfoliosLocation']}/Archive"
    historicPortfolioByDateByAccount = getPortfolioOverviews(
        portfolioDir, isinBySymbol, fundOverviews
    )
    # Add in current portfolio values to historic ones
    for acc, portfolioByDate in currentPortfolioByDateByAccount.items():
        for dt, portfolio in portfolioByDate.items():
            historicPortfolioByDateByAccount[acc][dt] = portfolio

    # For each account process each stock transactions to work out cash flow and share ledger
    allAccounts = list()
    taxAllowances = dict()
    for allowance, val in config["tax_thresholds"].items():
        taxAllowances[allowance] = val
    for account, stocks in stockListByAcc.items():
        print(f"{datetime.now()}: Processing account: {account}")
        stockLedger = dict()
        rates = taxAllowances.copy()
        for rate, val in config[f"{account}_tax_rates"].items():
            rates[rate] = val
        accountSummary = AccountSummary(
            owner=owner,
            name=account,
            portfolioPerc=config[f"{owner}_portfolio_ratios"],
            taxRates=rates,
        )
        currentByDate = currentPortfolioByDateByAccount.get(account, None)
        if currentByDate:
            currentPortfolio = currentByDate[list(currentByDate)[0]]
            accountSummary.portfolioValueDate = list(currentByDate.keys())[0]
        else:
            currentPortfolio = None
        sortedStocks = dict()
        for stock in stocks:
            # Sort all transactions by date first
            sortedStocks[stock] = sorted(
                list(stocks[stock].values()), key=lambda txn: txn.date
            )
        print(
            f"{datetime.now()}:\tProcessing stock txns for {len(stocks)} stocks",
            flush=True,
        )
        for stock in stocks:
            if stock != NO_STOCK and stock != USD and stock != EUR:
                # Dont process currency conversion txns or ones that are not related to a security
                stockLedger[stock] = processStockTxns(
                    accountSummary, currentPortfolio, fundOverviews, sortedStocks, stock
                )
        print(
            f"{datetime.now()}:\tProcessing all account txns: {len(allTxns[account])} stocks",
            flush=True,
        )
        processAccountTxns(
            accountSummary,
            allTxns[account],
            sortedStocks,
            historicPortfolioByDateByAccount,
        )
        accountSummary.stocks = sorted(
            list(stockLedger.values()),
            key=lambda stock: stock.avgGainPerYearPerc(),
            reverse=True,
        )
        # Save to Dropbox file
        print(f"{datetime.now()}:\tSaving account summary", flush=True)
        saveStockLedger(configStore, accountSummary)
        # Summarise account performance
        print(f"{datetime.now()}:\tSummarising account performance", flush=True)
        summarisePerformance(accountSummary, fundOverviews)
        allAccounts.append(accountSummary)
    print(f"{datetime.now()}: Summarising all accounts", flush=True)
    totalSummary = AccountSummary(
        owner=owner, name="Total", portfolioPerc=config[f"{owner}_portfolio_ratios"]
    )
    currentTaxableIncome = Decimal(0.0)
    lastTaxableIncome = Decimal(0.0)
    currentTaxYear = getTaxYear(datetime.now())
    totalSummary.interestTxnsByYear = dict()
    totalSummary.dividendTxnsByYear = dict()
    totalSummary.incomeTxnsByYear = dict()
    lastTaxYear = getTaxYear(datetime.now() - timedelta(weeks=52))
    for summary in allAccounts:
        currentTaxableIncome += summary.taxableIncome(currentTaxYear)
        lastTaxableIncome += summary.taxableIncome(lastTaxYear)
        totalSummary.mergeInAccountSummary(summary)

    otherIncome = config[f"{owner}_other_income"]
    currentTaxableIncome += Decimal(otherIncome["salary_current"]) + Decimal(
        otherIncome["pension_current"]
    )
    lastTaxableIncome += Decimal(otherIncome["salary_last"]) + Decimal(
        otherIncome["pension_last"]
    )
    # Based on total income, calculate the taxband
    totalSummary.taxBandByYear[currentTaxYear] = calcTaxBand(
        taxAllowances, currentTaxableIncome
    )
    totalSummary.taxBandByYear[lastTaxYear] = calcTaxBand(
        taxAllowances, lastTaxableIncome
    )
    for summary in allAccounts:
        summary.taxBandByYear = totalSummary.taxBandByYear
        saveAccountSummary(configStore, summary)  # Create overall summary of account

    # Add in other account totals that are outside of the scope of these calcs
    # NOTE: If these have a (significant) impact on taxable earnings, they need to be brought into scope and account created for them
    otherAccs = config[f"{owner}_other_accs"]
    rates = taxAllowances.copy()
    for rate, val in config[f"{owner}_other_accs_tax_rates"].items():
        rates[rate] = val
    otherAccounts = AccountSummary(
        owner=owner,
        name="Other Accs",
        portfolioPerc=config[f"{owner}_portfolio_ratios"],
        taxRates=rates,
    )
    total = Decimal(0)
    totalInvested = Decimal(0)
    totalCash = Decimal(0)
    for ft, otherVal in otherAccs.items():
        val = Decimal(otherVal)
        fundt = FundType[ft.upper()]
        if fundt != FundType.CASH:
            totalInvested += val
        else:
            totalCash += val
        otherAccounts.fundTotals[fundt] = FundOverview(
            isin="None",
            name="Other savings",
            symbol="None",
            fundType=fundt,
            totalValue=val,
        )
        total += val
    otherAccounts.cashInByYear["total"] = total
    otherAccounts.totalInvestedInSecurities = totalInvested
    otherAccounts.cashBalance = {STERLING: totalCash}
    otherAccounts.totalMarketValue = total
    otherAccounts.totalByInstitution["Other"] = total
    totalSummary.mergeInAccountSummary(otherAccounts)
    print(f"{datetime.now()}:Saving and generating summary", flush=True)
    saveAccountSummary(configStore, totalSummary)  # Create overall summary
    # Run drawdown model
    print(
        f"{datetime.now()}:Running drawdown model based on latest account details",
        flush=True,
    )
    runDrawdownModel(config)
