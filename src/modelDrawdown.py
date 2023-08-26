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
    config: configparser.ConfigParser,
    ratesOfReturn: list,
    accounts: dict[str, AccountSummary],
):
    pensionConfig = config["pension_model"]
    noOfYears = int(pensionConfig["ageMoneyRequiredUntil"]) - int(
        pensionConfig["ageAtRetirement"]
    )
    montlyMoneyRequired = int(pensionConfig["monthlyIncomeRequired"])
    annualDBIncome = int(pensionConfig["finalSalaryPension"])
    pensionIncome = int(pensionConfig["statePensionPerMonth"]) * 12
    taxAllowance = int(config["tax_thresholds"]["incomeTaxAllowance"])
    cgtaxAllowance = int(config["tax_thresholds"]["capitalGainTaxAllowance"])
    cgtaxRate = int(config["trading_tax_rates"]["capitalGainLowerTax"])
    lowerTaxRate = int(config["sipp_tax_rates"]["withdrawlLowerTax"])
    upperTaxRate = int(config["sipp_tax_rates"]["withdrawlUpperTax"])
    maxTaxableIncome = int(config["tax_thresholds"]["incomeUpperThreshold"])
    maxISAInvestment = int(config["isa_tax_rates"]["maxYearlyInvestment"])
    netannualDBIncome = (
        annualDBIncome - (annualDBIncome - taxAllowance) * lowerTaxRate / 100
    )

    # Set up dict that contains a dict of model name that has a dict of all account values by year that can be plotted
    accValues: dict[str, dict[float, dict[str, Decimal]]] = dict()
    for rateReturn in ratesOfReturn:
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
        maxSippIncome = (
            maxTaxableIncome - annualDBIncome
        )  # Max can take out of SIPP to keep below upper tax threshold
        netMaxSippIncome = maxSippIncome - (
            maxSippIncome * lowerTaxRate / 100
        )  # Net of tax SIPP income
        netPensionMonthlyIncome = 0
        for year in np.arange(0.5, noOfYears + 0.5, 0.5):
            # Run model every 6 months
            # TODO: Allow for inflation
            # 0. Set up this years starting values as the same as end of last period
            accValues[model][year] = dict()
            for acc in accounts:
                accValues[model][year][acc] = accValues[model][lastYear][acc]
            lastYear = year
            currentAccs = accValues[model][year]
            isaAllowance = maxISAInvestment / 2
            if year == 7.0:
                maxSippIncome -= pensionIncome
                netMaxSippIncome = maxSippIncome - (
                    maxSippIncome * lowerTaxRate / 100
                )  # Net of tax SIPP income
                netPensionMonthlyIncome = (
                    pensionIncome - (pensionIncome * lowerTaxRate / 100)
                ) / 12
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
            totalRequired -= netPensionMonthlyIncome * 6
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
                elif currentAccs["isa"] > totalRequired:
                    # 2(c) Run out of funds in trading - take it from ISA
                    if currentAccs["trading"] > 0:
                        totalRequired -= float(currentAccs["trading"])
                        currentAccs["trading"] = 0
                    currentAccs["isa"] -= Decimal(totalRequired)
                    totalRequired = 0
                elif currentAccs["sipp"] > totalRequired:
                    # 2(d) Only have funds in SIPP - take amount required from there but taxed at upper rate
                    if currentAccs["trading"] > 0:
                        totalRequired -= float(currentAccs["trading"])
                        currentAccs["trading"] = 0
                    if currentAccs["isa"] > 0:
                        totalRequired -= float(currentAccs["isa"])
                        currentAccs["isa"] = 0
                    totalRequired += totalRequired * upperTaxRate / 100
                    if currentAccs["sipp"] > totalRequired:
                        currentAccs["sipp"] -= Decimal(totalRequired)
                    else:
                        currentAccs["sipp"] = 0

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


def plotAccountValues(
    dom: body,
    accountValues: dict[str, dict[float, dict[str, Decimal]]],
):
    # Plot summary showing total values across all scenarios
    dom.append(h2("Total account values for each scenario by year"))
    graphVals: dict[str, list[float]] = {"Year": list()}
    firstModel = True
    for model, accVals in accountValues.items():
        graphVals[model] = list()
        for year, fund_value in accVals.items():
            if firstModel:
                graphVals["Year"].append(year)
            graphVals[model].append(
                fund_value["trading"] + fund_value["isa"] + fund_value["sipp"]
            )
        firstModel = False
    df = DataFrame(graphVals)
    fig = px.line(
        df,
        x="Year",
        y=df.columns,
        hover_data={"Year"},
        labels={"Total": "£"},
    )
    # fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
    # fig.show()
    dom.appendChild(fig.to_html())

    # Plot each scenario
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
    #     print("\nYear\tTotal\ttrading\tisa\tsipp")int(x.strip())
    #     for year, fund_value in accVals.items():
    #         total = fund_value["trading"] + fund_value["isa"] + fund_value["sipp"]
    #         print(
    #             f"{year}\t£{total:,.0f}\t£{fund_value['trading']:,.0f}\t£{fund_value['isa']:,.0f}\t£{fund_value['sipp']:,.0f}\n"
    #         )


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
    ratesOfReturn = [
        int(x.strip()) for x in config["pension_model"]["ratesOfReturn"].split(",")
    ]
    accounts: dict[str, AccountSummary] = dict()
    for acc in accountList:
        accounts[acc] = AccountSummary.from_json(
            retrieveStringFromDropbox(
                config["store"],
                f"/{accountOwner}-performance/csvFiles/{acc}-Summary.json",
            )
        )

    accountValues = calculate_drawdown(config, ratesOfReturn, accounts)

    taxAllowance = int(config["tax_thresholds"]["incomeTaxAllowance"])
    lowerTaxRate = int(config["sipp_tax_rates"]["withdrawlLowerTax"])
    pensionConfig = config["pension_model"]
    monthlyMoneyRequired = int(pensionConfig["monthlyIncomeRequired"])
    annualDBIncome = int(pensionConfig["finalSalaryPension"])
    pensionIncome = int(pensionConfig["statePensionPerMonth"]) * 12
    netPensionMonthlyIncome = (
        pensionIncome - (pensionIncome * lowerTaxRate / 100)
    ) / 12
    netannualDBIncome = (
        annualDBIncome - (annualDBIncome - taxAllowance) * lowerTaxRate / 100
    )

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
    dom.append(h1("Modelling drawdown on investment funds"))
    dom.append(h3(f"Monthly Required Income: £{monthlyMoneyRequired:,.0f}"))
    dom.append(h3(f"Net Monthly Defined Benefit Income: £{netannualDBIncome/12:,.0f}"))
    dom.append(
        h3(f"Net Monthly Pension Income (Year 7+): £{netPensionMonthlyIncome:,.0f}")
    )

    plotAccountValues(dom, accountValues)
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
    with open("model-output.html", "w", encoding="utf-8") as fp:
        fp.write(retStr)


if __name__ == "__main__":
    main()
