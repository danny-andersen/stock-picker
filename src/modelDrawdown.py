import configparser
import locale

# import argparse
import numpy as np
from decimal import Decimal
import plotly.express as px
from pandas import DataFrame
from domonic.html import td, tr, th, body, table, h1, h2, h3, html, meta, style, head, b

from saveRetreiveFiles import retrieveStringFromDropbox, saveStringToDropbox
from transactionDefs import AccountSummary


def calculate_drawdown(
    config: configparser.ConfigParser,
    monthlyMoneyRequired: int,
    ratesOfReturn: list,
    accounts: dict[str, dict[str, AccountSummary]],
):
    pensionConfig = config["pension_model"]
    noOfYears = int(pensionConfig["ageMoneyRequiredUntil"]) - int(
        pensionConfig["ageAtRetirement"]
    )
    taxAllowance = int(config["tax_thresholds"]["incomeTaxAllowance"])
    cgtaxAllowance = int(config["tax_thresholds"]["capitalGainTaxAllowance"])
    cgtaxRate = int(config["trading_tax_rates"]["capitalGainLowerTax"])
    lowerTaxRate = int(config["sipp_tax_rates"]["withdrawlLowerTax"])
    upperTaxRate = int(config["sipp_tax_rates"]["withdrawlUpperTax"])
    maxTaxableIncome = int(config["tax_thresholds"]["incomeUpperThreshold"])
    maxISAInvestment = int(config["isa_tax_rates"]["maxYearlyInvestment"])
    minResidualValue = int(pensionConfig["requiredLegacyAmount"])

    owners = accounts.keys()
    pensionIncomeByOwner = dict()
    netAnnualDBIncomeByOwner = dict()
    annualDBIncomeByOwner = dict()
    for owner in owners:
        annualDBIncomeByOwner[owner] = int(pensionConfig[f"{owner}_finalSalaryPension"])
        pensionIncomeByOwner[owner] = (
            int(pensionConfig[f"{owner}_statePensionPerMonth"]) * 12
        )
        netAnnualDBIncomeByOwner[owner] = (
            annualDBIncomeByOwner[owner]
            - (annualDBIncomeByOwner[owner] - taxAllowance) * lowerTaxRate / 100
        )
    # work out ratios of income by owner, so contribute proportionate amount
    # for owner in accounts:
    #     for acc in accounts[owner]:
    #         total[owner] += accValues[model][lastYear][acc]
    #         grandTotal += accValues[model][lastYear][acc]
    contributionRatioByOwner: dict[str, float] = dict()
    for owner in accounts:
        contributionRatioByOwner[owner] = netAnnualDBIncomeByOwner[owner] / sum(
            netAnnualDBIncomeByOwner.values()
        )

    # Set up dict that contains a dict of model name that has a dict of owners with a dict of account values by year that can be plotted
    # Account values: model [ year [ owner [account, value]]]
    accValues: dict[str, dict[float, dict[str, dict[str, Decimal]]]] = dict()
    for rateReturn in ratesOfReturn:
        # Convert "special" rates passed in to historic rates
        if rateReturn == 3000:
            model = "hist3yr%"
        elif rateReturn == 5000:
            model = "hist5yr%"
        else:
            model = f"{rateReturn:.1f}%"
        # Set initial value based on current market value of accounts
        accValues[model] = dict()
        accValues[model][0] = dict()
        for owner in accounts:
            accValues[model][0][owner] = dict()
            for acc, summary in accounts[owner].items():
                accValues[model][0][owner][acc] = summary.totalMarketValue
            accValues[model][0][owner]["Total"] = sum(
                accValues[model][0][owner].values()
            )
        lastYear = 0
        lastRemainingTotal = 0
        for year in np.arange(0.5, noOfYears + 0.5, 0.5):
            # Run model every 6 months
            # 0. Set up this years starting values as the same as end of last period
            accValues[model][year] = dict()
            totalAccounts = 0
            for owner in accounts:
                accValues[model][year][owner] = dict()
                for acc in accounts[owner]:
                    accValues[model][year][owner][acc] = accValues[model][lastYear][
                        owner
                    ][acc]
                currentAccs = accValues[model][year][owner]
                for acc, summary in accounts[owner].items():
                    # 1(a). Increase value by 6 monthly return
                    # Convert "special" rates passed into historical rates
                    if rateReturn == 3000:
                        currentAccs[acc] *= Decimal(
                            1 + (summary.avgFund3YrReturn / 200)
                        )
                    elif rateReturn == 5000:
                        currentAccs[acc] *= Decimal(
                            1 + (summary.avgFund5YrReturn / 200)
                        )
                    else:
                        currentAccs[acc] *= Decimal(1 + rateReturn / 200)
                # 1(b). Add in state pension at 67
                if year < 7.0:
                    # No state pension
                    maxSippIncome = (
                        maxTaxableIncome - annualDBIncomeByOwner[owner]
                    )  # Max can take out of SIPP to keep below upper tax threshold
                    netMaxSippIncome = maxSippIncome - (
                        maxSippIncome * lowerTaxRate / 100
                    )  # Net of tax SIPP income
                    netPensionMonthlyIncome = 0
                else:
                    # With state pension
                    maxSippIncome = (
                        maxTaxableIncome
                        - annualDBIncomeByOwner[owner]
                        - pensionIncomeByOwner[owner]
                    )
                    if maxSippIncome < 0:
                        maxSippIncome = 0
                    netMaxSippIncome = maxSippIncome * (
                        1 - (lowerTaxRate / 100)
                    )  # Net of tax SIPP income
                    # Fully tax state pension
                    netPensionMonthlyIncome = (
                        pensionIncomeByOwner[owner] * (1 - (lowerTaxRate / 100))
                    ) / 12
                # 1(c). Take off required income from guaranteed income (DB + State pension)
                # adjusted by ratio of contribution required
                totalRequired = (
                    lastRemainingTotal
                    + contributionRatioByOwner[owner] * monthlyMoneyRequired * 6
                )
                guaranteedIncome = (netAnnualDBIncomeByOwner[owner] / 2) + (
                    netPensionMonthlyIncome * 6
                )
                if totalRequired > guaranteedIncome:
                    residual6MonthlyIncome = 0
                    totalRequired -= guaranteedIncome
                else:
                    residual6MonthlyIncome = guaranteedIncome - totalRequired
                    totalRequired = 0
                # Set this period's isaAllowance
                isaAllowance = maxISAInvestment / 2

                if maxSippIncome > 0:
                    if currentAccs["sipp"] >= maxSippIncome / 2:
                        # 2(a). Take out max income from SIPP, i.e. up to upper tax threshold, to make most of tax allowance
                        currentAccs["sipp"] -= Decimal(maxSippIncome / 2)
                        sippIncome = netMaxSippIncome / 2
                        if sippIncome > totalRequired:
                            # Work out how much money is left after taking out required spends from total income (Defined benefit + max SIPP)
                            # This will then be invested in ISA or trading accounts
                            residual6MonthlyIncome += sippIncome - totalRequired
                            totalRequired = 0
                        else:
                            # Income from DB and max SIPP income not enough
                            totalRequired -= sippIncome
                    else:
                        # Clear out SIPP
                        sippNet = float(currentAccs["sipp"]) * (1 - lowerTaxRate / 100)
                        if totalRequired > sippNet:
                            totalRequired -= sippNet
                        else:
                            residual6MonthlyIncome += sippNet - totalRequired
                        currentAccs["sipp"] = 0
                if totalRequired > 0:
                    # Still need more cash
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
                    elif currentAccs["sipp"] > 0:
                        # 2(d) Not enough in other accounts - take more from SIPP account (i.e. above upper tax threshold)
                        if currentAccs["trading"] > 0:
                            totalRequired -= float(currentAccs["trading"])
                            currentAccs["trading"] = 0
                        if currentAccs["isa"] > 0:
                            totalRequired -= float(currentAccs["isa"])
                            currentAccs["isa"] = 0
                        # 2(d) If only have funds in SIPP - take amount required from there but taxed at upper rate
                        totalRequired += totalRequired * upperTaxRate / 100
                        if currentAccs["sipp"] > totalRequired:
                            currentAccs["sipp"] -= Decimal(totalRequired)
                            totalRequired = 0
                        else:
                            totalRequired -= currentAccs["sipp"]
                            currentAccs["sipp"] = 0
                # Carry forward any remaining total
                lastRemainingTotal = totalRequired
                if residual6MonthlyIncome > 0:
                    # 3(a) If income left, add to investments
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
                currentAccs["Total"] = (
                    currentAccs["trading"] + currentAccs["isa"] + currentAccs["sipp"]
                )
                totalAccounts += currentAccs["Total"]
            if totalAccounts <= minResidualValue:
                # We are bust - break from simulation
                break
            lastYear = year

    return accValues


