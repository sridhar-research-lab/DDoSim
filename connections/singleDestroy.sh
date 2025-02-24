#!/bin/sh

# This file basically destroy the network bridge and TAP interface
# created by the singleSetup.sh script

if [ -z "$1" ]
  then
    echo "No name supplied"
    exit 1
fi

NAME=$1

sudo ip link set dev si-$NAME nomaster
sudo ip link set si-$NAME down
sudo ip link delete si-$NAME

# no need for the following
# sudo ip link set se-$NAME down &>/dev/null
# sudo ip link delete se-$NAME &>/dev/null

# sudo brctl delif br-$NAME tap-$NAME
# sudo ifconfig tap-$NAME down
# sudo tunctl -d tap-$NAME
sudo ip link set dev tap-$NAME nomaster
sudo ip link set tap-$NAME down
sudo ip link delete tap-$NAME

# sudo ifconfig br-$NAME down
# sudo brctl delbr br-$NAME
sudo ip link set dev br-$NAME down
sudo ip link del br-$NAME