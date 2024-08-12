import json
from hashlib import sha256
from typing import Optional
from uuid import UUID

from django.core.handlers.wsgi import WSGIRequest


def remove_scheme(uri: str, scheme: str) -> str:
    if uri.startswith(scheme):
        return uri[len(scheme + "://") :]
    return uri


def request_hash(request: WSGIRequest, header_keys: list) -> bytes:
    """Convert given request to a hash. The same hash is done on the client side and signed."""
    uri = remove_scheme(request.build_absolute_uri(), request.scheme).encode()
    method = request.method.encode()
    body = request.body

    headers = {key: request.headers.get(key) for key in filter(None, header_keys)}
    headers_json = json.dumps(
        headers, sort_keys=True, indent=None, separators=(",", ":")
    )

    data = uri + method + headers_json.encode("utf-8") + body

    return sha256(data).digest()


def is_valid_uuid(uuid: Optional[str] = None, version=4) -> bool:
    if not uuid:
        return False

    try:
        uuid_obj = UUID(uuid, version=version)
    except ValueError:
        return False

    return str(uuid_obj).lower() == uuid.lower()
