from django.conf.urls import url
from . import views

app_name='vici'

urlpatterns = [
    url(r'^$', views.index, name='index'),
]
