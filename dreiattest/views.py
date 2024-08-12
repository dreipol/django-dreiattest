from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from dreiattest.device_session import device_session_from_request
from dreiattest.key import key_from_request
from dreiattest.nonce import create_nonce, nonce_from_request


@require_http_methods(["GET"])
def nonce(request: WSGIRequest):
    """
    Request a nonce to create the attestation on the device. The Dreiattest-Uid header needs to be set
    with a valid device session id. The server will persist the nonce and persist it with the given uid.
    """
    device_session = device_session_from_request(request)
    nonce = create_nonce(device_session)

    return JsonResponse(nonce.value, safe=False)


@require_http_methods(["POST"])
@csrf_exempt
def key(request: WSGIRequest):
    """Store a public key belonging to a user in the database. Upcoming requests can be signed with said key."""
    device_session = device_session_from_request(request, create=False)
    nonce = nonce_from_request(request, device_session)
    public_key = key_from_request(request, nonce, device_session)

    return JsonResponse({"success": True, "key_id": public_key.public_key_id})
