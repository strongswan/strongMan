class DjangoAbstractBase(object):
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

    @classmethod
    def subclasses(cls, queryset):
        '''
        Tries to convert the queryset so its subclasses
        :return: subclass object
        '''
        id_list = []
        for dic in queryset.values('pk'):
            id_list.append(dic['pk'])

        subclasses = []
        for klass in cls.all_subclasses():
            try:
                results = klass.objects.filter(pk__in=id_list)
                for value in results:
                    subclasses.append(value)
            except Exception:
                pass
        return subclasses

    def subclass(self):
        '''
        Tries to convert this class to it's subclass
        (object):return: subclass object
        '''
        for klass in type(self).all_subclasses():
            try:
                return klass.objects.get(pk=self.pk)
            except Exception:
                pass
        raise CertificateException("Can't find subclass object")


class CertificateModel(object):
    class Meta(object):
        app_label = 'certificates'


class CertificateException(Exception):
    pass


class CertificateDoNotDelete(CertificateException):
    def __init__(self, message_obj):
        self.message_obj = message_obj

    def __str__(self):
        message = self.message_obj.__str__()
        return message

    @property
    def has_html(self):
        return self.message_obj.is_html

    @property
    def html(self):
        return self.message_obj.html


class MessageObj(object):
    @property
    def has_html(self):
        return False

    @property
    def html(self):
        raise NotImplementedError()

    def __str__(self):
        return ""
