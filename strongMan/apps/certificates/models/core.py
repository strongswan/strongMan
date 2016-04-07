from enum import Enum


class DjangoEnum(Enum):
    @classmethod
    def choices(cls):
        # This method converts a Python enum to Django Choises used in the database models
        return [(x.value, x.name) for x in cls]


class DjangoAbstractBase:
    @classmethod
    def all_subclasses(cls):
        '''
        :return: List of all subclasses of the current class
        '''
        all_subclasses = []

        for subclass in cls.__subclasses__():
            all_subclasses.append(subclass)
            all_subclasses.extend(subclass.all_subclasses())

        return all_subclasses

    def subclass(self):
        '''
        Tries to convert this class to it's subclass
        :return: subclass object
        '''
        for klass in type(self).all_subclasses():
            try:
                return klass.objects.get(pk=self.pk)
            except:
                pass
        raise CertificateException("Can't find subclass object")


class CertificateModel:
    class Meta:
        app_label = 'certificates'


class CertificateException(Exception):
    pass
