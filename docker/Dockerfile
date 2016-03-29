FROM django:latest
MAINTAINER Samuel Kurath <skurath@hsr.ch>

RUN mkdir /opt/strongSwan \
&& apt-get update \
&& apt-get install -y libgmp3-dev libssl-dev wget bzip2 make git \
&& wget http://download.strongswan.org/strongswan-5.3.5.tar.bz2 \
&& tar xjvf strongswan-5.3.5.tar.bz2 \
&& cd strongswan-5.3.5 \
&& ./configure --prefix=/usr --sysconfdir=/etc --enable-vici --enable-openssl --enable-eap-tls --enable-python-eggs \
&& make \
&& make install \
&& cd / \
&& git clone https://github.com/Sebubu/StrongMan.git
&& cd StrongMan \
&& pip install --upgrade pip \
&& pip install -r requirements.txt \
&& pip install oscrypto \
&& pip install asn1crypto \
&& python manage.py test --settings=strongMan.settings.local 



WORKDIR /



