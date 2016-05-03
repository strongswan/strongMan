from django.http import JsonResponse

from ..models import Connection, LogMessage


class LogHandler:
    def __init__(self, request, id):
        self.request = request
        self.id = id

    @property
    def connection(self):
        return Connection.objects.get(pk=self.id).subclass()

    def handle(self):
        response = dict(id=self.connection.id, name=self.connection.profile, has_log=False)
        log_message = LogMessage.objects.filter(connection=self.connection).order_by('timestamp').first()
        if log_message is not None:
            response['level'] = log_message.level
            response['message'] = log_message.message
            response['timestamp'] = log_message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            response['has_log'] = True
            log_message.delete()
        return JsonResponse(response)
