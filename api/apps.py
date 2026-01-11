from django.apps import AppConfig
import sys
import os
import logging
from django.conf import settings


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        # Start the UDP listener automatically when using the development
        # runserver command. We guard with RUN_MAIN to avoid starting the
        # listener twice due to Django's autoreloader.
        try:
            if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') == 'true':

                # Default bind address
                ip = '0.0.0.0'

                # Try to infer the HTTP runserver port from sys.argv (formats: "addr:port" or "port")
                port = None
                for arg in sys.argv[1:]:
                    if arg == 'runserver':
                        continue
                    if ':' in arg:
                        try:
                            port = int(arg.split(':')[-1])
                            break
                        except Exception:
                            continue
                    if arg.isdigit():
                        try:
                            port = int(arg)
                            break
                        except Exception:
                            continue

                # Fallback to a default if not found
                if port is None:
                    port = getattr(settings, 'RUNSERVER_PORT', 8000)

        except Exception:
            logging.getLogger(__name__).exception('Failed to start UDP listener in AppConfig.ready()')

