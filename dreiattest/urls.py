from . import settings as dreiattest_settings, views

from django.urls import re_path

app_name = 'dreiattest'
urlpatterns = [
    re_path(dreiattest_settings.DREIATTEST_BASE_URL + 'nonce', views.nonce, name='dreiattest.nonce'),
    re_path(dreiattest_settings.DREIATTEST_BASE_URL + 'key', views.key, name='dreiattest.key'),
]
