import os

from strongMan.apps.certificates.container_reader import X509Reader


class CertificateLoader(object):
    def __init__(self, path, name=None):
        self.path = path
        self.name = name

    def create(self, name):
        assert self.path
        return CertificateLoader(self.path, name)

    def open(self):
        assert self.name
        full_path = os.path.join(self.path, self.name)
        return open(full_path, 'rb')

    def read(self):
        with self.open() as f:
            return f.read()

    def read_x509(self, password=None):
        bytes = self.read()
        reader = X509Reader.by_bytes(bytes, password)
        reader.parse()
        return reader
