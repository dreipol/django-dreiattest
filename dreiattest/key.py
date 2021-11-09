import base64
import json
from hashlib import sha256
from json import JSONDecodeError
from typing import Tuple

from asn1crypto import pem
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from django.core.handlers.wsgi import WSGIRequest
from django.utils.module_loading import import_string
from pyattest.attestation import Attestation
from pyattest.configs.apple import AppleConfig
from pyattest.configs.google import GoogleConfig

from dreiattest.models import Nonce, Key, DeviceSession
from dreiattest import settings as dreiattest_settings
from dreiattest.exceptions import InvalidPayloadException, InvalidDriverException, UnsupportedEncryptionException


def resolve_plugins(request: WSGIRequest, attestation: Attestation):
    plugins = []
    for plugin in dreiattest_settings.DREIATTEST_PLUGINS:
        mod = import_string(plugin)
        plugins.append(mod)

    for plugin in plugins:
        plugin().run(request, attestation)


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
    driver_handler = drivers.get(driver, None)
    if not driver_handler:
        raise InvalidDriverException

    attestation, public_key = driver_handler(data, device_session, nonce)
    data = {
        'public_key': public_key,
        'public_key_id': get_key_id(public_key),
        'driver': driver
    }

    resolve_plugins(request, attestation)

    key, _ = Key.objects.update_or_create(device_session=device_session, defaults=data)
    nonce.mark_used()

    return key


def get_key_id(pem_public_key: str) -> str:
    """
    Get the sha256 of a given pem formatted public key. Apple does this by serialising the key with X962 and
    UncompressedPoint, so we do the same for google -> since key requests with the google driver don't
    contain a public_key_id but only the full public_key. We also have support for RSA keys, mainly because
    we use them in the unit tests.
    """
    public_key = serialization.load_pem_public_key(pem_public_key.encode())
    if isinstance(public_key, EllipticCurvePublicKey):
        public_key_formatted = public_key.public_bytes(serialization.Encoding.X962,
                                                       serialization.PublicFormat.UncompressedPoint)
    elif isinstance(public_key, RSAPublicKey):
        public_key_formatted = public_key.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.PKCS1)
    else:
        raise UnsupportedEncryptionException

    return base64.b64encode(sha256(public_key_formatted).digest()).decode()


def google(data: dict, device_session: DeviceSession, nonce: Nonce) -> Tuple[Attestation, str]:
    attestation = data.get('attestation', None)
    public_key = data.get('public_key', None)  # base64 encoded
    if not attestation or not public_key:
        raise InvalidPayloadException

    key_id = base64.b64encode(bytes.fromhex(dreiattest_settings.DREIATTEST_GOOGLE_APK_CERTIFICATE_DIGEST))
    config = GoogleConfig(key_ids=[key_id],
                          apk_package_name=dreiattest_settings.DREIATTEST_GOOGLE_APK_NAME,
                          production=dreiattest_settings.DREIATTEST_PRODUCTION)

    nonce = (str(device_session) + public_key + nonce.value)
    nonce = sha256(nonce.encode()).digest()

    attestation = Attestation(attestation, nonce, config)
    attestation.verify()

    # For the google driver the public_key_id is actually the base64 encoded public key
    public_key = serialization.load_der_public_key(base64.b64decode(public_key))
    public_key = public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)

    return attestation, public_key.decode()


def apple(data: dict, device_session: DeviceSession, nonce: Nonce) -> Tuple[Attestation, str]:
    attestation = base64.b64decode(data.get('attestation', None))
    public_key_id = data.get('key_id', None)  # base64 encoded
    if not attestation or not public_key_id:
        raise InvalidPayloadException

    config = AppleConfig(key_id=base64.b64decode(public_key_id), app_id=dreiattest_settings.DREIATTEST_APPLE_APPID,
                         production=dreiattest_settings.DREIATTEST_PRODUCTION)

    nonce = (str(device_session) + public_key_id + nonce.value).encode()

    attestation = Attestation(attestation, nonce, config)
    attestation.verify()

    certificate = attestation.data.get('certs')[-1]
    public_key = pem.armor('PUBLIC KEY', certificate.public_key.dump()).decode()

    return attestation, public_key


drivers = {
    'google': google,
    'apple': apple,
}
