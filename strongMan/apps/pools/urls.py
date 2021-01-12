from django.conf.urls import re_path

from . import views

app_name = 'pools'
urlpatterns = [
    re_path(r'^$', views.overview, name='index'),
    re_path(r'add$', views.add, name='add'),
    re_path(r'add_form$', views.add_form, name='add_form'),
    re_path(r'refreshdetails$', views.refreshdetails, name='refreshdetails'),
    re_path(r'^(?P<poolname>[0-9a-zA-Z_\-]+)$', views.edit, name='edit'),
]
