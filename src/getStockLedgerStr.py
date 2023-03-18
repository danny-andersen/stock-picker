import io
import csv
from datetime import timedelta, datetime, timezone
from statistics import mean
from decimal import Decimal
from dataclasses import asdict
from tabulate import tabulate
import plotly.express as px
from pandas import DataFrame
from domonic.html import td, tr, th, a, body, table, h1, h2, h3, html, meta, style, head

from transactionDefs import (
    AccountSummary,
    getTaxYear,
    FundType,
    SecurityDetails,
    CapitalGain,
)


def getAccountSummaryStrs(accountSummary: AccountSummary):
    retStrs = dict()
    ht = html(meta(_charset="UTF-8"))
    ht.appendChild(
        head(
            style(
                """
              .positive { color: green}
              .negative { color: red}
        """
            )
        )
    )
    dom = body()
    nowDate: datetime = datetime.now()
    if accountSummary.name == "Total":
        allAccounts = True
    else:
        allAccounts = False
    if allAccounts:
        dom.appendChild(h1("Summary for all Accounts\n"))
    else:
        dom.appendChild(h1(f"Summary for Account: {accountSummary.name}\n"))
    dom.appendChild(h2(f"Account Owner: {accountSummary.owner}\n"))
    smry = table()
    smry.appendChild(tr(td("Date report generated"), td(f"{nowDate.date()}")))
    smry.appendChild(
        tr(
            td("Portfolio Valuation Date"),
            td(f"{accountSummary.portfolioValueDate.date()}"),
        )
    )
    smry.appendChild(
        tr(td("Date account opened"), td(f"{accountSummary.dateOpened.date()}"))
    )
    smry.appendChild(
        tr(
            td("Total cash invested in account (all cash in less cash out)"),
            td(f"£{accountSummary.totalCashInvested():,.0f}"),
        )
    )
    smry.appendChild(
        tr(
            td("Total Dividends re-invested in account"),
            td(f"£{accountSummary.totalDiviReInvested:,.0f}"),
        )
    )
    smry.appendChild(
        tr(td("Total Dividends"), td(f"£{accountSummary.totalDividends():,.0f}"))
    )
    smry.appendChild(
        tr(
            td("Avg Dividend Yield"),
            td(
                f"{mean(accountSummary.dividendYieldByYear.values()) if len(accountSummary.dividendYieldByYear) > 0 else 0:0.2f}%"
            ),
        )
    )
    smry.appendChild(
        tr(td("Total Income"), td(f"£{accountSummary.totalIncome():,.0f}"))
    )
    smry.appendChild(
        tr(td("Avg Income Yield"), td(f"{accountSummary.avgIncomeYield():.2f}%"))
    )
    smry.appendChild(
        tr(td("Avg Total Yield"), td(f"{accountSummary.avgTotalYield():.2f}%"))
    )
    smry.appendChild(
        tr(
            td("Total Divi + Income"),
            td(
                f"£{accountSummary.totalIncome() + accountSummary.totalDividends():,.0f}"
            ),
        )
    )
    smry.appendChild(
        tr(td("Total Fees paid"), td(f"£{accountSummary.totalFees():,.0f}"))
    )
    smry.appendChild(
        tr(td("Total Dealing costs"), td(f"£{accountSummary.totalDealingCosts():,.0f}"))
    )
    smry.appendChild(
        tr(
            td("Total Historic Realised Capital gain"),
            td(f"£{accountSummary.totalRealisedGain():,.0f}"),
        )
    )
    smry.appendChild(
        tr(
            td("Total currently invested in securities"),
            td(f"£{accountSummary.totalInvestedInSecurities:,.0f}"),
        )
    )
    smry.appendChild(
        tr(
            td("Total current market value (of investments)"),
            td(f"£{accountSummary.totalMarketValue:,.0f}"),
        )
    )
    smry.appendChild(
        tr(
            td("Total Paper Capital Gain of current holdings"),
            td(
                f"£{accountSummary.totalPaperGainForTax:,.0f} ({accountSummary.totalPaperGainForTaxPerc():0.2f}%)",
                _class="positive"
                if accountSummary.totalPaperGainForTax > 0
                else "negative",
            ),
        )
    )
    smry.appendChild(tr(td("Cash Balance"), td(f"£{accountSummary.cashBalance:,.0f}")))
    if accountSummary.totalOtherAccounts > 0:
        smry.appendChild(
            tr(
                td("Total held in other accounts"),
                td(f"£{accountSummary.totalOtherAccounts:,.0f}"),
            )
        )
    smry.appendChild(
        tr(
            td("Total Account Market Value and cash"),
            td(f"£{accountSummary.totalValue():,.0f}"),
            _style="font-weight: bold;",
        )
    )
    smry.appendChild(
        tr(
            td("Total Capital gain (realised + current on paper)"),
            td(
                f"£{accountSummary.totalGainFromInvestments():,.0f}",
                _class="positive"
                if accountSummary.totalGainFromInvestments() > 0
                else "negative",
            ),
            _style="font-weight: bold;",
        )
    )
    smry.appendChild(
        tr(
            td(
                "Total Historic Return (Paper + realised gain. divi / income / interest paid, less fees and costs)"
            ),
            td(
                f"£{accountSummary.totalGainLessFees():,.0f} ({accountSummary.totalGainPerc():0.2f}%)",
                _class="positive"
                if accountSummary.totalGainLessFees() > 0
                else "negative",
            ),
            _style="font-weight: bold;",
        )
    )

    smry.appendChild(
        tr(
            td("Average return per year"),
            td(
                f"£{accountSummary.avgReturnPerYear():,.0f}",
                _class="positive"
                if accountSummary.totalGainLessFees() > 0
                else "negative",
            ),
            _style="font-weight: bold;",
        )
    )
    dom.appendChild(smry)

    dom.appendChild(h2("Tax liability"))
    currentTaxYear = getTaxYear(datetime.now())
    lastTaxYear = getTaxYear(datetime.now() - timedelta(weeks=52))
    if len(accountSummary.mergedAccounts) == 0:
        # Single account
        accounts = [accountSummary]
    else:
        accounts = accountSummary.mergedAccounts
    for yr in [lastTaxYear, currentTaxYear]:
        dom.appendChild(h3(f"Tax Year {yr}"))
        tx = table()
        tx.appendChild(
            tr(
                th(" Account "),
                th(" Capital Gain "),
                th(" Taxable CG "),
                th(" CG Tax "),
                th(" CGT Rem Allowance "),
                th(" Divi "),
                th(" Taxable Divi "),
                th(" Divi Tax "),
                th(" Divi All Rem "),
                th(" Income "),
                th(" Income Tax "),
            )
        )
        totalCG = Decimal(0.0)
        totalTaxableCG = Decimal(0.0)
        totalCGT = Decimal(0.0)
        totalDivi = Decimal(0.0)
        totalTaxableDivi = Decimal(0.0)
        totalDiviTax = Decimal(0.0)
        totalIncome = Decimal(0.0)
        totalIncomeTax = Decimal(0.0)
        for account in accounts:
            band = account.taxBandByYear.get(yr, "lower")
            cg = (
                account.realisedGainForTaxByYear.get(yr, Decimal(0.0))
                if len(account.realisedGainForTaxByYear) > 0
                else Decimal(0.0)
            )
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
            tx.appendChild(
                tr(
                    td(a(f"{account.name}", _href=accountLocation)),
                    td(f"£{cg:,.0f}"),
                    td(f"£{taxablecg:,.0f}"),
                    td(
                        f"£{cgt:,.0f}",
                        _class="positive" if cgt == 0 else "negative",
                    ),
                    td("-"),
                    td(f"£{divi:,.0f}"),
                    td(f"£{taxableDivi:,.0f}"),
                    td(
                        f"£{diviTax:,.0f}",
                        _class="positive" if diviTax == 0 else "negative",
                    ),
                    td("-"),
                    td(f"£{income:,.0f}"),
                    td(
                        f"£{incomeTax:,.0f}",
                        _class="positive" if incomeTax == 0 else "negative",
                    ),
                )
            )
        # Note: Use last account processed to get remaining allowance info
        tx.appendChild(
            tr(
                td("Total"),
                td(f"£{totalCG:,.0f}"),
                td(f"£{totalTaxableCG:,.0f}"),
                td(
                    f"£{totalCGT:,.0f}",
                    _class="positive" if totalCGT == 0 else "negative",
                ),
                td(f"£{account.getRemainingCGTAllowance(totalTaxableCG):,.0f}"),
                td(f"£{totalDivi:,.0f}"),
                td(f"£{totalTaxableDivi:,.0f}"),
                td(
                    f"£{totalDiviTax:,.0f}",
                    _class="positive" if totalDiviTax == 0 else "negative",
                ),
                td(f"£{account.getRemainingDiviAllowance(totalTaxableDivi):,.0f}"),
                td(f"£{totalIncome:,.0f}"),
                td(
                    f"£{totalIncomeTax:,.0f}",
                    _class="positive" if totalIncomeTax == 0 else "negative",
                ),
                _style="font-weight: bold;",
            )
        )
        dom.appendChild(tx)
        dom.appendChild(h3("Taxable Capital Gain Transactions"))
        tx = table()
        tx.appendChild(
            tr(
                th(" Account "),
                th(" Date "),
                th(" Stock "),
                th(" Qty "),
                th(" Avg Buy Price "),
                th(" Sell Price "),
                th(" Capital Gain "),
            )
        )
        totalTaxableCG = Decimal(0.0)
        cgtxns: list[(account, SecurityDetails, CapitalGain)] = []
        for account in accounts:
            accountLocation = f"./{account.name}-Summary.html#Tax%20Liability"
            cgRealised = account.realisedGainForTaxByYear.get(yr, 0)
            if cgRealised > 0 and Decimal(account.taxRates["capitalgainlowertax"]) > 0:
                # Have some CGT for this year for this account - go through each stock to get the CG transactions for that tax year - this will include all historic stocks
                for stock in account.stocks:
                    txns = stock.cgtransactionsByYear.get(yr, [])
                    for details in stock.historicHoldings:
                        txns.extend(details.cgtransactionsByYear.get(yr, []))
                    for txn in txns:
                        cgtxns.append((account, stock, txn))
        cgtxns = sorted(cgtxns, key=lambda txn: txn[-1].date, reverse=False)
        for cgtxn in cgtxns:
            (account, stock, cg) = cgtxn
            capGain = cg.qty * (cg.price - cg.avgBuyPrice)
            totalTaxableCG += capGain
            tx.appendChild(
                tr(
                    td(a(f"{account.name}", _href=accountLocation)),
                    td(f"{cg.date.date()}"),
                    td(
                        a(
                            f"{stock.symbol}",
                            _href=f"./{account.name}/{stock.symbol}.txt",
                        )
                    ),
                    td(f"{cg.qty:,.0f}"),
                    td(f"£{cg.avgBuyPrice:,.2f}"),
                    td(f"£{cg.price:,.2f}"),
                    td(f"£{capGain:,.2f}"),
                )
            )
        tx.appendChild(
            tr(
                td("Total"),
                td("-"),
                td("-"),
                td("-"),
                td("-"),
                td("-"),
                td(f"£{totalTaxableCG:,.0f}"),
                _style="font-weight: bold;",
            )
        )

        dom.appendChild(tx)

    if len(accountSummary.historicValue) > 0:
        dom.appendChild(h2("Historic value and return"))
        fundTypes = [
            FundType.FUND,
            FundType.SHARE,
            FundType.CORP_BOND,
            FundType.LONG_GILT,
        ]
        gainDict: dict[str, list] = {"Date": list()}
        gainDict["Total"] = list()
        for ft in fundTypes:
            gainDict[ft.name] = list()
        fs = table()
        fs.appendChild(
            tr(
                th("Date"),
                th("Total Market Value"),
                th("Total Book Cost"),
                th("Gain"),
                "".join([f'{th(ftyp.name+"   ")}' for ftyp in fundTypes]),
                "".join([f'{th(ftyp.name+"   ")}' for ftyp in fundTypes]),
            )
        )
        fs.appendChild(
            tr(
                th(""),
                th(""),
                th(""),
                th(""),
                th("Acc%"),
                th("Acc%"),
                th("Acc%"),
                th("Acc%"),
                th("Gain%"),
                th("Gain%"),
                th("Gain%"),
                th("Gain%"),
            )
        )
        dtime: datetime
        marketValue: Decimal
        bookCost: Decimal
        dateList = list(accountSummary.historicValue)
        dateList.sort()
        for dtime in dateList:
            (marketValue, bookCost) = accountSummary.historicValue[dtime]
            accgain = (
                100 * float((marketValue - bookCost) / bookCost) if bookCost > 0 else 0
            )
            gainDict["Date"].append(dtime)
            gainDict["Total"].append(accgain)
            lastElem = len(gainDict["Date"]) - 1
            ftv = accountSummary.historicValueByType[dtime]
            for ftyp in fundTypes:
                gainDict[ftyp.name].append(
                    100.0
                    * float(
                        (ftv.get(ftyp, (0, 0))[0] - ftv.get(ftyp, (0, 0))[1])
                        / ftv.get(ftyp, (1, 1))[1]
                    )
                )
            fs.appendChild(
                tr(
                    td(f"{dtime.date()}"),
                    td(f"£{marketValue:,.0f}"),
                    td(f"£{bookCost:,.0f}"),
                    td(f"{accgain:0.2f}%"),
                    "".join(
                        [
                            f"{td(100.0*float(ftv.get(ftyp,(0,0))[0]/marketValue)):0.1f}"
                            for ftyp in fundTypes
                        ]
                    ),
                    "".join(
                        [
                            f"{td(gainDict[ftyp.name][lastElem]):0.1f}"
                            for ftyp in fundTypes
                        ]
                    ),
                    _class="positive" if accgain > 0 else "negative",
                )
            )
        dom.appendChild(fs)
        df = DataFrame(gainDict)
        fig = px.line(
            df,
            x="Date",
            y=df.columns,
            hover_data={"Date": "|%B %d, %Y"},
            title="Gain % by asset type",
            labels={"value": "% Gain"},
        )
        fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
        # fig.show()
        dom.appendChild(fig.to_html())

    dom.appendChild(h2("Statistics By Investment Type"))
    dom.appendChild(h3("Fund values and returns (including other accounts)"))
    fs = table()
    funds = accountSummary.fundTotals
    isTotalAcc = len(accountSummary.mergedAccounts) > 0
    totalAccountValue = accountSummary.totalValue()
    if totalAccountValue == 0:
        totalAccountValue = Decimal(1.0)
    if isTotalAcc:
        fs.appendChild(
            tr(
                th("Type"),
                th("Total Invested"),
                th("Total Market Value"),
                th("%Account"),
                "".join(
                    [
                        f'{th(a(acc.name, _href="./"+acc.name+"-Summary.html#Statistics%20By%20Investment%20Type"))}'
                        for acc in accountSummary.mergedAccounts
                    ]
                ),
                th("Avg Fees"),
                th("Avg Ret"),
                th("3yr Ret"),
                th("5yr Ret"),
            )
        )
    else:
        fs.appendChild(
            tr(
                th("Type"),
                th("Total Invested"),
                th("Total Market Value"),
                th("%Account"),
                th("Avg Fees"),
                th("Avg Ret"),
                th("3yr Ret"),
                th("5yr Ret"),
            )
        )
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
            accFunds = (
                f"{acc.fundTotals[typ].totalValue if typ in acc.fundTotals else 0:,.0f}"
                for acc in accountSummary.mergedAccounts
            )
            fs.appendChild(
                tr(
                    td(typ.name),
                    td(f"£{fund.totalInvested:,.0f}"),
                    td(f"£{fund.totalValue:,.0f}"),
                    td(f"{100*fund.totalValue/totalAccountValue:0.2f}%"),
                    "".join([f"{td(acc)}" for acc in accFunds]),
                    td(f"{fund.fees:0.2f}%"),
                    td(f"{fund.actualReturn:0.2f}%"),
                    td(f"{fund.return3Yr:0.2f}%"),
                    td(f"{fund.return5Yr:0.2f}%"),
                    _class="positive" if fund.actualReturn > 0 else "negative",
                )
            )
        else:
            fs.appendChild(
                tr(
                    td(typ.name),
                    td(f"£{fund.totalInvested:,.0f}"),
                    td(f"£{fund.totalValue:,.0f}"),
                    td(f"{100*fund.totalValue/totalAccountValue:0.2f}%"),
                    td(f"{fund.fees:0.2f}%"),
                    td(f"{fund.actualReturn:0.2f}%"),
                    td(f"{fund.return3Yr:0.2f}%"),
                    td(f"{fund.return5Yr:0.2f}%"),
                    _class="positive" if fund.actualReturn > 0 else "negative",
                )
            )
        totInvested += fund.totalInvested
        totValue += fund.totalValue
        val = float(fund.totalValue)
        totfees += fund.fees * val
        totRet += fund.actualReturn * val
        tot3yrRet += fund.return3Yr * val
        tot5yrRet += fund.return5Yr * val
        if fund.isStockType():
            totStocks += fund.totalValue
        elif fund.isBondType():
            totBonds += fund.totalValue
        elif fund.isCashType():
            totCash += fund.totalValue
        elif fund.isGoldType():
            totGold += fund.totalValue
    totValue = totValue if totValue else Decimal(1.0)
    tot = float(totValue)
    if isTotalAcc:
        accTots = (f"{acc.totalValue():,.0f}" for acc in accountSummary.mergedAccounts)
        fs.appendChild(
            tr(
                td("Overall"),
                td(f"£{totInvested:,.0f}"),
                td(f"£{totValue:,.0f}"),
                td(f"{100*totValue/totalAccountValue:0.02f}%"),
                "".join([f"{td(accTot)}" for accTot in accTots]),
                td(f"{totfees/tot:0.02f}%"),
                td(f"{totRet/tot:0.02f}%"),
                td(f"{tot3yrRet/tot:0.02f}%"),
                td(f"{tot5yrRet/tot:0.02f}%"),
                _class="positive" if totRet > 0 else "negative",
                _style="font-weight: bold;",
            )
        )
    else:
        fs.appendChild(
            tr(
                td("Overall"),
                td(f"£{totInvested:,.0f}"),
                td(f"£{totValue:,.0f}"),
                td(f"{100*totValue/totalAccountValue:0.02f}%"),
                td(f"{totfees/tot:0.02f}%"),
                td(f"{totRet/tot:0.02f}%"),
                td(f"{tot3yrRet/tot:0.02f}%"),
                td(f"{tot5yrRet/tot:0.02f}%"),
                _class="positive" if totRet > 0 else "negative",
                _style="font-weight: bold;",
            )
        )
    dom.appendChild(fs)
    dom.appendChild(h3("Portfolio Percentages and guardrails"))
    fs = table()
    fs.appendChild(
        tr(
            th("Type"),
            th(" Total Market Value "),
            th(" Portfolio% "),
            th("  Min%  "),
            th("  Ideal%"),
            th("  Max%"),
            th("  Buy / (Sell)  "),
        )
    )
    stocksPerc = 100 * totStocks / totalAccountValue
    smin = int(portPerc["stocks_min"])
    smax = int(portPerc["stocks_max"])
    ideal = int(portPerc["stocks_ideal"])
    buy = ""
    cls = "positive"
    if stocksPerc <= smin:
        buy = f"£{(ideal-stocksPerc)*totalAccountValue/100:,.0f}"
        cls = "negative"
    elif stocksPerc >= smax:
        buy = f"(£{(stocksPerc-ideal)*totalAccountValue/100:,.0f})"
        cls = "negative"
    # if stocksPerc <= ideal:
    #     if smin smin(smin * 0.05)
    fs.appendChild(
        tr(
            td("Stocks"),
            td(f"£{totStocks:,.0f}"),
            td(f"{stocksPerc:0.02f}%"),
            td(f"{smin:0.01f}%"),
            td(f"{ideal:0.01f}%"),
            td(f"{smax:0.01f}%"),
            td(buy),
            _class=cls,
        )
    )
    bondsPerc = 100 * totBonds / totalAccountValue
    smin = int(portPerc["bonds_min"])
    smax = int(portPerc["bonds_max"])
    ideal = int(portPerc["bonds_ideal"])
    buy = ""
    if bondsPerc <= smin:
        buy = f"£{(ideal-bondsPerc)*totalAccountValue/100:,.0f}"
    elif bondsPerc >= smax:
        buy = f"(£{(bondsPerc-ideal)*totalAccountValue/100:,.0f})"
    fs.appendChild(
        tr(
            td("Bonds"),
            td(f"£{totBonds:,.0f}"),
            td(f"{bondsPerc:0.02f}%"),
            td(f"{smin:0.01f}%"),
            td(f"{ideal:0.01f}%"),
            td(f"{smax:0.01f}%"),
            td(buy),
        )
    )
    cashPerc = 100 * totCash / totalAccountValue
    smin = int(portPerc["cash_min"])
    smax = int(portPerc["cash_max"])
    ideal = int(portPerc["cash_ideal"])
    buy = ""
    if cashPerc <= smin:
        buy = f"£{(ideal-cashPerc)*totalAccountValue/100:,.0f}"
    elif cashPerc >= smax:
        buy = f"(£{(cashPerc-ideal)*totalAccountValue/100:,.0f})"
    fs.appendChild(
        tr(
            td("Cash"),
            td(f"£{totCash:,.0f}"),
            td(f"{cashPerc:0.02f}%"),
            td(f"{smin:0.01f}%"),
            td(f"{ideal:0.01f}%"),
            td(f"{smax:0.01f}%"),
            td(buy),
        )
    )
    goldPerc = 100 * totGold / totalAccountValue
    smin = int(portPerc["gold_min"])
    smax = int(portPerc["gold_max"])
    ideal = int(portPerc["gold_ideal"])
    buy = ""
    if goldPerc <= smin:
        buy = f"£{(ideal-goldPerc)*totalAccountValue/100:,.0f}"
    elif cashPerc >= smax:
        buy = f"(£{(goldPerc-ideal)*totalAccountValue/100:,.0f})"
    fs.appendChild(
        tr(
            td("Gold"),
            td(f"£{totGold:,.0f}"),
            td(f"{goldPerc:0.02f}%"),
            td(f"{smin:0.01f}%"),
            td(f"{ideal:0.01f}%"),
            td(f"{smax:0.01f}%"),
            td(buy),
        )
    )
    fs.appendChild(
        tr(
            td("Total"),
            td(f"£{totGold+totCash+totBonds+totStocks:,.0f}"),
            td(f"{goldPerc+cashPerc+bondsPerc+stocksPerc:0.02f}%"),
        )
    )
    dom.appendChild(fs)
    if len(accountSummary.totalByInstitution) > 0:
        dom.appendChild(h3("Value by Institution"))
        fi = table()
        totVal = Decimal(0.0)
        val = Decimal(0.0)
        fi.appendChild(tr(th("Institution"), th("Value"), th("Total Account %")))
        for inst, val in accountSummary.totalByInstitution.items():
            fi.appendChild(
                tr(
                    td(inst),
                    td(f"£{val:,.0f}"),
                    td(f"{100.0*float(val/totalAccountValue):0.02f}%"),
                )
            )
            totVal += val
        fi.appendChild(
            tr(
                td("Total"),
                td(f"£{totVal:,.0f}"),
                td(f"{100.0*float(totVal/totalAccountValue):0.02f}%"),
            )
        )
        dom.appendChild(fi)

    dom.appendChild(h3("Fund Risks"))
    fr = table()
    fr.appendChild(
        tr(
            th("Type"),
            th("Alpha"),
            th("Beta"),
            th("Sharpe"),
            th("Std Dev"),
            th("Maturity yrs"),
        )
    )
    totAlpha = 0.0
    totBeta = 0.0
    totSharpe = 0.0
    totSD = 0.0
    totalNonShareVal = 0.0
    totMat = 0.0
    totMatVal = 0.0
    for typ, fund in funds.items():
        if typ != FundType.SHARE:
            totPerc = fund.alpha3Yr + fund.beta3Yr + fund.sharpe3Yr + fund.stdDev3Yr
            fr.appendChild(
                tr(
                    td(typ.name),
                    td(f"{fund.alpha3Yr:0.02f}"),
                    td(f"{fund.beta3Yr:0.02f}"),
                    td(f"{fund.sharpe3Yr:0.02f}"),
                    td(f"{fund.stdDev3Yr:0.02f}", td(f"{fund.maturity:0.02f}")),
                )
            )
            val = float(fund.totalValue)
            if totPerc > 0:
                totalNonShareVal += val
                totAlpha += fund.alpha3Yr * val
                totBeta += fund.beta3Yr * val
                totSharpe += fund.sharpe3Yr * val
                totSD += fund.stdDev3Yr * val
            if fund.maturity > 0:
                totMat += fund.maturity * val
                totMatVal += val
    if totalNonShareVal == 0:
        totalNonShareVal = 1.0
    if totMatVal == 0:
        totMatVal = 1.0
    fr.appendChild(
        tr(
            td("Overall"),
            td(f"{totAlpha/totalNonShareVal:0.02f}"),
            td(f"{totBeta/totalNonShareVal:0.02f}"),
            td(f"{totSharpe/totalNonShareVal:0.02f}"),
            td(f"{totSD/totalNonShareVal:0.02f}"),
            td(f"{totMat/totMatVal:0.02f}"),
        )
    )
    dom.appendChild(fr)
    dom.appendChild(h3("Geographical Spread"))
    fr = table()
    fr.appendChild(
        tr(
            th("Type"),
            th("Americas"),
            th("Americas-Emerging"),
            th("Asia"),
            th("Asia-Emerging"),
            th("UK"),
            th("Europe"),
            th("Europe-Emerging"),
            th("Total"),
        )
    )
    totamer = 0.0
    totamerem = 0.0
    totasia = 0.0
    totasiaem = 0.0
    totuk = 0.0
    toteuro = 0.0
    toteuroem = 0.0
    totVal = 0.0
    for typ, fund in funds.items():
        totPerc = (
            fund.americas
            + fund.americasEmerging
            + fund.asia
            + fund.asiaEmerging
            + fund.uk
            + fund.europe
            + fund.europeEmerging
        )
        fr.appendChild(
            tr(
                td(typ.name),
                td(f"{fund.americas:0.02f}%"),
                td(f"{fund.americasEmerging:0.02f}%"),
                td(f"{fund.asia:0.02f}%"),
                td(f"{fund.asiaEmerging:0.02f}%"),
                td(f"{fund.uk:0.02f}%"),
                td(f"{fund.europe:0.02f}%"),
                td(f"{fund.europeEmerging:0.02f}%"),
                td(f"{totPerc:0.02f}%"),
            )
        )
        if totPerc != 0:
            val = float(fund.totalValue)
            totamer += fund.americas * val
            totamerem += fund.americasEmerging * val
            totasia += fund.asia * val
            totasiaem += fund.asiaEmerging * val
            totuk += fund.uk * val
            toteuro += fund.europe * val
            toteuroem += fund.europeEmerging * val
            totVal += val
    totVal = totVal if totVal else 1.0
    totPerc = (
        totamer + totamerem + totasia + totasiaem + totuk + toteuro + toteuroem
    ) / totVal
    fr.appendChild(
        tr(
            td("Overall"),
            td(f"{totamer/totVal:0.02f}%"),
            td(f"{totamerem/totVal:0.02f}%"),
            td(f"{totasia/totVal:0.02f}%"),
            td(f"{totasiaem/totVal:0.02f}%"),
            td(f"{totuk/totVal:0.02f}%"),
            td(f"{toteuro/totVal:0.02f}%"),
            td(f"{toteuroem/totVal:0.02f}%"),
            td(f"{totPerc:0.02f}%"),
        )
    )
    dom.appendChild(fr)
    dom.appendChild(h3("Fund Diversity"))
    fr = table()
    fr.appendChild(
        tr(th("Type"), th("Cyclical"), th("Sensitive"), th("Defensive"), th("Total"))
    )
    totCyc = 0.0
    totSens = 0.0
    totDef = 0.0
    totVal = 0.0
    for typ, fund in funds.items():
        if typ != FundType.SHARE:
            totPerc = fund.cyclical + fund.sensitive + fund.defensive
            fr.appendChild(
                tr(
                    td(typ.name),
                    td(f"{fund.cyclical:0.02f}%"),
                    td(f"{fund.sensitive:0.02f}%"),
                    td(f"{fund.defensive:0.02f}%"),
                    td(f"{totPerc:0.02f}%"),
                )
            )
            if totPerc != 0:
                val = float(fund.totalValue)
                totCyc += fund.cyclical * val
                totSens += fund.sensitive * val
                totDef += fund.defensive * val
                totVal += val
    totVal = totVal if totVal else 1.0
    totPerc = (totCyc + totSens + totDef) / totVal
    fr.appendChild(
        tr(
            td("Overall"),
            td(f"{totCyc/totVal:0.2f}%"),
            td(f"{totSens/totVal:0.2f}%"),
            td(f"{totDef/totVal:0.2f}%"),
            td(f"{totPerc:0.2f}%"),
        )
    )
    dom.appendChild(fr)

    startYear = accountSummary.dateOpened
    endYear = datetime.now(timezone.utc) + timedelta(
        days=365
    )  # Make sure we have this tax year
    # endYear = datetime.now(timezone.utc)
    procYear = startYear
    dom.appendChild(h2("Yearly breakdown"))
    byYear = table()
    byYear.appendChild(
        tr(
            th("Year"),
            th("Cash In"),
            th("Cash Out"),
            th("Agg Invested"),
            th("Gain Realised"),
            th("Dividends"),
            th("Yield%"),
            th("Dealing Costs"),
            th("Fees"),
        )
    )
    while procYear < endYear:
        taxYear = getTaxYear(procYear)
        yearRow = tr()
        yearRow.appendChild(td(f"{taxYear}"))
        yearRow.appendChild(
            td(f"£{accountSummary.cashInByYear.get(taxYear, Decimal(0.0)):,.0f}")
        )
        yearRow.appendChild(
            td(f"£{accountSummary.cashOutByYear.get(taxYear, Decimal(0.0)):,.0f}")
        )
        yearRow.appendChild(
            td(f"£{accountSummary.aggInvestedByYear.get(taxYear, Decimal(0.0)):,.0f}")
        )
        yearRow.appendChild(
            td(
                f"£{accountSummary.realisedGainForTaxByYear.get(taxYear, Decimal(0.0)):,.0f}"
            )
        )
        yearRow.appendChild(
            td(f"£{accountSummary.dividendsByYear.get(taxYear, Decimal(0.0)):,.0f}")
        )
        yearRow.appendChild(
            td(f"{accountSummary.dividendYieldByYear.get(taxYear, Decimal(0.0)):,.0f}%")
        )
        yearRow.appendChild(
            td(f"£{accountSummary.dealingCostsByYear.get(taxYear, Decimal(0.0)):,.0f}")
        )
        yearRow.appendChild(
            td(f"£{accountSummary.feesByYear.get(taxYear, Decimal(0.0)):,.0f}")
        )
        byYear.appendChild(yearRow)
        procYear += timedelta(days=365)
    dom.append(byYear)

    getSecurityStrs(accountSummary, allAccounts, dom, retStrs)

    dom.appendChild(h2("Payments by Tax Year"))
    for yr in [lastTaxYear, currentTaxYear]:
        dom.appendChild(h3(f"Tax Year {yr}"))
        dom.appendChild(h3("Dividend Payments"))
        txnTable = table()
        if allAccounts:
            txnTable.appendChild(
                tr(th("Account"), th("Date"), th("Txn Type"), th("Desc"), th("Amount"))
            )
        else:
            txnTable.appendChild(
                tr(th("Date"), th("Txn Type"), th("Desc"), th("Amount"))
            )
        total = Decimal(0)
        txns = sorted(
            accountSummary.dividendTxnsByYear[yr]
            if yr in accountSummary.dividendTxnsByYear
            else list(),
            key=lambda txn: txn.date,
            reverse=True,
        )
        for txn in txns:
            row = tr()
            if allAccounts:
                accountLocation = (
                    f"./{txn.accountName}-Summary.html#Dividend%20Payments"
                )
                row.appendChild(td(a(f"{txn.accountName}", _href=accountLocation)))
            row.appendChild(td(f"{txn.date}"))
            row.appendChild(td(f"{txn.type}"))
            row.appendChild(td(f"{txn.desc}"))
            row.appendChild(
                td(f"£{txn.credit if txn.credit != 0 else -txn.debit:0.2f}")
            )
            total += txn.credit
            txnTable.appendChild(row)
        txnTable.appendChild(tr(td(" "), td("Total"), td(" "), td(f"£{total:,.0f}")))
        dom.append(txnTable)
        dom.appendChild(h3("Income Payments"))
        txnTable = table()
        if allAccounts:
            txnTable.appendChild(
                tr(th("Account"), th("Date"), th("Txn Type"), th("Desc"), th("Amount"))
            )
        else:
            txnTable.appendChild(
                tr(th("Date"), th("Txn Type"), th("Desc"), th("Amount"))
            )
        total = Decimal(0)
        txns = (
            list(accountSummary.incomeTxnsByYear[yr])
            if yr in accountSummary.incomeTxnsByYear
            else list()
        )
        txns.extend(
            list(accountSummary.interestTxnsByYear[yr])
            if yr in accountSummary.interestTxnsByYear
            else list()
        )
        txns = sorted(txns, key=lambda txn: txn.date, reverse=True)
        for txn in txns:
            row = tr()
            if allAccounts:
                accountLocation = f"./{txn.accountName}-Summary.html#Income%20Payments"
                row.appendChild(td(a(f"{txn.accountName}", _href=accountLocation)))
            row.appendChild(td(f"{txn.date}"))
            row.appendChild(td(f"{txn.type}"))
            row.appendChild(td(f"{txn.desc}"))
            row.appendChild(
                td(f"£{txn.credit if txn.credit != 0 else -txn.debit:0.2f}")
            )
            total += txn.credit
            txnTable.appendChild(row)
        txnTable.appendChild(tr(td(" "), td("Total"), td(" "), td(f"£{total:,.0f}")))
        dom.append(txnTable)

    dom.append(h2("Account transactions"))
    txnTable = table()
    if allAccounts:
        txnTable.appendChild(
            tr(
                th("Date"),
                th("Account"),
                th("Txn Type"),
                th("Symbol"),
                th("Desc"),
                th("Amount"),
                th("Balance"),
            )
        )
    else:
        txnTable.appendChild(
            tr(
                th("Date"),
                th("Txn Type"),
                th("Symbol"),
                th("Desc"),
                th("Amount"),
                th("Balance"),
            )
        )
    txns = sorted(accountSummary.transactions, key=lambda txn: txn.date, reverse=True)
    for txn in txns:
        row = tr()
        row.appendChild(td(f"{txn.date}"))
        if allAccounts:
            accountLocation = f"./{txn.accountName}-Summary.html#Income%20Payments"
            row.appendChild(td(a(f"{txn.accountName}", _href=accountLocation)))
        row.appendChild(td(f"{txn.type}"))
        detailLocation = f"./{txn.accountName}/{txn.symbol}.txt"
        row.appendChild(td(a(f"{txn.symbol}", _href=detailLocation)))
        row.appendChild(td(f"{txn.desc}"))
        row.appendChild(td(f"£{txn.credit if txn.credit != 0 else -txn.debit:0.2f}"))
        row.appendChild(td(f"£{txn.accountBalance:0.2f}"))
        txnTable.appendChild(row)
    dom.appendChild(txnTable)

    ht.append(dom)
    retStrs[f"{accountSummary.name}-Summary.html"] = f"{ht}"
    return retStrs


