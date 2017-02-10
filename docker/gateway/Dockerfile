FROM django:latest

ARG BRANCH
ARG COMMIT
ARG REPO_SLUG

ENV STRONGSWAN_VERSION 5.4.0

RUN mkdir /opt/strongSwan \
&& apt-get update \
&& apt-get install -y libgmp-dev libssl-dev wget iptables xl2tpd bzip2 make git module-init-tools build-essential vim > /dev/null 2>&1 \
&& pip install --upgrade pip \
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
&& git clone --depth=50 --branch=${BRANCH} https://github.com/${REPO_SLUG}.git strongMan \
&& cd strongMan \
&& git checkout -qf ${COMMIT} \
&& pip install -r requirements.txt

RUN cp -rf /strongswan-$STRONGSWAN_VERSION/testing/hosts/moon/etc/swanctl/* /etc/swanctl/ \
&& cp /strongswan-$STRONGSWAN_VERSION/testing/hosts/moon/etc/ipsec.secrets /etc/

ADD swanctl.conf /etc/swanctl/swanctl.conf
ADD strongswan.conf /etc/strongswan.conf



