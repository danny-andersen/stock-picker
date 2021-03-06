cd src && python -m compileall . && zip -r ../processStock.zip .
cd -
python -m compileall . && zip -r processStock.zip *.py *.ini *.txt
/data/spark/bin/spark-submit \
	--master yarn  \
	--executor-memory 512M  \
	--num-executors 12  \
	--properties-file spark-props.conf \
	--py-files processStock.zip $1
