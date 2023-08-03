# from ast import DictComp
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum, IntEnum
from copy import deepcopy
from statistics import mean
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

CASH_IN = "Cash in"
CASH_OUT = "Cash out"
SELL = "Sell"
BUY = "Buy"
DIVIDEND = "Dividend"
# Equilisation is a return of part of the initial principle,
# so should be taken off the investment amount
EQUALISATION = "Equalisation"
FEES = "Fees"
REFUND = "Refund"
NO_STOCK = "No stock"
INTEREST = "Interest"
STERLING = "STERLING"
USD = "USDUSDUSDUS1"
EUR = "EUREUREUREU1"

SECONDS_IN_YEAR = 365.25 * 24 * 3600

TAX_YEAR_START = date(year=2021, month=4, day=6)


class BondGrade(IntEnum):
    AAA = 1
    AA = 2
    A = 3
    BBB = 4
    BB = 5
    B = 6
    CCC = 7
    CC = 8
    C = 9
    D = 10
    NONE = 11

    def isInvestmentGrade(self):
        return self <= 4

    def isJunkGrade(self):
        return not self.isInvestmentGrade()


class Risk(IntEnum):
    LOW = 1
    MED = 2
    HIGH = 3


class FundType(Enum):
    FUND = 1
    LONG_GILT = 2
    SHORT_GILT = 3
    CORP_BOND = 4
    STOCK_ETF = 5
    BOND_ETF = 6
    SHARE = 7
    CASH = 8
    GOLD = 9


