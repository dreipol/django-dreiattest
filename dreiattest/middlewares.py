from cryptography.exceptions import InvalidSignature, InvalidKey
from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse
from ninja import NinjaAPI
from pyattest.exceptions import (
    PyAttestException,
    InvalidNonceException,
    InvalidCertificateChainException,
    InvalidKeyIdException,
    ExtensionNotFoundException,
)

from dreiattest.exceptions import (
    DreiAttestException,
    UnsupportedEncryptionException,
    NoKeyForSessionException,
)
import logging



relevant_base = (PyAttestException, DreiAttestException, InvalidSignature, InvalidKey)
nonce_mismatch = (InvalidNonceException,)
invalid_key = (
    InvalidCertificateChainException,
    InvalidKeyIdException,
    UnsupportedEncryptionException,
    ExtensionNotFoundException,
    InvalidSignature,
    InvalidKey,
    NoKeyForSessionException,
)

logger = logging.getLogger("dreiattest")


def get_header(exception: Exception) -> str:
    """Set some custom headers for the mobile clients."""
    if isinstance(exception, nonce_mismatch):
        return "dreiAttest_nonce_mismatch"

    if isinstance(exception, invalid_key):
        return "dreiAttest_invalid_key"

    return "dreiAttest_policy_violation"


def process_exception(request: WSGIRequest, exception: Exception):
    code = exception.__class__.__name__
    if code.endswith("Exception"):
        code = code[:-9]

    logger.exception("Dreiattest-Exception", exc_info=exception)

    response = JsonResponse(data={"code": code}, status=403)
    response["Dreiattest-error"] = get_header(exception)

    return response


class HandleDreiattestExceptionsMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except Exception as e:
            if isinstance(e, relevant_base):
                response = process_exception(request, e)
            else:
                raise e

        return response


def register_exception_handlers(api: NinjaAPI):
    for exception_class in relevant_base:
        api.add_exception_handler(exception_class, process_exception)
