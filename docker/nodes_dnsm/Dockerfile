FROM ubuntu:20.04

ENV DEBIAN_FRONTEND noninteractive

# COPY sources.list /etc/apt/

RUN apt-get update && apt-get install -y apt-transport-https

RUN apt-get update

RUN apt-get update && apt-get install -q -y --no-install-recommends dialog debconf-utils apt-utils apt-file pciutils software-properties-common nano curl gcc g++ gdb unzip libbz2-dev aptitude dnsutils ifupdown procps iputils-ping telnet wget git make gnupg  python3 net-tools

RUN echo "deb http://archive.ubuntu.com/ubuntu/ xenial main" | tee -a /etc/apt/sources.list
RUN echo "deb http://archive.ubuntu.com/ubuntu/ xenial universe" | tee -a /etc/apt/sources.list
# RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 8B48AD6246925553 7638D0442B90D010 CBF8D6FD518E17E1
RUN apt-get update && apt-get install gcc-4.9 -y

RUN wget https://thekelleys.org.uk/dnsmasq/dnsmasq-2.77.tar.gz
RUN tar -xvzf dnsmasq-2.77.tar.gz
WORKDIR /dnsmasq-2.77

# to fix error: use of undeclared identifier 'SIOCGSTAMP' when compiling
# https://github.com/LibtraceTeam/libtrace/commit/cd7f4c79aa55823d2e3be9b753088c40bc44d183
RUN sed -i '18i#include <linux/sockios.h>' /dnsmasq-2.77/src/dhcp.c

# Patch Makefile so we can compile with ASAN
RUN sed -i'' 's/LDFLAGS       =/LDFLAGS       ?=/' Makefile
RUN sed -i'' 's/CFLAGS        =/CFLAGS        ?=/' Makefile

RUN CC="gcc-4.9" CFLAGS="-O2 -fno-stack-protector" make

WORKDIR /

COPY prep.sh /

RUN chmod +x /prep.sh

RUN apt-get install wondershaper iperf # in the client run: iperf -c 10.0.0.1 -d

CMD /prep.sh
# ENTRYPOINT /bin/bash
