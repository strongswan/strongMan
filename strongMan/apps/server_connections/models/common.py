from enum import Enum

from strongMan.apps.certificates.models import MessageObj


class DjangoEnum(Enum):
    @classmethod
    def choices(cls):
        return [(x.value, x.name) for x in cls]


class State(DjangoEnum):
    DOWN = 'DOWN'
    CONNECTING = 'CONNECTING'
    ESTABLISHED = 'ESTABLISHED'
    LOADED = 'LOADED'
    UNLOADED = 'UNLOADED'


class CertConDoNotDeleteMessage(MessageObj):
    def __init__(self, connection):
        self.connection = connection

    def __str__(self):
        return "Certificate is in use by the connection named '" + self.connection.profile + "'."


class KeyConDoNotDeleteMessage(MessageObj):
    def __init__(self, connection):
        self.connection = connection

    def __str__(self):
        return "Private key is in use by the connection named '" + self.connection.profile + "'."
