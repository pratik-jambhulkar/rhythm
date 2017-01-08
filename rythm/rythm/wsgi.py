"""
WSGI config for rythm project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os
import sys

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__),
	'/home/ubuntu/rythm/rythm/rythm/')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__),
	'/home/ubuntu/rythm/rythm/apiapp/')))

from django.core.wsgi import get_wsgi_application

sys.path.insert(1, '/var/www/html')
sys.path.insert(1, '/var/www')
sys.path.insert(1, '/home/ubuntu/rythm/rythm')
sys.path.insert(1, '/home/ubuntu/rythm/apiapp')
sys.path.insert(1, '/home/ubuntu/rythm')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rythm.settings")

application = get_wsgi_application()
