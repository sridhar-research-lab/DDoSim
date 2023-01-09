FROM ubuntu:20.04

ENV DEBIAN_FRONTEND noninteractive
RUN echo "resolvconf resolvconf/linkify-resolvconf boolean false" | debconf-set-selections

# COPY sources.list /etc/apt/

RUN apt-get update && apt-get install -y apt-transport-https

RUN apt-get update && apt-get install -q -y --no-install-recommends dialog debconf-utils apt-utils apt-file pciutils software-properties-common wget curl git gcc g++ make gnupg nano unzip libbz2-dev aptitude net-tools dnsutils ifupdown procps glib2.0 iputils-ping telnet gdb

RUN echo "deb http://archive.ubuntu.com/ubuntu/ xenial main" | tee -a /etc/apt/sources.list
RUN echo "deb http://archive.ubuntu.com/ubuntu/ xenial universe" | tee -a /etc/apt/sources.list
# RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 8B48AD6246925553 7638D0442B90D010 CBF8D6FD518E17E1
RUN apt-get update && apt-get install gcc-4.9 g++-4.9 -y

# if "glib2.0" is added here, it will cause lots of errors
RUN apt-get update && apt-get install -q -y libdbus-1-dev xtables-addons-source module-assistant libreadline-dev libexpat-dev expat libgmp3-dev nettle-dev libgtk2.0-dev libgcrypt-dev

RUN apt-get install -q -y xorg

WORKDIR /
RUN wget https://www.gnupg.org/ftp/gcrypt/gnutls/v2.4/gnutls-2.4.3.tar.bz2
RUN bzip2 -d gnutls-2.4.3.tar.bz2
RUN tar -xvf gnutls-2.4.3.tar
WORKDIR /gnutls-2.4.3
RUN ./configure --prefix=/usr
RUN make
RUN make install

WORKDIR /
RUN wget https://mirrors.edge.kernel.org/pub/linux/network/connman/connman-1.34.tar.gz
RUN tar -xzf connman-1.34.tar.gz
WORKDIR /connman-1.34
RUN ./configure CC="gcc-4.9" CFLAGS="-O2 -fno-stack-protector" --prefix=/usr --sysconfdir=/etc --localstatedir=/var
RUN make && make install

WORKDIR /
RUN rm -rf gnutls-2.4.3.tar.bz2 gnutls-2.4.3.tar connman-1.34.tar.gz gnutls-2.4.3/

COPY prep.sh /
COPY connman /etc/init.d

RUN chmod +x /prep.sh
RUN chmod +x /etc/init.d/connman

RUN apt-get install wondershaper iperf # in the client run: iperf -c 10.0.0.1 -d

CMD /prep.sh
# ENTRYPOINT /bin/bash

# RUN apt-get install resolvconf -y

# RUN apt-get remove --purge -y network-manager network-manager-gnome network-manager-pptp network-manager-pptp-gnome resolvconf
# RUN apt-get autoremove -y -q

# RUN service dbus start
