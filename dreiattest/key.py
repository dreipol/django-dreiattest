import base64
import json
from hashlib import sha256
from json import JSONDecodeError
from typing import Tuple

from asn1crypto import pem
from django.core.handlers.wsgi import WSGIRequest

from dreiattest.models import Nonce, Key, DeviceSession
from .exceptions import InvalidPayloadException, InvalidDriverException
from pyattest.attestation import Attestation
from pyattest.configs.apple import AppleConfig
from . import settings as dreiattest_settings


def key_from_request(request: WSGIRequest, nonce: Nonce, device_session: DeviceSession) -> Key:
    """
    Get the public key from given request, validate the attestation and either create or update the given key
    for that session.
    """
    try:
        data = json.loads(request.body.decode())
    except JSONDecodeError:
        raise InvalidPayloadException

    driver = drivers.get(data.get('driver', None), None)
    if not driver:
        raise InvalidDriverException

    public_key_id, public_key = driver(data, nonce, device_session)
    key, _ = Key.objects.update_or_create(
        device_session=device_session,
        defaults={'public_key': public_key, 'public_key_id': public_key_id}
    )
    nonce.mark_used()

    return key


def apple(data: dict, nonce, device_session: DeviceSession) -> Tuple[str, str]:
    public_key_id = data.get('key_id', None)  # base64 encoded
    raw_attestation = data.get('attestation', None)  # base64 encoded

    attestation = verify_apple(raw_attestation, public_key_id, nonce, device_session)

    certificate = attestation.data.get('certs')[-1]
    public_key = pem.armor('PUBLIC KEY', certificate.public_key.dump()).decode()

    return public_key_id, public_key


def verify_apple(attestation, key_id: str, nonce: Nonce, device_session: DeviceSession) -> Attestation:
    config = AppleConfig(key_id=base64.b64decode(key_id), app_id=dreiattest_settings.DREIATTEST_APPLE_APPID,
                         production=dreiattest_settings.DREIATTEST_PRODUCTION)

    nonce = (str(device_session) + key_id + nonce.value).encode()

    attestation = Attestation(base64.b64decode(attestation), nonce, config)
    attestation.verify()

    return attestation


def get_key_id(key: str) -> bytes:
    """ Get the sha256 fingerprint of the given base64 encoded public key. """
    return sha256(base64.b64decode(key)).digest()


drivers = {
    'apple': apple
}
