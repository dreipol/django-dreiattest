from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from pyattest.exceptions import PyAttestException

from dreiattest.exceptions import InvalidHeaderException, InvalidPayloadException
from dreiattest.key import key_from_request
from dreiattest.nonce import create_nonce, nonce_from_request
from dreiattest.device_session import device_session_from_request


@require_http_methods(['GET'])
def nonce(request: WSGIRequest):
    """
    Request a nonce to create the attestation on the device. The Dreiattest-Uid header needs to be set
    with a valid  user id. The server will persist the nonce and persist it with the given uid.
    """
    try:
        user = device_session_from_request(request)
    except InvalidHeaderException:
        return JsonResponse({'error': 'Invalid or missing Dreiattest-Uid header.'})

    nonce = create_nonce(user)

    return JsonResponse({'nonce': nonce.value})


@require_http_methods(['POST'])
@csrf_exempt
def key(request: WSGIRequest):
    """ Store a public key belonging to a user in the database. Upcoming requests can be signed with said key. """
    try:
        user = device_session_from_request(request, create=False)
        nonce = nonce_from_request(request, user)
        public_key = key_from_request(request, nonce, user)
    except InvalidHeaderException as exception:
        return JsonResponse({'error': 'Invalid or missing Dreiattest-Uid or Dreiattest-Nonce header.'}, status=400)
    except InvalidPayloadException as exception:
        return JsonResponse({'error': 'Invalid or missing json payload.'}, status=400)
    except (TypeError, PyAttestException) as exception:
        return JsonResponse({'error': 'Could not verify given attestation.'}, status=422)

    return JsonResponse({'success': True})
