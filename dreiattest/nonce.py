import base64
import os
from datetime import timedelta, datetime

from django.core.handlers.wsgi import WSGIRequest

from dreiattest.models import DeviceSession, Nonce
from . import settings as dreiattest_settings
from .exceptions import InvalidHeaderException


def create_nonce(device_session: DeviceSession) -> Nonce:
    value = base64.b64encode(os.urandom(32)).decode()

    nonce = Nonce(device_session=device_session, value=value)
    nonce.save()

    return nonce


def nonce_from_request(request: WSGIRequest, device_session: DeviceSession) -> Nonce:
    """Get the nonce from given request. If the data is not present or valid an exception is raised."""
    header = request.META.get(dreiattest_settings.DREIATTEST_NONCE_HEADER, None)
    if not header:
        raise InvalidHeaderException

    one_minute_ago = datetime.now() - timedelta(minutes=1)
    nonce = Nonce.objects.filter(
        value=header,
        device_session=device_session,
        used_at__isnull=True,
        created_at__gte=one_minute_ago,
    ).first()

    if not nonce:
        raise InvalidHeaderException

    return nonce
