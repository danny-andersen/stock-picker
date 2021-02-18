import sys
sys.path.insert(0, './src')
from saveRetreiveFiles import getStockScores, getStockMetricsSaved
from scoreStock import calcScore
from printResults import printResults
from tabulate import tabulate


def scoresOnTheDoors(storeConfig, scores, numToShow, local):
    scores.sort(key=lambda score:score['scorePerc'], reverse=True)
    numScores = len(scores)
    cont=True
    tab = tabulate(scores[0:numToShow], headers='keys', showindex="always")
    while (cont):
        #Show numbered list of stock symbols ordered by scores
        print (f"Showing {numToShow} stocks out of {len(scores)}")
        print (tab)
        
        #Display prompt. Read input number
        stockIndex = input('Enter Stock Number or Stock ticker (q to quit) > ')
        if (stockIndex == 'q'):
            sys.exit(0)
        found = False
        try:
            index = int(stockIndex)
            if (index < numScores):
                found = True
                stock = scores[index]['stock']    
                if (index > numToShow): 
                    numToShow = index
                    tab = tabulate(scores[0:numToShow], headers='keys', showindex="always")
        except:
            index = 0
            for score in scores:
                if (score['stock'] == stockIndex):
                    print (f"{index} {score}")
                    stock = stockIndex
                    found = True
                    break
                index += 1
        if (not found):
            print("Please enter a valid number or stock symbol!")
        else:
            #Show detailed metrics for selected stock
            metrics = getStockMetricsSaved(storeConfig, stock, local)
            if (metrics):
                stockScore = calcScore(stock, metrics)
                printResults(stock, stockScore, metrics)
        #Display prompt
        ret = input('Press Enter to continue or q to quit...')
        if (ret == 'q'):
            sys.exit(0)
            
if __name__ == "__main__":
    import argparse
    import configparser
    import locale
    parser = argparse.ArgumentParser(description='Re-calculate and display metrics and scores of given stock symbols')
    parser.add_argument('-n', '--num', type=int, default=10,
                       help='top number of stock scores to show, defaults to 10')
    parser.add_argument('-l', '--local', action='store_const', const=True, default=False,
                       help='Set if using local filesystem rather than HDFS store (False)')
    args = parser.parse_args()
    
    #Read in ini file
    config = configparser.ConfigParser()
    config.read('./stockpicker.ini')
    localeStr = config['stats']['locale']
    locale.setlocale( locale.LC_ALL, localeStr) 
    storeConfig = config['store']
    
    #Read score file
    scores = getStockScores(storeConfig, args.local)
    if (not scores):
        print("Failed to retreive saved scores - please check filesystem or re-run scoring")
        sys.exit(1)
    scoresOnTheDoors(storeConfig, scores, args.num, args.local)    
