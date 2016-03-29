FROM django:latest
MAINTAINER Samuel Kurath <skurath@hsr.ch>

RUN mkdir /opt/strongSwan \
&& apt-get update \
&& apt-get install -y libgmp3-dev libssl-dev wget \
&& wget http://download.strongswan.org/strongswan-5.3.5.tar.bz2 \
&& tar xjvf strongswan-5.3.5.tar.bz2 \
&& cd strongswan-5.3.5 \
&& make \
&& make install \
&& cd /etc/ipsec.d/cacerts/ \
&& ipsec start


WORKDIR /



