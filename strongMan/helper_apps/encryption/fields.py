'''
https://github.com/orcasgit/django-fernet-fields
'''
from django.conf import settings
from django.core.exceptions import FieldError, ImproperlyConfigured
from django.db import models
from django.utils.encoding import force_bytes, force_str
from django.utils.functional import cached_property
from pyaes import aes as aeslib

__all__ = [
    'EncryptedField',
    'EncryptedTextField',
    'EncryptedCharField',
    'EncryptedEmailField',
    'EncryptedIntegerField',
    'EncryptedDateField',
    'EncryptedDateTimeField',
]


class EncryptedField(models.Field):
    """A field that encrypts values using Fernet symmetric encryption."""
    _internal_type = 'BinaryField'

    def __init__(self, *args, **kwargs):
        if kwargs.get('primary_key'):
            raise ImproperlyConfigured(
                "%s does not support primary_key=True."
                % self.__class__.__name__
            )
        if kwargs.get('unique'):
            raise ImproperlyConfigured(
                "%s does not support unique=True."
                % self.__class__.__name__
            )
        if kwargs.get('db_index'):
            raise ImproperlyConfigured(
                "%s does not support db_index=True."
                % self.__class__.__name__
            )
        super(EncryptedField, self).__init__(*args, **kwargs)

    def encrypt(self, value):
        aes = aeslib.AESModeOfOperationCTR(self.key)
        return aes.encrypt(value)

    def decrypt(self, value):
        aes = aeslib.AESModeOfOperationCTR(self.key)
        return aes.decrypt(value)

    @cached_property
    def key(self):
        if not hasattr(settings, "DB_SECRET_KEY"):
            raise Exception("No DB_SECRET_KEY specified!")
        if len(settings.DB_SECRET_KEY) < 32:
            raise Exception("SECRET_KEY has to be equal bigger than 32 signs")
        key = settings.DB_SECRET_KEY[:32]
        encoded_key = str.encode(key)
        return encoded_key

    def get_internal_type(self):
        return self._internal_type

    def get_db_prep_save(self, value, connection):
        value = super(
            EncryptedField, self
        ).get_db_prep_save(value, connection)
        if value is not None:
            retval = self.encrypt(force_bytes(value))
            return connection.Database.Binary(retval)

    def get_prep_lookup(self, lookup_type, value):
        if lookup_type == 'isnull':
            return super(EncryptedField, self).get_prep_lookup(lookup_type,
                                                               value)
        else:
            raise FieldError(
                "%s '%s' does not support lookups."
                % (self.__class__.__name__, self.name)
            )

    def from_db_value(self, value, expression, connection, context=None):
        if value is not None:
            value = bytes(value)
            decrypted = self.decrypt(value)
            try:
                return self.to_python(force_str(decrypted))
            except Exception:
                return self.to_python(decrypted)

    @cached_property
    def validators(self):
        # Temporarily pretend to be whatever type of field we're masquerading
        # as, for purposes of constructing validators (needed for
        # IntegerField and subclasses).
        self.__dict__['_internal_type'] = super(
            EncryptedField, self
        ).get_internal_type()
        try:
            return super(EncryptedField, self).validators
        finally:
            del self.__dict__['_internal_type']


class EncryptedTextField(EncryptedField, models.TextField):
    pass


class EncryptedCharField(EncryptedField, models.CharField):
    pass


class EncryptedEmailField(EncryptedField, models.EmailField):
    pass


class EncryptedIntegerField(EncryptedField, models.IntegerField):
    pass


class EncryptedDateField(EncryptedField, models.DateField):
    pass


class EncryptedDateTimeField(EncryptedField, models.DateTimeField):
    pass


'''
Copyright (c) 2015 ORCAS, Inc
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above
      copyright notice, this list of conditions and the following
      disclaimer in the documentation and/or other materials provided
      with the distribution.
    * Neither the name of the author nor the names of other
      contributors may be used to endorse or promote products derived
      from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''
