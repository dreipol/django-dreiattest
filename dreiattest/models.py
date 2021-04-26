import base64
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric.ec import ECDSA
from django.db.models import Model, CharField, UUIDField, DateTimeField, ForeignKey, PROTECT, TextField
from cryptography.hazmat.primitives.serialization.base import load_pem_public_key
from cryptography.hazmat._types import _PUBLIC_KEY_TYPES
from cryptography.hazmat.primitives import hashes
from . import settings as dreiattest_settings

from cryptography.hazmat.primitives.asymmetric import (
    dsa,
    ec,
    ed25519,
    ed448,
    rsa,
)
from pyattest.configs.apple import AppleConfig
from pyattest.verifiers.apple import AppleVerifier


class DeviceSession(Model):
    user_id = CharField(max_length=255, null=True)
    session_id = UUIDField(unique=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        index_together = ['user_id', 'session_id']

    def __str__(self):
        session_id = str(self.session_id).upper()
        return f'{self.user_id};{session_id}'


class Nonce(Model):
    value = CharField(max_length=255)
    device_session = ForeignKey(DeviceSession, on_delete=PROTECT)
    used_at = DateTimeField(null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def mark_used(self):
        self.used_at = datetime.now()
        self.save()


class Key(Model):
    device_session = ForeignKey(DeviceSession, on_delete=PROTECT)
    public_key_id = CharField(max_length=255)
    public_key = TextField()
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def load_pem(self) -> _PUBLIC_KEY_TYPES:
        return load_pem_public_key(self.public_key.encode())

    def verify(self, signature_header: bytes, nonce: bytes) -> None:
        pem_key = self.load_pem()

        if isinstance(pem_key, ec.EllipticCurvePublicKey):
            config = AppleConfig(key_id=base64.b64decode(self.public_key_id),
                                 app_id=dreiattest_settings.DREIATTEST_APPLE_APPID,
                                 production=dreiattest_settings.DREIATTEST_PRODUCTION)

            AppleVerifier.verify_assertion(signature_header, nonce, pem_key, config)