def getSecurityStrs(
    accountSummary: AccountSummary,
    allAccounts: bool,
    dom: body,
    fileStrs: dict[str, str],
):
    historicStocks: list[SecurityDetails] = list()
    dom.append(h2("Security Summary"))
    stockTable = table()
    headings = ["Security"]
    if allAccounts:
        headings.append("Account")
    headings.extend(
        [
            "Type",
            "Name",
            "Fees",
            "Cash inv",
            "Market Value",
            "Yield",
            "Return",
            "Years Held",
            "Annualised Ret",
            "3yr-Ret",
            "5yr-Ret",
            "Alpha",
            "Beta",
            "Sharpe",
        ]
    )
    headrow = tr()
    for hd in headings:
        headrow.appendChild(th(hd))
    stockTable.appendChild(headrow)
    if len(accountSummary.stocks) > 0:
        secIO = io.StringIO()
        csvOut = csv.DictWriter(secIO, headings)
        csvOut.writeheader()
    else:
        csvOut = None
    for stockDetails in accountSummary.stocks:
        csvRow = {title: "" for title in headings}
        historicStocks.extend(stockDetails.historicHoldings)
        if stockDetails.totalInvested != 0:
            stockRow = tr(
                _class="positive" if stockDetails.totalGain() > 0 else "negative",
            )
            symbol = stockDetails.symbol
            if symbol != "":
                if symbol.endswith("."):
                    symbol = symbol + "L"
                elif len(symbol) < 6 and not symbol.endswith(".L"):
                    symbol = symbol + ".L"
            if allAccounts:
                detailLocation = f"./{stockDetails.account}/{symbol}.txt"
            else:
                detailLocation = f"./{accountSummary.name}/{symbol}.txt"
            stockRow.appendChild(td(a(f"{symbol}", _href=detailLocation)))
            csvRow["Security"] = symbol
            if allAccounts:
                accountLocation = (
                    f"./{stockDetails.account}-Summary.html#Stock%20Summary"
                )
                stockRow.appendChild(
                    td(a(f"{stockDetails.account}", _href=accountLocation))
                )
                csvRow["Account"] = stockDetails.account
            ft = (
                stockDetails.fundOverview.fundType.name
                if stockDetails.fundOverview
                else "None"
            )
            stockRow.appendChild(td(f"{ft}"))
            csvRow["Type"] = ft
            stockRow.appendChild(td(f"{stockDetails.name}"))
            csvRow["Name"] = stockDetails.name
            if stockDetails.fundOverview:
                fees = f"{stockDetails.fundOverview.fees:0.02f}%"
            else:
                fees = "N/A"
            stockRow.appendChild(td(fees))
            csvRow["Fees"] = fees
            stockRow.appendChild(td(f"£{stockDetails.cashInvested:,.0f}"))
            csvRow["Cash inv"] = stockDetails.cashInvested
            stockRow.appendChild(td(f"£{stockDetails.marketValue():,.0f}"))
            csvRow["Market Value"] = stockDetails.marketValue()
            stockRow.appendChild(td(f"{stockDetails.averageYearlyDiviYield():,.0f}%"))
            csvRow["Yield"] = stockDetails.averageYearlyDiviYield()
            stockRow.appendChild(
                td(
                    f"£{stockDetails.totalGain():,.0f} ({stockDetails.totalGainPerc():0.02f}%)"
                )
            )
            csvRow["Return"] = stockDetails.totalGain()
            stockRow.appendChild(td(f"{stockDetails.yearsHeld():0.01f}"))
            csvRow["Years Held"] = stockDetails.yearsHeld()
            stockRow.appendChild(td(f"{stockDetails.avgGainPerYearPerc():0.02f}%"))
            csvRow["Annualised Ret"] = stockDetails.avgGainPerYearPerc()
            fund = stockDetails.fundOverview
            if fund:
                stockRow.appendChild(td(f"{fund.return3Yr:0.02f}%"))
                csvRow["3yr-Ret"] = fund.return3Yr
                stockRow.appendChild(td(f"{fund.return5Yr:0.02f}%"))
                csvRow["5yr-Ret"] = fund.return5Yr
                stockRow.appendChild(td(f"{fund.alpha3Yr:0.02f}"))
                csvRow["Alpha"] = fund.alpha3Yr
                stockRow.appendChild(td(f"{fund.beta3Yr:0.02f}"))
                csvRow["Beta"] = fund.beta3Yr
                stockRow.appendChild(td(f"{fund.sharpe3Yr:0.02f}"))
                csvRow["Sharpe"] = fund.sharpe3Yr

            stockTable.appendChild(stockRow)
            if csvOut:
                csvOut.writerow(csvRow)
    dom.append(stockTable)
    if csvOut:
        fileStrs[f"csvFiles/{accountSummary.name}-securities.csv"] = secIO.getvalue()
        secIO.close()

    historicStocks = sorted(
        historicStocks, key=lambda stock: stock.endDate, reverse=True
    )
    dom.append(h2("Previous Security Holdings"))
    stockTable = table()
    headings = ["Security"]
    if allAccounts:
        headings.append("Account")
    headings.extend(
        [
            "Type",
            "Name",
            "Fees",
            "Cash inv",
            "Cash div",
            "Capital Gain",
            "Dividends",
            "Yield",
            "Total Gain",
            "Years Held",
            "Avg Gain/Yr",
            "From",
            "To",
        ]
    )
    headrow = tr()
    for hd in headings:
        headrow.appendChild(th(hd))
    stockTable.appendChild(headrow)
    if len(historicStocks) > 0:
        secIO = io.StringIO()
        csvOut = csv.DictWriter(secIO, headings)
        csvOut.writeheader()
    else:
        csvOut = None
    for stockDetails in historicStocks:
        stockRow = tr(
            _class="positive" if stockDetails.totalGain() > 0 else "negative",
        )
        csvRow = {title: "" for title in headings}
        if allAccounts:
            detailLocation = f"./{stockDetails.account}/{stockDetails.symbol}.txt"
        else:
            detailLocation = f"./{accountSummary.name}/{stockDetails.symbol}.txt"
        detailLocation = f"./{stockDetails.account}/{stockDetails.symbol}.txt"
        stockRow.appendChild(td(a(f"{stockDetails.symbol}", _href=detailLocation)))
        csvRow["Security"] = stockDetails.symbol
        if allAccounts:
            accountLocation = f"./{stockDetails.account}-Summary.html#Stock%20Summary"
            stockRow.appendChild(
                td(a(f"{stockDetails.account}", _href=accountLocation))
            )
            csvRow["Account"] = stockDetails.account
        ft = (
            stockDetails.fundOverview.fundType.name
            if stockDetails.fundOverview
            else "None"
        )
        stockRow.appendChild(td(f"{ft}"))
        csvRow["Type"] = ft
        stockRow.appendChild(td(f"{stockDetails.name}"))
        csvRow["Name"] = stockDetails.name
        if stockDetails.fundOverview:
            fees = f"{stockDetails.fundOverview.fees:0.02f}%"
        else:
            fees = "N/A"
        stockRow.appendChild(td(fees))
        csvRow["Fees"] = fees
        cashInvested = stockDetails.historicCashInvested()
        stockRow.appendChild(td(f"£{cashInvested:,.0f}"))
        csvRow["Cash inv"] = cashInvested
        cashed = stockDetails.historicCashDivested()
        stockRow.appendChild(td(f"£{cashed:,.0f}"))
        csvRow["Cash div"] = cashed
        stockRow.appendChild(td(f"£{stockDetails.realisedCapitalGain():,.0f}"))
        csvRow["Capital Gain"] = stockDetails.realisedCapitalGain()
        stockRow.appendChild(td(f"£{stockDetails.totalDividends():,.0f}"))
        csvRow["Dividends"] = stockDetails.totalDividends()
        stockRow.appendChild(td(f"{stockDetails.averageYearlyDiviYield():0.02f}%"))
        csvRow["Yield"] = stockDetails.averageYearlyDiviYield()
        stockRow.appendChild(
            td(
                f"£{stockDetails.totalGain():,.0f} ({stockDetails.totalGainPerc():0.02f}%)"
            )
        )
        csvRow["Total Gain"] = stockDetails.totalGain()
        stockRow.appendChild(td(f"{stockDetails.yearsHeld():0.01f}"))
        csvRow["Years Held"] = stockDetails.yearsHeld()
        stockRow.appendChild(td(f"{stockDetails.avgGainPerYearPerc():0.02f}%"))
        csvRow["Avg Gain/Yr"] = stockDetails.avgGainPerYearPerc()
        stockRow.appendChild(td(f"{stockDetails.startDate.date()}"))
        csvRow["From"] = stockDetails.startDate.date()
        stockRow.appendChild(td(f"{stockDetails.endDate.date()}"))
        csvRow["To"] = stockDetails.endDate.date()
        stockTable.appendChild(stockRow)
        if csvOut:
            csvOut.writerow(csvRow)
    dom.append(stockTable)
    if csvOut:
        fileStrs[
            f"csvFiles/{accountSummary.name}-historic-securities.csv"
        ] = secIO.getvalue()
        secIO.close()