# Account values: model [ owner [ account [year, value]]]
def plotAccountValues(
    dom: body,
    # Account values: model [ year [ owner [account, value]]]
    accountValues: dict[str, dict[float, dict[str, dict[str, Decimal]]]],
):
    # Plot summary showing total values across all scenarios
    dom.append(h2("Total account values for each scenario by year"))
    graphVals: dict[str, list[float]] = {"Year": list()}
    firstModel = True
    for model, accVals in accountValues.items():
        graphVals[model] = list()
        for year, owners in accVals.items():
            total = 0
            if firstModel:
                graphVals["Year"].append(year)
            for accs in owners.values():
                total += accs["Total"]
            graphVals[model].append(total)
        firstModel = False
    df = DataFrame(graphVals)
    fig = px.line(
        df,
        x="Year",
        y=df.columns,
        hover_data={"Year"},
        labels={"value": "Account Total £"},
    )
    # fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
    # fig.show()
    dom.appendChild(fig.to_html())

    # Plot each scenario
    for model, accVals in accountValues.items():
        dom.append(h2(f"Scenario: {model} annual return"))
        graphVals: dict[str, list[float]] = {
            "Year": list(),
        }
        firstYear = True
        for year, owners in accVals.items():
            graphVals["Year"].append(year)
            for owner, accs in owners.items():
                for acc, val in accs.items():
                    accName = f"{owner}-{acc}"
                    if firstYear:
                        graphVals[accName] = list()
                    graphVals[accName].append(val)
            firstYear = False
        df = DataFrame(graphVals)
        fig = px.line(
            df,
            x="Year",
            y=df.columns,
            hover_data={"Year"},
            labels={"value": "Account total £"},
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


def runDrawdownModel(config: configparser.ConfigParser):
    modelConfig = config["pension_model"]
    owners: list() = modelConfig["model_owners"].split(",")

    accounts: dict[str, dict[str, AccountSummary]] = dict()
    accountList = ("sipp", "trading", "isa")
    ratesOfReturn = [
        int(x.strip()) for x in config["pension_model"]["ratesOfReturn"].split(",")
    ]
    # Insert rates of return that indicate to use account historic rates
    ratesOfReturn.insert(0, 3000)
    ratesOfReturn.insert(0, 5000)
    for accountOwner in owners:
        # Read in account summaries
        accounts[accountOwner] = dict()
        for acc in accountList:
            retStr: str = retrieveStringFromDropbox(
                config["store"],
                f"/{accountOwner}-performance/csvFiles/{acc}-Summary.json",
            )
            if "NO FILE READ" not in retStr:
                accounts[accountOwner][acc] = AccountSummary.from_json(retStr)
            else:
                # Calculated Summary not available - use figure in ini file
                summary = AccountSummary(acc, accountOwner)
                summary.totalMarketValue = Decimal(
                    config["pension_model"][f"{accountOwner}_{acc}"]
                )
                accounts[accountOwner][acc] = summary

    # Initialise output html dom
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
            )
        )
    )
    dom = body()
    ht.append(dom)

    # Run drawdown with various monthlyRequired to get close as possible to the requiredlegacyAmount for the required number of years
    # This shows the maximum safe withdrawal rate as a net income
    ageRequiredTo = modelConfig["ageMoneyRequiredUntil"]
    noOfYears = int(ageRequiredTo) - int(modelConfig["ageAtRetirement"])

    minResidualValue = int(modelConfig["requiredLegacyAmount"])
    maxDrawdownByModel = dict()
    for rate in ratesOfReturn:
        monthlyMoneyRequired = int(modelConfig["monthlyIncomeRequired"])
        if rate == 3000:
            model = "hist3yr%"
        elif rate == 5000:
            model = "hist5yr%"
        else:
            model = f"{rate:,.1f}%"
        lastMonthly = 0
        while True:
            accVals = calculate_drawdown(config, monthlyMoneyRequired, [rate], accounts)
            total = 0
            # Check whether the given return rate failed, i.e. money ran out before the years were up
            fail = max(accVals[model].keys()) < noOfYears
            if not fail:
                for owner in owners:
                    total += accVals[model][noOfYears][owner]["Total"]
            if not fail and total > minResidualValue:
                # Had money left so increase monthly outgoings by 1% until we have used it all
                lastMonthly = monthlyMoneyRequired
                lastTotal = total
                monthlyMoneyRequired *= 1.01
            elif lastMonthly > 0:
                # Got max value, which is previous attempt
                maxDrawdownByModel[model] = (lastMonthly, lastTotal)
                break
            else:
                # First attempt failed - reduce by .5% until greater than 0
                monthlyMoneyRequired *= 0.995

    # Print out max drawdown results
    dom.append(
        h2(
            "Max monthly total income by rate of return relative to inflation, in terms of today's money"
        )
    )
    dom.append(
        h3(
            f"Required amount to be left at aged {ageRequiredTo}: £{minResidualValue:,.0f}"
        )
    )
    maxResults = table()
    maxResults.appendChild(
        tr(
            td(b("Rate of Return")),
            td(b("Monthly Income")),
            td(b(f"Residual value at {ageRequiredTo}")),
        )
    )
    for rate, (monthlyIncome, residual) in maxDrawdownByModel.items():
        if rate == "0.0%":
            zeroGrowthMaxDrawdown = monthlyIncome
        maxResults.appendChild(
            tr(td(f"{rate}"), td(f"£{monthlyIncome:,.0f}"), td(f"£{residual:,.0f}"))
        )
    dom.append(maxResults)

    # Run drawdown with various negative growths to get close as possible to requiredlegacyAmount for the required number of years
    # whilst maintaining the required net income.
    # This shows what the worst case growth rate that we can observe without impacting what monthly money is drawdown

    monthlyMoneyRequired = int(modelConfig["monthlyIncomeRequired"])
    rate = 0
    lastRate = 0.1
    lastTotal = -1
    while True:
        accVals = calculate_drawdown(config, monthlyMoneyRequired, [rate], accounts)
        total = 0
        fail = max(accVals[f"{rate:,.1f}%"].keys()) < noOfYears
        if not fail:
            for owner in owners:
                total += accVals[f"{rate:,.1f}%"][noOfYears][owner]["Total"]
        if not fail and total > minResidualValue:
            # Had money left so decrease rate of return by 0.1% until we hit zero
            lastRate = rate
            lastTotal = total
            rate -= 0.1
        elif lastTotal != -1:
            # Got min return rate, which is previous attempt
            break
        else:
            # First attempt failed - increase rate until final amount above legacy amount
            rate += 0.1

    # Save results
    minimiumSustainableRate = lastRate
    residualAmountAtMinRate = lastTotal

    # Run model drawdown with various rates of return for required income
    # This will show how the account values change over the drawdown period
    monthlyMoneyRequired = int(modelConfig["monthlyIncomeRequired"])
    ratesOfReturn.insert(0, minimiumSustainableRate)
    accountValues = calculate_drawdown(
        config, monthlyMoneyRequired, ratesOfReturn, accounts
    )

    # Print out results based on required drawdown
    taxAllowance = int(config["tax_thresholds"]["incomeTaxAllowance"])
    lowerTaxRate = int(config["sipp_tax_rates"]["withdrawlLowerTax"])
    monthlyMoneyRequired = int(modelConfig["monthlyIncomeRequired"])
    netAnnualDBIncome = 0
    netPensionMonthlyIncome = 0
    for owner in owners:
        annualDBIncome = int(modelConfig[f"{owner}_finalSalaryPension"])
        netAnnualDBIncome += (
            annualDBIncome - (annualDBIncome - taxAllowance) * lowerTaxRate / 100
        )
        pensionIncome = int(modelConfig[f"{owner}_statePensionPerMonth"]) * 12
        netPensionMonthlyIncome += (
            pensionIncome - (pensionIncome * lowerTaxRate / 100)
        ) / 12
    dom.append(h1("Modelling drawdown on investment funds"))
    dom.append(h3(f"Average Monthly Required Income: £{monthlyMoneyRequired:,.0f}"))
    dom.append(h3(f"Net Monthly Defined Benefit Income: £{netAnnualDBIncome/12:,.0f}"))
    dom.append(
        h3(
            f"Net Monthly State Pension Income (Year 7+): £{netPensionMonthlyIncome:,.0f}"
        )
    )
    dom.append(
        h3(
            f"Calculated minimum rate of return (less inflation) to support average required income is {minimiumSustainableRate:,.1f}%, giving residual value of £{residualAmountAtMinRate:,.0f} at aged {ageRequiredTo}"
        )
    )
    plotAccountValues(dom, accountValues)

    # Run model drawdown with max drawdown for 0% growth rate (as calculated above) with various rates of return
    # This will show how the account values change over the drawdown period
    monthlyMoneyRequired = zeroGrowthMaxDrawdown
    # Re-create rates of return array
    ratesOfReturn = [
        int(x.strip()) for x in config["pension_model"]["ratesOfReturn"].split(",")
    ]
    # Insert rates of return that indicate to use account historic rates
    ratesOfReturn.insert(0, 3000)
    ratesOfReturn.insert(0, 5000)
    accountValues = calculate_drawdown(
        config, monthlyMoneyRequired, ratesOfReturn, accounts
    )

    # Print out results based on required drawdown
    taxAllowance = int(config["tax_thresholds"]["incomeTaxAllowance"])
    lowerTaxRate = int(config["sipp_tax_rates"]["withdrawlLowerTax"])
    monthlyMoneyRequired = zeroGrowthMaxDrawdown
    netAnnualDBIncome = 0
    netPensionMonthlyIncome = 0
    for owner in owners:
        annualDBIncome = int(modelConfig[f"{owner}_finalSalaryPension"])
        netAnnualDBIncome += (
            annualDBIncome - (annualDBIncome - taxAllowance) * lowerTaxRate / 100
        )
        pensionIncome = int(modelConfig[f"{owner}_statePensionPerMonth"]) * 12
        netPensionMonthlyIncome += (
            pensionIncome - (pensionIncome * lowerTaxRate / 100)
        ) / 12
    dom.append(
        h1("Modelling max sustainable drawdown with zero growth on investment funds")
    )
    dom.append(h3(f"Average Monthly Drawdown amount: £{monthlyMoneyRequired:,.0f}"))
    dom.append(h3(f"Net Monthly Defined Benefit Income: £{netAnnualDBIncome/12:,.0f}"))
    dom.append(
        h3(
            f"Net Monthly State Pension Income (Year 7+): £{netPensionMonthlyIncome:,.0f}"
        )
    )
    dom.append(
        h3(
            f"Required amount to be left at aged {ageRequiredTo}: £{minResidualValue:,.0f}"
        )
    )
    plotAccountValues(dom, accountValues)

    # Display the results
    # for model, accVals in accountValues.items():
    #     print(f"Scenario: {model} annual return\n")
    #     print("\nYear\tTotal\ttrading\tisa\tsipp")
    #     for year, fund_value in accVals.items():
    #         total = fund_value["trading"] + fund_value["isa"] + fund_value["sipp"]
    #         print(
    #             f"{year}\t£{total:,.0f}\t£{fund_value['trading']:,.0f}\t£{fund_value['isa']:,.0f}\t£{fund_value['sipp']:,.0f}\n"
    #         )
    retStr = f"{ht}"
    saveStringToDropbox(config["store"], "/model-output.html", retStr)
    # with open("model-output.html", "w", encoding="utf-8") as fp:
    #     fp.write(retStr)


if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description="Process accounts to model drawdown")
    # parser.add_argument('-d', '--hdfs', action='store_const', const=False, default=True,
    #                    help='Set if using hdfs filesystem rather than local store (True)')
    # parser.add_argument(
    #     "--owner", default="danny", help="name of the owner of the accounts"
    # )
    # args = vars(parser.parse_args())
    # accountOwner = args["owner"]

    config = configparser.ConfigParser()
    config.read("./stockpicker.ini")
    localeStr = config["stats"]["locale"]
    locale.setlocale(locale.LC_ALL, localeStr)

    runDrawdownModel(config)
