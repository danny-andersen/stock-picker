import yfinance as yf
import pprint

pp = pprint.PrettyPrinter(indent=4)
stock = yf.Ticker("TSCO.L")

# get stock info
pp.pprint(stock.info.keys())
pp.pprint(stock.info)

# get historical market data
hist = stock.history(period="max")

# show actions (dividends, splits)
stock.actions

# show dividends
stock.dividends

# show splits
stock.splits

# show financials
stock.financials
stock.quarterly_financials

# show major holders
stock.major_holders

# show institutional holders
stock.institutional_holders

# show balance heet
stock.balance_sheet
stock.quarterly_balance_sheet

# show cashflow
stock.cashflow
stock.quarterly_cashflow

# show earnings
stock.earnings
stock.quarterly_earnings

# show sustainability
stock.sustainability

# show analysts recommendations
stock.recommendations

# show next event (earnings, etc)
stock.calendar

# show ISIN code - *experimental*
# ISIN = International Securities Identification Number
stock.isin

# show options expirations
#stock.options

# get option chain for specific expiration
#opt = stock.option_chain('YYYY-MM-DD')
# data available via: opt.calls, opt.puts
