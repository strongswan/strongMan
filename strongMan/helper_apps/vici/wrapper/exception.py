class ViciException(Exception):
    '''Vici Base Exception'''


class ViciSocketException(ViciException):
    '''Raise when socket of vici can't connect'''


class ViciLoadException(ViciException):
    '''Raise when load failes'''


class ViciInitiateException(ViciException):
    '''Raise when load failes'''


class ViciTerminateException(ViciException):
    '''Raise when load failes'''


class ViciPathNotASocketException(ViciException):
    '''Raise when load failes'''
