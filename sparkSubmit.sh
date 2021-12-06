cd src && python -m compileall . && zip -r ../processStock.zip .
cd -
#cd libs/ && zip -r ../processStock.zip .
#cd -
python -m compileall . && zip -r processStock.zip *.py *.ini *.txt
/data/spark/bin/spark-submit \
	--master yarn  \
	--executor-memory 512M  \
	--num-executors 8  \
	--properties-file spark-props.conf \
	--py-files processStock.zip $1
