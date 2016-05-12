from .base import *

DEBUG = False
ALLOWED_HOSTS = [
    '*'
]
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

FIXTURE_DIRS = (
   os.path.join(BASE_DIR, 'fixtures'),
) #Testuser: username=John, password=Lennon

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'