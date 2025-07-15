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

sudo ip link set dev tap-$NAME nomaster
sudo ip link set tap-$NAME down
sudo ip link delete tap-$NAME

sudo ip link set dev br-$NAME down
sudo ip link del br-$NAME

sudo modprobe -r br_netfilter