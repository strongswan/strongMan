from django.conf.urls import url

from . import views

app_name = 'eap_secrets'
urlpatterns = [
    url(r'add$', views.add, name='add'),
    url(r'^(?P<secret_id>[0-9]+)$', views.delete_secret, name='delete_secret'),
    url(r'$', views.overview, name='overview'),
]
