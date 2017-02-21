from django.http import JsonResponse
from strongMan.helper_apps.vici.wrapper.exception import ViciException

from strongMan.apps.server_connections.models.connections import Connection
from strongMan.helper_apps.vici.wrapper.wrapper import ViciWrapper


class SaInfoHandler(object):
    def __init__(self, request):
        self.request = request
        self.id = int(request.POST.get('id'))

    @property
    def connection(self):
        return Connection.objects.get(pk=self.id).subclass()

    def handle(self):
        response = dict(id=self.connection.id, success=False)
        try:
            vici_wrapper = ViciWrapper()
            sas = vici_wrapper.get_sas_by(self.connection.profile)
            if sas:
                ikesas = []
                for sa in sas:
                    sa = sa[self.connection.profile]
                    ikesas.append(IkeSA(sa))
                sadict = []
                for ikesa in ikesas:
                    sadict.append(ikesa.__dict__)
                response['child'] = sadict
                response['success'] = True
        except ViciException as e:
            response['message'] = str(e)
        except Exception as e:
            print(e)

        return JsonResponse(response)


class IkeSA(object):
    def __init__(self, sa):
        self.uniqueid = sa['uniqueid'].decode('ascii')
        self.remote_host = sa['remote-host'].decode('ascii')
        self.remote_id = sa['remote-id'].decode('ascii')
        child_sas = sa['child-sas']
        children = []
        for child_sa in child_sas:
            child_sa = child_sas[child_sa]
            children.append(ChildSA(child_sa))
        childrendict = []
        for child in children:
            childrendict.append(child.__dict__)
        self.child_sas = childrendict


class ChildSA(object):
    def __init__(self, child_sa):
        self.uniqueid = child_sa['uniqueid'].decode('ascii')
        self.remote_ts = child_sa['remote-ts'][0].decode('ascii')
        self.local_ts = child_sa['local-ts'][0].decode('ascii')
        self.bytes_in = child_sa['bytes-in'].decode('ascii')
        self.bytes_out = child_sa['bytes-out'].decode('ascii')
        self.packets_in = child_sa['packets-in'].decode('ascii')
        self.packets_out = child_sa['packets-out'].decode('ascii')
        self.install_time = child_sa['install-time'].decode('ascii')
