from datetime import datetime
import locale

from yahoofinance import getStockInfoYahoo
from adfn import getStockInfoAdfn

from checkStockInfo import checkStockInfo, isNewStockInfoBetter, countInfoNones
from saveRetreiveFiles import getStockInfoSaved, saveStockInfo

def retrieveStockInfoSpark(bcConfig, stock):
    return retrieveStockInfo(bcConfig.value, stock)

def retrieveStockInfo(config, stock):
    version = config['stats'].getfloat('version')
    statsMaxAgeDays = config['stats'].getint('statsMaxAgeDays')
    maxNonesInInfo = config['stats'].getint('maxNonesInInfo')
    storeConfig = config['store']
    localeStr = config['stats']['locale']

    locale.setlocale(locale.LC_ALL, localeStr)

    # Check to see if stock info needs to be updated
    # Read info from file
    info = getStockInfoSaved(storeConfig, stock)
    currentInfo = info
    newInfoReqd = False
    if (info):
        infoAge = datetime.now() - info['metadata']['storedDate']
        if (infoAge.days > statsMaxAgeDays or info['metadata']['version'] < version):
            newInfoReqd = True
            print(
                f"{stock}: Stored info v{info['metadata']['version']} needs to be updated to v{version}")
            info = None
    else:
        print(f"{stock}: No info stored")
    # Count if info has any nulls / nones,
    numNones = countInfoNones(info)
    # if it has more than a configured threshold then it will be replaced if what we get is any better
    if (numNones > maxNonesInInfo):
        print(f"{stock} Stored version has {numNones} nulls, which is more than the threshold ({maxNonesInInfo})")
        info = None
    if (info):
        # Check info is valid
        if (not checkStockInfo(info)):
            print(f"{stock}: Stored info invalid - retrying")
            info = None
    if (not info):
        print(f"{stock}: Retreiving latest stock info")
        info = getStockInfo(config, version, stock)
        goodNewInfo = checkStockInfo(info)
        betterInfo = isNewStockInfoBetter(currentInfo, info)
        if ((goodNewInfo and newInfoReqd) or betterInfo):
            #Save if we needed new info and its good or the old stuff could be improved and is better or same (but more recent)
            saveStockInfo(storeConfig, stock, info)
        else:
            print(f"{stock}: Retreived info not any better: good new Info: {goodNewInfo}, is better info: {betterInfo}")
            info = None
    return info

    
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

        