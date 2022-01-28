
from tabulate import tabulate
from datetime import timedelta, datetime, date, timezone
from statistics import mean
from dataclasses import asdict
from domonic.html import *

from transactionDefs import *

def getAccountSummaryStr(accountSummary: AccountSummary):
    retStr = f"Summary for Account: {accountSummary.name}\n"
    retStr += f"Date account opened: {accountSummary.dateOpened.date()}\n"
    retStr += f"Total cash invested in account: £{accountSummary.totalInvested():,.0f}\n"
    retStr += f"Total Dividends re-invested in account: £{accountSummary.totalDiviReInvested:,.0f}\n"
    retStr += f"Total invested in securities: £{accountSummary.totalInvestedInSecurities:,.0f}\n"
    retStr += f"Total current market value: £{accountSummary.totalMarketValue:,.0f}\n"
    retStr += f"Paper Capital Gain: £{accountSummary.totalPaperGainForTax:,.0f} ({accountSummary.totalPaperGainForTaxPerc():0.2f}%)\n"
    retStr += f"Realised Capital gain: £{accountSummary.totalRealisedGain():,.0f}\n"
    retStr += f"Total Capital gain: £{accountSummary.totalRealisedGain()+accountSummary.totalPaperGainForTax:,.0f}\n"
    retStr += f"Total Dividends: £{accountSummary.totalDividends():,.0f}\n"
    retStr += f"Avg Dividend Yield: {accountSummary.avgDividends():,.0f}%\n"
    retStr += f"Total Fees paid: £{accountSummary.totalFees():,.0f}\n"
    retStr += f"Total Dealing costs: £{accountSummary.totalDealingCosts():,.0f}\n"
    retStr += f"Total Return (Paper gain, dividends paid, realised gain, less fees and costs): £{accountSummary.totalGain:,.0f} ({accountSummary.totalGainPerc():0.2f}%) \n"
    retStr += f"Actual Return (Market value less Cash invested): £{accountSummary.totalGainFromInvestments():,.0f} ({accountSummary.totalGainFromInvPerc():0.2f}%) \n"
    retStr += f"Average return per year £{accountSummary.avgReturnPerYear():,.0f}\n"

    startYear = procYear = accountSummary.dateOpened
    endYear = datetime.now(timezone.utc) + timedelta(days=365) # Make sure we have this tax year
    # endYear = datetime.now(timezone.utc)
    retStr += f"\nYearly breakdown: \n"
    while procYear < endYear:
        years = (procYear-startYear).days/365
        if (years % 6 == 0):
            if years != 0:
                retStr += tabulate(byYear, headers='keys')
                retStr += "\n\n"
            byYear = dict()
            labels = list()
            labels.append('Cash In')
            labels.append('Cash Out')
            labels.append('Agg Invested')
            labels.append('Gain Realised (Tax)')
            labels.append('Dividends')
            labels.append('Yield %')
            labels.append('Dealing Costs')
            labels.append('Fees')
            byYear['0'] = labels
        taxYear = getTaxYear(procYear)
        values = list()
        values.append(accountSummary.cashInByYear.get(taxYear, Decimal(0.0)))
        values.append(accountSummary.cashOutByYear.get(taxYear, Decimal(0.0)))
        values.append(accountSummary.aggInvestedByYear.get(taxYear, Decimal(0.0)))
        values.append(accountSummary.realisedGainForTaxByYear.get(taxYear, Decimal(0.0)))
        values.append(accountSummary.dividendsByYear.get(taxYear, Decimal(0.0)))
        values.append(accountSummary.dividendYieldByYear.get(taxYear, Decimal(0.0)))
        values.append(accountSummary.dealingCostsByYear.get(taxYear, Decimal(0.0)))
        values.append(accountSummary.feesByYear.get(taxYear, Decimal(0.0)))
        procYear += timedelta(days=365)
        byYear[taxYear] = values

    retStr += tabulate(byYear, headers='keys')
    retStr += "\n\n\nStock Summary:\n"
    for details in accountSummary.stocks:
        retStr += getStockSummaryStr(details)
    retStr += "\n\n" 
    return retStr

