from statistics import mean
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum, IntEnum
from copy import deepcopy

CASH_IN = 'Cash in'
CASH_OUT = 'Cash out'
SELL = 'Sell'
BUY = 'Buy'
DIVIDEND = 'Dividend'
FEES = 'Fees'
REFUND ='Refund'
NO_STOCK = 'No stock'
INTEREST = 'Interest'
STERLING = 'STERLING'
USD = 'USDUSDUSDUS1'
EUR = 'EUREUREUREU1'

SECONDS_IN_YEAR = 365.25*24*3600

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
        return (self <= 4)
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
        retStr += f"Geographical Spread: Americas {self.americas}%, Americas Emerging {self.americasEmerging}%, UK {self.uk}%"
        retStr += f"Europe {self.europe}%, Europe Emerging {self.europeEmerging}%,"
        retStr += f"Asia {self.asia}%, Asia Emerging {self.asiaEmerging}%\n"
        retStr += f"3 year Stats: Alpha {self.alpha3Yr} Beta {self.beta3Yr} Sharpe {self.sharpe3Yr} Standard Dev {self.stdDev3Yr}\n"
        retStr += f"3 year Return: {self.return3Yr}% 5 year Return: {self.return5Yr}%\n"
        return retStr

    def isBondType(self):
        return self.fundType == FundType.LONG_GILT or \
                    self.fundType == FundType.BOND_ETF or \
                    self.fundType == FundType.CORP_BOND

    def isStockType(self):
        return self.fundType == FundType.FUND or \
                    self.fundType == FundType.SHARE or \
                    self.fundType == FundType.STOCK_ETF 

    def isCashType(self):
        return self.fundType == FundType.SHORT_GILT or \
                    self.fundType == FundType.CASH

    def isGoldType(self):
        return self.fundType == FundType.GOLD

    def merge(self, fund):
        currVal = float(self.totalValue)
        self.totalValue += fund.totalValue
        totValue = float(self.totalValue)
        val = float(fund.totalValue)
        self.totalInvested += fund.totalInvested

        if (totValue > 0):
            self.actualReturn = (self.actualReturn * currVal + fund.actualReturn * val) / totValue
            self.fees = (self.fees * currVal + fund.fees * val) / totValue
            self.return3Yr = (self.return3Yr * currVal + fund.return3Yr * val) / totValue
            self.return5Yr = (self.return5Yr * currVal + fund.return5Yr * val) / totValue

            if (self.maturity == 0 and fund.maturity != 0):
                self.maturity = fund.maturity
            elif (self.maturity != 0 and self.maturity != 0):
                self.maturity = (self.maturity * currVal + fund.maturity * val) / totValue

            ownTotRisk = self.alpha3Yr + self.beta3Yr + self.sharpe3Yr + self.stdDev3Yr
            newTotRisk = fund.alpha3Yr + fund.beta3Yr + fund.sharpe3Yr + fund.stdDev3Yr
            if (ownTotRisk == 0 and newTotRisk != 0):
                #Copy
                self.alpha3Yr = fund.alpha3Yr
                self.beta3Yr = fund.beta3Yr
                self.sharpe3Yr = fund.sharpe3Yr
                self.stdDev3Yr = fund.stdDev3Yr
            elif (ownTotRisk != 0 and newTotRisk != 0):
                #Merge
                self.alpha3Yr = (self.alpha3Yr * currVal + fund.alpha3Yr * val) / totValue
                self.beta3Yr = (self.beta3Yr * currVal + fund.beta3Yr * val) / totValue
                self.sharpe3Yr = (self.sharpe3Yr * currVal + fund.sharpe3Yr * val) / totValue
                self.stdDev3Yr = (self.stdDev3Yr * currVal + fund.stdDev3Yr * val) / totValue

            ownTotGeo = self.americas + self.americasEmerging + self.asia + self.asiaEmerging + self.europe + self.europeEmerging + self.uk
            newTotGeo = fund.americas + fund.americasEmerging + fund.asia + fund.asiaEmerging + fund.europe + fund.europeEmerging + fund.uk
            if (ownTotGeo == 0 and newTotGeo != 0):
                self.americas = fund.americas
                self.americasEmerging = fund.americasEmerging
                self.asia = fund.asia
                self.asiaEmerging = fund.asiaEmerging
                self.uk = fund.uk
                self.europe = fund.europe
                self.europeEmerging = fund.europeEmerging
            elif (ownTotGeo != 0 and newTotGeo != 0):
                self.americas = (self.americas * currVal + fund.americas * val) / totValue
                self.americasEmerging = (self.americasEmerging * currVal + fund.americasEmerging * val) / totValue
                self.asia = (self.asia * currVal + fund.asia * val) / totValue
                self.asiaEmerging = (self.asiaEmerging * currVal + fund.asiaEmerging * val) / totValue
                self.europe = (self.europe * currVal + fund.europe * val) / totValue
                self.europeEmerging = (self.europeEmerging * currVal + fund.europeEmerging * val) / totValue
                self.uk = (self.uk * currVal + fund.uk * val) / totValue


            ownTotDiv = self.cyclical + self.defensive + self.sensitive
            newTotDiv = fund.cyclical + fund.defensive + fund.sensitive
            if (ownTotDiv == 0 and newTotDiv != 0):
                self.cyclical = fund.cyclical
                self.defensive = fund.defensive
                self.sensitive = fund.sensitive
            elif (ownTotDiv != 0 and ownTotDiv != 0):
                self.cyclical = (self.cyclical * currVal + fund.cyclical * val) / totValue
                self.defensive = (self.defensive * currVal + fund.defensive * val) / totValue
                self.sensitive = (self.sensitive * currVal + fund.sensitive * val) / totValue


