# -*- coding: utf-8 -*-
"""
Created on Sat Nov  2 10:23:05 2019

@author: S243372
"""

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_squared_error
from statistics import mean

def calcRMSE(x, cfarray, fitIntercept=True):
    y = np.array(cfarray)
    model = LinearRegression(fitIntercept).fit(x,y)
    #Determine accuracy
    cfcheck = model.predict(x)
    #print( cfarray, cfcheck)
    #Determine root mean squared error as %
    #rmse = sum(((cfarray - cfcheck)/cfarray)**2/(4))**0.5
    rmse = mean_squared_error(cfarray, cfcheck)**0.5
    return (model, rmse)

def getBestFit(yr, cfarray):
    x = np.array(yr).reshape((-1,1))
    (model, rmse) = calcRMSE(x, cfarray)
#    print (f"n=1; Error: {rmse:.4f}")
    #Try with higher order polynomials
    p = 1
    #Polynomial regression causes overfitting and exponential errors - dont use
#    y = np.array(cfarray)
#    for d in range(2,5):
#        transformer = PolynomialFeatures(degree=d)
#        transformer = transformer.fit(x)
#        x_ = transformer.transform(x)
#        (modelp, rmsep) = calcRMSE(x_,y,False)
#        print (f"n={d}; Error: {rmsep:.4f}")
#        if (rmsep < rmse):
#            (model, p, rmse) = (modelp, d, rmsep)
    return (model, p, rmse)
    
# Params: historic free cash flow array, weighted average cost of capital, total number of years
def calculateDCF(fcf, wacc, numOfYears=10):
    #order historic cf into date order so can try and create a regression
    sortedfcf = sorted(fcf, key=lambda d: d[0])
    endYear = sortedfcf[len(sortedfcf)-1][0].date().year
    #n = 1
    wacc = wacc / 100
    cfarray = []
    yr = []
    for (d, cf) in sortedfcf:
         cfarray.append(cf)
         yr.append(d.date().year)
         #n += 1
    #Create regression model of the cash flow for the next up to 10 years
    (model, d, rmse) = getBestFit(yr, cfarray)
    slope = model.coef_
    vrange = max(cfarray) - min(cfarray)
    rmse = rmse / vrange
    #print (f"rmse = {rmse*100:0.2f}")
    if (rmse <= 0.2):
        #Predict later years using logistic regression
        yrp = []
        for i in range(endYear, endYear+numOfYears):
            yrp.append(i)
        xp = np.array(yrp).reshape((-1,1))
        if (d != 1):
            transformer = PolynomialFeatures(degree=d)
            transformer = transformer.fit(xp)
            xp = transformer.transform(xp)
        cfPred = model.predict(xp)
    else:
        #print(f"Linear regression prediction of cash flow error > 20% {rmse*100:0.2f}")
        #Use average fcf
        cfAvg = mean(cfarray)
        cfPred = []
        for p in range(endYear, endYear+numOfYears):
            cfPred.append(cfAvg)
        cfCheck = []
        for cf in cfarray: #Same size list
            cfCheck.append(cfAvg)
        #Calc error using mean
        rmse = mean_squared_error(cfarray, cfCheck)**0.5
        rmse = rmse / vrange
    n = 1
    dcf = 0
    #Calculate future CF (DCF) = Sum (cf/(1+wacc)^n)
    for cf in cfPred:
         dcf += cf / (1+wacc)**n
         n += 1
    
    return (dcf, rmse, slope)