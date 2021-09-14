#!/usr/bin/env python
import sys

sys.path.append('..')

from django.conf import settings

settings.configure(
    INSTALLED_APPS=['dreiattest'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': 'dreiattest.sqlite'}}
)

import django

django.setup()

from django.core.management import execute_from_command_line

execute_from_command_line(sys.argv)
