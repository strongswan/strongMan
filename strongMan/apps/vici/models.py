from django.db import models
from .vici import Session as vici_session
import socket
from collections import OrderedDict
from oscrypto import keys as k

from asn1crypto import keys
# Create your models here.
class ViciSession:
    def __init__(self):
        self.session = None

    def connect(self):
        s = socket.socket(socket.AF_UNIX)
        s.connect("/var/run/charon.vici")
        self.session = vici_session(s)

    def info(self):
        dict = OrderedDict()
        dict["list_conns"] = self._run(self.session.list_conns)
        dict["list_certs"] = self._run(self.session.list_certs)
        dict["list_policies"] = self._run(self.session.list_policies)
        dict["list_sas"] = self._run(self.session.list_sas)
        dict["stats"] = self._run(self.session.stats)
        dict["version"] = self._run(self.session.version)
        return dict

    def _run(self, f):
        out = ""
        value = f()
        if(isinstance(value, OrderedDict)):
                out += self._print_dict(value) + "\n"
        else:
            for entry in value:
                out += self._print_dict(entry) + "\n"
        return out

    def _print_dict(self, dict, tab=0, newline="\n", space="´"):
        def tabs(count):
            ret = ""
            for i in range(count):
                for ia in range(4): ret += space
            return ret

        def print_key(key):
            return tabs(tab) + "\"" + key + "\" : "

        def print_key_value(key, value):
            p = print_key(key) + str(value) + ","
            p = p.replace("'", "\"")
            p = p.replace("b\"", "\"")
            return p

        def print_key_list(key, list):
            if list.__len__() == 0: return ""
            p = print_key(key) + "["
            for val in list:
                p += str(val) + ", "
            p = p[0:p.__len__() -2]
            p += "]"
            p = p.replace("'", "\"")
            p = p.replace("b\"", "\"")
            return p

        def print_key_dict(key, dict):
            ret = print_key(key) + " {" + newline
            ret += self._print_dict(dict, tab+1)
            ret += tabs(tab) + "}"
            return ret

        ret = ""
        for key in dict:
            value = dict[key]
            if(isinstance(value,OrderedDict)):
                ret += print_key_dict(key, value)
            elif(isinstance(value,list)):
                if(value.__len__() == 0): continue
                ret += print_key_list(key, value)
            else:
                ret += print_key_value(key, value)
            ret += "," + newline
        ret = ret[0:ret.__len__() -2] + newline

        return ret

    def add_same_con(self):
        conns = self.session.list_conns()

        for con in conns:
            c = con
        print(c)
        self.session.load_conn(c)

    def add_con(self, config):
        self.session.load_conn(config)





class CertReader():

    def __init__(self):
        self.der_bytes = None
        self.asn1 = None
        self.cert_types = self._possible_cert_types()
        self.type = None
        self.public_key = None

    @classmethod
    def by_bytes(cls, bytes):
        der_bytes = bytes
        reader = cls()
        reader.der_bytes = der_bytes
        return reader

    @classmethod
    def by_path(cls, path):
        with open(path, 'rb') as f:
            der_bytes = f.read()
        reader = cls()
        reader.der_bytes = der_bytes
        return reader

    def _possible_cert_types(self):
        certTypes = OrderedDict()
        certTypes["X509"] = k.parse_certificate
        certTypes["PublicKey"] = k.parse_public
        certTypes["PrivateKey"] = k.parse_private
        certTypes["PKCS12"] = k.parse_pkcs12

        return certTypes

    def _is_type(self, f, password=None):
        try:
            if password == None:
                cert = f(self.der_bytes)
            else:
                cert = f(self.der_bytes, password=password)
            cert.native
            return True
        except Exception as e:
            return False

    def _type(self, password=None):
        for typ in self.cert_types:
            value = self.cert_types[typ]
            if self._is_type(value, password): return typ

        return None

    def read(self, password=None):
        self.type = self._type(password)
        if self.type == None:
            raise Exception("Can't detect a asn1 type. Are the bytes encrypted?")

        if password == None:
            self.asn1 = self.cert_types[self.type](self.der_bytes)
        else:
            self.asn1 = self.cert_types[self.type](self.der_bytes, password=password)

    def identifier(self):
        if self.type == "PrivateKey":
            reader = PrivateKeyIdentifier.by_container(self.asn1)
        elif self.type == "X509":
            reader = X509Identifier.by_container(self.asn1)
        self.public_key = reader.extract_public_key()
        return self.public_key

class AbstractIdentifier:
    def __init__(self):
        self.container = None

    @classmethod
    def by_container(cls, container):
        reader = cls()
        reader.container = container
        return reader

    def extract_public_key(self):
        pass


class PrivateKeyIdentifier(AbstractIdentifier):
    def __init__(self):
        self._possible_types = self._types_dict()

    def _types_dict(self):
        dict = OrderedDict()
        dict["rsa"] = self._pubkey_rsa
        dict["ec"] = self._pubkey_ec
        dict["dsa"] = self._pubkey_dsa
        return dict

    def extract_public_key(self):
        algorithm = self.container.algorithm
        extractor = self._possible_types[algorithm]
        return extractor()

    def _pubkey_dsa(self):
        return self.container.native["private_key_algorithm"]["parameters"]["g"]

    def _pubkey_rsa(self):
        private = keys.RSAPrivateKey.load(self.container.native["private_key"])
        return private.native["modulus"]

    def _pubkey_ec(self):
        private = keys.ECPrivateKey.load(self.container.native["private_key"])
        return private.native["public_key"]



class X509Identifier(AbstractIdentifier):
    def __init__(self):
        self._possible_types = self._types_dict()

    def _types_dict(self):
        dict = OrderedDict()
        dict["rsa"] = self._pubkey_rsa
        dict["ec"] = self._pubkey_ec
        dict["dsa"] = self._pubkey_dsa
        return dict

    def extract_public_key(self):
        self.container.native
        algorithm = self.container.public_key.algorithm
        extractor = self._possible_types[algorithm]
        return extractor()

    def _pubkey_dsa(self):
        return self.container.native["tbs_certificate"]["subject_public_key_info"]["algorithm"]["parameters"]["g"]

    def _pubkey_rsa(self):
        return self.container.native["tbs_certificate"]["subject_public_key_info"]["public_key"]["modulus"]

    def _pubkey_ec(self):
        return self.container.native["tbs_certificate"]["subject_public_key_info"]["public_key"]




class UploadFile(models.Model):
    file = models.FileField(upload_to='files/%Y/%m/%d')