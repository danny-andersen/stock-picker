cd src && python -m compileall . && zip -r ../processStock.zip .
cd -
/data/spark/bin/spark-submit \
	--master yarn  \
	--executor-memory 512M  \
	--num-executors 8  \
	--properties-file spark-props.conf \
	--py-files processStock.zip processStockListSpark.py 
