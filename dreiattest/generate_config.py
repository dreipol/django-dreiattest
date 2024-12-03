import base64

from pyattest.configs.apple import AppleConfig
from pyattest.configs.google import GoogleConfig
from pyattest.configs.google_play_integrity_api import GooglePlayIntegrityApiConfig

from . import settings as dreiattest_settings


def google_safety_net_config() -> list[GoogleConfig]:
    key_id = base64.b64encode(
        bytes.fromhex(dreiattest_settings.__DREIATTEST_GOOGLE_APK_CERTIFICATE_DIGEST)
    )
    return [
        GoogleConfig(
            key_ids=[key_id],
            apk_package_name=dreiattest_settings.__DREIATTEST_GOOGLE_APK_NAME,
            production=dreiattest_settings.DREIATTEST_PRODUCTION,
        )
    ]


def google_play_integrity_api_config(app_id: str) -> list[GooglePlayIntegrityApiConfig]:
    return [
        _generate_play_integrity_config(settings)
        for settings in dreiattest_settings.DREIATTEST_PLAY_INTEGRITY_CONFIGS
        if settings.get("apk_name") == app_id
    ]


def _generate_play_integrity_config(
    settings: dict[str, any]
) -> GooglePlayIntegrityApiConfig:
    if settings.get("certificate_digest"):
        signatures = [settings.get("certificate_digest")]
    else:
        signatures = None

    return GooglePlayIntegrityApiConfig(
        decryption_key=settings.get("decryption_key"),
        verification_key=settings.get("verification_key"),
        apk_package_name=settings.get("apk_name"),
        production=dreiattest_settings.DREIATTEST_PRODUCTION,
        allow_non_play_distribution=settings.get("allow_non_play_installs", False),
        verify_code_signature_hex=signatures,
        required_device_verdict=settings.get(
            "required_device_verdict", "MEETS_DEVICE_INTEGRITY"
        ),
    )


def apple_config(app_id: str, public_key_id: str) -> list[AppleConfig]:
    return [
        _generate_apple_config(app_id=declared_app_id, public_key_id=public_key_id)
        for declared_app_id in dreiattest_settings.DREIATTEST_APPLE_APPIDS
        if _get_bundle_id(declared_app_id) == app_id
    ]


def _generate_apple_config(app_id: str, public_key_id: str) -> AppleConfig:
    return AppleConfig(
        key_id=base64.b64decode(public_key_id),
        app_id=app_id,
        production=dreiattest_settings.DREIATTEST_PRODUCTION,
    )


def _get_bundle_id(app_id: str) -> str:
    return app_id.partition(".")[2]
