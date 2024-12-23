import configparser
import locale
import datetime

# import argparse
import numpy as np
from decimal import Decimal
import plotly.express as px
from pandas import DataFrame
from domonic.html import (
    td,
    tr,
    th,
    body,
    table,
    h1,
    h2,
    h3,
    html,
    meta,
    style,
    head,
    b,
    ul,
    li,
    colgroup,
    col,
)

from saveRetreiveFiles import retrieveStringFromDropbox, saveStringToDropbox
from transactionDefs import AccountSummary

HIST3YR = "3yr Historic return%"
HIST5YR = "5yr Historic return%"
TOTAL = "Total"


def calculate_drawdown(
    configIni: configparser.ConfigParser,
    monthlyMoneyRequired: int,
    ratesOfReturn: list,
    accounts: dict[str, dict[str, AccountSummary]],
    noOfYears: int,
):
    pensionConfig = configIni["pension_model"]
    taxAllowance = int(configIni["tax_thresholds"]["incomeTaxAllowance"])
    cgtaxAllowance = int(configIni["tax_thresholds"]["capitalGainTaxAllowance"])
    cgtaxRate = int(configIni["trading_tax_rates"]["capitalGainLowerTax"])
    lowerTaxRate = int(configIni["sipp_tax_rates"]["withdrawlLowerTax"])
    upperTaxRate = int(configIni["sipp_tax_rates"]["withdrawlUpperTax"])
    maxTaxableIncome = int(configIni["tax_thresholds"]["incomeUpperThreshold"])
    maxISAInvestment = int(configIni["isa_tax_rates"]["maxYearlyInvestment"])
    minResidualValue = int(pensionConfig["requiredLegacyAmount"])
    statePensionStart = pensionConfig["statePensionStart"]

    owners = accounts.keys()
    pensionIncomeByOwner = dict()
    netAnnualDBIncomeByOwner = dict()
    annualDBIncomeByOwner = dict()
    contributionRatioByOwner: dict[str, Decimal] = dict()
    statePensionDate = datetime.date.fromisoformat(statePensionStart)
    noOfYearsToStatePension = statePensionDate.year - datetime.date.today().year

    for owner in owners:
        annualDBIncomeByOwner[owner] = int(pensionConfig[f"{owner}_finalSalaryPension"])
        pensionIncomeByOwner[owner] = (
            int(pensionConfig[f"{owner}_statePensionPerMonth"]) * 12
        )
        netAnnualDBIncomeByOwner[owner] = (
            annualDBIncomeByOwner[owner]
            - (annualDBIncomeByOwner[owner] - taxAllowance) * lowerTaxRate / 100
        )
        # ratios of income by owner, so contribute proportionate amount
        contributionRatioByOwner[owner] = float(pensionConfig[f"{owner}_drawdownRatio"])

    # Set up dict that contains a dict of model name that has a dict of owners with a dict of account values by year that can be plotted
    # Account values: model [ year [ owner [account, value]]]
    accValues: dict[str, dict[float, dict[str, dict[str, Decimal]]]] = dict()
    for rateReturn in ratesOfReturn:
        # Convert "special" rates passed in to historic rates
        if rateReturn == 3000:
            model = HIST3YR
        elif rateReturn == 5000:
            model = HIST5YR
        else:
            model = f"{rateReturn:.1f}%"
        # Set initial value based on current market value of accounts
        accValues[model] = dict()
        accValues[model][0] = dict()
        for owner in accounts:
            accValues[model][0][owner] = dict()
            for acc, summary in accounts[owner].items():
                accValues[model][0][owner][acc] = summary.totalMarketValue
            accValues[model][0][owner][TOTAL] = sum(accValues[model][0][owner].values())
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
                if year < noOfYearsToStatePension:
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
                    if currentAccs["sipp"] > totalRequired:
                        # 2(b) Take more from SIPP account (i.e. above upper tax threshold) - we pay 40% tax but better than taking it from trading or ISA
                        # Firstly clear out the other funds of all the remaining cash
                        totalRequired += totalRequired * upperTaxRate / 100
                        currentAccs["sipp"] -= Decimal(totalRequired)
                        totalRequired = 0
                    elif currentAccs["trading"] > totalRequired:
                        # 2(b) Need more income - take out required income from trading account
                        # Firstly clear out the other funds of all the remaining cash
                        if currentAccs["sipp"] > 0:
                            totalRequired -= float(currentAccs["sipp"])
                            currentAccs["sipp"] = 0
                        if totalRequired > cgtaxAllowance:
                            # Need to take off cg tax, so amount need take out increased (this assumes that all we take out is capital gain)
                            amtTaxed = totalRequired - cgtaxAllowance
                            totalRequired += amtTaxed * cgtaxRate / 100
                        currentAccs["trading"] -= Decimal(totalRequired)
                        totalRequired = 0
                    elif currentAccs["isa"] > totalRequired:
                        # 2(d) Run out of funds in SIPP and trading - take it from ISA
                        # Firstly clear out the other funds of all the remaining cash
                        if currentAccs["sipp"] > 0:
                            totalRequired -= float(currentAccs["sipp"])
                            currentAccs["sipp"] = 0
                        if currentAccs["trading"] > 0:
                            totalRequired -= float(currentAccs["trading"])
                            currentAccs["trading"] = 0
                        currentAccs["isa"] -= Decimal(totalRequired)
                        totalRequired = 0
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
                if isaAllowance > 0 and (currentAccs["sipp"] > 0 or currentAccs["trading"] > 0):
                    # ISA allowance available - move from trading or SIPP to ISA
                    if currentAccs["sipp"] > isaAllowance:
                        currentAccs["isa"] += Decimal(isaAllowance)
                        isaAllowance += isaAllowance * upperTaxRate / 100
                        currentAccs["sipp"] -= Decimal(isaAllowance)
                        isaAllowance = 0
                    elif currentAccs["sipp"] > 0:
                        currentAccs["isa"] += currentAccs["sipp"]
                        isaAllowance -= int(currentAccs["sipp"])
                        currentAccs["sipp"] = 0
                    if isaAllowance > 0:
                        if currentAccs["trading"] > isaAllowance:
                            currentAccs["isa"] += Decimal(isaAllowance)
                            currentAccs["trading"] -= Decimal(isaAllowance)
                            isaAllowance = 0
                        elif currentAccs["trading"] > 0:
                            currentAccs["isa"] += currentAccs["trading"]
                            currentAccs["trading"] = 0
                            isaAllowance -= currentAccs["sipp"]
                currentAccs[TOTAL] = (
                    currentAccs["trading"] + currentAccs["isa"] + currentAccs["sipp"]
                )
                totalAccounts += currentAccs[TOTAL]
            if totalAccounts <= minResidualValue:
                # We are bust - break from simulation
                break
            lastYear = year

    return accValues


