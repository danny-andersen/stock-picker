./checkAndStartHDFS.sh
echo "Processing Stock Txns"
source venv/bin/activate
python processStockTransactions.py
