
from datetime import datetime
from decimal import Decimal
from requests_html import HTMLSession
from bs4 import BeautifulSoup

#header = {'user-agent': 'Mozilla/5.0 (X11; Linux armv7l) AppleWebKit/537.36 (KHTML, like Gecko) Raspbian Chromium/74.0.3729.157 Chrome/74.0.3729.157 Safari/537.36'}
#header = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'}

def getFundPrices(isin, priceData):
    nowTime = datetime.now()
    if (priceData):
        existingPrices = priceData['dailyPrices']
        lastAttemptDate = priceData.get('lastRetrievalDate', nowTime)
    else:
        existingPrices = None
        lastAttemptDate = nowTime
    if (existingPrices):
        priceDatesSorted = sorted(existingPrices)
        latestPriceDate = priceDatesSorted[len(priceDatesSorted)-1]
        earliestPriceDate = priceDatesSorted[0]
        startDate = datetime.fromtimestamp(earliestPriceDate)
        endDate = datetime.fromtimestamp(latestPriceDate)

    # latestPriceDate = priceData['endDate']
    baseUrl = "https://www.trustnet.com/fund/price-performance/o/ia-unit-trusts?tab=fundOverview&pageSize=25&searchText="
    #outputSize = "full"
    url = f"{baseUrl}{isin}"

    session = HTMLSession()

    resp = session.get(url)
    resp.html.render(timeout=30)

    soup = BeautifulSoup(resp.html.html, "lxml")
    retData = None #Only return data if new data added
    priceStrsTag = soup.find('td', class_='essential price')
    if priceStrsTag:
        priceStrs = priceStrsTag.stripped_strings
        for str in priceStrs:
            if str and str.strip() != '':
                str = str.strip()
                price = float(str.replace(',',''))
                newPrice = {int(datetime.now().timestamp()): (price, price)}
                if (existingPrices):
                    existingPrices.update(newPrice)
                else:
                    existingPrices = newPrice
                    startDate = datetime.now()
                endDate = datetime.now()
                lastAttemptDate = endDate
                retData = { "stock": isin, 
                            "startDate" : startDate,
                            "endDate": endDate,
                            "lastRetrievalDate" : lastAttemptDate,
                            "dailyPrices": existingPrices}
                break
            # else:
            #     print(f"No price in xml tag {priceStrs}")
    else:
        print(f"Could not find price for stock isin: {isin}")

    return retData

 
