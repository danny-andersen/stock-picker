./checkAndStartHDFS.sh
cp heldstocklist.txt stocklist.txt
./sparkSubmit.sh processStockListSpark.py
