FROM ubuntu:20.04

RUN apt-get update -y -q

COPY conf /conf.tar.gz

RUN tar -xvzf conf.tar.gz && rm conf.tar.gz

WORKDIR /dnsmasq-2.77
RUN bash 1.sh
RUN rm -rf /dnsmasq-2.77

WORKDIR /

RUN mv prep.sh /home/
RUN chmod +x /home/prep.sh

RUN apt-get install wondershaper net-tools curl -y -q

CMD ["/home/prep.sh"]