from django.conf.urls import url

from . import views

app_name = 'eap_secrets'
urlpatterns = [
    url(r'add$', views.add, name='add'),
    # url(r'add_form$', views.add_form, name='add_form'),
    # url(r'^(?P<certificate_id>[0-9]+)$', views.details, name='details'),
    url(r'$', views.overview, name='overview'),
]
