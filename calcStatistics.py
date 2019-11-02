# -*- coding: utf-8 -*-
"""
Created on Sat Nov  2 10:23:05 2019

@author: S243372
"""
import locale
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from statistics import mean

locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' ) 

def calcRMSE(x, cfarray, fitIntercept=True):
    y = np.array(cfarray)
    model = LinearRegression(fitIntercept).fit(x,y)
    #Determine accuracy
    cfcheck = model.predict(x)
    print( cfarray, cfcheck)
    #Determine root mean squared error as %
    rmse = sum(((cfarray - cfcheck)/cfarray)**2/(4))**0.5
    return (model, rmse)

def getBestFit(yr, cfarray):
    y = np.array(cfarray)
    x = np.array(yr).reshape((-1,1))
    (model, rmse) = calcRMSE(x, cfarray)
    print (f"n=1; Error: {rmse:.4f}")
    #Try with higher order polynomials
    p = 1
    for d in range(2,5):
        transformer = PolynomialFeatures(degree=d)
        transformer = transformer.fit(x)
        x_ = transformer.transform(x)
        (modelp, rmsep) = calcRMSE(x_,y,False)
        print (f"n={d}; Error: {rmsep:.4f}")
        if (rmsep < rmse):
            (model, p, rmse) = (modelp, d, rmsep)
    return (model, p, rmse)
    
# Params: historic free cash flow array, weighted average cost of capital, total number of years
def calculateDCF(fcf, wacc, numOfYears=10):
    sortedfcf = sorted(fcf, key=lambda d: d[0])
    n = sortedfcf[0][0].date().year    
    #n = 1
    wacc = wacc / 100
    cfarray = []
    yr = []
    for (d, cf) in sortedfcf:
         cf = locale.atoi(cf) 
         cfarray.append(cf)
         yr.append(n)
         n += 1
    #Create regression model of the cash flow for the next up to 10 years
    (model, d, rmse) = getBestFit(yr, cfarray)
    if (rmse <= 0.2):
        #Predict later years using logistic regression
        yrp = []
        for i in range(n, n+numOfYears):
            yrp.append(i)
        xp = np.array(yrp).reshape((-1,1))
        if (d != 1):
            transformer = PolynomialFeatures(degree=d)
            transformer = transformer.fit(xp)
            xp = transformer.transform(xp)
        cfPred = model.predict(xp)
    else:
        print(f"Linear regression prediction of cash flow error > 20% {rmse*100:0.2f}")
        #Use average fcf
        cfAvg = mean(cfarray)
        cfPred = []
        for p in range(n, n+numOfYears):
            cfPred.append(cfAvg)
    nl = n
    dcf = 0
    for cf in cfPred:
         dcf += cf / (1+wacc)**nl
         nl += 1
    
    return dcf