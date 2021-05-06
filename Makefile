# run: zip
# 	/data/spark/bin/spark-submit --master yarn --executor-memory 512M --py-files processStock.zip processStockListSpark.py 
	
zip:
	cd src && python -m compileall . && zip -r ../processStock.zip .
	cd -
	python -m compileall . && zip -r processStock.zip *.py *.ini *.txt