def getAccountSummaryHtml(accountSummary: AccountSummary):
    dom =  body()
    if (accountSummary.name == "Total"):
        allAccounts = True
    else:
        allAccounts = False
    if (allAccounts):
        dom.appendChild(h1(f"Summary for all Accounts\n"))
    else:
        dom.appendChild(h1(f"Summary for Account: {accountSummary.name}\n"))
    summary = table()
    summary.appendChild(tr(td("Date account opened"),td(f"{accountSummary.dateOpened.date()}")))
    summary.appendChild(tr(td("Total cash invested in account"),td(f"£{accountSummary.totalInvested():,.0f}")))
    summary.appendChild(tr(td("Total Dividends re-invested in account"),td(f"£{accountSummary.totalDiviReInvested:,.0f}")))
    summary.appendChild(tr(td("Total invested in securities"), td(f"£{accountSummary.totalInvestedInSecurities:,.0f}")))
    summary.appendChild(tr(td("Total current market value"), td(f"£{accountSummary.totalMarketValue:,.0f}")))
    summary.appendChild(tr(td("Cash Balance"), td(f"£{accountSummary.cashBalance:,.0f}")))
    if (accountSummary.totalOtherAccounts > 0):
        summary.appendChild(tr(td("Total held in other accounts"), td(f"£{accountSummary.totalOtherAccounts:,.0f}")))
    summary.appendChild(tr(td("Total Account Value"), td(f"£{accountSummary.totalValue():,.0f}")))
    summary.appendChild(tr(td("Paper Capital Gain"), td(f"£{accountSummary.totalPaperGainForTax:,.0f} ({accountSummary.totalPaperGainForTaxPerc():0.2f}%)")))
    summary.appendChild(tr(td("Realised Capital gain"), td(f"£{accountSummary.totalRealisedGain():,.0f}")))
    summary.appendChild(tr(td("Total Capital gain"), td(f"£{accountSummary.totalRealisedGain()+accountSummary.totalPaperGainForTax:,.0f}")))
    summary.appendChild(tr(td("Total Dividends"), td(f"£{accountSummary.totalDividends():,.0f}")))
    summary.appendChild(tr(td("Avg Dividend Yield"), td(f"{mean(accountSummary.dividendYieldByYear.values()) if len(accountSummary.dividendYieldByYear) > 0 else 0:,.0f}%")))
    summary.appendChild(tr(td("Total Income"), td(f"£{accountSummary.totalIncome():,.0f}")))
    summary.appendChild(tr(td("Avg Income Yield"), td(f"{accountSummary.avgIncomeYield():.2f}%")))
    summary.appendChild(tr(td("Avg Total Yield"), td(f"{accountSummary.avgTotalYield():.2f}%")))
    summary.appendChild(tr(td("Total Divi + Income"), td(f"£{accountSummary.totalIncome() + accountSummary.totalDividends():,.0f}")))
    summary.appendChild(tr(td("Total Fees paid"), td(f"£{accountSummary.totalFees():,.0f}")))
    summary.appendChild(tr(td("Total Dealing costs"), td(f"£{accountSummary.totalDealingCosts():,.0f}")))
    summary.appendChild(tr(td("Total Return (Paper gain, dividends paid, realised gain, less fees and costs)"),td(f"£{accountSummary.totalGainLessFees():,.0f} ({accountSummary.totalGainPerc():,.0f}%)")))
    summary.appendChild(tr(td("Current Return of investments (Market value less Cash invested)"), td(f"£{accountSummary.totalGainFromInvestments():,.0f} ({accountSummary.totalGainFromInvPerc():0.2f}%)")))

    summary.appendChild(tr(td("Average return per year"),td(f"£{accountSummary.avgReturnPerYear():,.0f}")))
    dom.appendChild(summary)

    dom.appendChild(h2("Tax liability"))
    currentTaxYear = getTaxYear(datetime.now())
    lastTaxYear = getTaxYear(datetime.now() - timedelta(weeks=52))
    if len(accountSummary.mergedAccounts) == 0:
        #Single account
        accounts = [accountSummary]
    else:
        accounts = accountSummary.mergedAccounts
    for yr in [lastTaxYear, currentTaxYear]:
        dom.appendChild(h3(f"Tax Year {yr}"))
        tx = table()
        tx.appendChild(tr(th(' Account '),th(' Capital Gain '),th(' Taxable CG '),th(' CG Tax '),th(' CGT Rem Allowance '),
                                th(' Divi '),th(' Taxable Divi '),th(' Divi Tax '),th(' Divi All Rem '),th(' Income '),th(' Income Tax ')))
        totalCG = Decimal(0.0)
        totalTaxableCG = Decimal(0.0)
        totalCGT = Decimal(0.0)
        totalDivi = Decimal(0.0)
        totalTaxableDivi = Decimal(0.0)
        totalDiviTax = Decimal(0.0)
        totalIncome = Decimal(0.0)
        totalIncomeTax = Decimal(0.0)
        for account in accounts:
            band = account.taxBandByYear.get(yr, 'lower')
            cg = account.realisedGainForTaxByYear.get(yr, Decimal(0.0)) if len(account.realisedGainForTaxByYear) > 0 else Decimal(0.0)
            totalCG += cg
            taxablecg = account.taxableCG(yr)
            totalTaxableCG += taxablecg
            cgt = account.calcCGT(band, yr)
            totalCGT += cgt
            divi = account.dividendsByYear.get(yr, Decimal(0.0))
            totalDivi += divi
            taxableDivi = account.taxableDivi(yr)
            totalTaxableDivi += taxableDivi
            diviTax = account.calcDividendTax(band, yr)
            totalDiviTax += diviTax
            income = account.totalIncomeByYear(yr)
            totalIncome += income
            incomeTax = account.calcIncomeTax(band, yr)
            totalIncomeTax += incomeTax
            accountLocation = f"./{account.name}-Summary.html#Tax%20Liability"
            tx.appendChild(tr(td(a(f"{account.name}", _href=accountLocation)),td(f"£{cg:,.0f}"), td(f"£{taxablecg:,.0f}"),
                        td(f"£{cgt:,.0f}"), td("-"),
                        td(f"£{divi:,.0f}"), 
                        td(f"£{taxableDivi:,.0f}"), td(f"£{diviTax:,.0f}"), td("-"),
                        td(f"£{income:,.0f}"),
                        td(f"£{incomeTax:,.0f}"),
                    ))
        #Note: Use last account processed to get remaining allowance info
        tx.appendChild(tr(td("Total"), td(f"£{totalCG:,.0f}"), td(f"£{totalTaxableCG:,.0f}"), 
                        td(f"£{totalCGT:,.0f}"), td(f"£{account.getRemainingCGTAllowance(totalTaxableCG):,.0f}"),
                        td(f"£{totalDivi:,.0f}"), 
                        td(f"£{totalTaxableDivi:,.0f}"), td(f"£{totalDiviTax:,.0f}"),
                        td(f"£{account.getRemainingDiviAllowance(totalTaxableDivi):,.0f}"),
                        td(f"£{totalIncome:,.0f}"),
                        td(f"£{totalIncomeTax:,.0f}"),
                        ))
        dom.appendChild(tx)

    dom.appendChild(h2("Statistics By Investment Type"))
    dom.appendChild(h3("Fund values and returns (including other acccounts)"))
    fs = table()
    funds = accountSummary.fundTotals
    isTotalAcc = len(accountSummary.mergedAccounts) > 0
    totalAccountValue = accountSummary.totalValue()
    if (totalAccountValue == 0): totalAccountValue = Decimal(1.0)
    if isTotalAcc:
        fs.appendChild(tr(th('Type'),th('Total Invested'),th('Total Market Value'),th('%Account'),
            ''.join([f'{th(a(acc.name, _href="./"+acc.name+"-Summary.html#Statistics%20By%20Investment%20Type"))}' for acc in accountSummary.mergedAccounts]),
            th('Avg Fees'),th('Avg Ret'),th('3yr Ret'),th('5yr Ret')))
    else:
        fs.appendChild(tr(th('Type'),th('Total Invested'),th('Total Market Value'),th('%Account'),th('Avg Fees'),th('Avg Ret'),th('3yr Ret'),th('5yr Ret')))
    totInvested = Decimal(0.0)
    totValue = Decimal(0.0)
    totfees = 0.0
    totRet = 0.0
    tot3yrRet = 0.0
    tot5yrRet = 0.0
    totStocks = Decimal(0.0)
    totBonds = Decimal(0.0)
    totCash = Decimal(0.0)
    totGold = Decimal(0.0)
    portPerc = accountSummary.portfolioPerc
    for typ, fund in funds.items():
        if isTotalAcc:
            accFunds = (f"{acc.fundTotals[typ].totalValue if typ in acc.fundTotals else 0:,.0f}" for acc in accountSummary.mergedAccounts)
            fs.appendChild(tr(td(typ.name),td(f"£{fund.totalInvested:,.0f}"), td(f"£{fund.totalValue:,.0f}"),td(f"{100*fund.totalValue/totalAccountValue:0.2f}%"),
                    ''.join([f"{td(acc)}" for acc in accFunds]),
                    td(f"{fund.fees:0.2f}%"), td(f"{fund.actualReturn:0.2f}%"), td(f"{fund.return3Yr:0.2f}%"), td(f"{fund.return5Yr:0.2f}%") ))
        else:
            fs.appendChild(tr(td(typ.name),td(f"£{fund.totalInvested:,.0f}"), td(f"£{fund.totalValue:,.0f}"),td(f"{100*fund.totalValue/totalAccountValue:0.2f}%"),
                    td(f"{fund.fees:0.2f}%"), td(f"{fund.actualReturn:0.2f}%"), td(f"{fund.return3Yr:0.2f}%"), td(f"{fund.return5Yr:0.2f}%") ))
        totInvested += fund.totalInvested
        totValue += fund.totalValue
        val = float(fund.totalValue)
        totfees += fund.fees * val
        totRet += fund.actualReturn * val
        tot3yrRet += fund.return3Yr * val
        tot5yrRet += fund.return5Yr * val
        if (fund.isStockType()):
            totStocks += fund.totalValue
        elif (fund.isBondType()):
            totBonds += fund.totalValue
        elif (fund.isCashType()):
            totCash += fund.totalValue
        elif (fund.isGoldType()):
            totGold += fund.totalValue
    totValue = totValue if totValue else Decimal(1.0)
    tot = float(totValue)
    if isTotalAcc:
        accTots = (f"{acc.totalValue():,.0f}" for acc in accountSummary.mergedAccounts)
        fs.appendChild(tr(td("Overall"),td(f"£{totInvested:,.0f}"), td(f"£{totValue:,.0f}"),td(f"{100*totValue/totalAccountValue:0.02f}%"),
                    ''.join([f'{td(accTot)}' for accTot in accTots]),
                    td(f"{totfees/tot:0.02f}%"), td(f"{totRet/tot:0.02f}%"), td(f"{tot3yrRet/tot:0.02f}%"), td(f"{tot5yrRet/tot:0.02f}%") ))
    else:
        fs.appendChild(tr(td("Overall"),td(f"£{totInvested:,.0f}"), td(f"£{totValue:,.0f}"),td(f"{100*totValue/totalAccountValue:0.02f}%"),
                td(f"{totfees/tot:0.02f}%"), td(f"{totRet/tot:0.02f}%"), td(f"{tot3yrRet/tot:0.02f}%"), td(f"{tot5yrRet/tot:0.02f}%") ))
    dom.appendChild(fs)
    dom.appendChild(h3("Portfolio Percentages and guardrails"))
    fs = table()
    fs.appendChild(tr(th('Type'),th(' Total Market Value '),th(' Portfolio% '),th('  Min%  '),th('  Ideal%'  ),th('  Max%'  ),th('  Buy / (Sell)  ')))
    stocksPerc = 100*totStocks/totalAccountValue
    min = int(portPerc['stocks_min'])
    max = int(portPerc['stocks_max'])
    ideal = int(portPerc['stocks_ideal'])
    buy = ''
    if stocksPerc <= min:
        buy = f"£{(ideal-stocksPerc)*totalAccountValue/100:,.0f}"
    elif stocksPerc >= max:
        buy = f"(£{(stocksPerc-ideal)*totalAccountValue/100:,.0f})"
    fs.appendChild(tr(td("Stocks"),td(f"£{totStocks:,.0f}"),td(f"{stocksPerc:0.02f}%"),
                        td(f"{min:0.01f}%"), td(f"{ideal:0.01f}%"), td(f"{max:0.01f}%"), td(buy) ))
    bondsPerc = 100*totBonds/totalAccountValue
    min = int(portPerc['bonds_min'])
    max = int(portPerc['bonds_max'])
    ideal = int(portPerc['bonds_ideal'])
    buy = ''
    if bondsPerc <= min:
        buy = f"£{(ideal-bondsPerc)*totalAccountValue/100:,.0f}"
    elif bondsPerc >= max:
        buy = f"(£{(bondsPerc-ideal)*totalAccountValue/100:,.0f})"
    fs.appendChild(tr(td("Bonds"),td(f"£{totBonds:,.0f}"),td(f"{bondsPerc:0.02f}%"),
                        td(f"{min:0.01f}%"), td(f"{ideal:0.01f}%"), td(f"{max:0.01f}%"), td(buy) ))
    cashPerc = 100*totCash/totalAccountValue
    min = int(portPerc['cash_min'])
    max = int(portPerc['cash_max'])
    ideal = int(portPerc['cash_ideal'])
    buy = ''
    if cashPerc <= min:
        buy = f"£{(ideal-cashPerc)*totalAccountValue/100:,.0f}"
    elif cashPerc >= max:
        buy = f"(£{(cashPerc-ideal)*totalAccountValue/100:,.0f})"
    fs.appendChild(tr(td("Cash"),td(f"£{totCash:,.0f}"),td(f"{cashPerc:0.02f}%"),
                        td(f"{min:0.01f}%"), td(f"{ideal:0.01f}%"), td(f"{max:0.01f}%"), td(buy) ))
    goldPerc = 100*totGold/totalAccountValue
    min = int(portPerc['gold_min'])
    max = int(portPerc['gold_max'])
    ideal = int(portPerc['gold_ideal'])
    buy = ''
    if goldPerc <= min:
        buy = f"£{(ideal-goldPerc)*totalAccountValue/100:,.0f}"
    elif cashPerc >= max:
        buy = f"(£{(goldPerc-ideal)*totalAccountValue/100:,.0f})"
    fs.appendChild(tr(td("Gold"), td(f"£{totGold:,.0f}"),td(f"{goldPerc:0.02f}%"),
                        td(f"{min:0.01f}%"), td(f"{ideal:0.01f}%"), td(f"{max:0.01f}%"), td(buy) ))
    fs.appendChild(tr(td("Total"), td(f"£{totGold+totCash+totBonds+totStocks:,.0f}"),td(f"{goldPerc+cashPerc+bondsPerc+stocksPerc:0.02f}%") ))
    dom.appendChild(fs)
    if (len(accountSummary.totalByInstitution) > 0):
        dom.appendChild(h3("Value by Institution"))
        fi = table()
        totVal = Decimal(0.0)
        val = Decimal(0.0)
        fi.appendChild(tr(th('Institution'),th('Value'),th('Total Account %') ))
        for inst, val in accountSummary.totalByInstitution.items():
            fi.appendChild(tr(td(inst),td(f"£{val:,.0f}"), td(f"{100.0*float(val/totalAccountValue):0.02f}%") ))
            totVal += val
        fi.appendChild(tr(td("Total"),td(f"£{totVal:,.0f}"), td(f"{100.0*float(totVal/totalAccountValue):0.02f}%") ))
        dom.appendChild(fi)

    dom.appendChild(h3("Fund Risks"))
    fr = table()
    fr.appendChild(tr(th('Type'),th('Alpha'),th('Beta'),th('Sharpe'),th('Std Dev'),th('Maturity yrs') ))
    totAlpha = 0.0
    totBeta = 0.0
    totSharpe = 0.0
    totSD = 0.0
    totalNonShareVal = 0.0
    totMat = 0.0
    totMatVal = 0.0
    for typ, fund in funds.items():
        if (typ != FundType.SHARE):
            totPerc = fund.alpha3Yr+fund.beta3Yr+fund.sharpe3Yr+fund.stdDev3Yr
            fr.appendChild(tr(td(typ.name),td(f"{fund.alpha3Yr:0.02f}"), td(f"{fund.beta3Yr:0.02f}"),td(f"{fund.sharpe3Yr:0.02f}"),
                                        td(f"{fund.stdDev3Yr:0.02f}", td(f"{fund.maturity:0.02f}")) ))
            val = float(fund.totalValue)
            if (totPerc > 0):
                totalNonShareVal += val
                totAlpha += fund.alpha3Yr * val
                totBeta += fund.beta3Yr * val
                totSharpe += fund.sharpe3Yr * val
                totSD += fund.stdDev3Yr * val
            if (fund.maturity > 0): 
                totMat += fund.maturity * val
                totMatVal += val
    if totalNonShareVal == 0: totalNonShareVal = 1.0
    if totMatVal == 0: totMatVal = 1.0
    fr.appendChild(tr(td("Overall"),td(f"{totAlpha/totalNonShareVal:0.02f}"), td(f"{totBeta/totalNonShareVal:0.02f}"),
                td(f"{totSharpe/totalNonShareVal:0.02f}"),td(f"{totSD/totalNonShareVal:0.02f}"),td(f"{totMat/totMatVal:0.02f}") ))
    dom.appendChild(fr)
    dom.appendChild(h3("Geographical Spread"))
    fr = table()
    fr.appendChild(tr(th('Type'),th('Americas'),th('Americas-Emerging'),th('Asia'),th('Asia-Emerging'),th('UK'),th('Europe'),th('Europe-Emerging'),th('Total') ))
    totamer = 0.0
    totamerem = 0.0
    totasia = 0.0
    totasiaem = 0.0
    totuk = 0.0
    toteuro = 0.0
    toteuroem = 0.0
    totVal = 0.0
    for typ, fund in funds.items():
            totPerc = fund.americas + fund.americasEmerging + fund.asia + fund.asiaEmerging + fund.uk + fund.europe + fund.europeEmerging
            fr.appendChild(tr(td(typ.name),td(f"{fund.americas:0.02f}%"), td(f"{fund.americasEmerging:0.02f}%"),
                        td(f"{fund.asia:0.02f}%"),td(f"{fund.asiaEmerging:0.02f}%"), td(f"{fund.uk:0.02f}%"),
                        td(f"{fund.europe:0.02f}%"),td(f"{fund.europeEmerging:0.02f}%"),
                        td(f"{totPerc:0.02f}%") ))
            if (totPerc != 0):
                val = float(fund.totalValue)
                totamer += (fund.americas * val)
                totamerem += (fund.americasEmerging * val)
                totasia += (fund.asia * val)
                totasiaem += (fund.asiaEmerging * val)
                totuk += (fund.uk * val)
                toteuro += (fund.europe * val)
                toteuroem += (fund.europeEmerging * val)
                totVal += val
    totVal = totVal if totVal else 1.0
    totPerc = (totamer + totamerem + totasia + totasiaem + totuk + toteuro + toteuroem)/totVal
    fr.appendChild(tr(td("Overall"),td(f"{totamer/totVal:0.02f}%"), td(f"{totamerem/totVal:0.02f}%"),
                        td(f"{totasia/totVal:0.02f}%"),td(f"{totasiaem/totVal:0.02f}%"),td(f"{totuk/totVal:0.02f}%"),
                        td(f"{toteuro/totVal:0.02f}%"),td(f"{toteuroem/totVal:0.02f}%"),
                        td(f"{totPerc:0.02f}%") ))
    dom.appendChild(fr)
    dom.appendChild(h3("Fund Diversity"))
    fr = table()
    fr.appendChild(tr(th('Type'),th('Cyclical'),th('Sensitive'),th('Defensive'),th('Total') ))
    totCyc = 0.0
    totSens = 0.0
    totDef = 0.0
    totVal = 0.0
    for typ, fund in funds.items():
        if (typ != FundType.SHARE):
            totPerc = fund.cyclical+fund.sensitive+fund.defensive
            fr.appendChild(tr(td(typ.name),td(f"{fund.cyclical:0.02f}%"), td(f"{fund.sensitive:0.02f}%"),td(f"{fund.defensive:0.02f}%"),td(f"{totPerc:0.02f}%")))
            if (totPerc != 0):
                val = float(fund.totalValue)
                totCyc += fund.cyclical * val
                totSens += fund.sensitive * val
                totDef += fund.defensive * val
                totVal += val
    totVal = totVal if totVal else 1.0
    totPerc = (totCyc + totSens + totDef)/totVal
    fr.appendChild(tr(td("Overall"),td(f"{totCyc/totVal:0.2f}%"), td(f"{totSens/totVal:0.2f}%"),td(f"{totDef/totVal:0.2f}%"),td(f"{totPerc:0.2f}%")))
    dom.appendChild(fr)

    startYear = accountSummary.dateOpened
    endYear = datetime.now(timezone.utc) + timedelta(days=365) # Make sure we have this tax year
    # endYear = datetime.now(timezone.utc)
    procYear = startYear
    dom.appendChild(h2("Yearly breakdown"))
    byYear = table()
    byYear.appendChild(tr(th('Year'),th('Cash In'),th('Cash Out'),th('Agg Invested'),th('Gain Realised'),th('Dividends'),th('Yield%'),th('Dealing Costs'),th('Fees')))
    while procYear < endYear:
        taxYear = getTaxYear(procYear)
        yearRow = tr()
        yearRow.appendChild(td(f"{taxYear}"))
        yearRow.appendChild(td(f"£{accountSummary.cashInByYear.get(taxYear, Decimal(0.0)):,.0f}"))
        yearRow.appendChild(td(f"£{accountSummary.cashOutByYear.get(taxYear, Decimal(0.0)):,.0f}"))
        yearRow.appendChild(td(f"£{accountSummary.aggInvestedByYear.get(taxYear, Decimal(0.0)):,.0f}"))
        yearRow.appendChild(td(f"£{accountSummary.realisedGainForTaxByYear.get(taxYear, Decimal(0.0)):,.0f}"))
        yearRow.appendChild(td(f"£{accountSummary.dividendsByYear.get(taxYear, Decimal(0.0)):,.0f}"))
        yearRow.appendChild(td(f"{accountSummary.dividendYieldByYear.get(taxYear, Decimal(0.0)):,.0f}%"))
        yearRow.appendChild(td(f"£{accountSummary.dealingCostsByYear.get(taxYear, Decimal(0.0)):,.0f}"))
        yearRow.appendChild(td(f"£{accountSummary.feesByYear.get(taxYear, Decimal(0.0)):,.0f}"))
        byYear.appendChild(yearRow)
        procYear += timedelta(days=365)
    dom.append(byYear)

    historicStocks: list[SecurityDetails] = list()
    dom.append(h2('Stock Summary'))
    stockTable = table()
    if (allAccounts):
        stockTable.appendChild(tr(th('Stock'),th('Account'),th('Type'),th('Name'),th('Fees'),th('Cash inv'), th('Market Value'), th('Yield'),th('Return'),th('Years Held'),th('Annualised Ret'), th('3yr-Ret'), th('5yr-Ret'),th('Alpha'), th('Beta'), th('Sharpe')))
    else:
        stockTable.appendChild(tr(th('Stock'),th('Type'),th('Name'),th('Fees'),th('Cash inv'), th('Market Value'), th('Yield'),th('Return'),th('Years Held'),th('Annualised Ret'), th('3yr-Ret'), th('5yr-Ret'),th('Alpha'), th('Beta'), th('Sharpe')))
    for details in accountSummary.stocks:
        historicStocks.extend(details.historicHoldings)
        if (details.totalInvested != 0):
            stockRow = tr()
            detailLocation = f"./{details.account}/{details.symbol}.txt"
            stockRow.appendChild(td(a(f"{details.symbol}", _href=detailLocation)))
            if (allAccounts):
                accountLocation = f"./{details.account}-Summary.html#Stock%20Summary"
                stockRow.appendChild(td(a(f"{details.account}", _href=accountLocation)))
            stockRow.appendChild(td(f"{details.fundOverview.fundType.name if details.fundOverview else 'None'}"))
            stockRow.appendChild(td(f"{details.name}"))
            if (details.fundOverview):
                stockRow.appendChild(td(f"{details.fundOverview.fees:0.02f}%"))
            else:
                stockRow.appendChild(td("N/A"))
            stockRow.appendChild(td(f"£{details.cashInvested:,.0f}"))
            # stockRow.appendChild(td(f"£{details.totalInvested:,.0f}"))
            stockRow.appendChild(td(f"£{details.marketValue():,.0f}"))
            # stockRow.appendChild(td(f"£{details.capitalGain():,.0f}"))
            # stockRow.appendChild(td(f"£{details.totalDividends():,.0f}"))
            stockRow.appendChild(td(f"{details.averageYearlyDiviYield():,.0f}%"))
            stockRow.appendChild(td(f"£{details.totalGain():,.0f} ({details.totalGainPerc():0.02f}%)"))
            stockRow.appendChild(td(f"{details.yearsHeld():0.01f}"))
            stockRow.appendChild(td(f"{details.avgGainPerYearPerc():0.02f}%"))
            fund = details.fundOverview
            if (fund):
                stockRow.appendChild(td(f"{fund.return3Yr:0.02f}%"))
                stockRow.appendChild(td(f"{fund.return5Yr:0.02f}%"))
                stockRow.appendChild(td(f"{fund.alpha3Yr:0.02f}"))
                stockRow.appendChild(td(f"{fund.beta3Yr:0.02f}"))
                stockRow.appendChild(td(f"{fund.sharpe3Yr:0.02f}"))

            stockTable.appendChild(stockRow)
    dom.append(stockTable)

    historicStocks = sorted(historicStocks, key = lambda stock: stock.avgGainPerYearPerc(), reverse = True)
    dom.append(h2('Previous Stock Holdings'))
    stockTable = table()
    if (allAccounts):
        stockTable.appendChild(tr(th('Stock'),th('Account'),th('Type'),th('Name'),th('Fees'),th('Cash inv'), th('Capital Gain'), th('Dividends'), th('Yield'),th('Total Gain'),th('Years Held'),th('Avg Gain/Yr'),th('From'),th('To')))
    else:
        stockTable.appendChild(tr(th('Stock'),th('Type'),th('Name'),th('Fees'),th('Cash inv'), th('Capital Gain'), th('Dividends'), th('Yield'),th('Total Gain'),th('Years Held'),th('Avg Gain/Yr'),th('From'),th('To')))
    for details in historicStocks:
        stockRow = tr()
        if (allAccounts):
            detailLocation = f"./{details.account}/{details.symbol}.txt"
        else:
            detailLocation = f"./{accountSummary.name}/{details.symbol}.txt"
        stockRow.appendChild(td(a(f"{details.symbol}", _href=detailLocation)))
        if (allAccounts):
            accountLocation = f"./{details.account}-Summary.html#Stock%20Summary"
            stockRow.appendChild(td(a(f"{details.account}", _href=accountLocation)))
        stockRow.appendChild(td(f"{details.fundOverview.fundType.name if details.fundOverview else 'None'}"))
        stockRow.appendChild(td(f"{details.name}"))
        if (details.fundOverview):
            stockRow.appendChild(td(f"{details.fundOverview.fees:0.02f}%"))
        else:
            stockRow.appendChild(td("N/A"))
        stockRow.appendChild(td(f"£{details.cashInvested:,.0f}"))
        stockRow.appendChild(td(f"£{details.realisedCapitalGain():,.0f}"))
        stockRow.appendChild(td(f"£{details.totalDividends():,.0f}"))
        stockRow.appendChild(td(f"{details.averageYearlyDiviYield():0.02f}%"))
        stockRow.appendChild(td(f"£{details.totalGain():,.0f} ({details.totalGainPerc():0.02f}%)"))
        stockRow.appendChild(td(f"{details.yearsHeld():0.01f}"))
        stockRow.appendChild(td(f"{details.avgGainPerYearPerc():0.02f}%"))
        stockRow.appendChild(td(f"{details.startDate.date()}"))
        stockRow.appendChild(td(f"{details.endDate.date()}"))
        stockTable.appendChild(stockRow)
    dom.append(stockTable)

    dom.appendChild(h2(f"Payments by Tax Year"))
    for yr in [lastTaxYear, currentTaxYear]:
        dom.appendChild(h3(f"Tax Year {yr}"))
        dom.appendChild(h3(f"Dividend Payments"))
        txnTable = table()
        if (allAccounts):
            txnTable.appendChild(tr(th('Account'),th('Date'),th('Txn Type'), th('Desc'),th('Amount')))
        else:
            txnTable.appendChild(tr(th('Date'),th('Txn Type'), th('Desc'),th('Amount')))
        total = Decimal(0)
        txns = sorted(accountSummary.dividendTxnsByYear[yr] if yr in accountSummary.dividendTxnsByYear else list(), key= lambda txn: txn.date)
        for txn in txns:
            row = tr()
            if (allAccounts):
                accountLocation = f"./{txn.accountName}-Summary.html#Dividend%20Payments"
                row.appendChild(td(a(f"{txn.accountName}", _href=accountLocation)))
            row.appendChild(td(f"{txn.date}"))
            row.appendChild(td(f"{txn.type}"))
            row.appendChild(td(f"{txn.desc}"))
            row.appendChild(td(f"£{txn.credit if txn.credit != 0 else -txn.debit:0.2f}"))
            total += txn.credit
            txnTable.appendChild(row)
        txnTable.appendChild(tr(td(" "),td("Total"),td(" "),td(f"£{total:,.0f}")))
        dom.append(txnTable)
        dom.appendChild(h3(f"Income Payments"))
        txnTable = table()
        if (allAccounts):
            txnTable.appendChild(tr(th('Account'),th('Date'),th('Txn Type'), th('Desc'),th('Amount')))
        else:
            txnTable.appendChild(tr(th('Date'),th('Txn Type'), th('Desc'),th('Amount')))
        total = Decimal(0)
        txns = list(accountSummary.incomeTxnsByYear[yr]) if yr in accountSummary.incomeTxnsByYear else list()
        txns.extend(accountSummary.interestTxnsByYear[yr] if yr in accountSummary.interestTxnsByYear else list())
        txns = sorted(txns, key= lambda txn: txn.date)
        for txn in txns:
            row = tr()
            if (allAccounts):
                accountLocation = f"./{txn.accountName}-Summary.html#Income%20Payments"
                row.appendChild(td(a(f"{txn.accountName}", _href=accountLocation)))
            row.appendChild(td(f"{txn.date}"))
            row.appendChild(td(f"{txn.type}"))
            row.appendChild(td(f"{txn.desc}"))
            row.appendChild(td(f"£{txn.credit if txn.credit != 0 else -txn.debit:0.2f}"))
            total += txn.credit
            txnTable.appendChild(row)
        txnTable.appendChild(tr(td(" "),td("Total"),td(" "),td(f"£{total:,.0f}")))
        dom.append(txnTable)

    dom.append(h2('Account transactions'))
    txnTable = table()
    if (allAccounts):
        txnTable.appendChild(tr(th('Date'),th('Account'),th('Txn Type'), th('Desc'),th('Amount'),th('Balance')))
    else:
        txnTable.appendChild(tr(th('Date'),th('Txn Type'), th('Desc'),th('Amount'),th('Balance')))
    for txn in accountSummary.transactions:
        detailLocation = f"./{txn.accountName}/{txn.symbol}.txt"
        row = tr()
        row.appendChild(td(f"{txn.date}"))
        if (allAccounts):
            accountLocation = f"./{txn.accountName}-Summary.html#Income%20Payments"
            row.appendChild(td(a(f"{txn.accountName}", _href=accountLocation)))
        row.appendChild(td(f"{txn.type}"))
        row.appendChild(td(f"{txn.desc}"))
        row.appendChild(td(f"£{txn.credit if txn.credit != 0 else -txn.debit:0.2f}"))
        row.appendChild(td(f"£{txn.accountBalance:0.2f}"))
        txnTable.appendChild(row)
    dom.appendChild(txnTable)

    ht = html(meta(_charset='UTF-8'))
    ht.append(dom)
    return f"{ht}"

