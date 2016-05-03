
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

    @classmethod
    def subclasses(cls, queryset):
        '''
        Tries to convert the queryset so its subclasses
        :return: subclass object
        '''
        id_list = []
        for dict in queryset.values('pk'):
            id_list.append(dict['pk'])

        subclasses = []
        for klass in cls.all_subclasses():
            try:
                results = klass.objects.filter(pk__in=id_list)
                for value in results:
                    subclasses.append(value)
            except:
                pass
        return subclasses

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
