from dataclasses import dataclass
from dataclasses_json import dataclass_json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

CASH_IN = 'Cash in'
CASH_OUT = 'Cash out'
SELL = 'Sell'
BUY = 'Buy'
DIVIDEND = 'Dividend'
FEES = 'Fees'
REFUND ='Refund'
NONE = 'No stock'
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