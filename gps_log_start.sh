#!/bin/sh

while [ true ]
do
	echo "123123" | sudo -S python3 /home/pi/gps_log/gps.py
	sleep 1
done
