from base64 import b64decode
from functools import wraps
from hashlib import sha256

from cryptography.exceptions import InvalidSignature
from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse

from dreiattest.device_session import device_session_from_request
from dreiattest.exceptions import InvalidHeaderException
from dreiattest.helpers import request_hash
from dreiattest.models import Key
from . import settings as dreiattest_settings


def signature_required():
    """ Check that the given request has a valid signature from a known device session. """

    def decorator(func):
        @wraps(func)
        def inner(request: WSGIRequest, *args, **kwargs):
            try:
                session = device_session_from_request(request, create=False)
                public_key = Key.objects.filter(device_session=session).order_by('-id').first()
                if not public_key:
                    raise InvalidHeaderException

                nonce_header = request.META.get(dreiattest_settings.DREIATTEST_NONCE_HEADER).encode("utf-8")
                signature_header = b64decode(request.META.get(dreiattest_settings.DREIATTEST_SIGNATURE_HEADER, ''))

                expected_client_data_hash = request_hash(request).digest()
                client_data_with_nonce = sha256(expected_client_data_hash + nonce_header).digest()

                public_key.verify(signature_header, client_data_with_nonce)
            except InvalidHeaderException as exception:
                return JsonResponse({'error': 'Invalid or missing json payload.'}, status=400)
            except InvalidSignature as exception:
                return JsonResponse({'error': 'Invalid signature.'}, status=403)
            return func(request, *args, **kwargs)

        return inner

    return decorator
