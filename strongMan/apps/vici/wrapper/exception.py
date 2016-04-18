class ViciExceptoin(Exception):
    '''Vici Base Exception'''

class ViciSocketException(ViciExceptoin):
     '''Raise when socket of vici can't connect'''

class ViciLoadException(ViciExceptoin):
    '''Raise when load failes'''

class ViciInitiateException(ViciExceptoin):
    '''Raise when load failes'''

class ViciTerminateException(ViciExceptoin):
    '''Raise when load failes'''