@dataclass
class FundOverview:
    isin: str
    symbol: str
    name: str
    fundType: FundType
    institution: str = None
    income: bool = False
    fees: float = 0.0
    risk: Risk = Risk.MED
    maturity: float = 0.0
    bondGrade: BondGrade = BondGrade.NONE
    americas: float = 0.0
    americasEmerging: float = 0.0
    uk: float = 0.0
    europe: float = 0.0
    europeEmerging: float = 0.0
    asia: float = 0.0
    asiaEmerging: float = 0.0
    cyclical: float = 0.0
    sensitive: float = 0.0
    defensive: float = 0.0
    alpha3Yr: float = 0.0
    beta3Yr: float = 0.0
    sharpe3Yr: float = 0.0
    stdDev3Yr: float = 0.0
    return3Yr: float = 0.0
    return5Yr: float = 0.0
    totalValue: Decimal = Decimal(0.0)
    totalInvested: Decimal = Decimal(0.0)
    actualReturn: float = 0.0
    totRiskVal: Decimal = Decimal(0.0)
    totGeoVal: Decimal = Decimal(0.0)
    totDivVal: Decimal = Decimal(0.0)
    totMatVal: Decimal = Decimal(0.0)

    def getStr(self):
        retStr = "Fund overview:\n"
        retStr += f"Type: {self.fundType.name}\n"
        retStr += f"Income fund? {'Yes' if self.income else 'No'}\n"
        retStr += f"Annual fees: {self.fees}%\n"
        retStr += f"Risk: {self.risk.name}\n"
        if self.isBondType():
            retStr += f"Bond Maturity Average: {self.maturity} years\n"
            retStr += f"Bond Grade: {self.bondGrade.name}\n"
        else:
            retStr += f"Stock spread: Cyclical {self.cyclical}%, Sensitive {self.sensitive}%, Defensive {self.defensive}%\n"
        retStr += f"Geographical Spread: Americas {self.americas}%, Americas Emerging {self.americasEmerging}%, UK {self.uk}%,"
        retStr += f"Europe {self.europe}%, Europe Emerging {self.europeEmerging}%,"
        retStr += f"Asia {self.asia}%, Asia Emerging {self.asiaEmerging}%\n"
        retStr += f"3 year Stats: Alpha {self.alpha3Yr} Beta {self.beta3Yr} Sharpe {self.sharpe3Yr} Standard Dev {self.stdDev3Yr}\n"
        retStr += f"3 year Return: {self.return3Yr}% 5 year Return: {self.return5Yr}%\n"
        return retStr

    def isBondType(self):
        return (
            self.fundType == FundType.LONG_GILT
            or self.fundType == FundType.BOND_ETF
            or self.fundType == FundType.CORP_BOND
        )

    def isStockType(self):
        return (
            self.fundType == FundType.FUND
            or self.fundType == FundType.SHARE
            or self.fundType == FundType.STOCK_ETF
        )

    def isCashType(self):
        return self.fundType == FundType.SHORT_GILT or self.fundType == FundType.CASH

    def isGoldType(self):
        return self.fundType == FundType.GOLD

    def merge(self, fund):
        currVal = float(self.totalValue)
        self.totalValue += fund.totalValue
        totValue = float(self.totalValue)
        val = float(fund.totalValue)
        self.totalInvested += fund.totalInvested

        if totValue > 0:
            self.actualReturn = (
                self.actualReturn * currVal + fund.actualReturn * val
            ) / totValue
            self.fees = (self.fees * currVal + fund.fees * val) / totValue
            self.return3Yr = (
                self.return3Yr * currVal + fund.return3Yr * val
            ) / totValue
            self.return5Yr = (
                self.return5Yr * currVal + fund.return5Yr * val
            ) / totValue

            if self.maturity == 0 and fund.maturity != 0:
                self.maturity = fund.maturity
            elif self.maturity != 0 and self.maturity != 0:
                self.maturity = (
                    self.maturity * currVal + fund.maturity * val
                ) / totValue

            ownTotRisk = self.alpha3Yr + self.beta3Yr + self.sharpe3Yr + self.stdDev3Yr
            newTotRisk = fund.alpha3Yr + fund.beta3Yr + fund.sharpe3Yr + fund.stdDev3Yr
            if ownTotRisk == 0 and newTotRisk != 0:
                # Copy
                self.alpha3Yr = fund.alpha3Yr
                self.beta3Yr = fund.beta3Yr
                self.sharpe3Yr = fund.sharpe3Yr
                self.stdDev3Yr = fund.stdDev3Yr
            elif ownTotRisk != 0 and newTotRisk != 0:
                # Merge
                self.alpha3Yr = (
                    self.alpha3Yr * currVal + fund.alpha3Yr * val
                ) / totValue
                self.beta3Yr = (self.beta3Yr * currVal + fund.beta3Yr * val) / totValue
                self.sharpe3Yr = (
                    self.sharpe3Yr * currVal + fund.sharpe3Yr * val
                ) / totValue
                self.stdDev3Yr = (
                    self.stdDev3Yr * currVal + fund.stdDev3Yr * val
                ) / totValue

            ownTotGeo = (
                self.americas
                + self.americasEmerging
                + self.asia
                + self.asiaEmerging
                + self.europe
                + self.europeEmerging
                + self.uk
            )
            newTotGeo = (
                fund.americas
                + fund.americasEmerging
                + fund.asia
                + fund.asiaEmerging
                + fund.europe
                + fund.europeEmerging
                + fund.uk
            )
            if ownTotGeo == 0 and newTotGeo != 0:
                self.americas = fund.americas
                self.americasEmerging = fund.americasEmerging
                self.asia = fund.asia
                self.asiaEmerging = fund.asiaEmerging
                self.uk = fund.uk
                self.europe = fund.europe
                self.europeEmerging = fund.europeEmerging
            elif ownTotGeo != 0 and newTotGeo != 0:
                self.americas = (
                    self.americas * currVal + fund.americas * val
                ) / totValue
                self.americasEmerging = (
                    self.americasEmerging * currVal + fund.americasEmerging * val
                ) / totValue
                self.asia = (self.asia * currVal + fund.asia * val) / totValue
                self.asiaEmerging = (
                    self.asiaEmerging * currVal + fund.asiaEmerging * val
                ) / totValue
                self.europe = (self.europe * currVal + fund.europe * val) / totValue
                self.europeEmerging = (
                    self.europeEmerging * currVal + fund.europeEmerging * val
                ) / totValue
                self.uk = (self.uk * currVal + fund.uk * val) / totValue

            ownTotDiv = self.cyclical + self.defensive + self.sensitive
            newTotDiv = fund.cyclical + fund.defensive + fund.sensitive
            if ownTotDiv == 0 and newTotDiv != 0:
                self.cyclical = fund.cyclical
                self.defensive = fund.defensive
                self.sensitive = fund.sensitive
            elif ownTotDiv != 0 and ownTotDiv != 0:
                self.cyclical = (
                    self.cyclical * currVal + fund.cyclical * val
                ) / totValue
                self.defensive = (
                    self.defensive * currVal + fund.defensive * val
                ) / totValue
                self.sensitive = (
                    self.sensitive * currVal + fund.sensitive * val
                ) / totValue


@dataclass_json
@dataclass
class Transaction:
    # An investment transaction of some sort
    date: datetime
    ref: str
    symbol: str
    sedol: str
    isin: str
    desc: str
    accountName: str
    qty: float = 0.0
    price: Decimal = Decimal(0.0)
    priceCurrency: str = "£"
    debit: Decimal = Decimal(0.0)
    debitCurrency: str = "£"
    credit: Decimal = Decimal(0.0)
    creditCurrency: str = "£"
    type: str = "Unknown"
    accountBalance: Decimal = Decimal(0.0)

    def __eq__(self, other):
        if not isinstance(other, Transaction):
            return False
        return (
            self.date == other.date
            and self.ref == other.ref
            and self.sedol == other.sedol
            and self.isin == other.isin
            and self.desc == other.desc
            and self.credit == other.credit
            and self.debit == other.debit
        )

    def __hash__(self):
        return hash(
            (
                self.date,
                self.ref,
                self.sedol,
                self.isin,
                self.desc,
                self.credit,
                self.debit,
            )
        )


