from cryptography.exceptions import InvalidSignature, InvalidKey
from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse
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
from dreiattest import settings as dreiattest_settings
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

class HandleDreiattestExceptionsMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request: WSGIRequest, exception: Exception):
        if isinstance(exception, relevant_base):
            return self.handle(request, exception)

    def handle(self, request: WSGIRequest, exception: Exception):
        code = exception.__class__.__name__
        if code.endswith("Exception"):
            code = code[:-9]

        logger.exception("Dreiattest-Exception", exc_info=exception)

        response = JsonResponse(data={"code": code}, status=403)
        response["Dreiattest-error"] = self.get_header(exception)

        return response

    def get_header(self, exception: Exception) -> str:
        """Set some custom headers for the mobile clients."""
        if isinstance(exception, nonce_mismatch):
            return "dreiAttest_nonce_mismatch"

        if isinstance(exception, invalid_key):
            return "dreiAttest_invalid_key"

        return "dreiAttest_policy_violation"
