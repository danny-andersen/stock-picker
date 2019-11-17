# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 18:10:11 2019

@author: S243372
"""

from alphaAdvantage import getLatestDailyPrices

if __name__ == "__main__":
    stock="TSCO.L"
    keyFile = "alphaAdvantage.apikey"
    f = open(keyFile)
    apiKey = f.readline().strip('\n');
    stats = getLatestDailyPrices(apiKey, stock)
    print (stats)
