
from tabulate import tabulate
from datetime import datetime, timedelta, date
from dataclasses import asdict

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
    retStr += f"Date account opened: {accountSummary['dateOpened']}\n"
    retStr += f"Total Currently invested: £{accountSummary['totalInvested']:0.2f}\n"
    retStr += f"Total Invested in Securities: £{accountSummary['totalInvestedInSecurities']:0.2f}\n"
    retStr += f"Capital Gain on paper: £{accountSummary['totalPaperGain']:0.2f}\n"
    retStr += f"Total Realised Capital gain: £{sum(accountSummary['realisedGainPerYear'].values()):0.2f}\n"
    retStr += f"Total Dividends: £{sum(accountSummary['dividendsPerYear'].values()):0.2f}\n"
    retStr += f"Total Fees paid: £{accountSummary['totalFees']:0.2f}\n"
    retStr += f"Total Dealing costs: £{accountSummary['totalDealingCosts']:0.2f}\n"
    totalReturn = accountSummary['totalGain'] - accountSummary['totalFees'] - accountSummary['totalDealingCosts']
    retStr += f"Total Return on paper (Paper gain, dividends paid, less fees and costs): £{totalReturn:0.2f}\n"
    procYear = accountSummary['dateOpened']
    endYear = datetime.now()
    timeHeld = endYear - procYear
    avgReturnPerYear = float(totalReturn) / (timeHeld.days / 365)
    retStr += f"Average return per year £{avgReturnPerYear:0.2f}\n"

    byYear = dict()
    while procYear < endYear:
        taxYear = getTaxYear(procYear)
        values = dict()
        values['Cash In'] = accountSummary['cashInPerYear'].get(taxYear, 0)
        values['Cash Out'] = accountSummary['cashOutPerYear'].get(taxYear, 0)
        values['Agg Invested'] = accountSummary['aggInvestedByYear'].get(taxYear, 0)
        values['Gain Realised'] = accountSummary['realisedCapitalTaxGainPerYear'].get(taxYear, 0)
        values['Dividends'] = accountSummary['dividendsPerYear'].get(taxYear, 0)
        values['Yield'] = accountSummary['dividendYieldPerYear'].get(taxYear, 0)
        values['DealingCosts'] = accountSummary['dealingCostsPerYear'].get(taxYear, 0)
        values['Fees'] = accountSummary['feesPerYear'].get(taxYear, 0)
        procYear += timedelta(days=365)
        byYear[taxYear] = values

    retStr += f"Yearly breakdown: \n"
    retStr += tabulate(byYear, headers='keys')
    return retStr

def getStockLedgerStr(details):
    
    retStr = f"Stock: {details['stockSymbol']} Description: {details['stockName']}\n\n"
    retStr += f"Held since {details['heldSince']}\n"
    retStr += f"Number of shares: {details['stockHeld']}\n"
    retStr += f"Amount invested {details['totalInvested']:0.2f}\n"
    retStr += f"Average Share Price {details['avgSharePrice']:0.2f}\n"
    if details.get('currentSharePrice', None):
        retStr += f"Current Share Price {details['currentSharePrice']:0.2f}\n"
        retStr += f"Share price date {details['priceDate']}\n"
        retStr += f"Total Paper Gain {details['totalPaperGain']:0.2f}\n"
    else:
        retStr += "**** No current price data available, so total gain info doesnt include current value\n"
    retStr += f"Total Dividends {sum(details['dividendsPerYear'].values()):0.2f}\n"
    retStr += f"Average Yearly Dividend Yield {details['averageYearlyDiviYield']:0.2f}\n"
    retStr += f"Stock Dealing costs {details['dealingCosts']:0.2f}\n"
    retStr += f"\nTotal Gain: {details['totalGain']:0.2f}\n"

    retStr += "Dividends Per Year:\n"
    divs = list(details['dividendsPerYear'].items())
    retStr += tabulate(divs, headers=['Tax Year', 'Dividend Paid'])

    retStr += "\nInvestments Made:\n"
    hist = list()
    for dc in details['investmentHistory']:
        hist.append(asdict(dc))
    retStr += tabulate(hist, headers='keys')

    retStr += "\nRealised Capital Gain Per Year:\n"
    gains = list(details['realisedCapitalGainPerYear'].items())
    retStr += tabulate(gains, headers=['Tax Year', 'Realised Capital Gain (taxable value)'])

    retStr += "\nCapital Gain For Tax Per Year:\n"
    gains = list(details['capitalGainForTaxPerYear'].items())
    retStr += tabulate(gains, headers=['Tax Year', 'Capital Gain (actual)'])

    retStr += "\nDealing Costs Per Year:\n"
    costs = list(details['dealingCostsPerYear'].items())
    retStr += tabulate(costs, headers=['Tax Year', 'Dealing Costs'])

    return retStr