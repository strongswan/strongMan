from django.conf.urls import re_path

from . import views

app_name = 'eap_secrets'
urlpatterns = [
    re_path(r'add$', views.add, name='add'),
    re_path(r'^(?P<secret_name>[0-9a-zA-Z_\-]+)$', views.edit, name='edit'),
    re_path(r'$', views.overview, name='overview'),
]
