ssh pi4desktop sudo -u hdfs -i hdfs dfsadmin -report
if [ $? == 0 ]
then
	echo "HDFS running - stopping cluster"
	ssh pi4desktop sudo -u hdfs -i /home/hdfs/stopCluster.sh
	ssh pi4desktop ./backup.sh
	sleep 30
fi
ssh pi4desktop sudo -u hdfs -i hdfs dfsadmin -report
if [ $? == 0 ]
then
	echo "******Could not stop HDFS cluster"
else
	hosts="pi4node0 pi4node1 pi4node2 pi4desktop"
	for h in ${hosts}
	do
		echo "ssh ${h} sudo shutdown -h now"
		ssh ${h} sudo shutdown -h now
	done
	echo "Waiting for shutdown to complete before powering off nodes"
        sleep 15
	echo "Powering nodes off"
	scp cluster_off.txt thermostat-host:control_station/relay_command.txt

fi
