FROM ubuntu:20.04

RUN apt-get update

COPY conf /conf.tar.gz
RUN tar -xvzf conf.tar.gz && rm conf.tar.gz

# glib-dev
RUN apt-get install -y ./glib/multiarch-support_2.19-0ubuntu6_amd64.deb
RUN apt-get install --allow-downgrades -y ./glib/zlib1g_1%3a1.2.8.dfsg-1ubuntu1_amd64.deb
RUN apt-get install -y ./glib/zlib1g-dev_1%3a1.2.8.dfsg-1ubuntu1_amd64.deb
RUN apt-get install --allow-downgrades -y ./glib/libpcre3_1%3a8.31-2ubuntu2_amd64.deb
RUN apt-get install --allow-downgrades -y ./glib/libpcrecpp0_1%3a8.31-2ubuntu2_amd64.deb
RUN apt-get install -y ./glib/libpcre3-dev_1%3a8.31-2ubuntu2_amd64.deb
RUN apt-get install -y ./glib/libffi6_3.1~rc1+r3.0.13-12_amd64.deb
RUN apt-get install -y ./glib/libelfg0_0.8.13-5_amd64.deb
RUN apt-get install -y ./glib/libglib2.0-0_2.40.0-2_amd64.deb
RUN apt-get install -y ./glib/libglib2.0-bin_2.40.0-2_amd64.deb
RUN apt-get install -y ./glib/libglib2.0-dev_2.40.0-2_amd64.deb
RUN rm -rf /glib

# dbus
RUN apt-get install -q -y dbus libdbus-1-dev

# gnutls
RUN apt-get install -y -q ./gnutls/libgcrypt11_1.5.3-2ubuntu4_amd64.deb
RUN apt-get install -y -q ./gnutls/libgnutls26_2.12.23-12ubuntu2_amd64.deb
RUN apt-get install -y -q ./gnutls/libnettle4_2.7.1-1_amd64.deb
RUN apt-get install -y -q ./gnutls/libhogweed2_2.7.1-1_amd64.deb
RUN apt-get install -y -q ./gnutls/libgnutls28_3.2.11-2ubuntu1_amd64.deb
RUN apt-get install -y -q ./gnutls/libgnutlsxx28_3.2.11-2ubuntu1_amd64.deb
RUN apt-get install -y -q ./gnutls/libgnutls-xssl0_3.2.11-2ubuntu1_amd64.deb
RUN apt-get install -y -q ./gnutls/libgnutls28-dev_3.2.11-2ubuntu1_amd64.deb
RUN rm -rf /gnutls

# iptables & readline
RUN apt-get update && apt-get install -q -y xtables-addons-source libreadline-dev

WORKDIR /connman-1.34/
RUN bash 1.sh

RUN rm -rf /connman-1.34
WORKDIR /

RUN mv connman /etc/init.d/
RUN chmod +x /etc/init.d/connman

RUN mv prep.sh /home/
RUN chmod +x /home/prep.sh

RUN apt-get install -y -q wondershaper dnsutils net-tools

CMD ["/home/prep.sh"]