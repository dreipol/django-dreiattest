import base64
import json
from json import JSONDecodeError
from typing import Tuple

from asn1crypto import pem
from django.core.handlers.wsgi import WSGIRequest
from pyattest.configs.config import Config
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
    if not driver or driver not in drivers.keys():
        raise InvalidDriverException

    attestation, public_key_id = create_and_verify_attestation(driver, data, nonce, device_session)
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


def create_and_verify_attestation(driver: str, data: dict, nonce: Nonce,
                                  device_session: DeviceSession) -> Tuple[Attestation, str]:
    driver = drivers.get(driver)
    attestation, public_key_id, config = driver(data)

    nonce = (str(device_session) + public_key_id + nonce.value).encode()

    attestation = Attestation(attestation, nonce, config)
    attestation.verify()

    return attestation, public_key_id


def google(data: dict) -> Tuple[str, str, Config]:
    attestation = data.get('attestation', None)
    public_key_id = data.get('public_key', None)  # base64 encoded
    if not attestation or not public_key_id:
        raise InvalidPayloadException

    config = GoogleConfig(key_ids=[base64.b64decode(public_key_id)],
                          apk_package_name=dreiattest_settings.DREIATTEST_GOOGLE_APK_NAME,
                          production=dreiattest_settings.DREIATTEST_PRODUCTION)

    return attestation, public_key_id, config


def apple(data: dict) -> Tuple[bytes, str, Config]:
    attestation = base64.b64decode(data.get('attestation', None))
    public_key_id = data.get('key_id', None)  # base64 encoded
    if not attestation or not public_key_id:
        raise InvalidPayloadException

    config = AppleConfig(key_id=base64.b64decode(public_key_id), app_id=dreiattest_settings.DREIATTEST_APPLE_APPID,
                         production=dreiattest_settings.DREIATTEST_PRODUCTION)

    return attestation, public_key_id, config


drivers = {
    'google': google,
    'apple': apple,
}
