import sys
import os
if (os.path.exists('processStock.zip')):
    sys.path.insert(0, 'processStock.zip')
else:
    sys.path.insert(0, './src')

from processTransactionFiles import processTransactions
import configparser
import locale
import argparse


parser = argparse.ArgumentParser(description='Process accounts and transactions to work out current holding and return')
# parser.add_argument('-d', '--hdfs', action='store_const', const=False, default=True,
#                    help='Set if using hdfs filesystem rather than local store (True)')
parser.add_argument('--owner', default='danny',
                    help='name of the owner of the accounts')
args = vars(parser.parse_args())
accountOwner = args['owner']

config = configparser.ConfigParser() 
config.read('./stockpicker.ini')
localeStr = config['stats']['locale']
locale.setlocale( locale.LC_ALL, localeStr) 
config.set('owner','accountowner', accountOwner)

processTransactions(config)
