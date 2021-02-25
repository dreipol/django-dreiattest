from typing import Optional, Union
from uuid import UUID

from django.core.handlers.wsgi import WSGIRequest


def request_as_dict(request: WSGIRequest) -> dict:
    """ Convert given request to dict so we can check if the signature matches. """
    return {
        'url': request.get_full_path_info(),
        'method': request.method,
    }

def is_valid_uuid(uuid: Optional[str] = None, version=4) -> bool:
    if not uuid:
        return False

    try:
        uuid_obj = UUID(uuid, version=version)
    except ValueError:
        return False

    return str(uuid_obj) == uuid


