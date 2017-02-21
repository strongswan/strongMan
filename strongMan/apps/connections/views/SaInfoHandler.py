from django.http import JsonResponse
from strongMan.helper_apps.vici.wrapper.exception import ViciException

from strongMan.apps.connections.models.connections import Connection
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
            sa = vici_wrapper.get_sas_by(self.connection.profile)
            if sa:
                child = ChildSA(sa[0], self.connection.profile)
                response['child'] = child.__dict__
                response['success'] = True
        except ViciException as e:
            response['message'] = str(e)
        except Exception as e:
            print(e)

        return JsonResponse(response)


class ChildSA(object):
    def __init__(self, sa, connection_name):
        sa = sa[connection_name]
        child_sas = sa['child-sas']
        child_sa = child_sas[connection_name]
        self.remote_ts = child_sa['remote-ts'][0].decode('ascii')
        self.local_ts = child_sa['local-ts'][0].decode('ascii')
        self.bytes_in = child_sa['bytes-in'].decode('ascii')
        self.bytes_out = child_sa['bytes-out'].decode('ascii')
        self.packets_in = child_sa['packets-in'].decode('ascii')
        self.packets_out = child_sa['packets-out'].decode('ascii')
