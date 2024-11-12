import base64

from pyattest.configs.apple import AppleConfig
from pyattest.configs.google import GoogleConfig
from pyattest.configs.google_play_integrity_api import GooglePlayIntegrityApiConfig

from . import settings as dreiattest_settings


def google_safety_net_config() -> list[GoogleConfig]:
    key_id = base64.b64encode(
        bytes.fromhex(dreiattest_settings.DREIATTEST_GOOGLE_APK_CERTIFICATE_DIGEST)
    )
    return [
        GoogleConfig(
            key_ids=[key_id],
            apk_package_name=dreiattest_settings.DREIATTEST_GOOGLE_APK_NAME,
            production=dreiattest_settings.DREIATTEST_PRODUCTION,
        )
    ]


def google_play_integrity_api_config(app_id: str) -> list[GooglePlayIntegrityApiConfig]:
    if dreiattest_settings.DREIATTEST_PLAY_INTEGRITY_CONFIGS:
        return [
            _generate_play_integrity_config(settings)
            for settings in dreiattest_settings.DREIATTEST_PLAY_INTEGRITY_CONFIGS
            if settings.get("apk_name") == app_id
        ]
    else:
        return [_legacy_generate_play_integrity_config()]


def _generate_play_integrity_config(
    settings: dict[str, any]
) -> GooglePlayIntegrityApiConfig:
    return GooglePlayIntegrityApiConfig(
        decryption_key=settings.get("decryption_key"),
        verification_key=settings.get("verification_key"),
        apk_package_name=settings.get("apk_name"),
        production=dreiattest_settings.DREIATTEST_PRODUCTION,
        allow_non_play_distribution=settings.get("allow_non_play_installs", False),
        verify_code_signature_hex=settings.get("certificate_digest"),
        required_device_verdict=settings.get(
            "required_device_verdict", "MEETS_DEVICE_INTEGRITY"
        ),
    )


def _legacy_generate_play_integrity_config() -> GooglePlayIntegrityApiConfig:
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
        required_device_verdict=dreiattest_settings.DREIATTEST_GOOGLE_REQUIRED_DEVICE_VERDICT,
    )


def apple_config(app_id: str, public_key_id: bytes) -> list[AppleConfig]:
    return [
        _generate_apple_config(app_id=declared_app_id, public_key_id=public_key_id)
        for declared_app_id in dreiattest_settings.DREIATTEST_APPLE_APPID
        if _get_bundle_id(declared_app_id) == app_id
    ]


def _generate_apple_config(app_id: str, public_key_id: bytes) -> AppleConfig:
    return AppleConfig(
        key_id=base64.b64decode(public_key_id),
        app_id=app_id,
        production=dreiattest_settings.DREIATTEST_PRODUCTION,
    )


def _get_bundle_id(app_id: str) -> str:
    return app_id.partition(".")[2]
