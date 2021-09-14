from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse
from pyattest.exceptions import PyAttestException

from dreiattest.exceptions import DreiAttestException


class HandleDreiattestExceptionsMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request: WSGIRequest, exception: Exception):
        if isinstance(exception, (PyAttestException, DreiAttestException)):
            return self.handle(request, exception)

    def handle(self, request: WSGIRequest, exception: Exception):
        code = exception.__class__.__name__
        if code.endswith('Exception'):
            code = code[:-9]

        return JsonResponse(data={'code': code}, status=400)