@dataclass_json
@dataclass
class Security:
    # An investment security held in an Account
    date: datetime
    symbol: str
    desc: str
    isin: str = None
    type: FundType = None
    qty: int = 0
    currentPrice: Decimal = Decimal(0.0)
    currency: str = "£"
    avgBuyPrice: Decimal = Decimal(0.0)
    gain: Decimal = Decimal(0.0)
    marketValue: Decimal = Decimal(0.0)
    bookCost: Decimal = Decimal(0.0)


@dataclass
class CapitalGain:
    # Buy and sell history of stock
    date: datetime
    qty: float
    price: Decimal
    transaction: str
    avgBuyPrice: Decimal


@dataclass
class SecurityDetails:
    sedol: str = None
    symbol: str = None
    isin: str = None
    name: str = None
    account: str = None
    qtyHeld: float = 0.0
    startDate: datetime = None
    endDate: datetime = None
    cashInvested: Decimal = Decimal(0.0)
    diviInvested: Decimal = Decimal(0.0)
    totalInvested: Decimal = Decimal(0.0)
    avgSharePrice: Decimal = Decimal(0.0)
    realisedCapitalGainByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    cgtransactionsByYear: dict[str, list[CapitalGain]] = field(default_factory=dict)
    currentSharePrice: Decimal = Decimal(0.0)
    currentSharePriceDate: datetime = None
    costsByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    dividendsByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    dividendYieldByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    investmentHistory: list[CapitalGain] = field(default_factory=list)
    transactions: set[Transaction] = field(default_factory=set)
    dividendTxnsByYear: dict[str, set[Transaction]] = field(default_factory=dict)
    historicHoldings: list = field(default_factory=list)
    fundOverview: FundOverview = None

    def yearsHeld(self):
        if self.startDate:
            if self.endDate:
                return float(
                    (self.endDate.timestamp() - self.startDate.timestamp())
                    / SECONDS_IN_YEAR
                )
            else:
                return (
                    float((datetime.now(timezone.utc) - self.startDate).total_seconds())
                    / SECONDS_IN_YEAR
                )
        else:
            return 0.0

    def historicCashInvested(self):
        cashInv = 0
        for inv in self.investmentHistory:
            if inv.transaction == BUY:
                cashInv += inv.avgBuyPrice * Decimal(inv.qty)
        return cashInv

    def historicCashDivested(self):
        cashDiv = 0
        for inv in self.investmentHistory:
            if inv.transaction == SELL:
                cashDiv += inv.price * Decimal(inv.qty)
        return cashDiv

    def totalGain(self):
        gain = self.totalDividends() + self.realisedCapitalGain()
        if self.cashInvested > 0:
            # Live investment add in paperGain
            gain += self.paperCGT()
        return gain

    def avgGainPerYear(self):
        if self.yearsHeld() > 0:
            return float(self.totalGain()) / self.yearsHeld()
        else:
            return 0.0

    def totalGainPerc(self):
        if self.cashInvested > 0:
            cashInvested = float(self.historicCashInvested())
        else:
            # Historic stock - use historic investment
            cashInvested = float(self.historicCashInvested())
        if cashInvested > 0:
            return 100.0 * float(self.totalGain()) / cashInvested
        else:
            return 0.0

    def avgGainPerYearPerc(self):
        if self.yearsHeld() > 0:
            return float(self.totalGainPerc()) / self.yearsHeld()
        else:
            return 0.0

    def totalCosts(self):
        return (
            sum(self.costsByYear.values())
            if len(self.costsByYear) > 0
            else Decimal(0.0)
        )

    def totalDividends(self):
        return (
            sum(self.dividendsByYear.values())
            if len(self.dividendsByYear) > 0
            else Decimal(0.0)
        )

    def averageYearlyDivi(self):
        return (
            mean(self.dividendsByYear.values())
            if len(self.dividendsByYear) > 0
            else Decimal(0.0)
        )

    def averageYearlyDiviYield(self):
        return (
            mean(self.dividendYieldByYear.values())
            if len(self.dividendYieldByYear) > 0
            else Decimal(0.0)
        )

    def realisedCapitalGain(self):
        return (
            sum(self.realisedCapitalGainByYear.values())
            if len(self.realisedCapitalGainByYear) > 0
            else Decimal(0.0)
        )

    def marketValue(self):
        return self.currentSharePrice * Decimal(self.qtyHeld)

    def capitalGain(self):
        return self.realisedCapitalGain() + self.paperCGT()

    def paperCGT(self):
        return self.marketValue() - self.totalInvested

    def paperCGTPerc(self):
        if self.totalInvested:
            return 100.0 * float(self.paperCGT() / self.totalInvested)
        else:
            return Decimal(0.0)


