import sys
import os
if (os.path.exists('../processStock.zip')):
    print ("Using zip")
    sys.path.insert(0, '../processStock.zip')
else:
    sys.path.insert(0, '../src')

from processStock import processStock
import configparser
import locale

local=False  #False = from HDFS, True = local filesystem
stockFileName = '../stocklist.txt'

config = configparser.ConfigParser()
config.read('../stockpicker.ini')
localeStr = config['stats']['locale']
locale.setlocale( locale.LC_ALL, localeStr) 

with open(stockFileName, 'r') as stockFile:
    for stock in stockFile:
        stock = stock.strip(' \n\r')
        processStock(config, stock, local)