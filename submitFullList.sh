./checkAndStartHDFS.sh
cp stocklist-full.txt stocklist.sh
./sparkSubmit.sh processStockListSpark.py
