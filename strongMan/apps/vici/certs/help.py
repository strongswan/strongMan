from collections import OrderedDict
from pyasn1.type import univ
from pyasn1.codec.der import encoder, decoder
import os
import json


class OidTranslator:

    def __init__(self):
        self._dict = None

    def init(self):
        dirpath = os.path.dirname(os.path.realpath(__file__))
        filepath = dirpath + '/oids.json'
        oidjson = open(filepath, 'r').read()
        self._dict = json.loads(oidjson)

    def translate(self, oid):
        return self._dict[oid]

translator = OidTranslator()
translator.init()


def make_dict(seq):
    """Return simple dictionary of labeled key elements as simple types.
    Returns:
      {str, value} where `value` is simple type like `long`
    """
    dict = OrderedDict()
    for i in range(len(seq._componentValues)):
      if seq._componentValues[i] is not None:
        componentType = seq.getComponentType()
        if componentType is not None:
          if isinstance(seq, univ.SequenceOf) or isinstance(seq, univ.SetOf):
              name = i
          else:
              name = componentType.getNameByPosition(i)
          val = seq[name]
          if isinstance(val, univ.Sequence) or isinstance(val, univ.Choice):
              value = make_dict(val)
          elif isinstance(val, univ.SequenceOf) or isinstance(val, univ.SetOf):
              value = make_dict(val)
          elif isinstance(val, univ.ObjectIdentifier):
              oid = str(seq._componentValues[i].prettyPrint())
              oid = oid.replace(', ', '.').replace('(','').replace(')','')
              translation = translator.translate(oid)
              value = translation['d'] + " (" + oid + ")"
          else:
            value = seq._componentValues[i].prettyPrint()
            if isinstance(val, univ.Any):
                value = decoder.decode(val)[0]

          dict[name] = value
    return dict

def print_dict(dict, tab=0, newline="\n<br/>", space="´"):
    def tabs(count):
        ret = ""
        for i in range(count):
            for ia in range(4): ret += space
        return ret

    def print_key(key):
        return tabs(tab) + "\"" + str(key) + "\" : "

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
        ret += print_dict(dict, tab+1)
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