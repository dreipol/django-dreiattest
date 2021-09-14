from types import Union

from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse
from pyattest.exceptions import PyAttestException

from dreiattest.exceptions import DreiAttestException


class HandleDreiattestExceptionsMiddleware(object):
    def process_exception(self, request: WSGIRequest, exception: Exception):
        if isinstance(exception, (PyAttestException, DreiAttestException)):
            return self.handle(request, exception)

    def handle(self, request: WSGIRequest, exception: Exception):
        name = exception.__class__.__name__
        code = name.removesuffix('Exception')

        return JsonResponse(data={'code': code}, status=400)
