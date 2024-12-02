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
from pyattest.configs.config import Config
from pyattest.exceptions import PyAttestException, InvalidAppIdException

from dreiattest import settings as dreiattest_settings
from dreiattest.exceptions import (
    InvalidPayloadException,
    InvalidDriverException,
    UnsupportedEncryptionException,
)
from dreiattest.models import Nonce, Key, DeviceSession
from .generate_config import (
    apple_config,
    google_safety_net_config,
    google_play_integrity_api_config,
)

_dreiattest_app_id_header = dreiattest_settings.DREIATTEST_APPID_HEADER


def resolve_plugins(request: WSGIRequest, attestation: Attestation):
    plugins = []
    for plugin in dreiattest_settings.DREIATTEST_PLUGINS:
        mod = import_string(plugin)
        plugins.append(mod)

    for plugin in plugins:
        plugin().run(request, attestation)


def key_from_request(
    request: WSGIRequest, nonce: Nonce, device_session: DeviceSession
) -> Key:
    """
    Get the public key from given request, validate the attestation and either create or update the given key
    for that session.
    """
    nonce.mark_used()

    try:
        data = json.loads(request.body.decode())
    except JSONDecodeError:
        raise InvalidPayloadException

    app_id = request.META.get(_dreiattest_app_id_header, None)
    driver = data.get("driver", None)
    driver_handler = drivers.get(driver, None)
    if not driver_handler:
        raise InvalidDriverException

    attestation, public_key = driver_handler(app_id, data, device_session, nonce)
    data = {
        "public_key": public_key,
        "public_key_id": get_key_id(public_key),
        "driver": driver,
    }

    resolve_plugins(request, attestation)

    key, _ = Key.objects.update_or_create(device_session=device_session, defaults=data)

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
        public_key_formatted = public_key.public_bytes(
            serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
        )
    elif isinstance(public_key, RSAPublicKey):
        public_key_formatted = public_key.public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.PKCS1
        )
    else:
        raise UnsupportedEncryptionException

    return base64.b64encode(sha256(public_key_formatted).digest()).decode()


def google(
    data: dict, device_session: DeviceSession, nonce: Nonce, configs: list[Config]
) -> Tuple[Attestation, str]:
    attestation = data.get("attestation", None)
    public_key = data.get("public_key", None)  # base64 encoded
    if not attestation or not public_key:
        raise InvalidPayloadException

    nonce = str(device_session) + public_key + nonce.value
    nonce = sha256(nonce.encode()).digest()

    attestation = _verify_with_configs(
        attestation_data=attestation, nonce=nonce, configs=configs
    )

    # For the google driver the public_key_id is actually the base64 encoded public key
    public_key = serialization.load_der_public_key(base64.b64decode(public_key))
    public_key = public_key.public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return attestation, public_key.decode()


def google_safety_net(
    app_id: str, data: dict, device_session: DeviceSession, nonce: Nonce
) -> Tuple[Attestation, str]:
    configs = google_safety_net_config()
    return google(data, device_session, nonce, configs)


def google_play_integrity_api(
    app_id: str, data: dict, device_session: DeviceSession, nonce: Nonce
) -> Tuple[Attestation, str]:
    configs = google_play_integrity_api_config(app_id=app_id)
    return google(data, device_session, nonce, configs)


def apple(
    app_id: str, data: dict, device_session: DeviceSession, nonce: Nonce
) -> Tuple[Attestation, str]:
    attestation = base64.b64decode(data.get("attestation", None))
    public_key_id = data.get("key_id", None)  # base64 encoded
    if not attestation or not public_key_id:
        raise InvalidPayloadException

    configs = apple_config(app_id=app_id, public_key_id=public_key_id)

    nonce = (str(device_session) + public_key_id + nonce.value).encode()
    attestation = _verify_with_configs(
        attestation_data=attestation, nonce=nonce, configs=configs
    )

    certificate = attestation.data.get("certs")[-1]
    public_key = pem.armor("PUBLIC KEY", certificate.public_key.dump()).decode()

    return attestation, public_key


def _verify_with_configs(
    attestation_data, nonce: bytes, configs: list[Config]
) -> Attestation:
    if not configs:
        # If configs is empty that means the user did not configure anything for that app id
        raise InvalidAppIdException

    error_to_raise = None

    for config in configs:
        try:
            attestation = Attestation(attestation_data, nonce, config)
            attestation.verify()
            return attestation

        except PyAttestException as error:
            # If we are unable to verify the attestation we raise the error we got for the first configuration. We
            # expect the user to configure dreiAttest in such a way that the first configuration is appropriate in most
            # cases.
            if error_to_raise is None:
                error_to_raise = error

    raise error_to_raise


drivers = {
    "google": google_safety_net,
    "google_play_integrity_api": google_play_integrity_api,
    "apple": apple,
}