@dataclass
class AccountSummary:
    name: str
    owner: str
    dateOpened: datetime = datetime.now(timezone.utc)
    portfolioValueDate: datetime = datetime.now()
    totalDiviReInvested: Decimal = Decimal(0.0)
    cashBalance: Decimal = Decimal(0.0)
    totalOtherAccounts: Decimal = Decimal(0.0)
    totalMarketValue: Decimal = Decimal(0.0)
    totalInvestedInSecurities: Decimal = Decimal(0.0)
    totalPaperGainForTax: Decimal = Decimal(
        0.0
    )  # All paper gain of currently held securities

    portfolioPerc: dict[str, str] = field(default_factory=dict)
    cashInByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    cashOutByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    taxfreeCashOutByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    feesByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    aggInvestedByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    realisedGainForTaxByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    dealingCostsByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    dividendsByYear: dict[str, Decimal(0.0)] = field(default_factory=dict) #This includes all payments - dividends, bond income, interest
    dividendTxnsByYear: dict[str, set[Transaction]] = field(default_factory=dict)
    dividendYieldByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    incomeByYear: dict[str, Decimal(0.0)] = field(default_factory=dict) #Total income by tax year
    allIncomeByYearMonth: dict[str, dict[str, Decimal(0.0)]] = field(default_factory=dict) #All types of income (divi, interest, bond income) broken down by month
    incomeTxnsByYear: dict[str, set[Transaction]] = field(default_factory=dict)
    interestByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    interestTxnsByYear: dict[str, set[Transaction]] = field(default_factory=dict)
    incomeYieldByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    totalYieldByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    fundTotals: dict[FundType, FundOverview] = field(default_factory=dict)
    totalByInstitution: dict[str, Decimal] = field(default_factory=dict)
    transactions: list[Transaction] = field(default_factory=list)
    stocks: list[SecurityDetails] = field(default_factory=list)
    taxRates: dict = field(default_factory=dict)
    taxBandByYear: dict[str, str] = field(default_factory=dict)
    mergedAccounts: list = field(default_factory=list)
    historicValue: dict[datetime, (Decimal(0.0), Decimal(0.0))] = field(
        default_factory=dict
    )  # (market value, book cost)
    historicValueByType: dict[datetime, dict[str, (float, float)]] = field(
        default_factory=dict
    )  # (market value, book cost)

    def mergeInAccountSummary(self, summary):
        self.mergedAccounts.append(summary)
        if summary.dateOpened < self.dateOpened:
            self.dateOpened = summary.dateOpened
        if summary.portfolioValueDate < self.portfolioValueDate:
            self.portfolioValueDate = summary.portfolioValueDate
        self.totalDiviReInvested += summary.totalDiviReInvested
        self.totalMarketValue += summary.totalMarketValue
        self.cashBalance += summary.cashBalance
        self.totalInvestedInSecurities += summary.totalInvestedInSecurities
        self.totalPaperGainForTax += summary.totalPaperGainForTax
        self.transactions.extend(summary.transactions)
        # Sort all transactions by date
        self.transactions = sorted(self.transactions, key=lambda txn: txn.date)
        self.stocks.extend(summary.stocks)
        # Sort all stocks by highest yearly gain
        self.stocks = sorted(
            self.stocks, key=lambda stock: stock.avgGainPerYearPerc(), reverse=True
        )

        for yr in self.cashInByYear:
            self.cashInByYear[yr] += summary.cashInByYear.get(yr, Decimal(0.0))
        for yr in summary.cashInByYear:
            if yr not in self.cashInByYear:
                self.cashInByYear[yr] = summary.cashInByYear[yr]

        for yr in self.cashOutByYear:
            self.cashOutByYear[yr] += summary.cashOutByYear.get(yr, Decimal(0.0))
        for yr in summary.cashOutByYear:
            if yr not in self.cashOutByYear:
                self.cashOutByYear[yr] = summary.cashOutByYear[yr]

        for yr in self.feesByYear:
            self.feesByYear[yr] += summary.feesByYear.get(yr, Decimal(0.0))
        for yr in summary.feesByYear:
            if yr not in self.feesByYear:
                self.feesByYear[yr] = summary.feesByYear[yr]

        for yr in self.aggInvestedByYear:
            self.aggInvestedByYear[yr] += summary.aggInvestedByYear.get(
                yr, Decimal(0.0)
            )
        for yr in summary.aggInvestedByYear:
            if yr not in self.aggInvestedByYear:
                self.aggInvestedByYear[yr] = summary.aggInvestedByYear[yr]

        for yr in self.realisedGainForTaxByYear:
            self.realisedGainForTaxByYear[yr] += summary.realisedGainForTaxByYear.get(
                yr, Decimal(0.0)
            )
        for yr in summary.realisedGainForTaxByYear:
            if yr not in self.realisedGainForTaxByYear:
                self.realisedGainForTaxByYear[yr] = summary.realisedGainForTaxByYear[yr]

        for yr in self.dealingCostsByYear:
            self.dealingCostsByYear[yr] += summary.dealingCostsByYear.get(
                yr, Decimal(0.0)
            )
        for yr in summary.dealingCostsByYear:
            if yr not in self.dealingCostsByYear:
                self.dealingCostsByYear[yr] = summary.dealingCostsByYear[yr]

        for yr in self.dividendsByYear:
            self.dividendsByYear[yr] += summary.dividendsByYear.get(yr, Decimal(0.0))
        for yr in summary.dividendsByYear:
            if yr not in self.dividendsByYear:
                self.dividendsByYear[yr] = summary.dividendsByYear[yr]

        for yr, txns in self.dividendTxnsByYear.items():
            txns.update(summary.dividendTxnsByYear.get(yr, set()))
        for yr, txns in summary.dividendTxnsByYear.items():
            if yr not in self.dividendTxnsByYear:
                self.dividendTxnsByYear[yr] = set(txns)

        for yr in self.incomeByYear:
            self.incomeByYear[yr] += summary.incomeByYear.get(yr, Decimal(0.0))
        for yr in summary.incomeByYear:
            if yr not in self.incomeByYear:
                self.incomeByYear[yr] = summary.incomeByYear[yr]

        for yr in self.allIncomeByYearMonth:
            if yr not in summary.allIncomeByYearMonth:
                summary.allIncomeByYearMonth[yr] = dict()
            for mon in self.allIncomeByYearMonth[yr]:
                self.allIncomeByYearMonth[yr][mon] += summary.allIncomeByYearMonth[yr].get(mon, Decimal(0.0))
            for mon in summary.allIncomeByYearMonth[yr]:
                if mon not in self.allIncomeByYearMonth:
                    self.allIncomeByYearMonth[yr][mon] = summary.allIncomeByYearMonth[yr][mon]
        for yr in summary.allIncomeByYearMonth:
            if yr not in self.allIncomeByYearMonth:
                self.allIncomeByYearMonth[yr] = dict()
            for mon in summary.allIncomeByYearMonth[yr]:
                self.allIncomeByYearMonth[yr][mon] = summary.allIncomeByYearMonth[yr][mon]

        for yr in self.taxfreeCashOutByYear:
            self.taxfreeCashOutByYear[yr] += summary.taxfreeCashOutByYear.get(
                yr, Decimal(0.0)
            )
        for yr, cash in summary.taxfreeCashOutByYear.items():
            if yr not in self.taxfreeCashOutByYear:
                self.taxfreeCashOutByYear[yr] = cash

        for yr, income in self.incomeTxnsByYear.items():
            income.update(summary.incomeTxnsByYear.get(yr, set()))
            # self.incomeTxnsByYear[yr] = sorted(self.incomeTxnsByYear[yr], key= lambda txn: txn.date)
        for yr, inc in summary.incomeTxnsByYear.items():
            if yr not in self.incomeTxnsByYear:
                self.incomeTxnsByYear[yr] = set(inc)

        for yr in self.interestByYear:
            self.interestByYear[yr] += summary.interestByYear.get(yr, Decimal(0.0))
        for yr in summary.interestByYear:
            if yr not in self.interestByYear:
                self.interestByYear[yr] = summary.interestByYear[yr]

        for yr in self.interestTxnsByYear:
            self.interestTxnsByYear[yr].update(
                summary.interestTxnsByYear.get(yr, set())
            )
            # self.interestTxnsByYear[yr] = sorted(self.interestTxnsByYear[yr], key= lambda txn: txn.date)
        for yr in summary.interestTxnsByYear:
            if yr not in self.interestTxnsByYear:
                self.interestTxnsByYear[yr] = set(summary.interestTxnsByYear[yr])

        for yr in self.dividendYieldByYear:
            self.dividendYieldByYear[yr] += summary.dividendYieldByYear.get(
                yr, Decimal(0.0)
            )
        for yr in summary.dividendYieldByYear:
            if yr not in self.dividendYieldByYear:
                self.dividendYieldByYear[yr] = summary.dividendYieldByYear[yr]

        for yr in self.totalYieldByYear:
            self.totalYieldByYear[yr] += summary.totalYieldByYear.get(yr, Decimal(0.0))
        for yr in summary.totalYieldByYear:
            if yr not in self.totalYieldByYear:
                self.totalYieldByYear[yr] = summary.totalYieldByYear[yr]

        for yr in self.incomeYieldByYear:
            self.incomeYieldByYear[yr] += summary.incomeYieldByYear.get(
                yr, Decimal(0.0)
            )
        for yr in summary.incomeYieldByYear:
            if yr not in self.incomeYieldByYear:
                self.incomeYieldByYear[yr] = summary.incomeYieldByYear[yr]

        for inst in self.totalByInstitution:
            self.totalByInstitution[inst] += summary.totalByInstitution.get(
                inst, Decimal(0.0)
            )
        for inst in summary.totalByInstitution:
            if inst not in self.totalByInstitution:
                self.totalByInstitution[inst] = summary.totalByInstitution[inst]

        for ft, fund in summary.fundTotals.items():
            current = self.fundTotals.get(ft, None)
            if current:
                current.merge(fund)
            else:
                # Copy
                self.fundTotals[ft] = deepcopy(fund)

        for dt in self.historicValue:
            self.historicValue[dt] = [
                sum(tup)
                for tup in zip(
                    self.historicValue[dt],
                    summary.historicValue.get(dt, (Decimal(0.0), Decimal(0.0))),
                )
            ]
        for dt in summary.historicValue:
            if dt not in self.historicValue:
                self.historicValue[dt] = summary.historicValue[dt]

        for dt, hvdt in self.historicValueByType.items():
            summaryhvdt = summary.historicValueByType.get(dt, dict())
            for ft in hvdt:
                hvdt[ft] = [
                    sum(tup)
                    for tup in zip(
                        hvdt[ft], summaryhvdt.get(ft, (Decimal(0.0), Decimal(0.0)))
                    )
                ]
        for dt in summary.historicValueByType:
            if dt not in self.historicValueByType:
                self.historicValueByType[dt] = deepcopy(summary.historicValueByType[dt])
            else:
                summaryhvdt = summary.historicValueByType[dt]
                hvdt = self.historicValueByType[dt]
                for ft in summaryhvdt:
                    if ft not in hvdt:
                        hvdt[ft] = summaryhvdt[ft]

    # Total amount of cash currently invested in the account, i.e. the difference between deposits and withdrawls, ignoring interest, costs etc
    def totalCashInvested(self):
        return sum(self.cashInByYear.values()) - sum(self.cashOutByYear.values())

    # Total of all fees paid
    def totalFees(self):
        return (
            sum(self.feesByYear.values()) if len(self.feesByYear) > 0 else Decimal(0.0)
        )

    def totalDealingCosts(self):
        return (
            sum(self.dealingCostsByYear.values())
            if len(self.dealingCostsByYear) > 0
            else Decimal(0.0)
        )

    # Total market value of account, including cash in hand
    def totalValue(self):
        return self.totalMarketValue + self.totalOtherAccounts + self.cashBalance

    def totalPaperGainForTaxPerc(self):
        if self.totalInvestedInSecurities > 0:
            return (
                100.0
                * float(self.totalPaperGainForTax)
                / float(self.totalInvestedInSecurities)
            )
        else:
            return 0

    # Sum of all realised gains
    def totalRealisedGain(self):
        return (
            sum(self.realisedGainForTaxByYear.values())
            if len(self.realisedGainForTaxByYear) > 0
            else Decimal(0.0)
        )

    # Paper gain based on current market value less cash coming into the account
    def totalGainFromInvestments(self):
        return self.totalPaperGainForTax + self.totalRealisedGain()

    def totalGainFromInvPerc(self):
        if self.totalInvestedInSecurities > 0:
            return (
                100
                * float(self.totalGainFromInvestments())
                / float(self.totalInvestedInSecurities)
            )
        else:
            return 0

    # All gains realised or on paper, including dividends and interest payments
    def totalGain(self):
        return (
            self.totalRealisedGain()
            + self.totalPaperGainForTax 
            + self.totalDividends()
            + self.totalIncome()
        )

    def totalGainLessFees(self):
        return (
            self.totalGain() - self.totalFees()
        )  # Dealing costs are wrapped up in stock price received

    def totalGainPerc(self):
        if self.totalInvestedInSecurities > 0:
            return (
                100
                * float(self.totalGainLessFees())
                / float(self.totalInvestedInSecurities)
            )
        else:
            return 0

    def totalDividends(self):
        return (
            sum(self.dividendsByYear.values())
            if len(self.dividendsByYear) > 0
            else Decimal(0.0)
        )

    # All divi + interest payments
    def totalIncome(self):
        inc = (
            sum(self.incomeByYear.values())
            if len(self.incomeByYear) > 0
            else Decimal(0.0)
        )
        inc += (
            sum(self.interestByYear.values())
            if len(self.interestByYear) > 0
            else Decimal(0.0)
        )
        # cashOutTax = float(self.taxRates.get("withdrawllowertax", 0))
        # if cashOutTax != 0:
        #     # Cash out or withdrawl of funds is treated as income (e.g. a SIPP)
        #     inc += (
        #         sum(self.cashOutByYear.values())
        #         if len(self.cashOutByYear) > 0
        #         else Decimal(0.0)
        #     )
        return inc

    def totalIncomeByYear(self, year):
        inc = self.incomeByYear.get(year, Decimal(0))
        inc += self.interestByYear.get(year, Decimal(0))
        # cashOutTax = float(self.taxRates.get("withdrawllowertax", 0))
        # if cashOutTax != 0:
        #     # Cash out or withdrawl of funds is treated as income (e.g. a SIPP)
        #     inc += self.cashOutByYear.get(year, Decimal(0))
        return inc

    def totalInterest(self):
        return (
            sum(self.interestByYear.values())
            if len(self.interestByYear) > 0
            else Decimal(0.0)
        )

    def avgDividends(self):
        return (
            mean(self.dividendYieldByYear.values())
            if len(self.dividendYieldByYear) > 0
            else Decimal(0.0)
        )

    def avgIncomeYield(self):
        incYield = (
            mean(self.incomeYieldByYear.values())
            if len(self.incomeYieldByYear) > 0
            else 0
        )
        return incYield

    def avgTotalYield(self):
        yld = (
            mean(self.totalYieldByYear.values())
            if len(self.totalYieldByYear) > 0
            else 0
        )
        return yld

    def avgReturnPerYear(self):
        startYear = self.dateOpened
        # endYear = datetime.now(timezone.utc) + timedelta(days=365) # Make sure we have this tax year
        endYear = datetime.now(timezone.utc)
        timeHeld = endYear - startYear
        if timeHeld.days != 0:
            return float(self.totalGainLessFees()) / (timeHeld.days / 365)
        else:
            return 0

    def getRemainingCGTAllowance(self, cg):
        cgtAllowance = Decimal(self.taxRates["capitalgaintaxallowance"])
        if cg > cgtAllowance:
            rem = Decimal(0)
        else:
            rem = cgtAllowance - cg
        return rem

    def taxableCG(self, taxYear):
        if Decimal(self.taxRates["capitalgainlowertax"]) == 0:
            cg = Decimal(0)
        else:
            cg = (
                self.realisedGainForTaxByYear.get(taxYear, Decimal(0.0))
                if len(self.realisedGainForTaxByYear) > 0
                else Decimal(0.0)
            )
        return cg

    def calcCGT(self, taxBand, taxYear):
        rate = Decimal(self.taxRates["capitalgain" + taxBand + "tax"])
        if rate == 0:
            cgt = Decimal(0.0)
        else:
            cg = self.taxableCG(taxYear)
            cgtAllowance = Decimal(self.taxRates["capitalgaintaxallowance"])
            if cgtAllowance > cg:
                cgt = Decimal(0)
            else:
                cgt = (cg - cgtAllowance) * rate / 100
        return cgt

    def calcIncomeTax(self, taxBand, taxYear):
        income = self.incomeByYear.get(taxYear, Decimal(0.0))
        interest = self.interestByYear.get(taxYear, Decimal(0.0))
        if interest > 0:
            allowance = self.getInterestAllowance(taxBand)
            if allowance < interest:
                income += interest - allowance
        rate = Decimal(self.taxRates["income" + taxBand + "tax"])
        tax = income * rate / 100
        # For a pension (SIPP) cash out is treated as income
        cashOutTax = Decimal(self.taxRates["withdrawl" + taxBand + "tax"])
        if cashOutTax != 0:
            income = self.cashOutByYear.get(
                taxYear, Decimal(0.0)
            ) - self.taxfreeCashOutByYear.get(taxYear, Decimal(0.0))
            tax += cashOutTax * income / 100
        return tax

    def getInterestAllowance(self, taxBand):
        if not taxBand or taxBand == "lower":
            allowance = Decimal(self.taxRates["interestlowerallowance"])
        else:
            allowance = Decimal(self.taxRates["interestupperallowance"])
        return allowance

    def taxableDivi(self, taxYear):
        rate = Decimal(self.taxRates["dividendlowertax"])
        if rate == 0:
            divi = Decimal(0)
        else:
            divi = (
                self.dividendsByYear.get(taxYear, Decimal(0.0))
                if len(self.dividendsByYear) > 0
                else Decimal(0.0)
            )
        return divi

    def calcDividendTax(self, taxBand, taxYear):
        divi = self.taxableDivi(taxYear)
        rate = Decimal(self.taxRates["dividend" + taxBand + "tax"])
        if rate == 0:
            tax = Decimal(0.0)
        elif divi != 0:
            allowance = Decimal(self.taxRates["dividendtaxallowance"])
            taxable = divi - allowance if divi > allowance else Decimal(0.0)
            tax = taxable * rate / 100
        else:
            tax = Decimal(0)
        return tax

    def getRemainingDiviAllowance(self, divi):
        allowance = Decimal(self.taxRates["dividendtaxallowance"])
        return allowance - divi if allowance > divi else Decimal(0.0)

    def getTotalTax(self, taxBand, taxYear):
        return (
            self.calcCGT(taxBand, taxYear)
            + self.calcDividendTax(taxBand, taxYear)
            + self.calcIncomeTax(taxBand, taxYear)
        )

    def taxableIncome(self, taxYear):
        income = Decimal(0.0)
        if self.taxRates["withdrawllowertax"] != 0:
            # Add in any withdrawals liable to tax for the tax year
            income += (
                self.cashOutByYear.get(taxYear, Decimal(0.0))
                if len(self.cashOutByYear) > 0
                else Decimal(0.0)
            )
            # Remove any tax free cash
            income -= (
                self.taxfreeCashOutByYear.get(taxYear, Decimal(0.0))
                if len(self.taxfreeCashOutByYear) > 0
                else Decimal(0.0)
            )
        if self.taxRates["incomelowertax"] != 0:
            # Add in any bond income for the tax year
            income += (
                self.incomeByYear.get(taxYear, Decimal(0.0))
                if len(self.incomeByYear) > 0
                else Decimal(0.0)
            )
            # Add in any interest income for the tax year
            income += (
                self.interestByYear.get(taxYear, Decimal(0.0))
                if len(self.interestByYear) > 0
                else Decimal(0.0)
            )

        return income


