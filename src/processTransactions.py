from decimal import Decimal
from datetime import datetime, timedelta, timezone

from transactionDefs import *


def processAccountTxns(
    account: AccountSummary,
    txns: list[Transaction],
    stocks: dict[str, list[Transaction]],
    historicValues: dict[str, dict[datetime, dict[str, Security]]],
):
    cashInByYear = dict()
    cashOutByYear = dict()
    feesByYear = dict()
    account.taxfreeCashOutByYear = dict()
    account.interestTxnsByYear = dict()
    # dateOpened = datetime.now().replace(tzinfo=None)
    dateOpened = datetime.now(timezone.utc)
    txns = sorted(txns, key=lambda txn: txn.date, reverse=False)
    for txn in txns:
        txn_type = txn.type
        taxYear = getTaxYear(txn.date)
        if txn.date < dateOpened:
            dateOpened = txn.date
        if txn_type == CASH_IN:
            cashInByYear[taxYear] = cashInByYear.get(taxYear, Decimal(0.0)) + txn.credit
            account.cashBalance += txn.credit
        elif txn_type == CASH_OUT:
            cashOutByYear[taxYear] = (
                cashOutByYear.get(taxYear, Decimal(0.0)) + txn.debit
            )
            account.cashBalance -= txn.debit
            if "tax-free" in txn.desc.lower():
                account.taxfreeCashOutByYear[taxYear] = (
                    account.taxfreeCashOutByYear.get(taxYear, Decimal(0.0)) + txn.debit
                )
        elif txn_type == FEES:
            feesByYear[taxYear] = feesByYear.get(taxYear, Decimal(0.0)) + txn.debit
            account.cashBalance -= txn.debit
        elif txn_type == REFUND:
            feesByYear[taxYear] = feesByYear.get(taxYear, Decimal(0.0)) - txn.credit
            account.cashBalance += txn.credit
        elif txn_type == BUY:
            debit = convertToSterling(
                stocks.get(txn.debitCurrency, None), txn, txn.debit
            )
            account.cashBalance -= debit
        elif txn_type in [SELL, REDEMPTION]:
            if txn.isin != USD and txn.isin != EUR:
                # Ignore currency sells as we have factored this in from dividends already
                credit = convertToSterling(
                    stocks.get(txn.creditCurrency, None), txn, txn.credit
                )
                account.cashBalance += credit
        elif txn_type == DIVIDEND:
            divi = convertToSterling(
                stocks.get(txn.creditCurrency, None), txn, txn.credit
            )
            account.cashBalance += divi
        elif txn_type == INTEREST:
            interest = convertToSterling(
                stocks.get(txn.creditCurrency, None), txn, txn.credit
            )
            account.cashBalance += interest
            yr = getTaxYear(txn.date)
            # Interest is account level and so add transaction to account
            account.interestByYear[yr] = (
                account.interestByYear.get(yr, Decimal(0.0)) + interest
            )
            if yr in account.interestTxnsByYear:
                account.interestTxnsByYear[yr].add(txn)
            else:
                account.interestTxnsByYear[yr] = {txn}
        elif txn_type == EQUALISATION:
            divi = convertToSterling(
                stocks.get(txn.creditCurrency, None), txn, txn.credit
            )
            account.cashBalance += divi
        else:
            print(
                f"Got a transaction type '{txn_type}' that isn't recognised for {account.name}: Detail: {txn}\n"
            )
        txn.accountBalance = (
            account.cashBalance
        )  # Capture running balance in transaction
    account.dateOpened = dateOpened
    account.cashInByYear = cashInByYear
    account.cashOutByYear = cashOutByYear
    account.feesByYear = feesByYear
    account.transactions = list(txns)
    securityByDate = historicValues.get(account.name, None)
    if securityByDate:
        securityBySymbol: dict[str, Security] = None
        for portDate, securityBySymbol in securityByDate.items():
            totalValue: Decimal = Decimal(0.0)
            totalCost: Decimal = Decimal(0.0)
            byFundType: dict[str, (Decimal(0.0), Decimal(0, 0))] = dict()
            for security in securityBySymbol.values():
                totalValue += security.marketValue
                totalCost += security.bookCost
                byFundType[security.type] = [
                    sum(x)
                    for x in zip(
                        byFundType.get(security.type, (Decimal(0.0), Decimal(0.0))),
                        (security.marketValue, security.bookCost),
                    )
                ]
            dt = portDate.timestamp()
            account.historicValue[dt] = (totalValue, totalCost)
            account.historicValueByType[dt] = byFundType
    return account


