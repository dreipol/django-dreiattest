from hashlib import sha256
from typing import Optional, Union
from uuid import UUID

from django.core.handlers.wsgi import WSGIRequest


def request_as_dict(request: WSGIRequest) -> dict:
    """ Convert given request to dict so we can check if the signature matches. """
    return {
        'url': request.get_full_path_info(),
        'method': request.method,
    }


def request_hash(request: WSGIRequest) -> sha256:
    """ Convert given request to a hash so we can check if the signature matches. """
    uri = request.build_absolute_uri().encode("utf-8")
    method = request.method.encode("utf-8")
    # TODO: Define headers
    headers = request.headers
    body = request.body
    data = uri + method + body
    return sha256(data)



def is_valid_uuid(uuid: Optional[str] = None, version=4) -> bool:
    if not uuid:
        return False

    try:
        uuid_obj = UUID(uuid, version=version)
    except ValueError:
        return False

    return str(uuid_obj).lower() == uuid.lower()
