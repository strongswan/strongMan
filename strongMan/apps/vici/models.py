from django.db import models
from .vici import Session as vici_session
import socket
from collections import OrderedDict

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







class UploadFile(models.Model):
    file = models.FileField(upload_to='files/%Y/%m/%d')