#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 23 08:30:01 2019

@author: danny
"""

import sys
sys.path.insert(0, './src')
from saveRetreiveFiles import getStockScores, getStockMetricsSaved
from scoreStock import calcScore
from printResults import printResults
import configparser
import locale
from tabulate import tabulate



def scoresOnTheDoors(storeConfig, scores, local):
    scores.sort(key=lambda score:score['scorePerc'], reverse=True)
    cont=True
    tab = tabulate(scores, headers='keys', showindex="always")
    while (cont):
        #Show numbered list of stock symbols ordered by scores
        print (tab)
        
        #Display prompt. Read input number
        stockIndex = input('Enter Stock Number (q to quit) > ')
        if (stockIndex == 'q'):
            exit()
        try:
            stock = scores[int(stockIndex)]['stock']    
            #Show detailed metrics for selected stock
            metrics = getStockMetricsSaved(storeConfig, stock, local)
            if (metrics):
                stockScore = calcScore(stock, metrics)
                printResults(stock, stockScore, metrics)
        except (ValueError, IndexError):
            print("Please enter a valid number!")
        #Display prompt
        input('Press Enter to continue...')

if __name__ == "__main__":
    #Read in ini file
    config = configparser.ConfigParser()
    config.read('./stockpicker.ini')
    localeStr = config['stats']['locale']
    locale.setlocale( locale.LC_ALL, localeStr) 
    storeConfig = config['store']
    
    local = False
    
    #Read score file
    scores = getStockScores(storeConfig, local)
    if (not scores):
        print("Failed to retreive saved scores - please check filesystem or re-run scoring")
        exit()
    scoresOnTheDoors(storeConfig, scores, local)    