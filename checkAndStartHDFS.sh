ssh pi4desktop sudo -u hdfs -i hdfs dfsadmin -report |  grep '^Live\|^DFS Used%\|^Name'
if [ $? != 0 ]
then
	echo "HDFS not running - starting up cluster"
	ssh pi4node0 sudo mount /data/logs
	ssh pi4node1 sudo mount /data/logs
	ssh pi4node2 sudo mount /data/logs
	ssh pi4desktop sudo -u hdfs -i /home/hdfs/startCluster.sh
	sleep 30
	ssh pi4desktop sudo -u hdfs -i hdfs dfsadmin -report
fi

