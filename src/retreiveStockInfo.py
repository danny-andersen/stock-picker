from yahoofinance import getStockInfoYahoo
from adfn import getStockInfoAdfn
from datetime import datetime

    
def getStockInfo(config, version, stock):
    api = config['stats']['api']
    if (api == "Yahoo"):
        info = getStockInfoYahoo(stock)
    elif (api == "ADFN"):
        info = getStockInfoAdfn(stock)
    else:
        info = dict()
        print(f"Invalid API {api}")
        
    meta = { 'version': version,
            'storedDate': datetime.now(),
            }
    info['metadata'] = meta
    return info

        