@dataclass_json
@dataclass
class Transaction:
    #An investment transaction of some sort
    date: datetime
    ref: str
    symbol: str
    sedol: str
    isin: str
    desc: str
    qty: float = 0.0
    price: Decimal = Decimal(0.0)
    priceCurrency: str = '£'
    debit: Decimal = Decimal(0.0)
    debitCurrency: str = '£'
    credit: Decimal = Decimal(0.0)
    creditCurrency: str = '£'
    type: str = 'Unknown'
    accountBalance: Decimal = Decimal(0.0)

@dataclass_json
@dataclass
class Security:
    #An investment security held in an Account
    date: datetime
    symbol: str
    desc: str
    qty: int = 0
    currentPrice: Decimal = Decimal(0.0)
    currency: str = '£'
    avgBuyPrice: Decimal = Decimal(0.0)
    bookCost: Decimal = Decimal(0.0)
    gain: Decimal = Decimal(0.0)

@dataclass
class CapitalGain:
    #Buy and sell history of stock
    date: datetime
    qty: int
    price: Decimal
    transaction: str = BUY
    def calcGain(self, sellDate, sellPrice, sellQty):
        timeHeld = sellDate - self.date
        gain = (sellPrice - self.price) * sellQty
        yld = float(100*gain/self.price)
        avgYieldPerYear = yld / (timeHeld.days / 365)
        return (gain, sellQty - self.qty, avgYieldPerYear)
    def calcTotalGain(self, sellDate, sellPrice):
        return self.calcGain(sellDate, sellPrice, self.qty)
    def calcTotalCurrentGain(self, sellPrice):
        return self.calcTotalGain(datetime.now(timezone.utc), sellPrice)

