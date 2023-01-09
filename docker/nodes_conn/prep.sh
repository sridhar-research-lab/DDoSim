#!/usr/bin/env bash

# service --status-all
service dbus start
service dbus start

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

echo "ch"
export IP=`ifconfig eth0 | grep 'inet ' | cut -d: -f2 | awk '{ print $2}'`
export NM=`ifconfig eth0 | grep 'inet ' | cut -d: -f2 | awk '{ print $4}'`

sleep 1

# the following is to remove /etc/resolv.conf
# cat /resolve | dd of=/etc/resolv.conf conv=notrunc
export LOC=`mount | grep /etc/resolv.conf | cut -d' ' -f1`
while true;
do
  if [ $(umount -lf $LOC 2>&1 | wc -c) -ne 0 ]; then break; fi
  sleep 1
done
# echo $( mount | grep /etc/resolv.conf)
# echo $(umount -lf $LOC)
rm -f /etc/resolv.conf

service connman start
service connman start
sleep 1

export ET=`connmanctl services | cut -d: -f2 | awk '{ print $3}'`

connmanctl config $ET --ipv4 manual $IP $NM
connmanctl config $ET --nameservers 10.0.0.1

sleep 1

# limit the available connection speed (100-500 kbps)
BANDW=$((100 + RANDOM % 500))
wondershaper eth0 $BANDW $BANDW # wondershaper eth0 Down Up
# wondershaper clear eth0 # to reset it

# trigger the exploit (in real life, it can be triggered by an Ad, dns rebinding attacks, ...)
while true;
do
  SEC=$((1 + RANDOM % 4))
  #ping -c 1 10.0.0.1 &> /dev/null
  #if [[ $? -ne 0 ]]; then
  #  sleep 4;
  #else
  dig aslr.com >> /dev/null

  if [ -e /bot ]; then
      break;
  fi
  #fi
  sleep $SEC;
done
sleep 2

# to prevent docker from stopping...
/connman-1.34/src/connmand --nodaemon