def plotScenarioChart(dom: body, accVals: dict[float, dict[str, dict[str, Decimal]]]):
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
                total += accs[TOTAL]
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
        plotScenarioChart(dom, accVals)

    # for model, accVals in accountValues.items():
    #     print(f"Scenario: {model} annual return\n")
    #     print("\nYear\tTotal\ttrading\tisa\tsipp")int(x.strip())
    #     for year, fund_value in accVals.items():
    #         total = fund_value["trading"] + fund_value["isa"] + fund_value["sipp"]
    #         print(
    #             f"{year}\t£{total:,.0f}\t£{fund_value['trading']:,.0f}\t£{fund_value['isa']:,.0f}\t£{fund_value['sipp']:,.0f}\n"
    #         )


def runDrawdownModel(configFile: configparser.ConfigParser):
    modelConfig = configFile["pension_model"]
    owners: list = modelConfig["model_owners"].split(",")

    accounts: dict[str, dict[str, AccountSummary]] = dict()
    accountList = ("sipp", "trading", "isa")
    ratesOfReturn = [
        int(x.strip()) for x in configFile["pension_model"]["ratesOfReturn"].split(",")
    ]
    # Insert rates of return that indicate to use account historic rates
    ratesOfReturn.insert(0, 3000)
    ratesOfReturn.insert(0, 5000)
    for accountOwner in owners:
        # Read in account summaries
        accounts[accountOwner] = dict()
        for acc in accountList:
            retStr: str = retrieveStringFromDropbox(
                configFile["store"],
                f"/{accountOwner}-performance/csvFiles/{acc}-Summary.json",
            )
            if "NO FILE READ" not in retStr:
                accounts[accountOwner][acc] = AccountSummary.from_json(retStr)
            else:
                # Calculated Summary not available - use figure in ini file
                summary = AccountSummary(acc, accountOwner)
                summary.totalMarketValue = Decimal(
                    configFile["pension_model"][f"{accountOwner}_{acc}"]
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
        ul {
                margin: 0px;
                padding-left: 0;
        }
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
    startDate = datetime.date.today()
    endOfDrawDown = datetime.date.fromisoformat(modelConfig["retirementEnd"])
    retirementDate = datetime.date.fromisoformat(modelConfig["retirementStart"])
    if (startDate < retirementDate):
        #Before retirement - start at retirementStart date
        startDate = retirementDate
    noOfYears = endOfDrawDown.year - startDate.year
    startYearNo = startDate.year - retirementDate.year + 1

    minResidualValue = int(modelConfig["requiredLegacyAmount"])
    maxDrawdownByModel = dict()
    for rate in ratesOfReturn:
        monthlyMoneyRequired = int(modelConfig["monthlyIncomeRequired"])
        if rate == 3000:
            model = HIST3YR
        elif rate == 5000:
            model = HIST5YR
        else:
            model = f"{rate:,.1f}%"
        lastMonthly = 0
        while True:
            accVals = calculate_drawdown(
                configFile, monthlyMoneyRequired, [rate], accounts, noOfYears
            )
            total = 0
            # Check whether the given return rate failed, i.e. money ran out before the years were up
            fail = max(accVals[model].keys()) < noOfYears
            if not fail:
                for owner in owners:
                    total += accVals[model][noOfYears][owner][TOTAL]
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
            td(b("Max Monthly Income")),
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

    dom.append(h2("Yearly gross income by source to give required net monthly income"))
    dom.append(
        h3("Note: Assumes investment growth + pension increase by RPI (0% growth)")
    )
    monthlyMoneyRequired = int(modelConfig["monthlyIncomeRequired"])
    results = table()
    # colborders = colgroup()
    # colborder = col()
    # colborder.style = "border: 1px solid black"
    # colborders.append(colborder)
    # results.append(colborders)
    headerRow = tr()
    headerRow.append(td(b("Source")))
    # Account values: model [ year [ owner [account, value]]]
    # Inv total value [ owner [ income]]
    sourceRows: dict[str, list] = dict()
    pensionIncomeByOwner = dict()
    annualDBIncomeByOwner = dict()

    for owner in owners:
        sourceRows[owner] = list()
        sourceRows[owner].append(tr(td(f"{owner} Final Salary Pension")))
        sourceRows[owner].append(tr(td(f"{owner} Gov Pension")))
        sourceRows[owner].append(tr(td(f"{owner} Inv + DD Income")))
        sourceRows[owner].append(tr(td(b(f"{owner} Gross Income"))))
        sourceRows[owner].append(
            tr(td(f"{owner} Residual value at age {ageRequiredTo}"))
        )
        annualDBIncomeByOwner[owner] = int(modelConfig[f"{owner}_finalSalaryPension"])
        pensionIncomeByOwner[owner] = (
            int(modelConfig[f"{owner}_statePensionPerMonth"]) * 12
        )
    grossRow = tr(td(b("Total Gross Income")))

    # Calculate income needed from investments based on different required monthly incomes
    invValue: dict[int, dict[str, dict[str, Decimal]]] = dict()
    invIncomeByReqdIncome: dict[int, dict[str, dict[str, int]]] = dict()
    finalPotByMoneyReqdByOwner: dict[int, dict[str, dict[str, int]]] = dict()
    for monthly in range(monthlyMoneyRequired, int(zeroGrowthMaxDrawdown), 1000):
        # Account values: model [ year [ owner [account, value]]]
        accountValues = calculate_drawdown(configFile, monthly, [0], accounts, noOfYears)
        finalPotByMoneyReqdByOwner[monthly] = dict()
        for year, ownerAccs in accountValues["0.0%"].items():
            invValue[year] = dict()
            for owner, accs in ownerAccs.items():
                invValue[year][owner] = accs.copy()
        invIncomeByReqdIncome[monthly] = dict()
        invIncomeByReqdIncome[monthly][f"{'Pre' if startYearNo < 8 else 'With'} State Pension, Year {startYearNo}"] = dict()
        if (startYearNo < 8):
            invIncomeByReqdIncome[monthly][f"With State Pension, Year 8"] = dict()
        invIncomeByReqdIncome[monthly]["With State Pension, Year 30"] = dict()
        for owner in owners:
            diff = dict()
            invIncomeByReqdIncome[monthly][f"{'Pre' if startYearNo < 8 else 'With'} State Pension, Year {startYearNo}"][owner] = diff
            for account, amount in invValue[0][owner].items():
                diff[account] = int(amount - invValue[1][owner][account])
            diff = dict()
            if (startYearNo < 8):
                invIncomeByReqdIncome[monthly]["With State Pension, Year 8"][owner] = diff
                for account, amount in invValue[8][owner].items():
                    diff[account] = int(amount - invValue[9][owner][account])
            diff = dict()
            invIncomeByReqdIncome[monthly]["With State Pension, Year 30"][owner] = diff
            for account, amount in invValue[noOfYears-1][owner].items():
                diff[account] = int(amount - invValue[noOfYears][owner][account])
            finalpots = dict()
            finalPotByMoneyReqdByOwner[monthly][owner] = finalpots
            for account, amount in invValue[noOfYears-1][owner].items():
                finalpots[account] = int(invValue[noOfYears][owner][account])
    for monthlyIncome, invIncomeByType in invIncomeByReqdIncome.items():
        for title, incomeByOwner in invIncomeByType.items():
            grandTotal = 0
            headerRow.append(
                td(f"For a net monthly income of £{monthlyIncome:n}, {title}")
            )
            for owner in owners:
                # Final salary pension
                db = annualDBIncomeByOwner[owner]
                sourceRows[owner][0].append(td(f"£{db:n}"))
                # State pension
                state = 0 if "Pre" in title else pensionIncomeByOwner[owner]
                sourceRows[owner][1].append(td(f"£{state:n}"))
                # Investment / DD income
                inc = incomeByOwner[owner][TOTAL]
                sourceRows[owner][2].append(
                    td(
                        ul(
                            "".join(
                                f'{li(f"{account}: £{amount:n}")}'
                                for account, amount in incomeByOwner[owner].items()
                            )
                        )
                    )
                )
                # Total gross income
                total = db + state + inc
                sourceRows[owner][3].append(td(b(f"£{total:n}")))
                # Final pot / residual savings value
                sourceRows[owner][4].append(
                    td(
                        ul(
                            "".join(
                                f'{li(f"{account}: £{amount:n}")}'
                                for account, amount in finalPotByMoneyReqdByOwner[
                                    monthlyIncome
                                ][owner].items()
                            ) if "30" in title else ""
                        )
                    )
                )
                grandTotal += total
            grossRow.append(td(b(f"£{grandTotal:n}")))

    results.appendChild(headerRow)
    for owner in owners:
        for i in range(0, len(sourceRows[owner])):
            results.appendChild(sourceRows[owner][i])
    results.appendChild(grossRow)
    dom.append(results)

    # Run drawdown with various negative growths to get close as possible to requiredlegacyAmount for the required number of years
    # whilst maintaining the required net income.
    # This shows what the worst case growth rate that we can observe without impacting what monthly money is drawdown

    rate = 0
    lastRate = 0.1
    lastTotal = -1
    while True:
        accVals = calculate_drawdown(configFile, monthlyMoneyRequired, [rate], accounts, noOfYears)
        total = 0
        fail = max(accVals[f"{rate:,.1f}%"].keys()) < noOfYears
        if not fail:
            for owner in owners:
                total += accVals[f"{rate:,.1f}%"][noOfYears][owner][TOTAL]
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

    # Run model drawdown with various rates of return for required income
    # This will show how the account values change over the drawdown period
    monthlyMoneyRequired = int(modelConfig["monthlyIncomeRequired"])
    ratesOfReturn.insert(0, minimiumSustainableRate)

    # Account values: model [ year [ owner [account, value]]]
    accountValues = calculate_drawdown(
        configFile, monthlyMoneyRequired, ratesOfReturn, accounts, noOfYears
    )

    # Print out results based on required drawdown
    taxAllowance = int(configFile["tax_thresholds"]["incomeTaxAllowance"])
    lowerTaxRate = int(configFile["sipp_tax_rates"]["withdrawlLowerTax"])
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
    dom.append(
        h3(f"Average Monthly Required Income (Net): £{monthlyMoneyRequired:,.0f}")
    )
    dom.append(h3(f"Net Monthly Defined Benefit Income: £{netAnnualDBIncome/12:,.0f}"))
    dom.append(
        h3(
            f"Net Monthly State Pension Income (Year 7+): £{netPensionMonthlyIncome:,.0f}"
        )
    )
    dom.append(
        h2(
            f"Residual value by rate of return (relative to inflation), in terms of today's money at age {ageRequiredTo}"
        )
    )

    results = table()
    results.appendChild(
        tr(
            td(b("Rate of Return")),
            td(b(f"{owners[0]} total value")),
            td(b(f"{owners[1]} total value")),
            td(b("Final total value")),
        )
    )
    for model, accVals in accountValues.items():
        accOwners = accVals[noOfYears]
        row = tr()
        row.append(td(model))
        total0 = accOwners[owners[0]][TOTAL]
        total1 = accOwners[owners[1]][TOTAL]
        row.appendChild(td(f"£{total0:,.0f}"))
        row.appendChild(td(f"£{total1:,.0f}"))
        row.appendChild(td(f"£{total0+total1:,.0f}"))
        results.appendChild(row)
    dom.append(results)

    plotAccountValues(dom, accountValues)

    # Run model drawdown with max drawdown for 0% growth rate (as calculated above) with various rates of return
    # This will show how the account values change over the drawdown period
    monthlyMoneyRequired = zeroGrowthMaxDrawdown
    # Re-create rates of return array
    ratesOfReturn = [
        int(x.strip()) for x in configFile["pension_model"]["ratesOfReturn"].split(",")
    ]
    # Insert rates of return that indicate to use account historic rates
    ratesOfReturn.insert(0, 3000)
    ratesOfReturn.insert(0, 5000)
    accountValues = calculate_drawdown(
        configFile, monthlyMoneyRequired, ratesOfReturn, accounts, noOfYears
    )

    # Print out results based on required drawdown
    taxAllowance = int(configFile["tax_thresholds"]["incomeTaxAllowance"])
    lowerTaxRate = int(configFile["sipp_tax_rates"]["withdrawlLowerTax"])
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
        h1(
            "Modelling max sustainable drawdown for different rate of return (above inflation) scenarios"
        )
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
    saveStringToDropbox(configFile["store"], "/model-output.html", retStr)
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
