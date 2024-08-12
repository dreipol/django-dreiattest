#!/usr/bin/env python
import sys
from django.conf import settings
import django
from django.core.management import execute_from_command_line

sys.path.append("..")

settings.configure(
    INSTALLED_APPS=["dreiattest"],
    DATABASES={
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "dreiattest.sqlite"}
    },
    DREIATTEST_GOOGLE_APK_CERTIFICATE_DIGEST="90f283bdab972dab7524b9208de4ef8f",  # dummy value
)

django.setup()

execute_from_command_line(sys.argv)