@dataclass
class SecurityDetails:
    sedol: str = None
    symbol: str = None
    isin: str = None
    name: str = None
    account: str = None
    qtyHeld: int = 0
    startDate: datetime = None
    endDate: datetime = None
    cashInvested: Decimal = Decimal(0.0)
    diviInvested: Decimal = Decimal(0.0)
    totalInvested: Decimal = Decimal(0.0)
    avgSharePrice: Decimal = Decimal(0.0)
    realisedCapitalGainByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    currentSharePrice: Decimal = Decimal(0.0)
    currentSharePriceDate: datetime = None
    costsByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    totalCosts: Decimal = Decimal(0.0)
    dividendsByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    dividendYieldByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    investmentHistory: list[CapitalGain] = field(default_factory=list)
    transactions: list[Transaction] = field(default_factory=list)
    historicHoldings: list = field(default_factory=list)
    fundOverview: FundOverview = None

    def yearsHeld(self):
        if (self.startDate):
            if (self.endDate):
                return float((self.endDate.timestamp() - self.startDate.timestamp())/SECONDS_IN_YEAR)
            else:
                return float((datetime.now(timezone.utc) - self.startDate).total_seconds())/SECONDS_IN_YEAR
        else:
            return 0.0
    def totalGain(self):
        return self.paperCGT() \
                + self.totalDividends() \
                + self.realisedCapitalGain()
    def avgGainPerYear(self):
        if self.yearsHeld() > 0:
            return float(self.totalGain())/self.yearsHeld()
        else:
            return 0.0
    def totalGainPerc(self):
        if self.cashInvested > 0:
            return 100.0 * float(self.totalGain()/self.cashInvested)
        else:
            return 0.0
    def avgGainPerYearPerc(self):
        if self.yearsHeld() > 0:
            return float(self.totalGainPerc())/self.yearsHeld()
        else:
            return 0.0
    def totalDividends(self):
        return sum(self.dividendsByYear.values()) if len(self.dividendsByYear) > 0 else Decimal(0.0)
    def averageYearlyDivi(self):
        return mean(self.dividendsByYear.values()) if len(self.dividendsByYear) > 0 else Decimal(0.0)
    def averageYearlyDiviYield(self):
        return mean(self.dividendYieldByYear.values()) if len(self.dividendYieldByYear) > 0 else Decimal(0.0)
    def realisedCapitalGain(self):
        return (sum(self.realisedCapitalGainByYear.values()) if len(self.realisedCapitalGainByYear) > 0 else Decimal(0.0))
    def marketValue(self):
        return self.currentSharePrice * self.qtyHeld
    def capitalGain(self):
        return self.realisedCapitalGain() + self.paperCGT()
    def paperCGT(self):
        if (self.currentSharePrice):
            return self.marketValue() - (self.avgSharePrice * self.qtyHeld)
        else:
            return Decimal(0.0)
    def paperCGTPerc(self):
        if self.totalInvested:
            return 100.0 * float(self.paperCGT() / self.totalInvested)
        else:
            return Decimal(0.0)

