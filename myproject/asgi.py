"""
ASGI config for myproject project.
"""

import os
import django
from pathlib import Path

# 首先设置Django环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# 然后初始化Django
django.setup()

# 之后导入其他依赖项
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.conf import settings
from whitenoise.middleware import WhiteNoiseMiddleware

# 最后导入应用特定的路由
import chat.routing

# WhiteNoise ASGI应用配置
from whitenoise import WhiteNoise
http_application = get_asgi_application()
http_application = WhiteNoise(http_application)
http_application.add_files(os.path.join(settings.BASE_DIR, 'staticfiles'), prefix='static/')
http_application.add_files(settings.MEDIA_ROOT, prefix='media/')

application = ProtocolTypeRouter({
    "http": http_application,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                chat.routing.websocket_urlpatterns
            )
        )
    ),
})
