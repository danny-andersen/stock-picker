import io
import csv
from datetime import timedelta, datetime, timezone
import calendar
from copy import deepcopy
from statistics import mean
from decimal import Decimal
from dataclasses import asdict
from tabulate import tabulate
import plotly.express as px
from pandas import DataFrame
from domonic.html import (
    td,
    tr,
    th,
    a,
    body,
    table,
    h1,
    h2,
    h3,
    html,
    meta,
    style,
    head,
    script,
    button,
)

from transactionDefs import (
    AccountSummary,
    getTaxYear,
    FundType,
    SecurityDetails,
    CapitalGain,
    convertCurrencyToStr,
    printCurrency,
    Regions,
    STERLING,
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
        /* Add CSS styles to make the table look attractive */
        table {
            font-family: Arial, sans-serif;
            border-collapse: collapse;
            width: 80%;
            margin: 20px auto;
            box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
        }

        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }

        th {
            background-color: #f2f2f2;
            color: #333;
        }

        tr:hover {
            background-color: #f5f5f5;
        }

        tr:nth-child(even) {
            background-color: #f2f2f2;
        }

        caption {
            font-size: 1.5em;
            margin-bottom: 10px;
        }
        """
            ),
            script(
                """
		function toggleTable(button, tableIds, tableDesc) {
            tableIds.forEach(id => {
                let table = document.getElementById(id);
                if (table.hidden) {
                    table.hidden = null;
                    button.innerText = "Hide " + tableDesc;
                } else {
                    table.hidden = "hidden";
                    button.innerText = "Show " + tableDesc;
                }
            });
		}
        function sortTable(tableID, columnIndex) {
			var table, rows, switching, i, x, y, shouldSwitch, direction, switchcount = 0;
			table = document.getElementById(tableID);
			switching = true;
			direction = "asc";

			while (switching) {
				switching = false;
				rows = table.rows;

				for (i = 1; i < (rows.length - 1); i++) {
					shouldSwitch = false;
                    //Never switch last row if a summary row
                    if (i == rows.length - 2 && rows[i + 1].getElementsByTagName("TD")[0].innerHTML == 'Overall') {
                        break;
                    }
					x = rows[i].getElementsByTagName("TD")[columnIndex];
					y = rows[i + 1].getElementsByTagName("TD")[columnIndex];

					var xContent = x.innerHTML;
					var yContent = y.innerHTML;
					// Remove text within brackets
					xContent = xContent.replace(/\(.*?\)|£|,|%/g, '').trim();
					yContent = yContent.replace(/\(.*?\)|£|,|%/g, '').trim();

					// Parse as float if the content is a number
					if (!isNaN(xContent)) {
						xContent = parseFloat(xContent);
					} else {
						xContent = xContent.toLowerCase();
					}
					if (!isNaN(yContent)) {
						yContent = parseFloat(yContent);
					} else {
						yContent = yContent.toLowerCase();
					}

					if (direction == "asc") {
						if (xContent > yContent) {
							shouldSwitch = true;
							break;
						}
					} else if (direction == "desc") {
						if (xContent < yContent) {
							shouldSwitch = true;
							break;
						}
					}
				}
				if (shouldSwitch) {
					rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
					switching = true;
					switchcount++;
				} else {
					if (switchcount == 0 && direction == "asc") {
						direction = "desc";
						switching = true;
					}
				}
			}
		}

        """
            ),
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
        tr(
            td("Historic 3yr Fund Return"),
            td(f"{accountSummary.avgFund3YrReturn:02.2f}%"),
        )
    )
    smry.appendChild(
        tr(
            td("Historic 5yr Fund Return"),
            td(f"{accountSummary.avgFund5YrReturn:02.2f}%"),
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
                _class=(
                    "positive"
                    if accountSummary.totalPaperGainForTax > 0
                    else "negative"
                ),
            ),
        )
    )
    smry.appendChild(
        tr(td("Cash Balance"), td(convertCurrencyToStr(accountSummary.cashBalance, 0)))
    )
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
                _class=(
                    "positive"
                    if accountSummary.totalGainFromInvestments() > 0
                    else "negative"
                ),
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
                _class=(
                    "positive" if accountSummary.totalGainLessFees() > 0 else "negative"
                ),
            ),
            _style="font-weight: bold;",
        )
    )

    smry.appendChild(
        tr(
            td("Average return per year"),
            td(
                f"£{accountSummary.avgReturnPerYear():,.0f}",
                _class=(
                    "positive" if accountSummary.totalGainLessFees() > 0 else "negative"
                ),
            ),
            _style="font-weight: bold;",
        )
    )
    dom.appendChild(smry)

    if allAccounts:
        dom.appendChild(h2("Account values and returns"))
        fundTableId = "fundTable"
        fs = table(id=fundTableId)
        funds = accountSummary.fundTotals
        isTotalAcc = len(accountSummary.mergedAccounts) > 0
        totalAccountValue = accountSummary.totalValue()
        if totalAccountValue == 0:
            totalAccountValue = Decimal(1.0)
        headings = [
            "Account",
            "Total Invested",
            "Total Cash",
            "Total Value",
            "% of Total",
            "Last year total income (%)",
            "Current Capital Gain (%)",
            "Total Historic Gain (%)",
            "Stocks/Bonds/Cash/Gold %",
            "Number of Securities held",
        ]
        headrow = tr()
        col = 0
        for hd in headings:
            headrow.appendChild(th(hd, onclick=f"sortTable('{fundTableId}', {col})"))
            col += 1
        fs.appendChild(headrow)

        lastTaxYear = getTaxYear(datetime.now() - timedelta(weeks=52))
        for acc in accountSummary.mergedAccounts:
            row = tr(
                _class=("positive" if acc.totalPaperGainForTax >= 0 else "negative")
            )
            row.appendChild(td(a(f"{acc.name}", _href=f"./{acc.name}-Summary.html")))
            row.appendChild(td(f"£{acc.totalInvestedInSecurities:,.0f}"))
            row.appendChild(td(f"£{acc.cashBalance.get(STERLING, 0):,.0f}"))
            row.appendChild(td(f"£{acc.totalValue():,.0f}"))
            row.appendChild(
                td(f"{100*acc.totalValue()/accountSummary.totalValue():.1f}%")
            )
            row.appendChild(
                td(
                    f"£{acc.totalReturnByYear(lastTaxYear):,.0f} ({100*acc.totalReturnByYear(lastTaxYear)/acc.totalValue():.1f}%)"
                )
            )
            row.appendChild(
                td(
                    f"£{acc.totalPaperGainForTax:,.0f} ({100*float(acc.totalPaperGainForTax)/float(acc.totalInvestedInSecurities) if acc.totalInvestedInSecurities != 0 else 0:.1f}%)"
                )
            )
            row.appendChild(
                td(
                    f"£{acc.totalGainLessFees():,.0f} ({acc.totalGainLessFeesPerc():.1f}%)"
                )
            )
            row.appendChild(td(f"{acc.getPercSplitByFundTypeStr()}"))
            row.appendChild(td(f"{acc.countOfCurrentStocks()}"))
            fs.append(row)
        row = tr()
        row.appendChild(td("Total"))
        row.appendChild(td(f"£{accountSummary.totalInvestedInSecurities:,.0f}"))
        row.appendChild(td(f"£{accountSummary.cashBalance.get(STERLING, 0):,.0f}"))
        row.appendChild(td(f"£{accountSummary.totalValue():,.0f}"))
        row.appendChild(td("100%"))
        row.appendChild(
            td(
                f"£{accountSummary.totalReturnByYear(lastTaxYear):,.0f} ({100*float(accountSummary.totalReturnByYear(lastTaxYear))/float(accountSummary.totalValue()):.1f}%)"
            )
        )
        row.appendChild(
            td(
                f"£{accountSummary.totalPaperGainForTax:,.0f} ({100*float(accountSummary.totalPaperGainForTax)/float(accountSummary.totalInvestedInSecurities):.1f}%)"
            )
        )
        row.appendChild(
            td(
                f"£{accountSummary.totalGainLessFees():,.0f} ({accountSummary.totalGainLessFeesPerc():.1f}%)"
            )
        )
        row.appendChild(td(f"{accountSummary.getPercSplitByFundTypeStr()}"))
        row.appendChild(td(f"{accountSummary.countOfCurrentStocks()}"))
        fs.appendChild(row)
        dom.appendChild(fs)

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
        gainDict["Zero line"] = list()
        for ft in fundTypes:
            gainDict[ft.name] = list()
        historicTableID = "historicTable"
        btn = button(
            "Show Historic Values",
            onclick=f"toggleTable(this,['{historicTableID}'], 'Historic Values')",
        )
        dom.appendChild(btn)
        fs = table(id=historicTableID, hidden="hidden")
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
            dt = datetime.fromtimestamp(dtime)
            gainDict["Date"].append(dt)
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
            gainDict["Zero line"].append(0)
            fs.appendChild(
                tr(
                    td(f"{dt.date()}"),
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
    statsTableId = "statsTable"
    fs = table(id=statsTableId)
    funds = accountSummary.fundTotals
    isTotalAcc = len(accountSummary.mergedAccounts) > 0
    totalAccountValue = accountSummary.totalValue()
    if totalAccountValue == 0:
        totalAccountValue = Decimal(1.0)
    headings = [
        "Type",
        "Total Invested",
        "Total Market Value",
        "%Account",
        "Avg Fees",
        "Avg Ret",
        "3yr Ret",
        "5yr Ret",
    ]
    headrow = tr()
    col = 0
    for hd in headings:
        headrow.appendChild(th(hd, onclick=f"sortTable('{statsTableId}', {col})"))
        col += 1
    if allAccounts:
        for acc in accountSummary.mergedAccounts:
            h = th(" [Sort] ", onclick=f"sortTable('{statsTableId}', {col})")
            col += 1
            h.appendChild(
                a(
                    acc.name,
                    _href="./"
                    + acc.name
                    + "-Summary.html#Statistics%20By%20Investment%20Type",
                )
            )
            headrow.appendChild(h)
    fs.appendChild(headrow)

    totInvested = Decimal(0.0)
    totValue = Decimal(0.0)
    totfees = 0.0
    totRet = 0.0
    tot3yrRet = 0.0
    tot5yrRet = 0.0
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
                    td(f"{fund.fees:0.2f}%"),
                    td(f"{fund.actualReturn:0.2f}%"),
                    td(f"{fund.return3Yr:0.2f}%"),
                    td(f"{fund.return5Yr:0.2f}%"),
                    "".join([f"{td(acc)}" for acc in accFunds]),
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
    (totStocks, totBonds, totCash, totGold) = accountSummary.getValueSplitByFundType()
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
                td(f"{totfees/tot:0.02f}%"),
                td(f"{totRet/tot:0.02f}%"),
                td(f"{tot3yrRet/tot:0.02f}%"),
                td(f"{tot5yrRet/tot:0.02f}%"),
                "".join([f"{td(accTot)}" for accTot in accTots]),
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
    percByType: dict[str, float] = dict()
    idealPercByType: dict[str, float] = dict()
    fs.appendChild(
        tr(
            th("Type"),
            th(" Total Market Value "),
            th(" Portfolio% "),
            th("  Min%  "),
            th("  Ideal%"),
            th("  Max%"),
            th("  Diff from Ideal "),
        )
    )
    stocksPerc = 100 * totStocks / totalAccountValue
    percByType["Stocks"] = stocksPerc
    smin = int(portPerc["stocks_min"])
    smax = int(portPerc["stocks_max"])
    ideal = int(portPerc["stocks_ideal"])
    idealPercByType["Stocks"] = ideal
    # Show row in green if in guardrails or red if not
    if stocksPerc <= smin or stocksPerc >= smax:
        cls = "negative"
    else:
        cls = "positive"
    diff = f"£{(stocksPerc-ideal)*totalAccountValue/100:,.0f}"
    fs.appendChild(
        tr(
            td("Stocks"),
            td(f"£{totStocks:,.0f}"),
            td(f"{stocksPerc:0.02f}%"),
            td(f"{smin:0.01f}%"),
            td(f"{ideal:0.01f}%"),
            td(f"{smax:0.01f}%"),
            td(diff),
            _class=cls,
        )
    )
    bondsPerc = 100 * totBonds / totalAccountValue
    percByType["Bonds"] = bondsPerc
    smin = int(portPerc["bonds_min"])
    smax = int(portPerc["bonds_max"])
    ideal = int(portPerc["bonds_ideal"])
    idealPercByType["Bonds"] = ideal
    # Show row in green if in guardrails or red if not
    if bondsPerc <= smin or bondsPerc >= smax:
        cls = "negative"
    else:
        cls = "positive"
    diff = f"£{(bondsPerc-ideal)*totalAccountValue/100:,.0f}"
    fs.appendChild(
        tr(
            td("Bonds"),
            td(f"£{totBonds:,.0f}"),
            td(f"{bondsPerc:0.02f}%"),
            td(f"{smin:0.01f}%"),
            td(f"{ideal:0.01f}%"),
            td(f"{smax:0.01f}%"),
            td(diff),
            _class=cls,
        )
    )
    cashPerc = 100 * totCash / totalAccountValue
    percByType["Cash"] = cashPerc
    smin = int(portPerc["cash_min"])
    smax = int(portPerc["cash_max"])
    ideal = int(portPerc["cash_ideal"])
    idealPercByType["Cash"] = ideal
    # Show row in green if in guardrails or red if not
    if cashPerc <= smin or cashPerc >= smax:
        cls = "negative"
    else:
        cls = "positive"
    diff = f"£{(cashPerc-ideal)*totalAccountValue/100:,.0f}"
    fs.appendChild(
        tr(
            td("Cash"),
            td(f"£{totCash:,.0f}"),
            td(f"{cashPerc:0.02f}%"),
            td(f"{smin:0.01f}%"),
            td(f"{ideal:0.01f}%"),
            td(f"{smax:0.01f}%"),
            td(diff),
            _class=cls,
        )
    )
    goldPerc = 100 * totGold / totalAccountValue
    percByType["Gold"] = goldPerc
    smin = int(portPerc["gold_min"])
    smax = int(portPerc["gold_max"])
    ideal = int(portPerc["gold_ideal"])
    idealPercByType["Gold"] = ideal
    # Show row in green if in guardrails or red if not
    if goldPerc <= smin or goldPerc >= smax:
        cls = "negative"
    else:
        cls = "positive"
    diff = f"£{(goldPerc-ideal)*totalAccountValue/100:,.0f}"
    fs.appendChild(
        tr(
            td("Gold"),
            td(f"£{totGold:,.0f}"),
            td(f"{goldPerc:0.02f}%"),
            td(f"{smin:0.01f}%"),
            td(f"{ideal:0.01f}%"),
            td(f"{smax:0.01f}%"),
            td(diff),
            _class=cls,
        )
    )
    fs.appendChild(
        tr(
            td("Total"),
            td(f"£{totGold+totCash+totBonds+totStocks:,.0f}"),
            td(f"{goldPerc+cashPerc+bondsPerc+stocksPerc:0.02f}%"),
        )
    )
    pieTable = table()
    pieTable.appendChild(
        tr(
            th("Actual Portfolio % spread by type"),
            th("Ideal Portfolio % spread by type"),
        )
    )
    row = tr()
    fig = px.pie(names=percByType.keys(), values=percByType.values())
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(
        legend=dict(
            xref="paper", orientation="h", x=0.4
        ),  # Position legend horizontally and adjust 'y' to position it
    )
    row.appendChild(td(fig.to_html()))
    fig = px.pie(names=idealPercByType.keys(), values=idealPercByType.values())
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(
        legend=dict(
            xref="paper", orientation="h", x=0.4
        ),  # Position legend horizontally and adjust 'y' to position it
    )
    row.appendChild(td(fig.to_html()))
    pieTable.appendChild(row)
    dom.appendChild(pieTable)
    # Show table below
    dom.appendChild(fs)

    percByInstitute = dict()
    if len(accountSummary.totalByInstitution) > 0:
        dom.appendChild(h3("Value by Institution and % split"))
        tableID = "instituteTable"
        btn = button(
            "Show Values by Institute",
            onclick=f"toggleTable(this,['{tableID}'], 'Values by Institute')",
        )
        dom.appendChild(btn)
        fi = table(id=tableID, hidden="hidden")
        totVal = Decimal(0.0)
        val = Decimal(0.0)
        fi.appendChild(tr(th("Institution"), th("Value"), th("Total Account %")))
        for inst, val in accountSummary.totalByInstitution.items():
            perc = 100.0 * float(val / totalAccountValue)
            percByInstitute[inst] = perc
            fi.appendChild(
                tr(
                    td(inst),
                    td(f"£{val:,.0f}"),
                    td(f"{perc:0.02f}%"),
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
        fig = px.pie(
            names=percByInstitute.keys(),
            values=percByInstitute.values(),
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(
            showlegend=True,  # Show legend
            legend=dict(
                xref="paper", orientation="v", x=0.75
            ),  # Position legend horizontally and adjust 'y' to position it
        )
        dom.appendChild(fig.to_html())
        # Show table below
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
    tableID = "geoTable"
    btn = button(
        "Show Values By Region",
        onclick=f"toggleTable(this,['{tableID}'], 'Values By Region')",
    )
    fr = table(id=tableID, hidden="hidden")
    headerRow = tr()
    headerRow.appendChild(th("Type"))
    for region in Regions:
        headerRow.appendChild(th(region.value))
    fr.appendChild(headerRow)
    totalsByRegion: dict[Regions, float] = dict()
    stocksTotalsByRegion: dict[Regions, float] = dict()
    bondTotalsByRegion: dict[Regions, float] = dict()
    for region in Regions:
        stocksTotalsByRegion[region] = 0.0
        bondTotalsByRegion[region] = 0.0
    totVal = 0.0
    stockTotal = 0.0
    bondTotal = 0.0
    for typ, fund in funds.items():
        row = tr(td(typ.name))
        val = float(fund.totalValue)
        if fund.isStockType():
            stockTotal += val
        elif fund.isBondType:
            bondTotal += val
        for region in Regions:
            if val != 0:
                regionVal = fund.valueByRegion.get(region, 0.0)
                row.appendChild(td(f"{100.0*regionVal/val:0.02f}%"))
                totalsByRegion[region] = totalsByRegion.get(region, 0.0) + regionVal
                if fund.isStockType():
                    stocksTotalsByRegion[region] = (
                        stocksTotalsByRegion.get(region, 0.0) + regionVal
                    )
                elif fund.isBondType():
                    bondTotalsByRegion[region] = (
                        bondTotalsByRegion.get(region, 0.0) + regionVal
                    )
            else:
                row.appendChild(td("0.00%"))
        fr.appendChild(tr(row))
        totVal += val
    if totVal > 0:
        row = tr(td("Overall"))
        for region in Regions:
            row.appendChild(td(f"{100.0*totalsByRegion[region]/totVal:0.02f}%"))
        fr.appendChild(tr(row))

    pieTable = table()
    pieTable.appendChild(
        tr(th("Total % by region"), th("Stocks % by region"), th("Bonds % by region"))
    )
    row = tr()
    if totVal > 0:
        fig = px.pie(
            names=[region.value for region in Regions],
            values=[100.0 * val / totVal for val in totalsByRegion.values()],
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(
            showlegend=True,  # Show legend
            legend=dict(
                xref="paper", orientation="h", x=0.4
            ),  # Position legend horizontally and adjust 'y' to position it
        )
        row.appendChild(td(fig.to_html()))
    if stockTotal > 0:
        fig = px.pie(
            names=[region.value for region in Regions],
            values=[100.0 * val / stockTotal for val in stocksTotalsByRegion.values()],
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(
            showlegend=True,  # Show legend
            legend=dict(
                xref="paper", orientation="h", x=0.4
            ),  # Position legend horizontally and adjust 'y' to position it
        )
        row.appendChild(td(fig.to_html()))
    if bondTotal > 0:
        fig = px.pie(
            names=[region.value for region in Regions],
            values=[100.0 * val / bondTotal for val in bondTotalsByRegion.values()],
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(
            showlegend=True,  # Show legend
            legend=dict(
                xref="paper", orientation="h", x=0.4
            ),  # Position legend horizontally and adjust 'y' to position it
        )
        row.appendChild(td(fig.to_html()))
    pieTable.appendChild(tr(row))
    dom.appendChild(pieTable)
    # Show table below chart
    dom.appendChild(btn)
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

    getSecurityStrs(accountSummary, allAccounts, dom, retStrs)

    startYear = accountSummary.dateOpened
    endYear = datetime.now(timezone.utc) + timedelta(
        days=365
    )  # Make sure we have this tax year
    # endYear = datetime.now(timezone.utc)
    procYear = startYear
    dom.appendChild(h2("Yearly cashflow breakdown"))
    tableID = "breakdownTable"
    btn = button(
        "Show Yearly Cashflow Table",
        onclick=f"toggleTable(this,['{tableID}'], 'Yearly Cashflow Table')",
    )
    dom.appendChild(btn)
    byYear = table(id=tableID, hidden="hidden")
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
    # Things only start getting interesting after 2017
    plotStartYear = datetime(year=2017, month=5, day=1, tzinfo=timezone.utc)
    valDict: dict[str, list] = {"Date": list()}
    valDict["Total Invested"] = list()
    valDict["Cash In"] = list()
    valDict["Cash Out"] = list()
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
        if procYear > plotStartYear:
            valDict["Total Invested"].append(
                accountSummary.aggInvestedByYear.get(taxYear, Decimal(0.0))
            )
            valDict["Cash In"].append(
                accountSummary.cashInByYear.get(taxYear, Decimal(0.0))
            )
            valDict["Cash Out"].append(
                accountSummary.cashOutByYear.get(taxYear, Decimal(0.0))
            )
            valDict["Date"].append(taxYear)
        procYear += timedelta(days=365)
    df = DataFrame(valDict)
    fig = px.line(
        df,
        x="Date",
        y=df.columns,
        hover_data={"Date": "|%B %d, %Y"},
        title="Yearly Cashflow",
        labels={"value": "£"},
    )
    fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
    dom.appendChild(fig.to_html())
    dom.append(byYear)

    dom.appendChild(h2("Monthly Income (exc Interest)"))
    tableID = "incomeTable"
    btn = button(
        "Show Income Table",
        onclick=f"toggleTable(this,['{tableID}'], 'Income Table')",
    )
    dom.appendChild(btn)
    incTable = table(id=tableID, hidden="hidden")
    if allAccounts:
        otherAccounts = accountSummary.mergedAccounts
        row = tr()
        row.appendChild(th("Year"))
        row.appendChild(th("Month"))
        for acc in otherAccounts:
            row.appendChild(th(acc.name))
        row.appendChild(th("Total Income"))
        incTable.appendChild(row)
    else:
        incTable.appendChild(tr(th("Year"), th("Month"), th("Total Income")))
    nowyr = datetime.now().year
    for yr in [f"{nowyr}", f"{nowyr-1}", f"{nowyr-2}"]:
        totals = dict()
        totals[accountSummary.name] = 0
        if yr in accountSummary.allIncomeByYearMonth:
            incMonths = accountSummary.allIncomeByYearMonth[yr]
            for month in range(12, 0, -1):
                if month in incMonths:
                    totals[accountSummary.name] += incMonths[month]
                    row = tr()
                    row.appendChild(td(yr))
                    row.appendChild(td(calendar.month_name[month]))
                    if allAccounts:
                        for acc in otherAccounts:
                            if acc.name not in totals:
                                totals[acc.name] = 0
                            val = acc.allIncomeByYearMonth.get(yr, dict()).get(
                                month, Decimal(0.0)
                            )
                            totals[acc.name] += val
                            row.appendChild(td(val))
                    row.appendChild(td(incMonths[month]))
                    incTable.appendChild(row)
            row = tr(_style="font-weight: bold;")
            row.appendChild(td(f"Total {yr} Income"))
            row.appendChild(td(""))
            if allAccounts:
                for acc in otherAccounts:
                    row.appendChild(td(totals[acc.name]))
            row.appendChild(td(totals[accountSummary.name]))
            incTable.appendChild(row)
    dom.appendChild(incTable)

    dom.appendChild(h1("Tax"))
    dom.appendChild(h2("Tax liability by Tax Year"))
    currentTaxYear = getTaxYear(datetime.now())
    lastTaxYear = getTaxYear(datetime.now() - timedelta(weeks=52))
    if len(accountSummary.mergedAccounts) == 0:
        # Single account
        accounts = [accountSummary]
    else:
        accounts = accountSummary.mergedAccounts
    for yr in [lastTaxYear, currentTaxYear]:
        dom.appendChild(h3(f"Tax Year {yr}"))
        tableID = f"taxTable{yr}"
        cgtableID = f"cgtaxTable{yr}"
        btn = button(
            f"Show Tax Year {yr} Table",
            onclick=f"toggleTable(this,['{tableID}', '{cgtableID}'], 'Tax Year {yr} Table')",
        )
        dom.appendChild(btn)
        tx = table(id=tableID, hidden="hidden")
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
        tx = table(id=cgtableID, hidden="hidden")
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
        cgtxns: list[(AccountSummary, SecurityDetails, CapitalGain)] = []
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
            capGain = Decimal(cg.qty) * (cg.price - cg.avgBuyPrice)
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

    dom.appendChild(h2("Payments by Tax Year"))
    for yr in [lastTaxYear, currentTaxYear]:
        dom.appendChild(h3(f"Tax Year {yr}"))
        divitableID = f"diviTable{yr}"
        inctableID = f"incometaxTable{yr}"
        btn = button(
            f"Show Tax Year {yr} Table",
            onclick=f"toggleTable(this,['{divitableID}', '{inctableID}'], 'Tax Year {yr} Table')",
        )
        dom.appendChild(btn)
        txnTable = table(id=divitableID, hidden="hidden")
        dom.appendChild(h3("Dividend Payments"))
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
            (
                accountSummary.dividendTxnsByYear[yr]
                if yr in accountSummary.dividendTxnsByYear
                else list()
            ),
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
        txnTable = table(id=inctableID, hidden="hidden")
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
    tableID = "txbTable"
    btn = button(
        "Show Transactions",
        onclick=f"toggleTable(this,['{tableID}'], 'Transactions')",
    )
    dom.appendChild(btn)
    txnTable = table(id=tableID, hidden="hidden")
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
        row.appendChild(
            td(
                f"{printCurrency(txn.creditCurrency, txn.credit, 2) if txn.credit != 0 else printCurrency(txn.debitCurrency, -txn.debit, 2)}"
            )
        )
        row.appendChild(td(convertCurrencyToStr(txn.accountBalance, 2)))
        txnTable.appendChild(row)
    dom.appendChild(txnTable)

    ht.append(dom)
    retStrs[f"{accountSummary.name}-Summary.html"] = f"{ht}"
    retStrs[f"csvFiles/{accountSummary.name}-Summary.json"] = accountSummary.to_json()
    return retStrs


def getSecurityStrs(
    accountSummary: AccountSummary,
    allAccounts: bool,
    dom: body,
    fileStrs: dict[str, str],
):
    historicStocks: list[SecurityDetails] = list()
    dom.appendChild(h2("Security Summary"))
    securityTableId = "security-summary"
    stockTable = table(id=securityTableId)
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
            "% of Account",
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
    col = 0
    for hd in headings:
        headrow.appendChild(th(hd, onclick=f"sortTable('{securityTableId}', {col})"))
        col += 1
    stockTable.appendChild(headrow)
    if len(accountSummary.stocks) > 0:
        secIO = io.StringIO()
        csvOut = csv.DictWriter(secIO, headings)
        csvOut.writeheader()
    else:
        csvOut = None
    stocksToShow = accountSummary.stocks
    accountTotalValue = accountSummary.totalValue()
    if allAccounts:
        # If all accounts then process stocklist twice
        # The first time aggregate the same stock held in multiple accounts
        # Put the aggreate into a new list
        # Sort by gain when done
        # The second pass, print the new aggregate list out out
        newStocks: list[SecurityDetails] = list()
        for stockDetails in accountSummary.stocks:
            if stockDetails.totalInvested != 0:
                # Ignore historic stocks
                newStock = None
                for stock in newStocks:
                    if stock.sedol == stockDetails.sedol:
                        newStock = stock
                        break
                if newStock:
                    # Merge in
                    newStock.mergeInStockLtd(stockDetails)
                else:
                    # Copy in
                    newStocks.append(deepcopy(stockDetails))
        stocksToShow = sorted(
            newStocks, key=lambda stock: stock.avgGainPerYearPerc(), reverse=True
        )

    for stockDetails in stocksToShow:
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
            # Need to allow for when a stock is in more than one account as the account is a comma delimited string
            stockAccounts = stockDetails.account.split(",")
            cell = td()
            if allAccounts:
                for acc in stockAccounts:
                    detailLocation = f"./{acc}/{symbol}.txt"
                    cell.appendChild(
                        (
                            a(
                                (
                                    f"{acc}: {symbol}"
                                    if len(stockAccounts) > 1
                                    else f"{symbol}"
                                ),
                                _href=detailLocation,
                            )
                        )
                    )
            else:
                detailLocation = f"./{accountSummary.name}/{symbol}.txt"
                cell.appendChild((a(f"{symbol}", _href=detailLocation)))
            stockRow.appendChild(cell)
            if allAccounts:
                cell = td()
                for acc in stockAccounts:
                    accountLocation = f"./{acc}-Summary.html#Stock%20Summary"
                    cell.appendChild(a(f"{acc}", _href=accountLocation))
                stockRow.appendChild(cell)
            ft = (
                stockDetails.fundOverview.fundType.name
                if stockDetails.fundOverview
                else "None"
            )
            stockRow.appendChild(td(f"{ft}"))
            stockRow.appendChild(td(f"{stockDetails.name}"))
            if stockDetails.fundOverview:
                fees = f"{stockDetails.fundOverview.fees:0.02f}%"
            else:
                fees = "N/A"
            stockRow.appendChild(td(fees))
            stockRow.appendChild(td(f"£{stockDetails.cashInvested:,.0f}"))
            stockRow.appendChild(td(f"£{stockDetails.marketValue():,.0f}"))
            stockRow.appendChild(
                td(f"{100*stockDetails.marketValue()/accountTotalValue:,.2f}%")
            )

            stockRow.appendChild(td(f"{stockDetails.averageYearlyDiviYield():,.0f}%"))
            stockRow.appendChild(
                td(
                    f"£{stockDetails.totalGain():,.0f} ({stockDetails.totalGainPerc():0.02f}%)"
                )
            )
            stockRow.appendChild(td(f"{stockDetails.yearsHeld():0.01f}"))
            stockRow.appendChild(td(f"{stockDetails.avgGainPerYearPerc():0.02f}%"))
            fund = stockDetails.fundOverview
            if fund:
                stockRow.appendChild(td(f"{fund.return3Yr:0.02f}%"))
                stockRow.appendChild(td(f"{fund.return5Yr:0.02f}%"))
                stockRow.appendChild(td(f"{fund.alpha3Yr:0.02f}"))
                stockRow.appendChild(td(f"{fund.beta3Yr:0.02f}"))
                stockRow.appendChild(td(f"{fund.sharpe3Yr:0.02f}"))

            stockTable.appendChild(stockRow)
    dom.appendChild(stockTable)

    if csvOut:
        for stockDetails in accountSummary.stocks:
            csvRow = {title: "" for title in headings}
            historicStocks.extend(stockDetails.historicHoldings)
            if stockDetails.totalInvested != 0:
                symbol = stockDetails.symbol
                if symbol != "":
                    if symbol.endswith("."):
                        symbol = symbol + "L"
                    elif len(symbol) < 6 and not symbol.endswith(".L"):
                        symbol = symbol + ".L"
                csvRow["Security"] = symbol
                if allAccounts:
                    csvRow["Account"] = stockDetails.account
                ft = (
                    stockDetails.fundOverview.fundType.name
                    if stockDetails.fundOverview
                    else "None"
                )
                csvRow["Type"] = ft
                csvRow["Name"] = stockDetails.name
                if stockDetails.fundOverview:
                    fees = f"{stockDetails.fundOverview.fees:0.02f}%"
                else:
                    fees = "N/A"
                csvRow["Fees"] = fees
                csvRow["Cash inv"] = stockDetails.cashInvested
                csvRow["Market Value"] = stockDetails.marketValue()
                csvRow["Yield"] = stockDetails.averageYearlyDiviYield()
                csvRow["Return"] = stockDetails.totalGain()
                csvRow["Years Held"] = stockDetails.yearsHeld()
                csvRow["Annualised Ret"] = stockDetails.avgGainPerYearPerc()
                fund = stockDetails.fundOverview
                if fund:
                    csvRow["3yr-Ret"] = fund.return3Yr
                    csvRow["5yr-Ret"] = fund.return5Yr
                    csvRow["Alpha"] = fund.alpha3Yr
                    csvRow["Beta"] = fund.beta3Yr
                    csvRow["Sharpe"] = fund.sharpe3Yr
                csvOut.writerow(csvRow)
        fileStrs[f"csvFiles/{accountSummary.name}-securities.csv"] = secIO.getvalue()
        secIO.close()

    historicStocks = sorted(
        historicStocks, key=lambda stock: stock.endDate, reverse=True
    )
    dom.appendChild(h2("Previous Security Holdings"))
    tableID = "previousTable"
    btn = button(
        "Show Previous Holdings",
        onclick=f"toggleTable(this,['{tableID}'], 'Previous Holdings')",
    )
    dom.appendChild(btn)
    stockTable = table(id=tableID, hidden="hidden")
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
    col = 0
    for hd in headings:
        headrow.appendChild(th(hd, onclick=f"sortTable('{tableID}', {col})"))
        col += 1
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
        csvRow["Security"] = stockDetails.symbol
        # Need to allow for when a stock is in more than one account as the account is a comma delimited string
        stockAccounts = stockDetails.account.split(",")
        cell = td()
        if allAccounts:
            for acc in stockAccounts:
                detailLocation = f"./{acc}/{stockDetails.symbol}.txt"
                cell.appendChild(
                    (
                        a(
                            (
                                f"{acc}: {stockDetails.symbol}"
                                if len(stockAccounts) > 1
                                else f"{stockDetails.symbol}"
                            ),
                            _href=detailLocation,
                        )
                    )
                )
        else:
            detailLocation = f"./{stockDetails.account}/{stockDetails.symbol}.txt"
            cell.appendChild((a(f"{stockDetails.symbol}", _href=detailLocation)))
        stockRow.appendChild(cell)
        if allAccounts:
            cell = td()
            for acc in stockAccounts:
                accountLocation = f"./{acc}-Summary.html#Stock%20Summary"
                cell.appendChild(a(f"{acc}", _href=accountLocation))
            stockRow.appendChild(cell)
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
        fileStrs[f"csvFiles/{accountSummary.name}-historic-securities.csv"] = (
            secIO.getvalue()
        )
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
