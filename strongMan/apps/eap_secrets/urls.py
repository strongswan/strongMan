from django.conf.urls import url

from . import views

app_name = 'eap_secrets'
urlpatterns = [
    url(r'add$', views.add, name='add'),
    url(r'^(?P<secret_name>[0-9a-zA-Z_\-]+)$', views.edit, name='edit'),
    url(r'$', views.overview, name='overview'),
]