@dataclass
class AccountSummary:
    name: str
    portfolioPerc: dict
    dateOpened: datetime = datetime.now(timezone.utc)
    totalCashInvested: Decimal = Decimal(0.0)
    totalDiviReInvested: Decimal = Decimal(0.0)
    totalDealingCosts: Decimal = Decimal(0.0)
    cashBalance: Decimal = Decimal(0.0)
    totalOtherAccounts: Decimal = Decimal(0.0)
    totalMarketValue: Decimal = Decimal(0.0)
    totalInvestedInSecurities: Decimal = Decimal(0.0)
    totalPaperGainForTax: Decimal = Decimal(0.0)
    totalGain: Decimal = Decimal(0.0)

    cashInByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    cashOutByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    feesByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    aggInvestedByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    realisedGainForTaxByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    dealingCostsByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    dividendsByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    dividendYieldByYear: dict[str, Decimal(0.0)] = field(default_factory=dict)
    fundTotals: dict[FundType, FundOverview] = field(default_factory=dict)
    totalByInstitution: dict[str, Decimal] = field(default_factory=dict)
    transactions: list[Transaction] = field(default_factory=list)

    def mergeInAccountSummary(self, summary):
        if (summary.dateOpened < self.dateOpened):
            self.dateOpened = summary.dateOpened
        self.totalCashInvested += summary.totalCashInvested
        self.totalDiviReInvested += summary.totalDiviReInvested
        self.totalDealingCosts += summary.totalDealingCosts
        self.totalMarketValue += summary.totalMarketValue
        self.cashBalance += summary.cashBalance
        self.totalInvestedInSecurities += summary.totalInvestedInSecurities
        self.totalPaperGainForTax += summary.totalPaperGainForTax
        self.totalGain += summary.totalGain
        self.transactions.extend(summary.transactions)
        #Sort all transactions by date
        self.transactions = sorted(self.transactions, key= lambda txn: txn.date)

        for yr in self.cashInByYear.keys():
            self.cashInByYear[yr] += summary.cashInByYear.get(yr, Decimal(0.0))
        for yr in summary.cashInByYear.keys():
            if (yr not in self.cashInByYear):
                self.cashInByYear[yr] = summary.cashInByYear[yr]

        for yr in self.cashOutByYear.keys():
            self.cashOutByYear[yr] += summary.cashOutByYear.get(yr, Decimal(0.0))
        for yr in summary.cashOutByYear.keys():
            if (yr not in self.cashOutByYear):
                self.cashOutByYear[yr] = summary.cashOutByYear[yr]

        for yr in self.feesByYear.keys():
            self.feesByYear[yr] += summary.feesByYear.get(yr, Decimal(0.0))
        for yr in summary.feesByYear.keys():
            if (yr not in self.feesByYear):
                self.feesByYear[yr] = summary.feesByYear[yr]

        for yr in self.aggInvestedByYear.keys():
            self.aggInvestedByYear[yr] += summary.aggInvestedByYear.get(yr, Decimal(0.0))
        for yr in summary.aggInvestedByYear.keys():
            if (yr not in self.aggInvestedByYear):
                self.aggInvestedByYear[yr] = summary.aggInvestedByYear[yr]

        for yr in self.realisedGainForTaxByYear.keys():
            self.realisedGainForTaxByYear[yr] += summary.realisedGainForTaxByYear.get(yr, Decimal(0.0))
        for yr in summary.realisedGainForTaxByYear.keys():
            if (yr not in self.realisedGainForTaxByYear):
                self.realisedGainForTaxByYear[yr] = summary.realisedGainForTaxByYear[yr]

        for yr in self.dealingCostsByYear.keys():
            self.dealingCostsByYear[yr] += summary.dealingCostsByYear.get(yr, Decimal(0.0))
        for yr in summary.dealingCostsByYear.keys():
            if (yr not in self.dealingCostsByYear):
                self.dealingCostsByYear[yr] = summary.dealingCostsByYear[yr]

        for yr in self.dividendsByYear.keys():
            self.dividendsByYear[yr] += summary.dividendsByYear.get(yr, Decimal(0.0))
        for yr in summary.dividendsByYear.keys():
            if (yr not in self.dividendsByYear):
                self.dividendsByYear[yr] = summary.dividendsByYear[yr]

        for yr in self.dividendYieldByYear.keys():
            self.dividendYieldByYear[yr] += summary.dividendYieldByYear.get(yr, Decimal(0.0))
        for yr in summary.dividendYieldByYear.keys():
            if (yr not in self.dividendYieldByYear):
                self.dividendYieldByYear[yr] = summary.dividendYieldByYear[yr]

        for inst in self.totalByInstitution.keys():
            self.totalByInstitution[inst] += summary.totalByInstitution.get(inst, Decimal(0.0))
        for inst in summary.totalByInstitution.keys():
            if (inst not in self.totalByInstitution):
                self.totalByInstitution[inst] = summary.totalByInstitution[inst]

        for ft, fund in summary.fundTotals.items():
            current = self.fundTotals.get(ft, None)
            if current:
                current.merge(fund)
            else:
                #Copy
                self.fundTotals[ft] = deepcopy(fund)


    def totalInvested(self): 
        return sum(self.cashInByYear.values()) - sum(self.cashOutByYear.values())
    def totalFees(self):
        return sum(self.feesByYear.values()) if len(self.feesByYear) > 0 else Decimal(0.0)
    def totalValue(self):
        return self.totalMarketValue + self.totalOtherAccounts
    def totalPaperGainForTaxPerc(self):
        if self.totalInvestedInSecurities > 0:
            return 100.0 * float(self.totalPaperGainForTax) / float(self.totalInvestedInSecurities)
        else:
            return 0
    def totalRealisedGain(self):
        return sum(self.realisedGainForTaxByYear.values()) if len(self.realisedGainForTaxByYear) > 0 else Decimal(0.0)
    def totalGainFromInvestments(self):
        return self.totalMarketValue - self.totalInvested()
    def totalGainFromInvPerc(self):
        if self.totalInvestedInSecurities > 0:
            return 100 * float(self.totalGainFromInvestments()) / float(self.totalInvestedInSecurities)
        else:
            return 0
    def totalGainLessFees(self):
        return self.totalGain - self.totalFees()  #Dealing costs are wrapped up in stock price received
    def totalGainPerc(self):
        if self.totalInvestedInSecurities > 0:
            return 100 * float(self.totalGainLessFees()) / float(self.totalInvestedInSecurities)
        else:
            return 0
    def totalDividends(self):
        return sum(self.dividendsByYear.values()) if len(self.dividendsByYear) > 0 else Decimal(0.0)
    def avgDividends(self):
        return mean(self.dividendYieldByYear.values()) if len(self.dividendYieldByYear) > 0 else Decimal(0.0)
    def avgReturnPerYear(self):
        startYear = self.dateOpened
        # endYear = datetime.now(timezone.utc) + timedelta(days=365) # Make sure we have this tax year
        endYear = datetime.now(timezone.utc)
        timeHeld = endYear - startYear
        if timeHeld.days != 0:
            return float(self.totalGain) / (timeHeld.days / 365)
        else:
            return 0

