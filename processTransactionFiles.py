import sys
import os
if (os.path.exists('processStock.zip')):
    sys.path.insert(0, 'processStock.zip')
else:
    sys.path.insert(0, './src')

from processStock import processStock
from showScores import scoresOnTheDoors
from saveRetreiveFiles import mergeAndSaveScores
from processTransactionFiles import processTxnFiles
import configparser
import locale

stockFileName = './stocklist.txt'

config = configparser.ConfigParser()
config.read('./stockpicker.ini')
localeStr = config['stats']['locale']
locale.setlocale( locale.LC_ALL, localeStr) 
configStore = config['store']

import argparse
parser = argparse.ArgumentParser(description='Re-calculate and display metrics and scores of given stock symbols')
parser.add_argument('-d', '--hdfs', action='store_const', const=False, default=True,
                   help='Set if using hdfs filesystem rather than local store (True)')
args = parser.parse_args()

scores = []
with open(stockFileName, 'r') as stockFile:
    for stock in stockFile:
        stock = stock.strip(' \n\r')
        scores.append(processStock(config, stock, args.hdfs))
        
mergeAndSaveScores(configStore, scores, args.hdfs)
scoresOnTheDoors(configStore, scores, 10, args.hdfs)
processTxnFiles(configStore)
