import base64
import json
from functools import wraps
from hashlib import sha256

from pyattest.verifiers.apple import AppleVerifier

from . import settings as dreiattest_settings

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization.base import load_pem_public_key
from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse

from dreiattest.helpers import request_as_dict, request_hash
from dreiattest.models import Key

from dreiattest.exceptions import InvalidHeaderException

from dreiattest.device_session import device_session_from_request
from cbor2 import loads as cbor_decode


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

                # TODO: Use whole URL
                # TODO: Define headers
                expected_client_data = request_hash(request)
                excpected_client_data_hash = sha256(expected_client_data).digest()
                nonce = request.META.get(dreiattest_settings.DREIATTEST_NONCE_HEADER)
                client_data_with_nonce = sha256(excpected_client_data_hash + nonce.encode("utf-8")).digest()

                print(base64.encodestring(excpected_client_data_hash))
                client_header = base64.b64decode(request.META.get(dreiattest_settings.DREIATTEST_SIGNATURE_HEADER, ''))
                unpacked = cbor_decode(client_header)
                authenticator_data =  unpacked["authenticatorData"]

                nonce = sha256(authenticator_data + client_data_with_nonce).digest()

                public_key.verify(unpacked["signature"], nonce)

            except InvalidHeaderException as exception:
                return JsonResponse({'error': 'Invalid or missing json payload.'}, status=400)
            except InvalidSignature as exception:
                return JsonResponse({'error': 'Invalid signature.'}, status=403)
            return func(request, *args, **kwargs)

        return inner

    return decorator
