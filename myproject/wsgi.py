"""
WSGI config for myproject project.
"""

import os
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

application = get_wsgi_application()
application = WhiteNoise(application)
application.add_files(os.path.join(settings.BASE_DIR, 'staticfiles'), prefix='static/')
application.add_files(settings.MEDIA_ROOT, prefix='media/')
