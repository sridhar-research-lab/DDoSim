#!/bin/sh

modprobe br_netfilter

pushd /proc/sys/net/bridge
for f in bridge-nf-*; do echo 0 > $f; done
popd