import base64
import json
from functools import wraps
from . import settings as dreiattest_settings

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization.base import load_pem_public_key
from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse

from dreiattest.helpers import request_as_dict
from dreiattest.models import Key

from dreiattest.exceptions import InvalidHeaderException

from dreiattest.device_session import device_session_from_request


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

                request_dict = request_as_dict(request)
                public_key = load_pem_public_key(public_key.public_key.encode())
                public_key.verify(
                    base64.b64decode(request.META.get(dreiattest_settings.DREIATTEST_SIGNATURE_HEADER, '')),
                    json.dumps(request_dict).encode(),
                    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                    hashes.SHA256()
                )
            except InvalidHeaderException as exception:
                return JsonResponse({'error': 'Invalid or missing json payload.'}, status=400)
            except InvalidSignature as exception:
                return JsonResponse({'error': 'Invalid signature.'}, status=403)
            return func(request, *args, **kwargs)

        return inner

    return decorator
