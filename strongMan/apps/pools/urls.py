from django.conf.urls import url

from . import views

app_name = 'pools'
urlpatterns = [
    url(r'^$', views.overview, name='index'),
    url(r'add$', views.add, name='add'),
    url(r'add_form$', views.add_form, name='add_form'),
    url(r'^(?P<poolname>[0-9a-zA-Z]+)$', views.edit, name='edit'),
    ]
