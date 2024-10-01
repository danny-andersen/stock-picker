./checkAndStartHDFS.sh
source venv/bin/activate
echo "Processing Sans Stock Txns"
python processStockTransactions.py --owner sandra
