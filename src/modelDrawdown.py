import configparser
import locale
import argparse
import numpy as np
from saveRetreiveFiles import retrieveStringFromDropbox
from transactionDefs import AccountSummary
from decimal import Decimal
import plotly.express as px
from pandas import DataFrame
from domonic.html import td, tr, th, a, body, table, h1, h2, h3, html, meta, style, head


def calculate_drawdown(
    config: configparser.ConfigParser, accounts: dict[str, AccountSummary]
):
    pensionConfig = config["pension_model"]
    noOfYears = int(pensionConfig["ageMoneyRequiredUntil"]) - int(
        pensionConfig["ageAtRetirement"]
    )
    montlyMoneyRequired = int(pensionConfig["monthlyIncomeRequired"])
    annualDBIncome = int(pensionConfig["finalSalaryPension"])
    taxAllowance = int(config["tax_thresholds"]["incomeTaxAllowance"])
    cgtaxAllowance = int(config["tax_thresholds"]["capitalGainTaxAllowance"])
    cgtaxRate = int(config["trading_tax_rates"]["capitalGainLowerTax"])
    lowerTaxRate = int(config["sipp_tax_rates"]["withdrawlLowerTax"])
    maxTaxableIncome = int(config["tax_thresholds"]["incomeUpperThreshold"])
    maxISAInvestment = int(config["isa_tax_rates"]["maxYearlyInvestment"])
    netannualDBIncome = (
        annualDBIncome - (annualDBIncome - taxAllowance) * lowerTaxRate / 100
    )
    maxSippIncome = (
        maxTaxableIncome - annualDBIncome
    )  # Max can take out of SIPP to keep below upper tax threshold
    netMaxSippIncome = maxSippIncome - (
        maxSippIncome * lowerTaxRate / 100
    )  # Net of tax SIPP income
    # Set up dict that contains a dict of model name that has a dict of all account values by year that can be plotted
    accValues: dict[str, dict[float, dict[str, Decimal]]] = dict()
    for rateReturn in [-3, -5, 1, 2, 3, 4, 5]:
        if rateReturn == -3:
            model = "hist3yr%"
        elif rateReturn == -5:
            model = "hist5yr%"
        else:
            model = f"{rateReturn}%"
        # Set initial value based on current market value of accounts
        accValues[model] = dict()
        accValues[model][0] = dict()
        for acc, summary in accounts.items():
            accValues[model][0][acc] = summary.totalMarketValue
        lastYear = 0
        for year in np.arange(1.0, noOfYears, 0.5):
            # Run model every 6 months
            # TODO: Allow for inflation
            # 0. Set up this years starting values as the same as end of last period
            accValues[model][year] = dict()
            for acc in accounts:
                accValues[model][year][acc] = accValues[model][lastYear][acc]
            lastYear = year
            currentAccs = accValues[model][year]
            isaAllowance = maxISAInvestment / 2
            for acc, summary in accounts.items():
                # 1. Increase value by 6 monthly return
                if rateReturn == -3:
                    currentAccs[acc] *= Decimal(
                        1 + (summary.avgFund3YrReturn / 100) / 2
                    )
                elif rateReturn == -5:
                    currentAccs[acc] *= Decimal(
                        1 + (summary.avgFund5YrReturn / 100) / 2
                    )
                else:
                    currentAccs[acc] *= Decimal(1 + (rateReturn / 100) / 2)
            totalRequired = montlyMoneyRequired * 6
            residual6MonthlyIncome = 0
            if currentAccs["sipp"] >= maxSippIncome / 2:
                # 2(a). Take out max income from SIPP
                currentAccs["sipp"] -= Decimal(maxSippIncome / 2)
                totalIncome = (netannualDBIncome + netMaxSippIncome) / 2
                if totalIncome > totalRequired:
                    # Work out how much money is left after taking out required spends from total income (Defined benefit + max SIPP)
                    residual6MonthlyIncome = totalIncome - totalRequired
                    totalRequired = 0
                else:
                    # Income from DB and max SIPP income not enough
                    totalRequired -= totalIncome
            if totalRequired > 0:
                if currentAccs["trading"] > totalRequired:
                    # 2(b) Need more income - take out required income from trading account
                    if totalRequired > cgtaxAllowance:
                        # Need to take off cg tax, so amount need take out increased
                        amtTaxed = totalRequired - cgtaxAllowance
                        totalRequired += amtTaxed * cgtaxRate / 100
                    currentAccs["trading"] -= Decimal(totalRequired)
                    totalRequired = 0
                else:
                    # 2(c) Run out of funds in both SIPP and trading - take it from ISA
                    currentAccs["isa"] -= Decimal(totalRequired)
                    totalRequired = 0
            if residual6MonthlyIncome > 0:
                # 3(a) If money left, add to investments
                if residual6MonthlyIncome < isaAllowance:
                    # 4(a) Put all residual income in ISA
                    currentAccs["isa"] += Decimal(residual6MonthlyIncome)
                    isaAllowance -= residual6MonthlyIncome
                else:
                    # 4(b) Amount exceeds ISA investment limits - invest remainder in trading account"
                    currentAccs["isa"] += Decimal(isaAllowance)
                    currentAccs["trading"] += Decimal(
                        residual6MonthlyIncome - isaAllowance
                    )
                    isaAllowance = 0
            if isaAllowance > 0 and currentAccs["trading"] > 0:
                # ISA allowance available - move from trading to ISA
                if currentAccs["trading"] > isaAllowance:
                    currentAccs["isa"] += Decimal(isaAllowance)
                    currentAccs["trading"] -= Decimal(isaAllowance)
                else:
                    currentAccs["isa"] += currentAccs["trading"]
                    currentAccs["trading"] = 0
                isaAllowance = 0

    return accValues


