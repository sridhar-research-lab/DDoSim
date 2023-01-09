FROM ubuntu:20.04

ENV DEBIAN_FRONTEND noninteractive

RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

# COPY sources.list /etc/apt/

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y apt-transport-https

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -q -y --no-install-recommends dialog debconf-utils apt-utils apt-file pciutils software-properties-common wget curl git gcc g++ make gnupg nano unzip libbz2-dev aptitude net-tools dnsutils ifupdown procps iputils-ping apache2 telnet

WORKDIR /

RUN echo "deb http://archive.ubuntu.com/ubuntu/ xenial main" | tee -a /etc/apt/sources.list
RUN echo "deb http://archive.ubuntu.com/ubuntu/ xenial universe" | tee -a /etc/apt/sources.list
# RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 8B48AD6246925553 7638D0442B90D010 CBF8D6FD518E17E1

RUN DEBIAN_FRONTEND=noninteractive add-apt-repository 'deb http://archive.ubuntu.com/ubuntu trusty universe' && apt-get update

RUN DEBIAN_FRONTEND=noninteractive apt-get -y update && echo "#!/bin/sh\nexit 0" > /usr/sbin/policy-rc.d && apt-get install -y debconf-utils && echo mysql-server mysql-server/root_password password root | debconf-set-selections && echo mysql-server mysql-server/root_password_again password root | debconf-set-selections && apt-get install -y mysql-server-5.7 -o pkg::Options::="--force-confdef" -o pkg::Options::="--force-confold" --fix-missing && apt-get install -y mysql-client-5.7

COPY prep.sh dns.py dhcp.py cnc db.sql /
COPY a.sh bot /var/www/html/
COPY maldns /etc/init.d

RUN chmod +x /etc/init.d/maldns
RUN chmod +x /prep.sh /dns.py /dhcp.py /cnc /db.sql

RUN apt-get install iperf # in the server run: iperf -s

CMD /prep.sh