def getTaxYear(inDate):
    d = date(year=2021, month=inDate.month, day=inDate.day)
    if d < TAX_YEAR_START:
        year = f"{inDate.year - 1}-{inDate.year}"
    else:
        year = f"{inDate.year}-{inDate.year+1}"
    return year

def getCalYear(taxYrStr: str, mon: int):
    yrs = taxYrStr.split('-')
    if mon in range(1,3):
        calYear = yrs[1]
    else:
        calYear = yrs[0]
    return calYear

def convertToSterling(currencyTxns, txn, amount):
    if currencyTxns:
        # Find the currency conversion transaction reference
        # Go forward in time to the next currency conversion event
        timeDiff = timedelta(weeks=1000)
        zeroDelta = timedelta(seconds=0)
        convTxn = None
        for ctxn in currencyTxns:
            if ctxn.credit != 0:
                txnDelta = ctxn.date - txn.date
                if txnDelta > zeroDelta and txnDelta < timeDiff:
                    convTxn = ctxn
        if not convTxn:
            # didnt fine one later - choose the nearest one
            for ctxn in currencyTxns:
                if ctxn.credit != 0:
                    txnDelta = abs(ctxn.date - txn.date)
                    if txnDelta < timeDiff:
                        convTxn = ctxn
        # Find the associated currency to sterling conversion rate
        if convTxn:
            convRate = convTxn.credit / convTxn.qty
            # Multiply amount by conversion rate
            ret = amount * convRate
        else:
            print(f"Failed to find a conversion transaction for currency for txn {txn}")
            ret = amount
    else:
        ret = amount

    return ret