def processStockTxns(
    account: AccountSummary,
    securities,
    funds: dict[str, FundOverview],
    stocks: dict[str, list[Transaction]],
    stock,
):
    txns = sorted(stocks[stock], key=lambda txn: txn.date, reverse=False)
    lastDiviDate = None
    lastDivi = Decimal(0.0)
    details = SecurityDetails()
    details.transactions = txns
    if not account.name or account.name == "None":
        print(f"No account name {account} for stock {stock} ")
    details.account = account.name
    for txn in txns:
        txn_type = txn.type
        taxYear = getTaxYear(txn.date)
        if not details.symbol:
            if txn.symbol != "":
                if txn.symbol.endswith("."):
                    txn.symbol = txn.symbol + "L"
                elif len(txn.symbol) < 6 and not txn.symbol.endswith(".L"):
                    txn.symbol = txn.symbol + ".L"
                details.symbol = txn.symbol
            elif txn.sedol:
                details.symbol = txn.sedol
        if not details.name:
            details.name = txn.desc
        if not details.sedol:
            details.sedol = txn.sedol
        if not details.isin:
            details.isin = txn.isin
            details.fundOverview = funds.get(details.isin, None)
        if not details.startDate:
            details.startDate = txn.date
        if txn_type == BUY:
            details.qtyHeld += float(txn.qty)
            debit = convertToSterling(
                stocks.get(txn.debitCurrency, None), txn, txn.debit
            )
            priceIncCosts = debit / Decimal(txn.qty)
            if txn.price != 0:
                costs = debit - (Decimal(txn.qty) * txn.price)
            else:
                costs = 0
            details.totalInvested += debit
            # If its a reinvested dividend, need to not include this in total cash invested
            if (
                lastDiviDate
                and (txn.date - lastDiviDate < timedelta(days=7))
                and (lastDivi >= debit)
            ):
                details.diviInvested += debit
            else:
                details.cashInvested += debit
            details.avgSharePrice = details.totalInvested / Decimal(details.qtyHeld)
            details.costsByYear[taxYear] = (
                details.costsByYear.get(taxYear, Decimal(0.0)) + costs
            )  # Stamp duty and charges
            details.investmentHistory.append(
                CapitalGain(
                    date=txn.date,
                    qty=float(txn.qty),
                    price=priceIncCosts,
                    transaction=BUY,
                    avgBuyPrice=priceIncCosts,
                )
            )
        elif txn_type in [SELL, REDEMPTION]:
            if txn_type == REDEMPTION:
                # All of held stock has been sold as fund has been closed <sigh>
                txn.qty = details.qtyHeld
            if not details.name:
                if details.isin == USD or details.isin == EUR:
                    details.name = details.isin
                    details.symbol = details.isin
            credit = convertToSterling(
                stocks.get(txn.creditCurrency, None), txn, txn.credit
            )
            priceIncCosts = credit / Decimal(txn.qty)
            gain = Decimal(
                float(priceIncCosts - details.avgSharePrice) * txn.qty
            )  # CGT uses average purchase price at time of selling
            details.cashInvested -= details.avgSharePrice * Decimal(
                txn.qty
            )  # Reduce amount of cash invested by amount of shares sold at avg buy price
            details.realisedCapitalGainByYear[taxYear] = (
                details.realisedCapitalGainByYear.get(taxYear, Decimal(0.0)) + gain
            )
            details.qtyHeld -= float(txn.qty)
            if txn.price != 0:
                costs = credit - (
                    txn.price * Decimal(txn.qty)
                )  # Diff between what should have received vs what was credited
                details.costsByYear[taxYear] = (
                    details.costsByYear.get(taxYear, Decimal(0.0)) + costs
                )  # Stamp duty and charges
            details.totalInvested = details.avgSharePrice * Decimal(details.qtyHeld)
            cg = CapitalGain(
                date=txn.date,
                qty=float(txn.qty),
                price=priceIncCosts,
                transaction=SELL,
                avgBuyPrice=details.avgSharePrice,
            )
            if taxYear in details.cgtransactionsByYear:
                details.cgtransactionsByYear[taxYear].append(cg)
            else:
                details.cgtransactionsByYear[taxYear] = [cg]
            details.investmentHistory.append(cg)
            if details.qtyHeld <= 0:
                # This is a stock close out txn
                # Start a new set of security details, with the old one stored in history
                details.endDate = txn.date
                details.qtyHeld = Decimal(0)
                details.cashInvested = Decimal(0)
                details.totalInvested = Decimal(0)
                newDetails = SecurityDetails()
                if len(details.historicHoldings) > 0:
                    # Promote previous holdings to the new parent
                    newDetails.historicHoldings.extend(details.historicHoldings)
                    details.historicHoldings = None
                newDetails.sedol = details.sedol
                newDetails.isin = details.isin
                newDetails.symbol = details.symbol
                newDetails.name = details.name
                newDetails.account = details.account
                newDetails.fundOverview = details.fundOverview
                newDetails.historicHoldings.append(details)
                details = newDetails
        elif txn_type == DIVIDEND:
            divi = convertToSterling(
                stocks.get(txn.creditCurrency, None), txn, txn.credit
            )
            lastDivi = divi
            lastDiviDate = txn.date
            details.dividendsByYear[taxYear] = (
                details.dividendsByYear.get(taxYear, Decimal(0.0)) + divi
            )
            if details.totalInvested > 0.01:
                yearYield = float(
                    details.dividendYieldByYear.get(taxYear, Decimal(0.0))
                ) + 100 * float(divi / details.totalInvested)
            else:
                yearYield = 0.0
            details.dividendYieldByYear[taxYear] = yearYield
            if taxYear in details.dividendTxnsByYear.keys():
                details.dividendTxnsByYear[taxYear].add(txn)
            else:
                details.dividendTxnsByYear[taxYear] = {txn}
        elif txn_type == EQUALISATION:
            # This is a return of part of the initial principle, so should be taken off the investment amount
            # But only if we still have stock - can get Equalisation payments post closing position
            if details.qtyHeld > 0:
                eql = convertToSterling(
                    stocks.get(txn.creditCurrency, None), txn, txn.credit
                )
                details.totalInvested -= eql
                details.avgSharePrice = details.totalInvested / Decimal(details.qtyHeld)
                details.cashInvested -= eql
        else:
            print(
                f"Got a transaction type {txn_type} that dont recognise for account {account.name} and stock {stock}: Detail: {txn}\n"
            )

    # From remaining stock history workout paper gain
    # totalPaperGain = 0
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
    if not details.symbol:
        # Its a fund
        details.symbol = details.sedol
    if securities:
        security = securities.get(details.symbol, None)
    else:
        security = None
    if security:
        details.currentSharePrice = security.currentPrice
        details.currentSharePriceDate = security.date
    return details
