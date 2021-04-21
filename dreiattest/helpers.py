import json
from hashlib import sha256
from typing import Optional
from uuid import UUID

from django.core.handlers.wsgi import WSGIRequest

from . import settings as dreiattest_settings
from .logging import logger


def request_as_dict(request: WSGIRequest) -> dict:
    """ Convert given request to dict so we can check if the signature matches. """
    return {
        'url': request.get_full_path_info(),
        'method': request.method,
    }


def remove_scheme(uri: str, scheme: str) -> str:
    if uri.startswith(scheme):
        return uri[len(scheme + "://"):]
    return uri


def request_hash(request: WSGIRequest) -> sha256:
    """ Convert given request to a hash so we can check if the signature matches. """
    uri = remove_scheme(request.build_absolute_uri(), request.scheme).encode('utf-8')
    method = request.method.encode('utf-8')
    body = request.body

    header_keys = request.META.get(dreiattest_settings.DREIATTEST_USER_HEADERS, '').split(',')
    headers = {k: request.headers.get(k) for k in header_keys}
    headers_json = json.dumps(headers, sort_keys=True, indent=None, separators=(',', ':'))

    data = uri + method + headers_json.encode('utf-8') + body

    logger.debug(f'Client data: {data}')
    return sha256(data)


def is_valid_uuid(uuid: Optional[str] = None, version=4) -> bool:
    if not uuid:
        return False

    try:
        uuid_obj = UUID(uuid, version=version)
    except ValueError:
        return False

    return str(uuid_obj).lower() == uuid.lower()
