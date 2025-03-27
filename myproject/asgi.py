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

# 最后导入应用特定的路由
import chat.routing

# 注意不要在ASGI环境中直接使用WhiteNoise
# 获取标准Django ASGI应用
http_application = get_asgi_application()

# ProtocolTypeRouter分派不同类型的连接
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
