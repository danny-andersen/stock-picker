from statistics import mean
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

CASH_IN = 'Cash in'
CASH_OUT = 'Cash out'
SELL = 'Sell'
BUY = 'Buy'
DIVIDEND = 'Dividend'
FEES = 'Fees'
REFUND ='Refund'
NO_STOCK = 'No stock'
STERLING = 'STERLING'
USD = 'USDUSDUSDUS1'
EUR = 'EUREUREUREU1'

SECONDS_IN_YEAR = 365.25*24*3600

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
    dateOpened: datetime = datetime.now(timezone.utc)
    totalCashInvested: Decimal = Decimal(0.0)
    totalDiviReInvested: Decimal = Decimal(0.0)
    totalDealingCosts: Decimal = Decimal(0.0)
    cashBalance: Decimal = Decimal(0.0)
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

    def totalInvested(self): 
        return sum(self.cashInByYear.values()) - sum(self.cashOutByYear.values())
    def totalFees(self):
        return sum(self.feesByYear.values()) if len(self.feesByYear) > 0 else Decimal(0.0)
    def totalValue(self):
        return self.totalMarketValue + self.cashBalance
    def totalPaperGainForTaxPerc(self):
        return 100.0 * float(self.totalPaperGainForTax / self.totalInvestedInSecurities)
    def totalRealisedGain(self):
        return sum(self.realisedGainForTaxByYear.values()) if len(self.realisedGainForTaxByYear) > 0 else Decimal(0.0)
    def totalGainFromInvestments(self):
        return self.totalMarketValue - self.totalInvested()
    def totalGainFromInvPerc(self):
        return 100 * float(self.totalGainFromInvestments() / self.totalInvestedInSecurities)
    def totalGainLessFees(self):
        return self.totalGain - self.totalFees()  #Dealing costs are wrapped up in stock price received
    def totalGainPerc(self):
        return 100 * float(self.totalGainLessFees() / self.totalInvestedInSecurities)
    def totalDividends(self):
        return sum(self.dividendsByYear.values()) if len(self.dividendsByYear) > 0 else Decimal(0.0)
    def avgDividends(self):
        return mean(self.dividendYieldByYear.values()) if len(self.dividendYieldByYear) > 0 else Decimal(0.0)
    def avgReturnPerYear(self):
        startYear = self.dateOpened
        # endYear = datetime.now(timezone.utc) + timedelta(days=365) # Make sure we have this tax year
        endYear = datetime.now(timezone.utc)
        timeHeld = endYear - startYear
        return float(self.totalGain) / (timeHeld.days / 365)


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