def getStockSummaryStr(details: SecurityDetails):
    retStr = f"{details.symbol} {details.name} "
    retStr += f"Cash in £{details.cashInvested:0.2f} "
    retStr += f"Invested £{details.totalInvested:0.2f} "
    retStr += f"Capital Gain £{details.realisedCapitalGain():,.0f} "
    retStr += f"Divis £{details.totalDividends():,.0f}, Avg Yield: {details.averageYearlyDiviYield():,.0f}% "
    retStr += f"Gain: £{details.totalGain():,.0f}, ({details.totalGainPerc():0.2f}%)\n"
    if (details.historicHoldings):
        for det in details.historicHoldings:
            retStr += "    Historic: " + getStockSummaryStr(det)
    return retStr

def getStockLedgerStr(securityDetails: SecurityDetails):
    retStr = f"Stock: {securityDetails.symbol}\nDescription: {securityDetails.name}\n"
    retStr += f"Sedol: {securityDetails.sedol} ISIN: {securityDetails.isin}\n\n"
    retStr += f"Current Holding:\n"
    retStr += getDetailsStr(securityDetails)
    if securityDetails.historicHoldings:
        for prev in securityDetails.historicHoldings:
            retStr += "\n\nPrevious holding:\n"
            retStr += getDetailsStr(prev)

    return retStr

