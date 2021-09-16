import base64
from functools import wraps
from hashlib import sha256

from django.core.handlers.wsgi import WSGIRequest
from pyattest.assertion import Assertion
from pyattest.configs.apple import AppleConfig

from dreiattest.device_session import device_session_from_request
from dreiattest.exceptions import InvalidHeaderException, InvalidDriverException
from dreiattest.helpers import request_hash
from dreiattest.models import Key
from . import settings as dreiattest_settings


def verify_assertion(key: Key, nonce: str, assertion: str, expected_hash: bytes):
    expected_hash = sha256(expected_hash.decode() + nonce).digest()

    if key.driver == 'apple':
        pem_key = key.load_pem()
        config = AppleConfig(key_id=base64.b64decode(key.public_key_id),
                             app_id=dreiattest_settings.DREIATTEST_APPLE_APPID,
                             production=dreiattest_settings.DREIATTEST_PRODUCTION)
        assertion = Assertion(base64.b64decode(assertion), expected_hash, pem_key, config)
        assertion.verify()
    else:
        raise InvalidDriverException


def signature_required():
    """ Check that the given request has a valid signature from a known device session. """

    def decorator(func):
        @wraps(func)
        def inner(request: WSGIRequest, *args, **kwargs):
            session = device_session_from_request(request, create=False)
            public_key = Key.objects.filter(device_session=session).order_by('-id').first()
            if not public_key:
                raise InvalidHeaderException

            nonce = request.META.get(dreiattest_settings.DREIATTEST_NONCE_HEADER).encode("utf-8")
            assertion = request.META.get(dreiattest_settings.DREIATTEST_ASSERTION_HEADER, '')
            headers = request.META.get(dreiattest_settings.DREIATTEST_ASSERTION_HEADERS_HEADER, '')
            expected_hash = request_hash(request, headers.split(','))

            verify_assertion(public_key, nonce, assertion, expected_hash)

            return func(request, *args, **kwargs)

        return inner

    return decorator
