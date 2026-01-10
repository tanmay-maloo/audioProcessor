"""
WSGI config for audio_processor project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
from pathlib import Path

from django.core.wsgi import get_wsgi_application

# Load environment variables from a .env file (if present) so secrets like
# ASSEMBLYAI_API_KEY are available to the WSGI process before Django loads.
try:
	from dotenv import load_dotenv
	# Look for a .env in the project root (one level up from this file)
	project_root = Path(__file__).resolve().parent.parent
	env_path = project_root / '.env'
	if env_path.exists():
		load_dotenv(dotenv_path=str(env_path))
	else:
		# Attempt a generic load (will look in cwd / parent dirs)
		load_dotenv()
except Exception:
	# If python-dotenv isn't installed, don't crash the WSGI import — the
	# environment may already provide the key. The webserver logs will show
	# import issues if needed.
	pass

# Ensure Django settings module is set
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'audio_processor.settings')

application = get_wsgi_application()

