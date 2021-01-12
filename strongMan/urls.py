from django.conf import settings
from django.conf.urls import re_path, include
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from .apps import views
from .apps.certificates import urls as certificates_url
from .apps.eap_secrets import urls as eap_secrets_url
from .apps.connections import urls as connections_urls
from .apps.server_connections import urls as server_connections_urls
from .apps.pools import urls as pools
from .apps.views import index

urlpatterns = [
    re_path(r'^$', index, name='index'),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^connections/', include(connections_urls)),
    re_path(r'^server_connections/', include(server_connections_urls)),
    re_path(r'^pools/', include(pools)),
    re_path(r'^certificates/', include(certificates_url)),
    re_path(r'^eap_secrets/', include(eap_secrets_url)),
    re_path(r'^login/?$', views.login, name='login'),
    re_path(r'^logout/?$', views.logout, name='logout'),
    re_path(r'change_pw$', views.pw_change, name='pw_change'),
    re_path(r'^about/?$', views.about, name='about'),
]

handler400 = 'strongMan.apps.views.bad_request'
handler403 = 'strongMan.apps.views.permission_denied'
handler404 = 'strongMan.apps.views.page_not_found'
handler500 = 'strongMan.apps.views.server_error'

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
