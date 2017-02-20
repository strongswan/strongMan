import time
from datetime import timedelta
from django.utils import timezone

from django.http import JsonResponse

from strongMan.apps.server_connections.models.specific import LogMessage


class LogHandler(object):
    def __init__(self, request):
        self.newest_log = None
        self.id = int(request.POST.get('id'))

    def handle(self):
        response = dict(logs=[])
        self._delete_old_logs()
        if self.id < 0:
            logs = self._get_logs()
        else:
            logs = self._get_new_logs()
        for log in logs:
            log_dict = dict(id=log.id, message=log.message, name=log.connection.profile)
            log_dict['timestamp'] = log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            response['logs'].append(log_dict)
        return JsonResponse(response)

    def _delete_old_logs(self):
        time_threshold = timezone.now() - timedelta(minutes=5)
        LogMessage.objects.filter(timestamp__lt=time_threshold).delete()

    def _get_logs(self):
        while LogMessage.objects.all().count() == 0:
            time.sleep(1)
        return LogMessage.objects.all().order_by('timestamp')

    def _get_new_logs(self):
        logs = LogMessage.objects.filter(pk__gt=self.id).order_by('timestamp')
        while logs.count() == 0:
            time.sleep(1)
            logs = LogMessage.objects.filter(pk__gt=self.id).order_by('timestamp')
        return logs
