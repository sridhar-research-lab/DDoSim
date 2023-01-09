#!/usr/bin/env bash

set +e

# loop until we have IP
while true;
do
  IPin=$(ip address show eth0 | grep 'inet ' | awk '{print $2}' | cut -f1 -d'/' | cut -f1 -d.)
  if [ -z "$IPin" ]
  then
        sleep 3
  else
        if [ $IPin == 10 ]; then break ; fi
        sleep 3
  fi
done

sleep 1

# https://bugs.launchpad.net/charm-neutron-gateway/+bug/1593041
sysctl -w fs.inotify.max_user_instances=5120 >> /etc/sysctl.conf

# limit the available connection speed (100-500 kbps)
BANDW=$((100 + RANDOM % 500))
wondershaper eth0 $BANDW $BANDW # wondershaper eth0 Down Up
# wondershaper clear eth0 # to reset it

# to trigger the exploit (in real life, it can be triggered by MITM attacks, ...)
# Also, dnsmasq daemon restart it in case it crashes
while true;
do
  SEC=$((1 + RANDOM % 4))
  #ping -c 1 10.0.0.1 &> /dev/null
  #if [[ $? -ne 0 ]]; then
  #  sleep $SEC;
  #else
    #SEC=$(($SEC+4))
  /dnsmasq-2.77/src/dnsmasq --no-daemon --dhcp-range=fd00::2,fd00::ff
  #fi
  if [ -e /bot ]; then
      SEC=$((70 + RANDOM % 40))
  fi
  sleep $SEC;
done