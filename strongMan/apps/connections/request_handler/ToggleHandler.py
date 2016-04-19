from django.http import JsonResponse

from strongMan.apps.vici.wrapper.exception import ViciExceptoin
from strongMan.apps.vici.wrapper.wrapper import ViciWrapper

from ..models import Connection, Secret


class ToggleHandler:
    def __init__(self, request):
        self.request = request

    def handle(self):
        connection = Connection.objects.get(id=self.request.POST['id']).subclass()
        response = dict(id=self.request.POST['id'], success=False)
        try:
            vici_wrapper = ViciWrapper()
            if vici_wrapper.is_connection_established(connection.profile) is False:
                self._load_connection(connection, vici_wrapper)
            else:
                self._unload_connection(connection, vici_wrapper)
                connection.save()
            response['success'] = True
        except ViciExceptoin as e:
            response['message'] = str(e)
        finally:
            return JsonResponse(response)

    def _load_connection(self, connection, vici_wrapper):
        vici_wrapper.load_connection(connection.dict())
        for secret in connection.secret_set:
            vici_wrapper.load_secret(secret.dict())

        self._load_private_key(connection, vici_wrapper)

        for child in connection.children.all():
            reports = vici_wrapper.initiate(child.name, connection.profile)
        connection.state = True

    def _unload_connection(self, connection, vici_wrapper):
        vici_wrapper.unload_connection(connection.profile)
        vici_wrapper.terminate_connection(connection.profile)
        connection.state = False

    def _load_private_key(self, connection, vici_wrapper):
        try:
            print("key dict" + str(connection.local.private_key_dict()))

            print("private key!")
            vici_wrapper.load_key(connection.local.private_key_dict())
            print("private key loaded!")
        except ViciExceptoin as e:
            print(str(e))
