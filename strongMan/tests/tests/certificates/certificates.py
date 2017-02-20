import os

from strongMan.tests.utils.certificates import CertificateLoader


class TestCertificates(object):
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "certs")
    loader = CertificateLoader(path)
    X509_rsa_ca = loader.create("ca.crt")
    X509_rsa_ca_samepk_differentsn = loader.create("hsrca_doppelt_gleicher_publickey.crt")
    X509_rsa_ca_samepk_differentsn_san = loader.create("cacert_gleicher_public_anderer_serial.der")
    PKCS1_rsa_ca = loader.create("ca2.key")
    PKCS1_rsa_ca_encrypted = loader.create("ca.key")
    PKCS8_rsa_ca = loader.create("ca2.pkcs8")
    PKCS8_ec = loader.create("ec.pkcs8")
    PKCS8_rsa_ca_encrypted = loader.create("ca_enrypted.pkcs8")
    X509_rsa_ca_der = loader.create("cacert.der")
    X509_ec = loader.create("ec.crt")
    PKCS1_ec = loader.create("ec2.key")
    X509_rsa = loader.create("warrior.crt")
    PKCS12_rsa = loader.create("warrior.pkcs12")
    PKCS12_rsa_encrypted = loader.create("warrior_encrypted.pkcs12")
    X509_googlecom = loader.create("google.com_der.crt")
    PKCS1_dsa = loader.create("dsa2.key")
    X509_dsa = loader.create("dsa.crt")
