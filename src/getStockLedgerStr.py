
from tabulate import tabulate
from datetime import timedelta, datetime, date, timezone
from statistics import mean
from dataclasses import asdict
from domonic.html import *

def getTaxYear(inDate):
    taxYearStart = date(year=2021, month=4, day=6)
    d = date(year=2021, month=inDate.month, day=inDate.day)
    if (d < taxYearStart):
        year = f"{inDate.year - 1}-{inDate.year}"
    else:
        year = f"{inDate.year}-{inDate.year+1}"
    return year

def getAccountSummaryStr(account, accountSummary):
    retStr = f"Summary for Account: {account}\n"
    retStr += f"Date account opened: {accountSummary['dateOpened'].date()}\n"
    retStr += f"Total cash invested in account: £{accountSummary['totalInvested']:0.2f}\n"
    retStr += f"Total Dividends re-invested in account: £{accountSummary['totalDiviReInvested']:0.2f}\n"
    retStr += f"Total invested in securities: £{accountSummary['totalInvestedInSecurities']:0.2f}\n"
    retStr += f"Total current market value: £{accountSummary['totalMarketValue']:0.2f}\n"
    # retStr += f"Capital Gain on paper: £{accountSummary['totalPaperGain']:0.2f} ({accountSummary['totalPaperGainPerc']:0.2f}%)\n"
    retStr += f"Paper Capital Gain: £{accountSummary['totalPaperGainForTax']:0.0f} ({accountSummary['totalPaperGainForTaxPerc']:0.2f}%)\n"
    retStr += f"Realised Capital gain: £{accountSummary['totalRealisedGain']:0.0f}\n"
    retStr += f"Total Capital gain: £{accountSummary['totalRealisedGain']+accountSummary['totalPaperGainForTax']:0.0f}\n"
    retStr += f"Total Dividends: £{sum(accountSummary['dividendsPerYear'].values()):0.2f}\n"
    retStr += f"Avg Dividend Yield: {mean(accountSummary['dividendYieldPerYear'].values()) if len(accountSummary['dividendYieldPerYear']) > 0 else 0:0.2f}%\n"
    retStr += f"Total Fees paid: £{accountSummary['totalFees']:0.2f}\n"
    retStr += f"Total Dealing costs: £{accountSummary['totalDealingCosts']:0.2f}\n"
    retStr += f"Total Return (Paper gain, dividends paid, realised gain, less fees and costs): £{accountSummary['totalGain']:0.2f} ({accountSummary['totalGainPerc']:0.2f}%) \n"
    retStr += f"Actual Return (Market value less Cash invested): £{accountSummary['totalGainFromInvestments']:0.2f} ({accountSummary['totalGainFromInvPerc']:0.2f}%) \n"
    startYear = accountSummary['dateOpened']
    endYear = datetime.now(timezone.utc) + timedelta(days=365) # Make sure we have this tax year
    timeHeld = endYear - startYear
    avgReturnPerYear = float(accountSummary['totalGain']) / (timeHeld.days / 365)
    retStr += f"Average return per year £{avgReturnPerYear:0.2f}\n"

    procYear = startYear
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
            # labels.append('Gain Realised (Real)')
            labels.append('Gain Realised (Tax)')
            labels.append('Dividends')
            labels.append('Yield %')
            labels.append('Dealing Costs')
            labels.append('Fees')
            byYear['0'] = labels
        taxYear = getTaxYear(procYear)
        values = list()
        values.append(accountSummary['cashInPerYear'].get(taxYear, 0))
        values.append(accountSummary['cashOutPerYear'].get(taxYear, 0))
        values.append(accountSummary['aggInvestedByYear'].get(taxYear, 0))
        # values.append(accountSummary['realisedGainPerYear'].get(taxYear, 0))
        values.append(accountSummary['realisedGainForTaxPerYear'].get(taxYear, 0))
        values.append(accountSummary['dividendsPerYear'].get(taxYear, 0))
        values.append(accountSummary['dividendYieldPerYear'].get(taxYear, 0))
        values.append(accountSummary['dealingCostsPerYear'].get(taxYear, 0))
        values.append(accountSummary['feesPerYear'].get(taxYear, 0))
        procYear += timedelta(days=365)
        byYear[taxYear] = values

    retStr += tabulate(byYear, headers='keys')
    retStr += "\n\n"

    return retStr

