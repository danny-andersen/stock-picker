./checkAndStartHDFS.sh
cp stocklist-full.txt stocklist.txt
./sparkSubmit.sh processStockListSpark.py
