import sys
import os
if (os.path.exists('processStock.zip')):
    sys.path.insert(0, 'processStock.zip')
else:
    sys.path.insert(0, './src')

from processTransactionFiles import processTxnFiles
import configparser
import locale

config = configparser.ConfigParser()
config.read('./stockpicker.ini')
localeStr = config['stats']['locale']
locale.setlocale( locale.LC_ALL, localeStr) 

import argparse
parser = argparse.ArgumentParser(description='Re-calculate and display metrics and scores of given stock symbols')
parser.add_argument('-d', '--hdfs', action='store_const', const=False, default=True,
                   help='Set if using hdfs filesystem rather than local store (True)')
args = parser.parse_args()

processTxnFiles(config)
