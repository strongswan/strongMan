ARG python_version=latest
FROM python:${python_version}

ARG strongswan_version

RUN apt-get -y update \
&& apt-get -y install libssl-dev wget bzip2 make build-essential vim \
&& apt-get -y clean

RUN wget https://download.strongswan.org/strongswan-${strongswan_version}.tar.bz2 \
&& tar xjvf strongswan-${strongswan_version}.tar.bz2 \
&& cd strongswan-${strongswan_version} \
&& ./configure --prefix=/usr --sysconfdir=/etc \
		--enable-eap-identity \
		--enable-eap-md5 \
		--enable-eap-tls \
		--enable-eap-ttls \
		--enable-eap-peap \
		--enable-eap-dynamic \
&& make -j \
&& make install \
&& cd - && rm -rf strongswan-*

COPY . /strongMan/

RUN cd /strongMan \
&& pip install --upgrade pip \
&& pip install -r requirements.txt

# assuming the repo root as context
COPY docker/gateway/swanctl /etc/swanctl/
COPY docker/gateway/strongswan.conf /etc/strongswan.conf