def getAccountSummaryHtml(account, accountSummary, stockLedger):
    dom =  body()
    dom.appendChild(h1(f"Summary for Account: {account}\n"))
    summary = table()
    summary.appendChild(tr(td("Date account opened"),td(f"{accountSummary['dateOpened'].date()}")))
    summary.appendChild(tr(td("Total cash invested in account"),td(f"£{accountSummary['totalInvested']:0.2f}")))
    summary.appendChild(tr(td("Total Dividends re-invested in account"),td(f"£{accountSummary['totalDiviReInvested']:0.2f}")))
    summary.appendChild(tr(td("Total invested in securities"), td(f"£{accountSummary['totalInvestedInSecurities']:0.2f}")))
    summary.appendChild(tr(td("Total current market value"), td(f"£{accountSummary['totalMarketValue']:0.2f}")))
    summary.appendChild(tr(td("Paper Capital Gain"), td(f"£{accountSummary['totalPaperGainForTax']:0.0f} ({accountSummary['totalPaperGainForTaxPerc']:0.2f}%)")))
    summary.appendChild(tr(td("Realised Capital gain"), td(f"£{accountSummary['totalRealisedGain']:0.0f}")))
    summary.appendChild(tr(td("Total Capital gain"), td(f"£{accountSummary['totalRealisedGain']+accountSummary['totalPaperGainForTax']:0.0f}")))
    summary.appendChild(tr(td("Total Dividends"), td(f"£{sum(accountSummary['dividendsPerYear'].values()):0.2f}")))
    summary.appendChild(tr(td("Avg Dividend Yield"), td(f"{mean(accountSummary['dividendYieldPerYear'].values()) if len(accountSummary['dividendYieldPerYear']) > 0 else 0:0.2f}%")))
    summary.appendChild(tr(td("Total Fees paid"), td(f"£{accountSummary['totalFees']:0.2f}")))
    summary.appendChild(tr(td("Total Dealing costs"), td(f"£{accountSummary['totalDealingCosts']:0.2f}")))
    summary.appendChild(tr(td("Total Return (Paper gain, dividends paid, realised gain, less fees and costs)"),td(f"£{accountSummary['totalGain']:0.2f} ({accountSummary['totalGainPerc']:0.2f}%)")))
    summary.appendChild(tr(td("Actual Return (Market value less Cash invested"), td(f"£{accountSummary['totalGainFromInvestments']:0.2f} ({accountSummary['totalGainFromInvPerc']:0.2f}%)")))

    startYear = accountSummary['dateOpened']
    endYear = datetime.now(timezone.utc) + timedelta(days=365) # Make sure we have this tax year
    timeHeld = endYear - startYear
    avgReturnPerYear = float(accountSummary['totalGain']) / (timeHeld.days / 365)
    summary.appendChild(tr(td("Average return per year"),td(f"£{avgReturnPerYear:0.2f}")))

    dom.appendChild(summary)
    procYear = startYear
    dom.appendChild(h2("\nYearly breakdown\n"))
    byYear = table()
    byYear.appendChild(tr(th('Cash In'),th('Cash Out'),th('Agg Invested'),th('Gain Realised (Tax)'),th('Dividends'),th('Yield%'),th('Dealing Costs'),th('Fees')))
    while procYear < endYear:
        years = (procYear-startYear).days/365
        taxYear = getTaxYear(procYear)
        values = list()
        yearRow = tr()
        yearRow.appendChild(td(f"£{accountSummary['cashInPerYear'].get(taxYear, 0):0.0f}"))
        yearRow.appendChild(td(f"£{accountSummary['cashOutPerYear'].get(taxYear, 0):0.0f}"))
        yearRow.appendChild(td(f"£{accountSummary['aggInvestedByYear'].get(taxYear, 0):0.0f}"))
        yearRow.appendChild(td(f"£{accountSummary['realisedGainForTaxPerYear'].get(taxYear, 0):0.0f}"))
        yearRow.appendChild(td(f"£{accountSummary['dividendsPerYear'].get(taxYear, 0):0.2f}"))
        yearRow.appendChild(td(f"{accountSummary['dividendYieldPerYear'].get(taxYear, 0):0.0f}%"))
        yearRow.appendChild(td(f"£{accountSummary['dealingCostsPerYear'].get(taxYear, 0):0.0f}"))
        yearRow.appendChild(td(f"£{accountSummary['feesPerYear'].get(taxYear, 0):0.0f}"))
        byYear.appendChild(yearRow)
        procYear += timedelta(days=365)
    dom.append(byYear)

    dom.append(h2('Stock Summary'))
    stockTable = table()
    stockTable.appendChild(tr(th('Stock'),th('Name'),th('Cash in'), th('Invested'), th('Divis'), th('Yield'),th('Gain')))
    for stock, details in stockLedger.items():
        stockRow = tr()
        stockRow.appendChild(td(f"{details['stockSymbol']}"))
        stockRow.appendChild(td(f"{details['stockName']}"))
        stockRow.appendChild(td(f"£{details['totalCashInvested']:0.0f}"))
        stockRow.appendChild(td(f"£{details['totalInvested']:0.0f}"))
        stockRow.appendChild(td(f"£{details['totalDividends']:0.0f}"))
        stockRow.appendChild(td(f"{details['averageYearlyDiviYield']:0.0f}%"))
        stockRow.appendChild(td(f"£{details['totalGain']:0.0f} ({details['totalGainPerc']:0.2f}%)"))
        stockTable.appendChild(stockRow)
    dom.append(stockTable)
    dom = html(dom)
    return f"{dom}"

