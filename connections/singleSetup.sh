#!/bin/sh

# This file creates a bridge with the tool brctl (ethernet bridge administration)
# and a TAP interface with the tool tunctl (create and manage persistent TUN/TAP interfaces)
# then the tap interface is configured in promisc mode, added to the bridge
# and started.

# The whole purpose of this script is to create the end of the NS3 node.
# So the NS3 nodes will try to connect to the tap-$NAME device,
# since this is connected to the bridge, and a docker container will be connected
# to the same bridge via other mechanism ... that will make the docker container
# to be able to communicate via the NS3 simulation.

if [ -z "$1" ]
  then
    echo "No name supplied"
    exit 1
fi

NAME=$1


# sudo tunctl -t tap-$NAME
# sudo ifconfig tap-$NAME 0.0.0.0 promisc up

sudo ip tuntap add mode tap tap-$NAME
sudo ip link set dev tap-$NAME up
sudo ip link set tap-$NAME promisc on

# sudo brctl addbr br-$NAME
# sudo ifconfig br-$NAME up
sudo ip link add name br-$NAME type bridge
sudo ip link set dev br-$NAME up

#sudo brctl addif br-$NAME tap-$NAME
sudo ip link set dev tap-$NAME master br-$NAME

# pushd /proc/sys/net/bridge
# for f in bridge-nf-*; do echo 0 > $f; done
# popd

# References
# brctl -> http://linuxcommand.org/man_pages/brctl8.html
# tunctl -> http://linux.die.net/man/8/tunctl