import base64
import json
from hashlib import sha256
from json import JSONDecodeError

from asn1crypto import pem
from django.core.handlers.wsgi import WSGIRequest
from pyattest.configs.google import GoogleConfig

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

    driver = data.get('driver', None)
    if not driver or driver not in ['apple', 'google']:
        raise InvalidDriverException

    public_key_id = data.get('key_id', None)  # base64 encoded
    raw_attestation = data.get('attestation', None)  # base64 encoded

    attestation = create_and_verify_attestation(driver, raw_attestation, public_key_id, nonce, device_session)
    public_key = public_key_from_attestation(attestation)

    key, _ = Key.objects.update_or_create(
        device_session=device_session,
        defaults={'public_key': public_key, 'public_key_id': public_key_id}
    )
    nonce.mark_used()

    return key


def public_key_from_attestation(attestation: Attestation) -> str:
    certificate = attestation.data.get('certs')[-1]
    public_key = pem.armor('PUBLIC KEY', certificate.public_key.dump()).decode()

    return public_key


def create_and_verify_attestation(driver: str, raw_attestation: str, public_key_id: str, nonce: Nonce,
                                  device_session: DeviceSession) -> Attestation:
    if driver == 'apple':
        config = AppleConfig(key_id=base64.b64decode(public_key_id), app_id=dreiattest_settings.DREIATTEST_APPLE_APPID,
                             production=dreiattest_settings.DREIATTEST_PRODUCTION)
    elif driver == 'google':
        config = GoogleConfig(key_ids=[base64.b64decode(public_key_id)],
                              apk_package_name=dreiattest_settings.DREIATTEST_GOOGLE_APK_NAME,
                              production=dreiattest_settings.DREIATTEST_PRODUCTION)
    else:
        raise InvalidDriverException

    nonce = (str(device_session) + public_key_id + nonce.value).encode()

    attestation = Attestation(base64.b64decode(raw_attestation), nonce, config)
    attestation.verify()

    return attestation


def get_key_id(key: str) -> bytes:
    """ Get the sha256 fingerprint of the given base64 encoded public key. """
    return sha256(base64.b64decode(key)).digest()
