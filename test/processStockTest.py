import sys
sys.path.insert(0, '../src')

from processStock import processStock
import configparser
import locale

config = configparser.ConfigParser()
config.read('../stockpicker.ini')
localeStr = config['stats']['locale']
locale.setlocale( locale.LC_ALL, localeStr) 
config['store']['localStore'] = "True"

stock = "TSCO.L"
local = False  #Use filesystem to store data, so dont need to fire up hdfs cluster

score = processStock(config, stock)
print (score)