def convertToSterling(currencyTxns, txn, amount):
    if (currencyTxns):
        #Find the currency conversion transaction reference
        #Go forward in time to the next currency conversion event
        timeDiff = timedelta(weeks=1000)
        zeroDelta = timedelta(seconds = 0)
        for ctxn in currencyTxns:
            if ctxn.credit != 0:
                txnDelta = ctxn.date - txn.date    
                if (txnDelta > zeroDelta and txnDelta < timeDiff):
                    convTxn = ctxn
        if not ctxn:
            #didnt fine one later - choose the nearest one 
            for ctxn in currencyTxns:
                if ctxn.credit != 0:
                    txnDelta = abs(ctxn.date - txn.date)    
                    if (txnDelta < timeDiff):
                        convTxn = ctxn
        #Find the associated currency to sterling conversion rate
        if ctxn:
            convRate = ctxn.credit / ctxn.qty
            #Multiply amount by conversion rate
            ret = amount * convRate
        else:
            print(f"Failed to find a conversion transaction for currency for txn {txn}")
            ret = amount
    else:
        ret = amount

    return ret

def priceStrToDec(strValue):
    if (not strValue or strValue.strip == ''):
        val = Decimal(0.0)
        currency = STERLING
    else:
        if strValue.startswith ('£'):
            valStr = strValue.replace('£', '')
            currency = STERLING
        elif strValue.endswith('p'):
            currency = STERLING
            valStr = strValue
        elif strValue.startswith ('$'):
            valStr = strValue.replace('$', '')
            currency = USD
        elif strValue.startswith ('€'):
            valStr = strValue.replace('€', '')
            currency = EUR
        else:
            valStr = strValue
            currency = STERLING
            print(f"Warning: Unrecognised currency, assuming sterling {strValue}")

        valStr = valStr.replace(',', '')
        if (currency == STERLING and 'p' in valStr):
            valStr = valStr.replace('p', '')
            val = Decimal(valStr) / 100
        else:
            val = Decimal(valStr)
    return (currency, val)