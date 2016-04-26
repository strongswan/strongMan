from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import RedirectView
from .apps import views
from .apps.certificates import urls as certificates_url
from .apps.connections import urls as connections_urls, views as connectionviews
from .apps.vici import urls as vici_urls
from .apps.views import index


urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^admin/', admin.site.urls),
    url(r'^vici/', include(vici_urls)),
    url(r'^connections/', include(connections_urls)),
    url(r'^certificates/', include(certificates_url)),
    url(r'^login/?$', views.login, name='login'),
    url(r'^logout/?$', views.logout, name='logout'),
    url(r'change_pw$', views.pw_change, name='pw_change'),
    url(r'^about/?$', views.about, name='about'),
]