def getStockSummaryStr(stockDetails: SecurityDetails):
    retStr = f"{stockDetails.symbol} {stockDetails.name} "
    retStr += f"Cash in £{stockDetails.cashInvested:0.2f} "
    retStr += f"Invested £{stockDetails.totalInvested:0.2f} "
    retStr += f"Capital Gain £{stockDetails.realisedCapitalGain():,.0f} "
    retStr += f"Divis £{stockDetails.totalDividends():,.0f}, Avg Yield: {stockDetails.averageYearlyDiviYield():,.0f}% "
    retStr += f"Gain: £{stockDetails.totalGain():,.0f}, ({stockDetails.totalGainPerc():0.2f}%)\n"
    if stockDetails.historicHoldings:
        for det in stockDetails.historicHoldings:
            retStr += "    Historic: " + getStockSummaryStr(det)
    return retStr


def getStockLedgerStr(securityDetails: SecurityDetails):
    retStr = f"Stock: {securityDetails.symbol}\nDescription: {securityDetails.name}\n"
    retStr += f"Sedol: {securityDetails.sedol} ISIN: {securityDetails.isin}\n\n"
    retStr += "Current Holding:\n"
    retStr += getDetailsStr(securityDetails)
    if securityDetails.historicHoldings:
        for prev in securityDetails.historicHoldings:
            retStr += "\n\nPrevious holding:\n"
            retStr += getDetailsStr(prev)

    return retStr


