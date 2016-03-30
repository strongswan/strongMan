FROM django:latest

MAINTAINER Samuel Kurath <skurath@hsr.ch>

ENV STRONGSWAN_VERSION 5.4.0

RUN mkdir /opt/strongSwan \
&& apt-get update \

&& apt-get install -y libgmp-dev libssl-dev wget iptables xl2tpd bzip2 make git module-init-tools build-essential \
&& wget http://download.strongswan.org/strongswan-$STRONGSWAN_VERSION.tar.bz2 \
&& tar xjvf strongswan-$STRONGSWAN_VERSION.tar.bz2 \
&& cd strongswan-$STRONGSWAN_VERSION \
&& ./configure --prefix=/usr --sysconfdir=/etc --enable-vici --enable-openssl --enable-eap-tls --enable-python-eggs \
&& make -j \
&& make install \
&& cd / \
&& git clone https://github.com/Sebubu/StrongMan.git \
&& cd StrongMan \
&& pip install --upgrade pip \
&& pip install -r requirements.txt




