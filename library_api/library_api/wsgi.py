"""
WSGI config for library_api project.

WSGI (Web Server Gateway Interface) is the Python standard for web server
communication. This file is used by production WSGI servers like Gunicorn.

For development, `manage.py runserver` handles this automatically.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_api.settings')

application = get_wsgi_application()