def getDetailsStr(details: SecurityDetails):
    retStr = ""
    if details.endDate:
        #Historic stock 
        retStr += f"Bought {details.startDate.date() if details.startDate else ''}\n"
        retStr += f"Sold remaining stock {details.endDate.date()}\n"
        retStr += f"Held for {details.yearsHeld():0.1f} years\n"
    else:
        retStr += f"Held since {details.startDate.date() if details.startDate else ''}\n"
        retStr += f"Held for {details.yearsHeld():0.1f} years\n"
        retStr += f"Number of shares: {details.qtyHeld}\n"
        if details.currentSharePrice:
            retStr += f"Current Share Price {details.currentSharePrice:0.2f}\n"
            retStr += f"Share price date {details.currentSharePriceDate.date()}\n"
            retStr += f"Average Share Price {details.avgSharePrice:0.2f}\n"
            retStr += f"Current Market Value £{details.marketValue():,.0f}\n"
            # retStr += f"Total Paper Gain £{details['totalPaperGain']:0.2f} {details['totalPaperGainPerc']:0.2f}%\n"
            retStr += f"Total Taxable Gain if sold £{details.paperCGT():,.0f} {details.paperCGTPerc():0.2f}%\n"
        else:
            retStr += "**** No current price data available, so total gain info doesnt include current value\n"
            retStr += f"Average Share Price {details.avgSharePrice:0.2f}\n"

    retStr += f"Cash invested £{details.cashInvested:,.0f}\n"
    retStr += f"Amount invested £{details.totalInvested:,.0f}\n"
    retStr += f"Amount dividends re-invested £{details.diviInvested:,.0f}\n"
    retStr += f"Total Dividends £{details.totalDividends():0.0f}\n"
    retStr += f"Average Yearly Dividend £{details.averageYearlyDivi():,.0f}, Yield: {details.averageYearlyDiviYield():0.2f}%\n"
    retStr += f"Realised Capital gain £{details.realisedCapitalGain():,.0f}\n"
    retStr += f"Total Capital gain £{details.capitalGain():,.0f}\n"
    retStr += f"Stock Dealing costs £{details.totalCosts():,.0f}\n"
    retStr += f"Total Gain: £{details.totalGain():,.0f}, ({details.totalGainPerc():0.2f}%) \n"
    retStr += f"Average Gain per year: £{details.avgGainPerYear():,.0f}, ({details.avgGainPerYearPerc():0.2f}%) \n"

    if details.fundOverview:
        retStr += "\n"
        retStr += details.fundOverview.getStr()

    divs = list()
    retStr += "\nDividends Per Year:\n"
    for year in details.dividendsByYear.keys():
        divs.append([year, details.dividendsByYear[year], details.dividendYieldByYear[year]])
    retStr += tabulate(divs, headers=['Tax Year', 'Dividend Paid', 'Yield'])

    retStr += "\n\nInvestments Made:\n"
    hist = list()
    for dc in details.investmentHistory:
        hist.append(asdict(dc))
    retStr += tabulate(hist, headers='keys')

    retStr += "\n\nRealised Capital Gain (taxable) Per Year:\n"
    gains = list(details.realisedCapitalGainByYear.items())
    retStr += tabulate(gains, headers=['Tax Year', 'Realised Capital Gain (taxable value)'])

    retStr += "\n\nDealing Costs Per Year:\n"
    costs = list(details.costsByYear.items())
    retStr += tabulate(costs, headers=['Tax Year', 'Dealing Costs'])

    retStr += "\n\nTransactions:\n"
    trans = list()
    total = Decimal(0.0)
    for txn in details.transactions:
        txnd = dict()
        txnd['Date'] = txn.date
        txnd['Type'] = txn.type
        # txnd['Qty'] = txn.qty
        if (txn.credit != 0):
            txnd['Amount'] = txn.credit
            txnd['Currency'] = txn.creditCurrency
            total += txn.credit
        elif (txn.debit != 0):
            txnd['Amount'] = -txn.debit
            txnd['Currency'] = txn.debitCurrency
            total -= txn.debit
        trans.append(txnd)
    retStr += tabulate(trans, headers='keys')
    if (total >= 0):
        retStr += f"\nTotal cash out: {total:,.0f}\n\n"
    else:
        retStr += f"\nTotal cash in: {-total:,.0f}\n\n"

    return retStr