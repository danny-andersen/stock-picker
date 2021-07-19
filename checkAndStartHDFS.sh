sudo -u hdfs -i hdfs dfsadmin -report
if [ $? != 0 ]
then
	#HDFS not running
	sudo -u hdfs -i /home/hdfs/startCluster.sh
	sleep 30
	sudo -u hdfs -i hdfs dfsadmin -report
fi

