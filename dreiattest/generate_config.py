import base64

from pyattest.configs.apple import AppleConfig
from pyattest.configs.google import GoogleConfig
from pyattest.configs.google_play_integrity_api import GooglePlayIntegrityApiConfig

from . import settings as dreiattest_settings


def google_safety_net_config() -> GoogleConfig:
    key_id = base64.b64encode(bytes.fromhex(dreiattest_settings.DREIATTEST_GOOGLE_APK_CERTIFICATE_DIGEST))
    return GoogleConfig(
        key_ids=[key_id],
        apk_package_name=dreiattest_settings.DREIATTEST_GOOGLE_APK_NAME,
        production=dreiattest_settings.DREIATTEST_PRODUCTION
    )


def google_play_integrity_api_config() -> GooglePlayIntegrityApiConfig:
    if dreiattest_settings.DREIATTEST_GOOGLE_APK_CERTIFICATE_DIGEST:
        signatures = [dreiattest_settings.DREIATTEST_GOOGLE_APK_CERTIFICATE_DIGEST]
    else:
        signatures = None
    return GooglePlayIntegrityApiConfig(
        decryption_key=dreiattest_settings.DREIATTEST_GOOGLE_DECRYPTION_KEY,
        verification_key=dreiattest_settings.DREIATTEST_GOOGLE_VERIFICATION_KEY,
        apk_package_name=dreiattest_settings.DREIATTEST_GOOGLE_APK_NAME,
        production=dreiattest_settings.DREIATTEST_PRODUCTION,
        allow_non_play_distribution=dreiattest_settings.DREIATTEST_GOOGLE_ALLOW_NON_PLAY_INSTALLS,
        verify_code_signature_hex=signatures,
        required_device_verdict=dreiattest_settings.DREIATTEST_GOOGLE_REQUIRED_DEVICE_VERDICT
    )


def apple_config(public_key_id: bytes) -> AppleConfig:
    return AppleConfig(
        key_id=base64.b64decode(public_key_id),
        app_id=dreiattest_settings.DREIATTEST_APPLE_APPID,
        production=dreiattest_settings.DREIATTEST_PRODUCTION
    )