def getDetailsStr(secDetails: SecurityDetails):
    retStr = ""
    if secDetails.endDate:
        # Historic stock
        retStr += (
            f"Bought {secDetails.startDate.date() if secDetails.startDate else ''}\n"
        )
        retStr += f"Sold remaining stock {secDetails.endDate.date()}\n"
        retStr += f"Held for {secDetails.yearsHeld():0.1f} years\n"
    else:
        retStr += f"Held since {secDetails.startDate.date() if secDetails.startDate else ''}\n"
        retStr += f"Held for {secDetails.yearsHeld():0.1f} years\n"
        retStr += f"Number of shares: {secDetails.qtyHeld}\n"
        if secDetails.currentSharePrice:
            retStr += f"Current Share Price {secDetails.currentSharePrice:0.2f}\n"
            retStr += f"Share price date {secDetails.currentSharePriceDate.date()}\n"
            retStr += f"Average Share Price {secDetails.avgSharePrice:0.2f}\n"
            retStr += f"Current Market Value £{secDetails.marketValue():,.0f}\n"
            # retStr += f"Total Paper Gain £{details['totalPaperGain']:0.2f} {details['totalPaperGainPerc']:0.2f}%\n"
            retStr += f"Total Taxable Gain if sold £{secDetails.paperCGT():,.0f} {secDetails.paperCGTPerc():0.2f}%\n"
        else:
            retStr += "**** No current price data available, so total gain info doesnt include current value\n"
            retStr += f"Average Share Price {secDetails.avgSharePrice:0.2f}\n"

    retStr += f"Cash invested £{secDetails.cashInvested:,.0f}\n"
    retStr += f"Amount invested £{secDetails.totalInvested:,.0f}\n"
    retStr += f"Amount dividends re-invested £{secDetails.diviInvested:,.0f}\n"
    retStr += f"Total Dividends £{secDetails.totalDividends():0.0f}\n"
    retStr += f"Average Yearly Dividend £{secDetails.averageYearlyDivi():,.0f}, Yield: {secDetails.averageYearlyDiviYield():0.2f}%\n"
    retStr += f"Realised Capital gain £{secDetails.realisedCapitalGain():,.0f}\n"
    retStr += f"Total Capital gain £{secDetails.capitalGain():,.0f}\n"
    retStr += f"Stock Dealing costs £{secDetails.totalCosts():,.0f}\n"
    retStr += f"Total Gain: £{secDetails.totalGain():,.0f}, ({secDetails.totalGainPerc():0.2f}%) \n"
    retStr += f"Average Gain per year: £{secDetails.avgGainPerYear():,.0f}, ({secDetails.avgGainPerYearPerc():0.2f}%) \n"

    if secDetails.fundOverview:
        retStr += "\n"
        retStr += secDetails.fundOverview.getStr()

    divs = list()
    retStr += "\nDividends Per Year:\n"
    for year in secDetails.dividendsByYear.keys():
        divs.append(
            [
                year,
                secDetails.dividendsByYear[year],
                secDetails.dividendYieldByYear[year],
            ]
        )
    retStr += tabulate(divs, headers=["Tax Year", "Dividend Paid", "Yield"])

    retStr += "\n\nInvestments Made:\n"
    hist = list()
    for dc in secDetails.investmentHistory:
        hist.append(asdict(dc))
    retStr += tabulate(hist, headers="keys")

    retStr += "\n\nRealised Capital Gain (taxable) Per Year:\n"
    gains = list(secDetails.realisedCapitalGainByYear.items())
    retStr += tabulate(
        gains, headers=["Tax Year", "Realised Capital Gain (taxable value)"]
    )

    retStr += "\n\nDealing Costs Per Year:\n"
    costs = list(secDetails.costsByYear.items())
    retStr += tabulate(costs, headers=["Tax Year", "Dealing Costs"])

    retStr += "\n\nTransactions:\n"
    trans = list()
    total = Decimal(0.0)
    for txn in secDetails.transactions:
        txnd = dict()
        txnd["Date"] = txn.date
        txnd["Type"] = txn.type
        # txnd['Qty'] = txn.qty
        if txn.credit != 0:
            txnd["Amount"] = txn.credit
            txnd["Currency"] = txn.creditCurrency
            total += txn.credit
        elif txn.debit != 0:
            txnd["Amount"] = -txn.debit
            txnd["Currency"] = txn.debitCurrency
            total -= txn.debit
        trans.append(txnd)
    retStr += tabulate(trans, headers="keys")
    if total >= 0:
        retStr += f"\nTotal cash out: {total:,.0f}\n\n"
    else:
        retStr += f"\nTotal cash in: {-total:,.0f}\n\n"

    return retStr
