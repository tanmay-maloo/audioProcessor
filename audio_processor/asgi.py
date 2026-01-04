"""
ASGI config for audio_processor project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'audio_processor.settings')

# Use Channels' ProtocolTypeRouter so WebSocket connections can be handled
try:
	from channels.routing import ProtocolTypeRouter, URLRouter
	import api.routing

	application = ProtocolTypeRouter({
		"http": get_asgi_application(),
		"websocket": URLRouter(api.routing.websocket_urlpatterns),
	})
except Exception:
	# Fallback to plain ASGI app if channels isn't available
	application = get_asgi_application()

