#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks.

Common commands:
  python manage.py runserver          — Start development server
  python manage.py migrate            — Apply database migrations
  python manage.py makemigrations     — Create new migrations from model changes
  python manage.py createsuperuser    — Create an admin user
  python manage.py shell              — Open Django interactive shell
"""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_api.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
