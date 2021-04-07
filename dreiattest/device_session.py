from typing import Optional, Tuple
from uuid import UUID

from . import settings as dreiattest_settings

from django.core.handlers.wsgi import WSGIRequest

from .exceptions import InvalidHeaderException
from .helpers import is_valid_uuid
from .models import DeviceSession


def get_or_create_device_session(user_id: str, session_id: UUID, create: bool = True) -> DeviceSession:
    """ Return matching DeviceSession model from the db, user_id and session_id need to be validated."""
    if create:
        session, _ = DeviceSession.objects.get_or_create(session_id=session_id, user_id=user_id)
        return session

    session = DeviceSession.objects.filter(session_id=session_id, user_id=user_id).first()
    if not session:
        raise InvalidHeaderException

    return session


def device_session_from_request(request: WSGIRequest, create: bool = True) -> DeviceSession:
    """ Get the uid from given request. If the data is not present or valid an exception is raised. """
    header = request.META.get(dreiattest_settings.DREIATTEST_UID_HEADER, None)
    if not header:
        raise InvalidHeaderException

    user_id, session_id = parse_header(header)

    return get_or_create_device_session(user_id, session_id, create)


def parse_header(header: str) -> Optional[Tuple[str, UUID]]:
    """
    The format is user_id;session_id where the identifier has to be a string with maxlength 128 and the
    session_id has to be a valid v4 uuid.
    """
    try:
        user_id, session_id = header.split(';')
    except ValueError:
        raise InvalidHeaderException

    if not is_valid_uuid(session_id):
        raise InvalidHeaderException

    if not is_valid_user_id(user_id):
        raise InvalidHeaderException

    return user_id, UUID(session_id)


def is_valid_user_id(user_id: str) -> bool:
    if user_id == '':
        return True

    if len(user_id) > 128:
        return False

    return True
