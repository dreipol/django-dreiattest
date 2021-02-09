from typing import Optional, Tuple

from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from . import settings as dreiattest_settings

from django.core.handlers.wsgi import WSGIRequest

from .exceptions import InvalidHeaderException
from .helpers import is_valid_uuid
from .models import User


def get_or_create_user(uuid: str, identifier: str, create: bool = True) -> User:
    """ Return matching User model from the db, uuid and identifier need to be validated."""
    if create:
        user, _ = User.objects.get_or_create(identifier=identifier, uuid=uuid)
        return user

    user = User.objects.filter(identifier=identifier, uuid=uuid).first()
    if not user:
        raise InvalidHeaderException

    return user


def user_from_request(request: WSGIRequest, create: bool = True) -> User:
    """ Get the uid from given request. If the data is not present or valid an exception is raised. """
    header = request.META.get(dreiattest_settings.DREIATTEST_UID_HEADER, None)
    if not header:
        raise InvalidHeaderException

    uuid, identifier = parse_header(header)

    return get_or_create_user(uuid, identifier, create)


def parse_header(header: str) -> Optional[Tuple[str, str]]:
    """
    The format is identifier;uuid where the identifier has to be a valid email address and the uuid has
    to be a valid v4 uuid.
    """
    try:
        identifier, uuid = header.split(';')
    except ValueError:
        raise InvalidHeaderException

    if not is_valid_uuid(uuid):
        raise InvalidHeaderException

    if not is_valid_identifier(identifier):
        raise InvalidHeaderException

    return uuid, identifier


def is_valid_identifier(identifier: str) -> bool:
    if identifier == '':
        return True

    try:
        validate_email(identifier)
        return True
    except ValidationError:
        return False