def strToDec(p: str):
    retVal = -1
    try:
        retVal = int(p)
    except:
        try:
            retVal = Decimal(p)
        except:
            pass
    return retVal
    
    
def priceStrToDec(strValue: str):
    if not strValue or strValue.strip() == "" or strValue.strip().lower() == "n/a":
        val = Decimal(0.0)
        currency = STERLING
    else:
        if strValue.startswith("£"):
            valStr = strValue.replace("£", "")
            currency = STERLING
        elif strValue.endswith("p"):
            currency = STERLING
            valStr = strValue
        elif strValue.startswith("$"):
            valStr = strValue.replace("$", "")
            currency = USD
        elif strValue.startswith("€"):
            valStr = strValue.replace("€", "")
            currency = EUR
        else:
            valStr = strValue
            currency = STERLING
            print(f"Warning: Unrecognised currency, assuming sterling: {strValue}")

        valStr = valStr.replace(",", "")
        if currency == STERLING and "p" in valStr:
            valStr = valStr.replace("p", "")
            val = Decimal(valStr) / 100
        else:
            val = Decimal(valStr)
    return (currency, val)


def calcTaxBand(thresholds, income):
    incomeTaxAllowance = Decimal(thresholds["incometaxallowance"])
    incomeUpperThreshold = Decimal(thresholds["incomeupperthreshold"])
    incomeAdditionalThreshold = Decimal(thresholds["incomeadditionalthreshold"])

    if income > incomeTaxAllowance and income <= incomeUpperThreshold:
        taxBand = "lower"
    elif income > incomeUpperThreshold and income <= incomeAdditionalThreshold:
        taxBand = "upper"
    elif income > incomeAdditionalThreshold:
        taxBand = "additional"
    else:
        taxBand = None

    return taxBand