def getStockSummaryStr(details):
    retStr = f"{details['stockSymbol']} {details['stockName']} "
    retStr += f"Cash in £{details['totalCashInvested']:0.2f} "
    retStr += f"Invested £{details['totalInvested']:0.2f} "
    retStr += f"Divis £{details['totalDividends']:0.2f}, Avg Yield: {details['averageYearlyDiviYield']:0.2f}% "
    retStr += f"Gain: £{details['totalGain']:0.2f}, ({details['totalGainPerc']:0.2f}%)\n"
    return retStr

def getStockLedgerStr(details):
    
    retStr = f"Stock: {details['stockSymbol']}\nDescription: {details['stockName']}\n\n"
    retStr += f"Held since {details['heldSince'].date()}\n"
    retStr += f"Cash invested £{details['totalCashInvested']:0.2f}\n"
    retStr += f"Number of shares: {details['stockHeld']}\n"
    retStr += f"Amount invested £{details['totalInvested']:0.2f}\n"
    retStr += f"Amount dividends re-invested £{details['totalDiviReinvested']:0.2f}\n"
    retStr += f"Average Share Price {details['avgSharePrice']:0.2f}\n"
    if details.get('currentSharePrice', None):
        retStr += f"Current Share Price {details['currentSharePrice']:0.2f}\n"
        retStr += f"Share price date {details['priceDate'].date()}\n"
        retStr += f"Current Market Value £{details['marketValue']:0.2f}\n"
        # retStr += f"Total Paper Gain £{details['totalPaperGain']:0.2f} {details['totalPaperGainPerc']:0.2f}%\n"
        retStr += f"Total Taxable Gain if sold £{details['totalPaperCGT']:0.2f} {details['totalPaperCGTPerc']:0.2f}%\n"
    else:
        retStr += "**** No current price data available, so total gain info doesnt include current value\n"
    retStr += f"Total Dividends £{details['totalDividends']:0.2f}\n"
    retStr += f"Average Yearly Dividend £{details['averageYearlyDivi']:0.2f}, Yield: {details['averageYearlyDiviYield']:0.2f}%\n"
    retStr += f"Stock Dealing costs £{details['dealingCosts']:0.2f}\n"
    retStr += f"Total Gain: £{details['totalGain']:0.2f}, ({details['totalGainPerc']:0.2f}%) \n"
    retStr += f"Average Gain per year: £{details['avgGainPerYear']:0.2f}, ({details['avgGainPerYearPerc']:0.2f}%) \n"

    divs = list()
    retStr += "\nDividends Per Year:\n"
    for year in details['dividendsPerYear'].keys():
        divs.append([year, details['dividendsPerYear'][year], details['dividendYieldPerYear'][year]])
    # divs = list(details['dividendsPerYear'].items())
    retStr += tabulate(divs, headers=['Tax Year', 'Dividend Paid', 'Yield'])

    retStr += "\n\nInvestments Made:\n"
    hist = list()
    for dc in details['investmentHistory']:
        hist.append(asdict(dc))
    retStr += tabulate(hist, headers='keys')

    retStr += "\n\nRealised Capital Gain (taxable) Per Year:\n"
    gains = list(details['realisedCapitalGainForTaxPerYear'].items())
    retStr += tabulate(gains, headers=['Tax Year', 'Realised Capital Gain (taxable value)'])

    retStr += "\n\nDealing Costs Per Year:\n"
    costs = list(details['dealingCostsPerYear'].items())
    retStr += tabulate(costs, headers=['Tax Year', 'Dealing Costs'])

    return retStr