"""
WSGI config for myproject project.
"""

import os
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise
from django.conf import settings
import pathlib

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# 获取标准WSGI应用
base_application = get_wsgi_application()

# 配置WhiteNoise，添加媒体文件支持
application = WhiteNoise(base_application)
application.add_files(str(pathlib.Path(settings.STATIC_ROOT)), prefix='static/')
application.add_files(str(pathlib.Path(settings.MEDIA_ROOT)), prefix='media/')
