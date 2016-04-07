FROM django:latest

MAINTAINER Samuel Kurath <skurath@hsr.ch>

ENV STRONGSWAN_VERSION 5.4.0

RUN mkdir /opt/strongSwan \
&& apt-get update \

&& apt-get install -y libgmp-dev libssl-dev wget iptables xl2tpd bzip2 make git module-init-tools build-essential curl freeradius > /dev/null 2>&1 \
&& wget http://download.strongswan.org/strongswan-$STRONGSWAN_VERSION.tar.bz2 > /dev/null 2>&1 \
&& tar xjvf strongswan-$STRONGSWAN_VERSION.tar.bz2 > /dev/null 2>&1 \
&& cd strongswan-$STRONGSWAN_VERSION \
&& ./configure --prefix=/usr --sysconfdir=/etc \
        --enable-vici \
        --enable-openssl \
        --enable-python-eggs \
		--enable-eap-radius \
		--enable-eap-identity \
		--enable-eap-md5 \
		--enable-eap-tls \
		--enable-eap-ttls \
		--enable-eap-peap \
		--enable-eap-tnc \
		--enable-eap-dynamic > /dev/null 2>&1 \
&& make -j > /dev/null 2>&1 \
&& make install > /dev/null 2>&1 \
&& cd / \
&& git clone https://github.com/Sebubu/StrongMan.git \
&& cd StrongMan \
&& pip install --upgrade pip \
&& pip install -r requirements.txt \
&& cp -rf /strongswan-$STRONGSWAN_VERSION/testing/hosts/moon/etc/swanctl/* /etc/swanctl/

ADD swanctl.conf /etc/swanctl/swanctl.conf
ADD strongswan.conf /etc/strongswan.conf
ADD radiusd.conf /etc/freeradius/radiusd.conf