def htmlReport(
    dom: body,
    monthlyAmtRequired,
    monthlyDBGrossIncome,
    accountValues: dict[str, dict[float, dict[str, Decimal]]],
):
    dom.append(h1("Modelling drawdown on investment funds"))
    dom.append(h3(f"Monthly Required Income: £{monthlyAmtRequired:,.0f}"))
    dom.append(
        h3(f"Monthly Gross Defined Benefit Income: £{monthlyDBGrossIncome:,.0f}")
    )
    for model, accVals in accountValues.items():
        dom.append(h2(f"Scenario: {model} annual return"))
        graphVals: dict[str, list[float]] = {
            "Year": list(),
            "Total": list(),
            "trading": list(),
            "isa": list(),
            "sipp": list(),
        }
        for year, fund_value in accVals.items():
            graphVals["Year"].append(year)
            graphVals["Total"].append(
                fund_value["trading"] + fund_value["isa"] + fund_value["sipp"]
            )
            for key, val in fund_value.items():
                graphVals[key].append(val)
        df = DataFrame(graphVals)
        fig = px.line(
            df,
            x="Year",
            y=df.columns,
            hover_data={"Year"},
            labels={"Value": "£"},
        )
        # fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
        # fig.show()
        dom.appendChild(fig.to_html())

    # for model, accVals in accountValues.items():
    #     print(f"Scenario: {model} annual return\n")
    #     print("\nYear\tTotal\ttrading\tisa\tsipp")
    #     for year, fund_value in accVals.items():
    #         total = fund_value["trading"] + fund_value["isa"] + fund_value["sipp"]
    #         print(
    #             f"{year}\t£{total:,.0f}\t£{fund_value['trading']:,.0f}\t£{fund_value['isa']:,.0f}\t£{fund_value['sipp']:,.0f}\n"
    #         )
    # for dtime in dateList:
    # (marketValue, bookCost) = accountSummary.historicValue[dtime]
    # accgain = (
    #     100 * float((marketValue - bookCost) / bookCost) if bookCost > 0 else 0
    # )
    # dt = datetime.fromtimestamp(dtime)
    # gainDict["Date"].append(dt)
    # gainDict["Total"].append(accgain)
    # lastElem = len(gainDict["Date"]) - 1
    # ftv = accountSummary.historicValueByType[dtime]
    # for ftyp in fundTypes:
    #     gainDict[ftyp.name].append(
    #         100.0
    #         * float(
    #             (ftv.get(ftyp, (0, 0))[0] - ftv.get(ftyp, (0, 0))[1])
    #             / ftv.get(ftyp, (1, 1))[1]
    #         )
    #     )
    # fs.appendChild(
    #     tr(
    #         td(f"{dt.date()}"),
    #         td(f"£{marketValue:,.0f}"),
    #         td(f"£{bookCost:,.0f}"),
    #         td(f"{accgain:0.2f}%"),
    #         "".join(
    #             [
    #                 f"{td(100.0*float(ftv.get(ftyp,(0,0))[0]/marketValue)):0.1f}"
    #                 for ftyp in fundTypes
    #             ]
    #         ),
    #         "".join(
    #             [
    #                 f"{td(gainDict[ftyp.name][lastElem]):0.1f}"
    #                 for ftyp in fundTypes
    #             ]
    #         ),
    #         _class="positive" if accgain > 0 else "negative",
    #     )
    # )
    # dom.appendChild(fs)


def main():
    parser = argparse.ArgumentParser(description="Process accounts to model drawdown")
    # parser.add_argument('-d', '--hdfs', action='store_const', const=False, default=True,
    #                    help='Set if using hdfs filesystem rather than local store (True)')
    parser.add_argument(
        "--owner", default="danny", help="name of the owner of the accounts"
    )
    args = vars(parser.parse_args())
    accountOwner = args["owner"]

    config = configparser.ConfigParser()
    config.read("./stockpicker.ini")
    localeStr = config["stats"]["locale"]
    locale.setlocale(locale.LC_ALL, localeStr)
    config.set("owner", "accountowner", accountOwner)

    # Read in account summaries
    accountList = config["pension_model"][f"{accountOwner}_accounts"].split(",")
    accounts: dict[str, AccountSummary] = dict()
    for acc in accountList:
        accounts[acc] = AccountSummary.from_json(
            retrieveStringFromDropbox(
                config["store"],
                f"/{accountOwner}-performance/csvFiles/{acc}-Summary.json",
            )
        )

    accountValues = calculate_drawdown(config, accounts)

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
    ht.append(dom)
    pensionConfig = config["pension_model"]
    montlyMoneyRequired = int(pensionConfig["monthlyIncomeRequired"])
    annualDBIncome = int(pensionConfig["finalSalaryPension"]) / 12

    htmlReport(dom, montlyMoneyRequired, annualDBIncome, accountValues)
    # # Display the results
    # for model, accVals in accountValues.items():
    #     print(f"Scenario: {model} annual return\n")
    #     print("\nYear\tTotal\ttrading\tisa\tsipp")
    #     for year, fund_value in accVals.items():
    #         total = fund_value["trading"] + fund_value["isa"] + fund_value["sipp"]
    #         print(
    #             f"{year}\t£{total:,.0f}\t£{fund_value['trading']:,.0f}\t£{fund_value['isa']:,.0f}\t£{fund_value['sipp']:,.0f}\n"
    #         )
    retStr = f"{ht}"
    with open("model-output.html", "w") as fp:
        fp.write(retStr)


if __name__ == "__main__":
    main()
